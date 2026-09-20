import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class Company(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    raison_sociale = models.CharField(max_length=255)
    forme_juridique = models.CharField(max_length=100, blank=True)
    capital_social = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    ice = models.CharField(max_length=64, blank=True)
    if_fiscal = models.CharField(max_length=64, blank=True)
    rc = models.CharField(max_length=64, blank=True)
    rc_city = models.CharField(max_length=120, blank=True)
    cnss = models.CharField(max_length=64, blank=True)
    adresse_complete = models.TextField(blank=True)
    ville = models.CharField(max_length=120, blank=True)
    telephone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    site_web = models.URLField(max_length=500, blank=True)
    representant_nom = models.CharField(max_length=100, blank=True)
    representant_prenom = models.CharField(max_length=100, blank=True)
    representant_fonction = models.CharField(max_length=150, blank=True)
    logo = models.ImageField(
        upload_to="companies/logos/",
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])],
    )
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "companies_company"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["raison_sociale"]),
        ]

    def __str__(self):
        return self.raison_sociale


class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="memberships")
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="memberships")
    role = models.CharField(max_length=20, choices=Role.choices)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "companies_membership"
        constraints = [
            models.UniqueConstraint(fields=["user", "company"], name="uniq_membership_user_company"),
        ]
        indexes = [
            models.Index(fields=["user", "active"]),
            models.Index(fields=["company", "active"]),
        ]
