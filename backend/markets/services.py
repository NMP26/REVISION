from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    FormulaTemplate, FormulaTerm, Market, MarketFormula, PriceItem, PriceSchedule,
    MonthlyIndexValue, RevisionGroup,
)


def resolve_index(index_code, year, month):
    """Resolve one exact code/month. There is intentionally no month fallback."""
    value = MonthlyIndexValue.objects.select_related("index_definition", "publication").filter(
        index_definition__code=index_code,
        year=year,
        month=month,
    ).first()
    if value is None:
        return {"status": "INDEX_NOT_AVAILABLE", "code": index_code, "index_code": index_code, "year": year, "month": month, "base_year": year, "base_month": month, "value": None, "publication": None, "source_type": None, "source_reference": None}
    return {
        "status": value.status,
        "code": value.index_definition.code,
        "index_code": value.index_definition.code,
        "designation": value.index_definition.designation,
        "domain": value.index_definition.domain,
        "year": value.year,
        "month": value.month,
        "value": str(value.value),
        "base_year": value.year,
        "base_month": value.month,
        "publication": value.publication.document_reference,
        "source_type": value.publication.source_type,
        "source_reference": value.source_reference or value.source_document or value.publication.document_reference,
        "source": {
            "publication_id": str(value.publication_id),
            "document_reference": value.publication.document_reference,
            "source_type": value.publication.source_type,
            "source_reference": value.source_reference or value.source_document or value.publication.document_reference,
            "source_url": value.source_url or value.publication.source_url or None,
            "publication_date": value.publication.publication_date,
        },
    }


def resolve_base_index(market, formula=None):
    """Resolve the V1 base index from the offer deadline and formula term."""
    if formula is None:
        group = market.global_revision_group
        formula = group.formulas.exclude(status="INACTIVE").order_by("-version_number").first() if group else None
    term = formula.terms.order_by("position").first() if formula else None
    if market.date_limite_remise_offres is None:
        return {"index_code": term.index_code if term else None, "base_year": None, "base_month": None, "value": None, "status": "DATE_MISSING", "publication": None, "source_type": None, "source_reference": None, "base_index_code": term.index_code if term else None, "base_index_value": None, "base_index_status": "DATE_MISSING", "base_index_source": None}
    base_month = market.date_limite_remise_offres
    resolved = resolve_index(term.index_code, base_month.year, base_month.month) if term else {"status": "INDEX_NOT_AVAILABLE"}
    source = resolved.get("source")
    return {
        "index_code": term.index_code if term else None,
        "base_year": base_month.year,
        "base_month_number": base_month.month,
        "value": resolved.get("value"),
        "status": resolved.get("status", "INDEX_NOT_AVAILABLE"),
        "publication": resolved.get("publication"),
        "source_type": resolved.get("source_type"),
        "source_reference": resolved.get("source_reference"),
        "base_month": base_month.strftime("%Y-%m"),
        "base_index_code": term.index_code if term else None,
        "base_index_value": resolved.get("value"),
        "base_index_status": resolved.get("status", "INDEX_NOT_AVAILABLE"),
        "base_index_source": source.get("document_reference") if source else None,
        "base_index_publication": source,
    }


def resolve_v1_base_index(*, market, formula):
    return resolve_base_index(market, formula)


def activate_v1_formula(*, formula):
    """Select one formula for a SINGLE market while preserving prior versions.

    This is deliberately scoped to the V1 simple journey.  MULTIPLE markets
    keep their existing group/formula lifecycle for the future LOT 2B flow.
    """
    market = Market.objects.select_for_update().get(pk=formula.revision_group.market_id)
    if market.formula_structure != Market.FormulaStructure.SINGLE:
        return formula

    active_formulas = MarketFormula.objects.select_for_update().filter(
        revision_group__market_id=market.pk,
    ).exclude(status=MarketFormula.Status.INACTIVE).exclude(pk=formula.pk)
    for previous in active_formulas:
        previous.status = MarketFormula.Status.INACTIVE
        previous.save(update_fields=["status", "updated_at"])

    market.revision_application_mode = Market.RevisionApplicationMode.GLOBAL_FORMULA
    market.global_revision_group_id = formula.revision_group_id
    market.save(update_fields=["revision_application_mode", "global_revision_group", "updated_at"])
    return formula


