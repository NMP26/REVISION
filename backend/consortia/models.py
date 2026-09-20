import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Consortium(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="owned_consortia")
    created_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="created_consortia")
    name = models.CharField(max_length=255)
    consortium_type = models.CharField(max_length=80, blank=True)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "consortia_consortium"
        constraints = [models.CheckConstraint(condition=models.Q(name__regex=r"\S"), name="consortium_name_not_blank")]


class ConsortiumMember(models.Model):
    class Role(models.TextChoices):
        MANDATAIRE = "MANDATAIRE", "Mandataire"
        MEMBER = "MEMBER", "Membre"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consortium = models.ForeignKey(Consortium, on_delete=models.PROTECT, related_name="members")
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="consortium_memberships")
    role = models.CharField(max_length=20, choices=Role.choices)
    share_percent = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True, validators=[MinValueValidator(Decimal("0.0001")), MaxValueValidator(Decimal("100"))])
    sort_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "consortia_consortiummember"
        constraints = [
            models.UniqueConstraint(fields=["consortium", "company"], name="uniq_consortium_company"),
            models.CheckConstraint(condition=models.Q(share_percent__isnull=True) | models.Q(share_percent__gt=0, share_percent__lte=100), name="consortium_share_percent_range"),
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
