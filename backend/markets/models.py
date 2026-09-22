import uuid
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.deletion import ProtectedError

from companies.models import Company


class FormulaQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Les formules doivent être modifiées par leur service métier.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("Les formules ne peuvent pas être modifiées en bulk.")

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False, update_conflicts=False, update_fields=None, unique_fields=None):
        raise ValidationError("Les formules doivent être créées par leur service métier.")

    def delete(self):
        raise ProtectedError("Une formule ne peut pas être supprimée physiquement.", self)


class FormulaTermQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Les termes doivent être modifiés par leur service métier.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("Les termes ne peuvent pas être modifiés en bulk.")

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False, update_conflicts=False, update_fields=None, unique_fields=None):
        raise ValidationError("Les termes doivent être créés unitairement par leur service métier.")

    def delete(self):
        if self.filter(formula__status=MarketFormula.Status.VALIDATED).exists():
            raise ProtectedError("Les termes d'une formule validée sont immuables.", self)
        return super().delete()


class FormulaTemplateQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Les templates doivent être modifiés par leur service de curation.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("Les templates ne peuvent pas être modifiés en bulk.")

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False, update_conflicts=False, update_fields=None, unique_fields=None):
        if any(obj.status == FormulaTemplate.Status.VERIFIED for obj in objs):
            raise ValidationError("Une version VERIFIED doit être publiée par le service de curation.")
        return super().bulk_create(
            objs,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts,
            update_fields=update_fields,
            unique_fields=unique_fields,
        )

    def delete(self):
        if self.filter(status=FormulaTemplate.Status.VERIFIED).exists() or self.filter(market_copies__isnull=False).exists():
            raise ProtectedError("Un template vérifié ou utilisé ne peut pas être supprimé.", self)
        return super().delete()


class FormulaTemplateTermQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Les termes de templates doivent être modifiés par le service de curation.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("Les termes de templates ne peuvent pas être modifiés en bulk.")

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False, update_conflicts=False, update_fields=None, unique_fields=None):
        template_ids = {obj.template_id for obj in objs if obj.template_id}
        if FormulaTemplate.objects.filter(id__in=template_ids, status=FormulaTemplate.Status.VERIFIED).exists():
            raise ValidationError("Les termes d'un template VERIFIED sont immuables.")
        return super().bulk_create(
            objs,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts,
            update_fields=update_fields,
            unique_fields=unique_fields,
        )

    def delete(self):
        if self.filter(template__status=FormulaTemplate.Status.VERIFIED).exists():
            raise ProtectedError("Les termes d'un template VERIFIED sont immuables.", self)
        return super().delete()