@transaction.atomic
def copy_formula_template(*, template_id, revision_group_id, user):
    """Create an independent DRAFT formula from one verified GLOBAL template."""
    template = FormulaTemplate.objects.select_for_update().prefetch_related("terms").filter(
        id=template_id,
        scope=FormulaTemplate.Scope.GLOBAL,
        status=FormulaTemplate.Status.VERIFIED,
    ).first()
    if template is None:
        raise ValidationError({"template_id": "Ce template GLOBAL n'est pas disponible pour une copie."})

    group = RevisionGroup.objects.select_for_update().select_related("market").filter(id=revision_group_id).first()
    if group is None:
        raise ValidationError({"revision_group": "Groupe de révision introuvable."})

    market = Market.objects.select_for_update().get(pk=group.market_id)
    if market.formula_structure == Market.FormulaStructure.SINGLE:
        existing = MarketFormula.objects.select_for_update().filter(
            revision_group__market_id=market.pk,
            source_template_id=template.pk,
        ).exclude(status=MarketFormula.Status.INACTIVE).order_by("-version_number").first()
        if existing is not None:
            return activate_v1_formula(formula=existing)

    last_version = group.formulas.order_by("-version_number").values_list("version_number", flat=True).first()
    formula = MarketFormula.objects.create(
        revision_group=group,
        source_template=template,
        source_template_version=template.version_number,
        version_number=(last_version or 0) + 1,
        label=template.designation,
        expression_display=template.expression_display,
        constant_term=template.constant_term,
        status=MarketFormula.Status.DRAFT,
        valid_from=template.valid_from,
        valid_to=template.valid_to,
        reference_source=template.source_reference,
        created_by=user,
    )
    for term in template.terms.all():
        FormulaTerm.objects.create(
            formula=formula,
            position=term.position,
            coefficient=term.coefficient,
            term_type=term.term_type,
            index_code=term.index_code,
            base_period_year=term.base_period_year,
            base_period_month=term.base_period_month,
            base_value=term.base_value,
            base_source=term.base_source,
            reference_note=term.reference_note,
        )
    return activate_v1_formula(formula=formula)


@transaction.atomic
def set_revision_application(*, market_id, mode, global_revision_group_id=None, expected_updated_at=None):
    market = Market.objects.select_for_update().get(pk=market_id)
    if expected_updated_at is not None and market.updated_at != expected_updated_at:
        raise ValidationError({"expected_updated_at": "La configuration du marché a changé. Rechargez la page."})
    if mode not in Market.RevisionApplicationMode.values:
        raise ValidationError({"revision_application_mode": "Le mode d'application est invalide."})

    group = None
    if mode == Market.RevisionApplicationMode.GLOBAL_FORMULA:
        if not global_revision_group_id:
            raise ValidationError({"global_revision_group": "Une formule globale doit être sélectionnée."})
        group = market.revision_groups.select_for_update().filter(pk=global_revision_group_id, active=True).first()
        if group is None:
            raise ValidationError({"global_revision_group": "La formule globale doit appartenir au marché."})
        available_formula_count = group.formulas.exclude(status=MarketFormula.Status.INACTIVE).count()
        if available_formula_count != 1:
            raise ValidationError({"global_revision_group": "Le mode global exige une seule formule active ou en brouillon dans le groupe sélectionné."})
        if PriceItem.objects.filter(price_schedule__market=market).exists():
            raise ValidationError({"revision_application_mode": "Le passage en formule globale est refusé tant que des données BDP existent. Aucune donnée n'a été supprimée."})
    else:
        if global_revision_group_id is not None:
            raise ValidationError({"global_revision_group": "Le mode d'affectation par prix ne prend pas de formule globale."})

    market.revision_application_mode = mode
    market.global_revision_group = group
    market.save(update_fields=["revision_application_mode", "global_revision_group", "updated_at"])
    return market


@transaction.atomic
def create_price_schedule(*, market, validated_data):
    schedule, created = PriceSchedule.objects.get_or_create(market=market, defaults=validated_data)
    if not created:
        raise ValidationError({"price_schedule": "Un bordereau existe déjà pour ce marché."})
    return schedule


@transaction.atomic
def create_price_item(*, schedule, validated_data):
    item = PriceItem(price_schedule=schedule, **validated_data)
    item.full_clean()
    item.save(force_insert=True)
    schedule.change_version += 1
    schedule.save(update_fields=["change_version", "updated_at"])
    return item


@transaction.atomic
def update_price_item(*, item, validated_data):
    locked = PriceItem.objects.select_for_update().get(pk=item.pk)
    schedule = PriceSchedule.objects.select_for_update().get(pk=locked.price_schedule_id)
    for field, value in validated_data.items():
        setattr(locked, field, value)
    locked.save()
    schedule.change_version += 1
    schedule.save(update_fields=["change_version", "updated_at"])
    return locked


