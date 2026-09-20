import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from companies.models import Company


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