class Market(models.Model):
    class HolderType(models.TextChoices):
        SOLE_COMPANY = "SOLE_COMPANY", "Société"
        CONSORTIUM = "CONSORTIUM", "Groupement"
    class FormulaStructure(models.TextChoices):
        SINGLE = "SINGLE", "Formule unique"
        MULTIPLE = "MULTIPLE", "Formules multiples"

    class RevisionApplicationMode(models.TextChoices):
        GLOBAL_FORMULA = "GLOBAL_FORMULA", "Une seule formule pour l'ensemble du marché"
        PRICE_ASSIGNMENT = "PRICE_ASSIGNMENT", "Affectation des formules prix par prix"

    class DurationUnit(models.TextChoices):
        DAYS = "DAYS", "Jours"
        MONTHS = "MONTHS", "Mois"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archivée"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="markets")
    holder_type = models.CharField(max_length=20, choices=HolderType.choices, default=HolderType.SOLE_COMPANY)
    holder_company = models.ForeignKey(Company, on_delete=models.PROTECT, null=True, blank=True, related_name="held_markets")
    consortium = models.ForeignKey("consortia.Consortium", on_delete=models.PROTECT, null=True, blank=True, related_name="markets")
    authority = models.ForeignKey("authorities.ContractingAuthority", on_delete=models.PROTECT, null=True, blank=True, related_name="markets")
    market_number = models.CharField(max_length=120)
    contracting_authority = models.CharField(max_length=255)
    subject = models.TextField()
    amount_ht = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    vat_rate = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    date_limite_remise_offres = models.DateField(null=True, blank=True)
    date_ouverture_plis = models.DateField(null=True, blank=True)
    date_signature = models.DateField(null=True, blank=True)
    date_os_commencement = models.DateField(null=True, blank=True)
    contract_duration_value = models.PositiveIntegerField(null=True, blank=True)
    contract_duration_unit = models.CharField(
        max_length=10,
        choices=DurationUnit.choices,
        null=True,
        blank=True,
    )
    formula_structure = models.CharField(
        max_length=10,
        choices=FormulaStructure.choices,
    )
    revision_application_mode = models.CharField(
        max_length=30,
        choices=RevisionApplicationMode.choices,
        default=RevisionApplicationMode.PRICE_ASSIGNMENT,
    )
    global_revision_group = models.ForeignKey(
        "RevisionGroup",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="global_markets",
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "markets_market"
        constraints = [
            models.UniqueConstraint(fields=["company", "market_number"], name="uniq_market_company_number"),
            models.CheckConstraint(
                condition=(models.Q(consortium__isnull=True, holder_company__isnull=False, holder_type="SOLE_COMPANY") | models.Q(consortium__isnull=False, holder_company__isnull=True, holder_type="CONSORTIUM")),
                name="market_holder_exactly_one",
            ),
            models.CheckConstraint(
                condition=models.Q(amount_ht__gte=0) | models.Q(amount_ht__isnull=True),
                name="market_amount_ht_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(vat_rate__gte=0, vat_rate__lte=100) | models.Q(vat_rate__isnull=True),
                name="market_vat_rate_range",
            ),
            models.CheckConstraint(
                condition=models.Q(contract_duration_value__isnull=True, contract_duration_unit__isnull=True)
                | models.Q(contract_duration_value__isnull=False, contract_duration_unit__isnull=False),
                name="market_duration_pair",
            ),
            models.CheckConstraint(
                condition=models.Q(contract_duration_value__isnull=True)
                | models.Q(contract_duration_value__gt=0),
                name="market_duration_value_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(contract_duration_unit__isnull=True)
                | models.Q(contract_duration_unit__in=["DAYS", "MONTHS"]),
                name="market_duration_unit_allowed",
            ),
            models.CheckConstraint(
                condition=models.Q(market_number__regex=r"\S"),
                name="market_number_not_blank",
            ),
            models.CheckConstraint(
                condition=models.Q(contracting_authority__regex=r"\S"),
                name="market_contracting_authority_not_blank",
            ),
            models.CheckConstraint(
                condition=models.Q(subject__regex=r"\S"),
                name="market_subject_not_blank",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(revision_application_mode="GLOBAL_FORMULA", global_revision_group__isnull=False)
                    | models.Q(revision_application_mode="PRICE_ASSIGNMENT", global_revision_group__isnull=True)
                ),
                name="market_revision_mode_group_consistent",
            ),
        ]
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["market_number"]),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}
        if self.vat_rate is not None and not Decimal("0") <= self.vat_rate <= Decimal("100"):
            errors["vat_rate"] = "Le taux de TVA doit être compris entre 0 et 100 %."
        if (self.contract_duration_value is None) != (self.contract_duration_unit is None):
            errors["contract_duration_value"] = "La valeur et l'unité du délai doivent être renseignées ensemble."
        if self.contract_duration_value is not None and self.contract_duration_value <= 0:
            errors["contract_duration_value"] = "La valeur du délai doit être strictement positive."
        if self.holder_type == self.HolderType.SOLE_COMPANY and self.holder_company_id is None:
            errors["holder_company"] = "La société titulaire est obligatoire."
        if self.holder_type == self.HolderType.CONSORTIUM and self.consortium_id is None:
            errors["consortium"] = "Le groupement titulaire est obligatoire."
        if self.holder_type == self.HolderType.SOLE_COMPANY and self.consortium_id is not None:
            errors["consortium"] = "Une société titulaire ne peut pas avoir de groupement."
        if self.holder_type == self.HolderType.CONSORTIUM and self.holder_company_id is not None:
            errors["holder_company"] = "Un groupement titulaire ne peut pas avoir de société titulaire directe."
        if self.revision_application_mode not in self.RevisionApplicationMode.values:
            errors["revision_application_mode"] = "Le mode d'application de la révision est invalide."
        if self.revision_application_mode == self.RevisionApplicationMode.GLOBAL_FORMULA and self.global_revision_group_id is None:
            errors["global_revision_group"] = "Une formule globale doit être sélectionnée."
        if self.revision_application_mode == self.RevisionApplicationMode.PRICE_ASSIGNMENT and self.global_revision_group_id is not None:
            errors["global_revision_group"] = "Un marché en affectation par prix ne peut pas avoir de formule globale."
        if self.global_revision_group_id is not None:
            group_market_id = RevisionGroup.objects.filter(pk=self.global_revision_group_id).values_list("market_id", flat=True).first()
            if group_market_id is not None and group_market_id != self.pk:
                errors["global_revision_group"] = "La formule globale doit appartenir au même marché."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.holder_type == self.HolderType.SOLE_COMPANY and self.holder_company_id is None:
            self.holder_company_id = self.company_id
        super().save(*args, **kwargs)

    def __str__(self):
        return self.market_number


