from django.core.exceptions import ValidationError
from django.db import transaction

from .models import FormulaTemplate, FormulaTerm, MarketFormula, RevisionGroup


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
    return formula
