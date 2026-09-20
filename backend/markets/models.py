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


class Market(models.Model):
    class HolderType(models.TextChoices):
        SOLE_COMPANY = "SOLE_COMPANY", "Société"
        CONSORTIUM = "CONSORTIUM", "Groupement"
    class FormulaStructure(models.TextChoices):
        SINGLE = "SINGLE", "Formule unique"
        MULTIPLE = "MULTIPLE", "Formules multiples"

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
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.holder_type == self.HolderType.SOLE_COMPANY and self.holder_company_id is None:
            self.holder_company_id = self.company_id
        super().save(*args, **kwargs)

    def __str__(self):
        return self.market_number


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


class MarketFormula(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        VALIDATED = "VALIDATED", "Validée"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    revision_group = models.ForeignKey(RevisionGroup, on_delete=models.PROTECT, related_name="formulas")
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