class Statement(models.Model):
    """Simple V1 statement envelope; detailed BDP lines belong to future lots."""

    class AllocationMethod(models.TextChoices):
        ACTUAL_EXECUTION = "ACTUAL_EXECUTION", "Jours d'exécution saisis"
        CALENDAR_DAY_PRORATA = "CALENDAR_DAY_PRORATA", "Prorata de jours calendaires"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    market = models.ForeignKey(Market, on_delete=models.PROTECT, related_name="statements")
    number = models.PositiveIntegerField()
    date = models.DateField()
    amount_ht = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    observation = models.TextField(blank=True)
    allocation_method = models.CharField(max_length=32, choices=AllocationMethod.choices, default=AllocationMethod.ACTUAL_EXECUTION)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "markets_statement"
        ordering = ["number"]
        constraints = [models.UniqueConstraint(fields=["market", "number"], name="uniq_statement_market_number")]

    def clean(self):
        errors = {}
        if self.number <= 0:
            errors["number"] = "Le numéro du décompte doit être strictement positif."
        if self.amount_ht < Decimal("0"):
            errors["amount_ht"] = "Le montant HT ne peut pas être négatif."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class MonthlyWorkAllocation(models.Model):
    """User-entered execution days retained even when the value is zero."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    statement = models.ForeignKey(Statement, on_delete=models.CASCADE, related_name="monthly_allocations")
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    work_days = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "markets_monthlyworkallocation"
        ordering = ["year", "month"]
        constraints = [models.UniqueConstraint(fields=["statement", "year", "month"], name="uniq_work_allocation_statement_month")]

    def clean(self):
        errors = {}
        if self.work_days < Decimal("0"):
            errors["work_days"] = "Le nombre de jours ne peut pas être négatif."
        if not 1 <= self.month <= 12:
            errors["month"] = "Le mois doit être compris entre 1 et 12."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class MarketLot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="lots")
    lot_number = models.CharField(max_length=120)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amount_ht = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    display_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "markets_marketlot"
        ordering = ["display_order", "lot_number"]
        constraints = [
            models.UniqueConstraint(fields=["market", "lot_number"], name="uniq_marketlot_market_number"),
            models.CheckConstraint(
                condition=models.Q(amount_ht__gte=0) | models.Q(amount_ht__isnull=True),
                name="marketlot_amount_ht_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(lot_number__regex=r"\S"),
                name="marketlot_number_not_blank",
            ),
            models.CheckConstraint(
                condition=models.Q(title__regex=r"\S"),
                name="marketlot_title_not_blank",
            ),
        ]
        indexes = [
            models.Index(fields=["market", "display_order", "lot_number"]),
        ]

    def __str__(self):
        return f"{self.market.market_number} — {self.lot_number}"


class PriceScheduleQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):
        raise ProtectedError("Un bordereau ne peut pas être supprimé physiquement.", self)


class PriceItemQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Les prix doivent être modifiés par leur service métier.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("Les prix ne peuvent pas être modifiés en bulk.")

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False, update_conflicts=False, update_fields=None, unique_fields=None):
        raise ValidationError("Les prix doivent être créés par leur service métier.")

    def delete(self, *args, **kwargs):
        raise ProtectedError("Un prix ne peut pas être supprimé physiquement.", self)


class PriceSchedule(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        ACTIVE = "ACTIVE", "Actif"
        ARCHIVED = "ARCHIVED", "Archivé"

    class SourceType(models.TextChoices):
        MANUAL = "MANUAL", "Saisie manuelle"
        IMPORT = "IMPORT", "Import"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    market = models.OneToOneField(Market, on_delete=models.PROTECT, related_name="price_schedule")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.MANUAL)
    name = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    change_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = PriceScheduleQuerySet.as_manager()

    class Meta:
        db_table = "markets_priceschedule"
        constraints = [
            models.CheckConstraint(condition=models.Q(change_version__gt=0), name="priceschedule_change_version_positive"),
        ]

    def delete(self, *args, **kwargs):
        raise ProtectedError("Un bordereau ne peut pas être supprimé physiquement.", self)


class PriceItem(models.Model):
    class ClassificationStatus(models.TextChoices):
        PENDING_CLASSIFICATION = "PENDING_CLASSIFICATION", "À classer"
        REVISABLE = "REVISABLE", "Révisable"
        NON_REVISABLE = "NON_REVISABLE", "Sans révision"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    price_schedule = models.ForeignKey(PriceSchedule, on_delete=models.PROTECT, related_name="items")
    lot = models.ForeignKey(MarketLot, on_delete=models.PROTECT, null=True, blank=True, related_name="price_items")
    price_number = models.CharField(max_length=120)
    designation = models.TextField()
    unit = models.CharField(max_length=80)
    estimated_quantity = models.DecimalField(max_digits=18, decimal_places=6, validators=[MinValueValidator(Decimal("0"))])
    unit_price_ht = models.DecimalField(max_digits=18, decimal_places=8, validators=[MinValueValidator(Decimal("0"))])
    estimated_amount_ht = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    revision_group = models.ForeignKey("RevisionGroup", on_delete=models.PROTECT, null=True, blank=True, related_name="price_items")
    classification_status = models.CharField(max_length=30, choices=ClassificationStatus.choices, default=ClassificationStatus.PENDING_CLASSIFICATION)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = PriceItemQuerySet.as_manager()

    class Meta:
        db_table = "markets_priceitem"
        ordering = ["price_number", "id"]
        constraints = [
            models.UniqueConstraint(fields=["price_schedule", "price_number"], name="uniq_priceitem_schedule_number"),
            models.CheckConstraint(condition=models.Q(price_number__regex=r"\S"), name="priceitem_number_not_blank"),
            models.CheckConstraint(condition=models.Q(designation__regex=r"\S"), name="priceitem_designation_not_blank"),
            models.CheckConstraint(condition=models.Q(unit__regex=r"\S"), name="priceitem_unit_not_blank"),
            models.CheckConstraint(condition=models.Q(estimated_quantity__gte=0), name="priceitem_quantity_nonnegative"),
            models.CheckConstraint(condition=models.Q(unit_price_ht__gte=0), name="priceitem_unit_price_nonnegative"),
            models.CheckConstraint(condition=models.Q(estimated_amount_ht__gte=0), name="priceitem_amount_nonnegative"),
            models.CheckConstraint(
                condition=(models.Q(classification_status="REVISABLE", revision_group__isnull=False) | models.Q(classification_status__in=["PENDING_CLASSIFICATION", "NON_REVISABLE"], revision_group__isnull=True)),
                name="priceitem_classification_assignment_consistent",
            ),
        ]
        indexes = [
            models.Index(fields=["price_schedule", "classification_status"]),
            models.Index(fields=["price_schedule", "revision_group"]),
            models.Index(fields=["lot", "active"]),
        ]

    def clean(self):
        errors = {}
        if self.pk:
            previous_schedule_id = type(self).objects.filter(pk=self.pk).values_list("price_schedule_id", flat=True).first()
            if previous_schedule_id is not None and previous_schedule_id != self.price_schedule_id:
                errors["price_schedule"] = "Le bordereau d'un prix est immuable."
        self.price_number = self.price_number.strip()
        self.designation = self.designation.strip()
        self.unit = self.unit.strip()
        if not self.price_number:
            errors["price_number"] = "Le numéro de prix est obligatoire."
        if not self.designation:
            errors["designation"] = "La désignation est obligatoire."
        if not self.unit:
            errors["unit"] = "L'unité est obligatoire."
        if self.classification_status == self.ClassificationStatus.REVISABLE and self.revision_group_id is None:
            errors["revision_group"] = "Un prix révisable doit être affecté à une formule."
        if self.classification_status != self.ClassificationStatus.REVISABLE and self.revision_group_id is not None:
            errors["revision_group"] = "Un prix non classé ou sans révision ne peut pas être affecté à une formule."
        market_id = self.price_schedule.market_id if self.price_schedule_id and hasattr(self, "price_schedule") else PriceSchedule.objects.filter(pk=self.price_schedule_id).values_list("market_id", flat=True).first()
        if self.lot_id is not None:
            lot_market_id = MarketLot.objects.filter(pk=self.lot_id).values_list("market_id", flat=True).first()
            if lot_market_id is not None and market_id is not None and lot_market_id != market_id:
                errors["lot"] = "Le lot doit appartenir au même marché que le prix."
        if self.revision_group_id is not None:
            group_market_id = RevisionGroup.objects.filter(pk=self.revision_group_id).values_list("market_id", flat=True).first()
            if group_market_id is not None and market_id is not None and group_market_id != market_id:
                errors["revision_group"] = "La formule doit appartenir au même marché que le prix."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ProtectedError("Un prix ne peut pas être supprimé physiquement.", self)


class RevisionGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    market = models.ForeignKey(Market, on_delete=models.PROTECT, related_name="revision_groups")
    code = models.CharField(max_length=80)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "markets_revisiongroup"
        ordering = ["sort_order", "code"]
        constraints = [
            models.UniqueConstraint(fields=["market", "code"], name="uniq_revisiongroup_market_code"),
            models.CheckConstraint(condition=models.Q(code__regex=r"\S"), name="revisiongroup_code_not_blank"),
            models.CheckConstraint(condition=models.Q(name__regex=r"\S"), name="revisiongroup_name_not_blank"),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        self.code = self.code.strip()
        self.name = self.name.strip()
        if not self.code:
            raise ValidationError({"code": "Le code du groupe est obligatoire."})
        if not self.name:
            raise ValidationError({"name": "Le nom du groupe est obligatoire."})

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            previous_market_id = type(self).objects.only("market_id").get(pk=self.pk).market_id
            if previous_market_id != self.market_id:
                raise ValidationError("Le marché d'un groupe de révision est immuable.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.market.market_number} — {self.name}"


class IndexDefinition(models.Model):
    """Stable definition of an official index code."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=120, unique=True)
    designation = models.CharField(max_length=255)
    domain = models.CharField(max_length=120, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "markets_indexdefinition"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.designation}"