@transaction.atomic
def bulk_assign_price_items(*, market, action, revision_group_id=None, price_item_ids=None, filters=None, expected_version=None):
    schedule = PriceSchedule.objects.select_for_update().filter(market=market).first()
    if schedule is None:
        raise ValidationError({"price_schedule": "Un bordereau est nécessaire pour une affectation par prix."})
    if expected_version is not None and schedule.change_version != expected_version:
        raise ValidationError({"expected_version": "Le bordereau a changé. Rechargez la matrice."})
    action = str(action or "").upper()
    if action == "VALIDATE":
        return validate_price_assignment(market=market, schedule=schedule)
    if action not in {"ASSIGN", "UNASSIGN", "NON_REVISABLE"}:
        raise ValidationError({"action": "L'action doit être ASSIGN, UNASSIGN, NON_REVISABLE ou VALIDATE."})

    group = None
    if action == "ASSIGN":
        group = market.revision_groups.select_for_update().filter(pk=revision_group_id, active=True).first()
        if group is None:
            raise ValidationError({"revision_group_id": "La formule doit appartenir au marché et être active."})

    if price_item_ids is not None:
        requested_ids = {str(item_id) for item_id in price_item_ids}
        existing_ids = {str(item_id) for item_id in PriceItem.objects.filter(id__in=requested_ids, price_schedule=schedule).values_list("id", flat=True)}
        if existing_ids != requested_ids:
            raise ValidationError({"price_item_ids": "Tous les prix sélectionnés doivent appartenir au bordereau de ce marché."})

    items = PriceItem.objects.select_for_update().filter(price_schedule=schedule)
    if price_item_ids is not None:
        items = items.filter(id__in=price_item_ids)
    filters = filters or {}
    if filters.get("price_number"):
        items = items.filter(price_number__icontains=filters["price_number"])
    if filters.get("designation"):
        items = items.filter(designation__icontains=filters["designation"])
    if filters.get("lot_id"):
        items = items.filter(lot_id=filters["lot_id"])
    if filters.get("classification_status"):
        items = items.filter(classification_status=filters["classification_status"])
    if filters.get("revision_group_id"):
        items = items.filter(revision_group_id=filters["revision_group_id"])
    selected = list(items)
    if not selected:
        return {"updated": 0, "change_version": schedule.change_version}

    if action == "ASSIGN":
        conflicting = [item.price_number for item in selected if item.revision_group_id and item.revision_group_id != group.id]
        if conflicting:
            raise ValidationError({"price_items": f"Les prix {', '.join(conflicting)} sont déjà affectés à une autre formule."})

    for item in selected:
        if action == "ASSIGN":
            if item.classification_status == PriceItem.ClassificationStatus.NON_REVISABLE:
                raise ValidationError({"price_items": "Un prix NON_REVISABLE doit être reclassé explicitement avant affectation."})
            item.revision_group = group
            item.classification_status = PriceItem.ClassificationStatus.REVISABLE
        elif action == "UNASSIGN":
            item.revision_group = None
            if item.classification_status == PriceItem.ClassificationStatus.REVISABLE:
                item.classification_status = PriceItem.ClassificationStatus.PENDING_CLASSIFICATION
        else:
            item.revision_group = None
            item.classification_status = PriceItem.ClassificationStatus.NON_REVISABLE
        item.save()
    schedule.change_version += 1
    schedule.save(update_fields=["change_version", "updated_at"])
    return {"updated": len(selected), "change_version": schedule.change_version}


def validate_price_assignment(*, market, schedule=None):
    schedule = schedule or PriceSchedule.objects.filter(market=market).first()
    if schedule is None:
        raise ValidationError({"price_schedule": "Un bordereau est nécessaire pour valider l'affectation."})

    items = list(schedule.items.select_related("revision_group").all())
    if not items:
        raise ValidationError({"price_items": "Le bordereau doit contenir au moins un prix."})

    pending = [item.price_number for item in items if item.classification_status == PriceItem.ClassificationStatus.PENDING_CLASSIFICATION]
    unassigned = [item.price_number for item in items if item.classification_status == PriceItem.ClassificationStatus.REVISABLE and item.revision_group_id is None]
    if pending or unassigned:
        labels = pending + unassigned
        raise ValidationError({"price_items": f"Les prix suivants restent à classer ou à affecter : {', '.join(labels)}."})

    invalid_groups = [item.price_number for item in items if item.classification_status == PriceItem.ClassificationStatus.REVISABLE and (item.revision_group is None or not item.revision_group.active or not item.revision_group.formulas.exclude(status=MarketFormula.Status.INACTIVE).exists())]
    if invalid_groups:
        raise ValidationError({"price_items": f"Les prix suivants sont liés à une formule indisponible : {', '.join(invalid_groups)}."})

    return {"validated": True, "price_count": len(items), "change_version": schedule.change_version}
