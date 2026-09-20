import uuid
import unicodedata

from django.db import models


def normalize_authority(value):
    value = " ".join((value or "").strip().split()).casefold()
    return "".join(char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char))


class ContractingAuthority(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255, unique=True, editable=False)
    short_name = models.CharField(max_length=120, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "authorities_contractingauthority"
        indexes = [models.Index(fields=["active", "normalized_name"])]

    def save(self, *args, **kwargs):
        self.name = " ".join(self.name.strip().split())
        self.short_name = " ".join(self.short_name.strip().split())
        self.normalized_name = normalize_authority(self.name)
        super().save(*args, **kwargs)


class AuthorityAlias(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    authority = models.ForeignKey(ContractingAuthority, on_delete=models.PROTECT, related_name="aliases")
    alias = models.CharField(max_length=255)
    normalized_alias = models.CharField(max_length=255, unique=True, editable=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.alias = " ".join(self.alias.strip().split())
        self.normalized_alias = normalize_authority(self.alias)
        super().save(*args, **kwargs)


class CompanyAuthority(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="authority_links")
    authority = models.ForeignKey(ContractingAuthority, on_delete=models.PROTECT, related_name="company_links")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "authority"], name="uniq_company_authority")]