class IndexPublication(models.Model):
    class SourceType(models.TextChoices):
        OFFICIAL = "OFFICIAL", "Officielle"
        EXTERNAL_SECONDARY = "EXTERNAL_SECONDARY", "Source externe secondaire"
        MANUAL_VALIDATED = "MANUAL_VALIDATED", "Validation manuelle"

    class Status(models.TextChoices):
        IMPORTED = "IMPORTED", "Importée"
        VALIDATED = "VALIDATED", "Validée"
        PENDING_VALIDATION = "PENDING_VALIDATION", "Validation en attente"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    publication_date = models.DateField(null=True, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    document_reference = models.CharField(max_length=255)
    document_hash = models.CharField(max_length=64, blank=True)
    source_type = models.CharField(max_length=32, choices=SourceType.choices, default=SourceType.OFFICIAL)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.IMPORTED)
    imported_at = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "markets_indexpublication"
        ordering = ["-year", "-month"]
        constraints = [models.UniqueConstraint(fields=["year", "month", "source_type"], name="uniq_indexpublication_period_source")]

    def __str__(self):
        return f"{self.year:04d}-{self.month:02d} — {self.document_reference}"


class MonthlyIndexValue(models.Model):
    class Status(models.TextChoices):
        DEFINITIVE = "DEFINITIVE", "Définitive"
        PROVISIONAL = "PROVISIONAL", "Provisoire"
        PENDING_VALIDATION = "PENDING_VALIDATION", "Validation en attente"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    index_definition = models.ForeignKey(IndexDefinition, on_delete=models.PROTECT, related_name="monthly_values")
    publication = models.ForeignKey(IndexPublication, on_delete=models.PROTECT, related_name="values")
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    value = models.DecimalField(max_digits=18, decimal_places=8)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING_VALIDATION)
    source_url = models.URLField(max_length=500, blank=True)
    source_document = models.CharField(max_length=255, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    source_reference = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "markets_monthlyindexvalue"
        ordering = ["-year", "-month", "index_definition__code"]
        constraints = [
            models.UniqueConstraint(fields=["index_definition", "year", "month"], name="uniq_monthlyindex_definition_month"),
            models.CheckConstraint(condition=models.Q(value__gt=0), name="monthlyindexvalue_positive"),
        ]
        indexes = [models.Index(fields=["index_definition", "year", "month", "status"], name="monthlyindex_lookup_idx")]

    def clean(self):
        if self.publication_id and (self.year != self.publication.year or self.month != self.publication.month):
            errors = {"publication": "La publication source doit correspondre au même mois que la valeur."}
        else:
            errors = {}
        if not 1 <= self.month <= 12:
            errors["month"] = "Le mois doit être compris entre 1 et 12."
        if self.value <= 0:
            errors["value"] = "La valeur de l’index doit être strictement positive."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class IndexSourceDocument(models.Model):
    """Immutable audit metadata for a source PDF kept outside the repository."""

    class ExtractionMethod(models.TextChoices):
        NATIVE_TEXT = "NATIVE_TEXT", "Texte natif"
        TABLE_EXTRACTION = "TABLE_EXTRACTION", "Extraction de tableau"
        OCR = "OCR", "OCR"
        MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED", "Revue manuelle requise"

    class ExtractionStatus(models.TextChoices):
        PROCESSED = "PROCESSED", "Traité"
        PENDING_VALIDATION = "PENDING_VALIDATION", "Validation en attente"
        ERROR = "ERROR", "Erreur"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sha256 = models.CharField(max_length=64, unique=True)
    original_filename = models.CharField(max_length=255)
    nominal_year = models.PositiveSmallIntegerField(null=True, blank=True)
    nominal_month = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    file_size = models.BigIntegerField()
    page_count = models.PositiveIntegerField(null=True, blank=True)
    detected_periods = models.JSONField(default=list)
    source_reference = models.CharField(max_length=1000)
    source_url = models.URLField(max_length=500, blank=True)
    extraction_method = models.CharField(max_length=32, choices=ExtractionMethod.choices)
    extraction_status = models.CharField(max_length=32, choices=ExtractionStatus.choices)
    retrieved_at = models.DateTimeField(auto_now_add=True, null=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "markets_indexsourcedocument"
        ordering = ["original_filename"]


class RawIndexExtraction(models.Model):
    """Reviewable intermediate row; never bypasses normalization/validation."""

    class Method(models.TextChoices):
        NATIVE_TEXT = "NATIVE_TEXT", "Texte natif"
        TABLE_EXTRACTION = "TABLE_EXTRACTION", "Extraction de tableau"
        OCR = "OCR", "OCR"
        MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED", "Revue manuelle requise"

    source_document = models.ForeignKey(IndexSourceDocument, on_delete=models.PROTECT, related_name="raw_extractions")
    page_number = models.PositiveIntegerField(null=True, blank=True)
    raw_code = models.CharField(max_length=120, blank=True)
    raw_designation = models.TextField(blank=True)
    raw_value = models.CharField(max_length=120, blank=True)
    source_column = models.CharField(max_length=40, blank=True)
    raw_status = models.CharField(max_length=40, blank=True)
    extraction_method = models.CharField(max_length=32, choices=Method.choices)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    ambiguity = models.TextField(blank=True)
    normalized_code = models.CharField(max_length=120, blank=True)
    normalized_value = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    validation_status = models.CharField(max_length=32, default="PENDING_VALIDATION")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "markets_rawindexextraction"
        indexes = [models.Index(fields=["source_document", "page_number"], name="raw_index_doc_page_idx")]


class OfficialExtractedValue(models.Model):
    """A reviewable value extracted from an official document, before promotion."""

    class Status(models.TextChoices):
        EXTRACTED = "EXTRACTED", "Extraite"
        PENDING_VALIDATION = "PENDING_VALIDATION", "Validation en attente"
        VALIDATED = "VALIDATED", "Validée"
        CONFLICT = "CONFLICT", "Conflit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    publication = models.ForeignKey(IndexPublication, on_delete=models.PROTECT, related_name="official_values")
    source_document = models.ForeignKey(IndexSourceDocument, on_delete=models.PROTECT, related_name="official_values")
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    raw_code = models.CharField(max_length=120)
    raw_designation = models.TextField(blank=True)
    normalized_code = models.CharField(max_length=120, blank=True)
    raw_value = models.CharField(max_length=120)
    normalized_value = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING_VALIDATION)
    extraction_method = models.CharField(max_length=32)
    page_number = models.PositiveIntegerField(null=True, blank=True)
    source_reference = models.CharField(max_length=1000, blank=True)
    ambiguity = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "markets_officialextractedvalue"
        constraints = [models.UniqueConstraint(fields=["source_document", "year", "month", "normalized_code"], name="uniq_official_extracted_document_period_code")]
        indexes = [models.Index(fields=["year", "month", "normalized_code"], name="official_value_period_code_idx")]


class IndexValidationComparison(models.Model):
    """Persisted triple comparison between official, API and local values."""

    class Status(models.TextChoices):
        ALL_MATCH = "ALL_MATCH", "Toutes les sources concordent"
        OFFICIAL_API_MATCH_LOCAL_MISSING = "OFFICIAL_API_MATCH_LOCAL_MISSING", "Officiel/API concordants, local absent"
        OFFICIAL_LOCAL_MATCH_API_CONFLICT = "OFFICIAL_LOCAL_MATCH_API_CONFLICT", "Officiel/local concordants, API en conflit"
        OFFICIAL_API_CONFLICT = "OFFICIAL_API_CONFLICT", "Officiel/API en conflit"
        OFFICIAL_LOCAL_CONFLICT = "OFFICIAL_LOCAL_CONFLICT", "Officiel/local en conflit"
        LOCAL_MISSING = "LOCAL_MISSING", "Local absent"
        API_MISSING = "API_MISSING", "API absente"
        PENDING_VALIDATION = "PENDING_VALIDATION", "Validation en attente"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    official_value = models.ForeignKey(OfficialExtractedValue, on_delete=models.PROTECT, related_name="comparisons")
    index_definition = models.ForeignKey(IndexDefinition, on_delete=models.PROTECT, null=True, blank=True, related_name="validation_comparisons")
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    api_value = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    local_value = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    status = models.CharField(max_length=48, choices=Status.choices)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "markets_indexvalidationcomparison"
        constraints = [models.UniqueConstraint(fields=["official_value", "index_definition"], name="uniq_index_validation_comparison")]


class IndexValidationAudit(models.Model):
    """Append-only audit trail for a controlled official validation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    monthly_value = models.ForeignKey(MonthlyIndexValue, on_delete=models.PROTECT, related_name="validation_audits")
    value_before = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    status_before = models.CharField(max_length=30, blank=True)
    value_after = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    status_after = models.CharField(max_length=30)
    publication = models.ForeignKey(IndexPublication, on_delete=models.PROTECT, related_name="validation_audits")
    document_hash = models.CharField(max_length=64, blank=True)
    method = models.CharField(max_length=64)
    actor = models.ForeignKey("accounts.User", on_delete=models.PROTECT, null=True, blank=True, related_name="index_validation_audits")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "markets_indexvalidationaudit"
        ordering = ["created_at"]


class ExternalIndexStaging(models.Model):
    """Candidate data received from an external index provider."""

    class ComparisonStatus(models.TextChoices):
        NEW = "NEW", "Nouveau"
        MATCHED = "MATCHED", "Correspondant"
        CONFLICT = "CONFLICT", "Conflit"
        MISSING_LOCAL = "MISSING_LOCAL", "Absent du référentiel local"
        MISSING_SOURCE = "MISSING_SOURCE", "Absent de la source"
        LOCAL_ONLY = "LOCAL_ONLY", "Présent uniquement en local"
        DESIGNATION_CONFLICT = "DESIGNATION_CONFLICT", "Conflit de désignation"
        INVALID = "INVALID", "Invalide"

    class ValidationStatus(models.TextChoices):
        PENDING_VALIDATION = "PENDING_VALIDATION", "Validation en attente"
        VALIDATED = "VALIDATED", "Validé"
        INVALID = "INVALID", "Invalide"

    SOURCE_PROVIDER = "revisiondesprix.ma"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_provider = models.CharField(max_length=120, default=SOURCE_PROVIDER)
    source_endpoint = models.CharField(max_length=500)
    retrieved_at = models.DateTimeField()
    external_code = models.CharField(max_length=120)
    external_designation = models.CharField(max_length=255, null=True, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    month = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    raw_value = models.CharField(max_length=120, blank=True)
    normalized_value = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    raw_payload_hash = models.CharField(max_length=64)
    previous_raw_value = models.CharField(max_length=120, blank=True)
    previous_normalized_value = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    previous_raw_payload_hash = models.CharField(max_length=64, blank=True)
    source_changed = models.BooleanField(default=False)
    comparison_status = models.CharField(max_length=32, choices=ComparisonStatus.choices, default=ComparisonStatus.NEW)
    validation_status = models.CharField(max_length=32, choices=ValidationStatus.choices, default=ValidationStatus.PENDING_VALIDATION)
    matched_index_definition = models.ForeignKey(IndexDefinition, on_delete=models.PROTECT, null=True, blank=True, related_name="external_staging_rows")
    local_value = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    pdf_value = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    pdf_comparison_status = models.CharField(max_length=32, default="PDF_NOT_CHECKED")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "markets_externalindexstaging"
        ordering = ["-retrieved_at", "external_code", "year", "month"]
        constraints = [models.UniqueConstraint(fields=["source_provider", "source_endpoint", "external_code", "year", "month"], name="uniq_external_index_stage_source_period", nulls_distinct=False)]
        indexes = [
            models.Index(fields=["year", "month", "external_code"], name="external_stage_period_code_idx"),
            models.Index(fields=["comparison_status"], name="external_stage_comparison_idx"),
        ]

    def clean(self):
        errors = {}
        if bool(self.year) != bool(self.month):
            errors["month"] = "L'année et le mois doivent être fournis ensemble."
        if self.normalized_value is not None and self.normalized_value <= 0:
            errors["normalized_value"] = "La valeur normalisée doit être strictement positive."
        if self.local_value is not None and self.local_value <= 0:
            errors["local_value"] = "La valeur locale doit être strictement positive."
        if self.pdf_value is not None and self.pdf_value <= 0:
            errors["pdf_value"] = "La valeur PDF doit être strictement positive."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class FormulaTemplate(models.Model):
    class Scope(models.TextChoices):
        GLOBAL = "GLOBAL", "Global"
        COMPANY = "COMPANY", "Société"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        VERIFIED = "VERIFIED", "Vérifié"
        DEPRECATED = "DEPRECATED", "Déprécié"

    class SourceType(models.TextChoices):
        OFFICIAL = "OFFICIAL", "Officielle"
        CONTRACT_EXAMPLE = "CONTRACT_EXAMPLE", "Exemple contractuel"
        INTERNAL = "INTERNAL", "Interne"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family_key = models.UUIDField(default=uuid.uuid4)
    version_number = models.PositiveIntegerField()
    scope = models.CharField(max_length=20, choices=Scope.choices, default=Scope.GLOBAL)
    owner_company = models.ForeignKey(Company, on_delete=models.PROTECT, null=True, blank=True, related_name="formula_templates")
    code = models.CharField(max_length=120)
    designation = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    domain = models.CharField(max_length=120, blank=True)
    expression_display = models.CharField(max_length=500, blank=True)
    constant_term = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    source_title = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    source_reference = models.CharField(max_length=255, blank=True)
    source_date = models.DateField(null=True, blank=True)
    verification_status = models.CharField(max_length=80, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, null=True, blank=True, related_name="verified_formula_templates")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = FormulaTemplateQuerySet.as_manager()

    class Meta:
        db_table = "markets_formulatemplate"
        ordering = ["code", "version_number"]
        constraints = [
            models.UniqueConstraint(fields=["family_key", "version_number"], name="uniq_formulatemplate_family_version"),
            models.CheckConstraint(condition=models.Q(version_number__gt=0), name="formulatemplate_version_positive"),
            models.CheckConstraint(condition=models.Q(scope="GLOBAL", owner_company__isnull=True) | models.Q(scope="COMPANY", owner_company__isnull=False), name="formulatemplate_scope_owner_consistent"),
            models.CheckConstraint(condition=models.Q(valid_to__isnull=True) | models.Q(valid_from__isnull=True) | models.Q(valid_to__gte=models.F("valid_from")), name="formulatemplate_valid_dates_order"),
        ]
        indexes = [
            models.Index(fields=["scope", "status", "code"], name="template_scope_status_code_idx"),
            models.Index(fields=["family_key", "version_number"], name="template_family_version_idx"),
        ]

    def clean(self):
        errors = {}
        self.code = self.code.strip()
        self.designation = self.designation.strip()
        if not self.code:
            errors["code"] = "Le code du template est obligatoire."
        if not self.designation:
            errors["designation"] = "La désignation du template est obligatoire."
        if self.scope == self.Scope.GLOBAL and self.owner_company_id is not None:
            errors["owner_company"] = "Un template GLOBAL ne peut pas avoir de société propriétaire."
        if self.scope == self.Scope.COMPANY and self.owner_company_id is None:
            errors["owner_company"] = "Un template COMPANY doit avoir une société propriétaire."
        if self.status == self.Status.VERIFIED and (not self.source_title.strip() or not self.source_reference.strip()):
            errors["status"] = "Un template VERIFIED doit avoir une source et une référence documentaire."
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            errors["valid_to"] = "La fin de validité doit être postérieure ou égale au début."
        if self.constant_term is not None and not isinstance(self.constant_term, Decimal):
            errors["constant_term"] = "La constante doit être une valeur Decimal."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.constant_term is not None and not isinstance(self.constant_term, Decimal):
            raise ValidationError("La constante doit être une valeur Decimal.")
        if self.status == self.Status.VERIFIED and self.verified_at is None:
            from django.utils import timezone
            self.verified_at = timezone.now()
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            previous = type(self).objects.only("family_key", "version_number", "scope", "owner_company_id", "status").get(pk=self.pk)
            if previous.family_key != self.family_key or previous.version_number != self.version_number:
                raise ValidationError("L'identité et la version d'un template sont immuables.")
            if previous.status == self.Status.VERIFIED:
                changed_fields = {
                    field.name for field in self._meta.concrete_fields
                    if field.name not in {"updated_at", "status", "verified_at", "verified_by"}
                    and getattr(previous, field.name) != getattr(self, field.name)
                }
                if changed_fields or self.status not in {self.Status.VERIFIED, self.Status.DEPRECATED}:
                    raise ValidationError("Une version VERIFIED est immuable.")
            if previous.status == self.Status.DEPRECATED and self.status != self.Status.DEPRECATED:
                raise ValidationError("Un template DEPRECATED ne peut pas être réactivé.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status == self.Status.VERIFIED or self.market_copies.exists():
            raise ProtectedError("Un template vérifié ou utilisé ne peut pas être supprimé.", self)
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.designation} v{self.version_number}"


class FormulaTemplateTerm(models.Model):
    class TermType(models.TextChoices):
        INDEX_RATIO = "INDEX_RATIO", "Ratio d’index"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(FormulaTemplate, on_delete=models.PROTECT, related_name="terms")
    position = models.PositiveIntegerField()
    coefficient = models.DecimalField(max_digits=18, decimal_places=8)
    term_type = models.CharField(max_length=40, choices=TermType.choices, default=TermType.INDEX_RATIO)
    index_code = models.CharField(max_length=120)
    base_period_year = models.PositiveSmallIntegerField(null=True, blank=True)
    base_period_month = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    base_value = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    base_source = models.TextField(blank=True)
    reference_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = FormulaTemplateTermQuerySet.as_manager()

    class Meta:
        db_table = "markets_formulatemplateterm"
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["template", "position"], name="uniq_template_term_position"),
            models.CheckConstraint(condition=models.Q(position__gt=0), name="template_term_position_positive"),
            models.CheckConstraint(condition=models.Q(base_value__isnull=True) | models.Q(base_value__gt=0), name="template_term_base_positive"),
        ]

    def clean(self):
        errors = {}
        self.index_code = self.index_code.strip()
        if not self.index_code:
            errors["index_code"] = "Le code de l’index est obligatoire."
        if self.term_type not in self.TermType.values:
            errors["term_type"] = "Le type de terme est invalide."
        if not isinstance(self.coefficient, Decimal):
            errors["coefficient"] = "Le coefficient doit être une valeur Decimal."
        if self.base_value is not None and not isinstance(self.base_value, Decimal):
            errors["base_value"] = "La valeur de base doit être une valeur Decimal."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not isinstance(self.coefficient, Decimal) or (self.base_value is not None and not isinstance(self.base_value, Decimal)):
            raise ValidationError("Les valeurs numériques du terme doivent être des Decimal.")
        template_status = FormulaTemplate.objects.filter(pk=self.template_id).values_list("status", flat=True).first() if self.template_id else None
        if template_status == FormulaTemplate.Status.VERIFIED:
            raise ValidationError("Les termes d'un template VERIFIED sont immuables.")
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            previous_template_id = type(self).objects.only("template_id").get(pk=self.pk).template_id
            if previous_template_id != self.template_id:
                raise ValidationError("Le template d'un terme est immuable.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if FormulaTemplate.objects.filter(pk=self.template_id, status=FormulaTemplate.Status.VERIFIED).exists():
            raise ProtectedError("Les termes d'un template VERIFIED sont immuables.", self)
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.template} — {self.index_code}"


class MarketFormula(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        VALIDATED = "VALIDATED", "Validée"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    revision_group = models.ForeignKey(RevisionGroup, on_delete=models.PROTECT, related_name="formulas")
    source_template = models.ForeignKey("FormulaTemplate", on_delete=models.PROTECT, null=True, blank=True, related_name="market_copies")
    source_template_version = models.PositiveIntegerField(null=True, blank=True)
    version_number = models.PositiveIntegerField()
    label = models.CharField(max_length=255)
    expression_display = models.CharField(max_length=500, blank=True)
    constant_term = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    reference_period_year = models.PositiveSmallIntegerField(null=True, blank=True)
    reference_period_month = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    reference_rule_code = models.CharField(max_length=120, blank=True)
    reference_source = models.TextField(blank=True)
    created_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="created_market_formulas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    objects = FormulaQuerySet.as_manager()

    class Meta:
        db_table = "markets_marketformula"
        ordering = ["version_number"]
        constraints = [
            models.UniqueConstraint(fields=["revision_group", "version_number"], name="uniq_marketformula_group_version"),
            models.CheckConstraint(condition=models.Q(version_number__gt=0), name="marketformula_version_positive"),
            models.CheckConstraint(condition=models.Q(source_template__isnull=True, source_template_version__isnull=True) | models.Q(source_template__isnull=False, source_template_version__isnull=False), name="marketformula_source_template_pair"),
            models.CheckConstraint(condition=models.Q(valid_to__isnull=True) | models.Q(valid_from__isnull=True) | models.Q(valid_to__gte=models.F("valid_from")), name="marketformula_valid_dates_order"),
        ]
        indexes = [
            models.Index(fields=["revision_group", "status"], name="formula_group_status_idx"),
        ]

    def clean(self):
        errors = {}
        if not self.label.strip():
            errors["label"] = "Le libellé de la formule est obligatoire."
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            errors["valid_to"] = "La fin de validité doit être postérieure ou égale au début."
        if self.status not in self.Status.values:
            errors["status"] = "Le statut de la formule est invalide."
        if self.constant_term is not None and not isinstance(self.constant_term, Decimal):
            errors["constant_term"] = "La constante doit être une valeur Decimal."
        if self.status == self.Status.VALIDATED:
            if self.constant_term is None:
                errors["constant_term"] = "La constante est obligatoire pour valider la formule."
            elif self.constant_term < Decimal("0.15"):
                errors["constant_term"] = "La constante doit être supérieure ou égale à 0,15."
            terms = list(self.terms.all()) if self.pk else []
            if not terms:
                errors["terms"] = "Une formule validée doit comporter au moins un terme."
            else:
                total = self.constant_term + sum((term.coefficient for term in terms), Decimal("0"))
                if total != Decimal("1"):
                    errors["terms"] = "La constante et les coefficients doivent totaliser exactement 1,00."
                for term in terms:
                    if term.term_type not in FormulaTerm.TermType.values:
                        errors["terms"] = "Le type de terme est invalide."
                    if not term.index_code.strip():
                        errors["terms"] = "Le code de l’index est obligatoire."
                    if not isinstance(term.coefficient, Decimal):
                        errors["terms"] = "Le coefficient doit être une valeur Decimal."
                    if term.term_type == FormulaTerm.TermType.INDEX_RATIO and (term.base_value is None or term.base_value <= 0):
                        errors["terms"] = "Chaque ratio d’index validé doit avoir une valeur de base strictement positive."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.constant_term is not None and not isinstance(self.constant_term, Decimal):
            raise ValidationError("La constante doit être une valeur Decimal.")
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            previous = type(self).objects.only("revision_group_id", "version_number", "status").get(pk=self.pk)
            if previous.revision_group_id != self.revision_group_id:
                raise ValidationError("Le groupe d'une formule est immuable.")
            if previous.version_number != self.version_number:
                raise ValidationError("Le numéro de version est immuable.")
            if previous.status == self.Status.INACTIVE and self.status != self.Status.INACTIVE:
                raise ValidationError("Une formule inactive ne peut pas être réactivée.")
            if previous.status == self.Status.VALIDATED:
                changed_fields = {
                    field.name for field in self._meta.concrete_fields
                    if field.name != "updated_at" and getattr(previous, field.name) != getattr(self, field.name)
                }
                if changed_fields != {"status"} or self.status != self.Status.INACTIVE:
                    raise ValidationError("Une formule validée est immuable.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ProtectedError("Une formule ne peut pas être supprimée physiquement.", self)

    def __str__(self):
        return f"{self.revision_group.name} v{self.version_number}"


class FormulaTerm(models.Model):
    class TermType(models.TextChoices):
        INDEX_RATIO = "INDEX_RATIO", "Ratio d’index"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    formula = models.ForeignKey(MarketFormula, on_delete=models.PROTECT, related_name="terms")
    position = models.PositiveIntegerField()
    coefficient = models.DecimalField(max_digits=18, decimal_places=8)
    term_type = models.CharField(max_length=40, choices=TermType.choices, default=TermType.INDEX_RATIO)
    index_code = models.CharField(max_length=120)
    base_period_year = models.PositiveSmallIntegerField(null=True, blank=True)
    base_period_month = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    base_value = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    base_source = models.TextField(blank=True)
    reference_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = FormulaTermQuerySet.as_manager()

    class Meta:
        db_table = "markets_formulaterm"
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["formula", "position"], name="uniq_formulaterm_formula_position"),
            models.CheckConstraint(condition=models.Q(position__gt=0), name="formulaterm_position_positive"),
            models.CheckConstraint(condition=models.Q(base_value__isnull=True) | models.Q(base_value__gt=0), name="formulaterm_base_positive"),
        ]

    def clean(self):
        errors = {}
        self.index_code = self.index_code.strip()
        if not self.index_code:
            errors["index_code"] = "Le code de l’index est obligatoire."
        if self.term_type not in self.TermType.values:
            errors["term_type"] = "Le type de terme est invalide."
        if self.coefficient is not None and not isinstance(self.coefficient, Decimal):
            errors["coefficient"] = "Le coefficient doit être une valeur Decimal."
        if self.base_value is not None and not isinstance(self.base_value, Decimal):
            errors["base_value"] = "La valeur de base doit être une valeur Decimal."
        formula_status = MarketFormula.objects.filter(pk=self.formula_id).values_list("status", flat=True).first() if self.formula_id else None
        if formula_status == MarketFormula.Status.VALIDATED and self.term_type == self.TermType.INDEX_RATIO and (self.base_value is None or self.base_value <= 0):
            errors["base_value"] = "La valeur de base de l’index est obligatoire et strictement positive."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.coefficient is not None and not isinstance(self.coefficient, Decimal):
            raise ValidationError("Le coefficient doit être une valeur Decimal.")
        if self.base_value is not None and not isinstance(self.base_value, Decimal):
            raise ValidationError("La valeur de base doit être une valeur Decimal.")
        formula_status = MarketFormula.objects.filter(pk=self.formula_id).values_list("status", flat=True).first() if self.formula_id else None
        if formula_status == MarketFormula.Status.VALIDATED:
            raise ValidationError("Les termes d'une formule validée sont immuables.")
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            previous_formula_id = type(self).objects.only("formula_id").get(pk=self.pk).formula_id
            if previous_formula_id != self.formula_id:
                raise ValidationError("La formule d'un terme est immuable.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        formula_status = MarketFormula.objects.filter(pk=self.formula_id).values_list("status", flat=True).first()
        if formula_status == MarketFormula.Status.VALIDATED:
            raise ProtectedError("Les termes d'une formule validée sont immuables.", self)
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.formula} — {self.index_code}"
