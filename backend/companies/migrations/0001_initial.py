import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("raison_sociale", models.CharField(max_length=255)),
                ("forme_juridique", models.CharField(blank=True, max_length=100)),
                ("capital_social", models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True)),
                ("ice", models.CharField(blank=True, max_length=64)),
                ("if_fiscal", models.CharField(blank=True, max_length=64)),
                ("rc", models.CharField(blank=True, max_length=64)),
                ("cnss", models.CharField(blank=True, max_length=64)),
                ("adresse_complete", models.TextField(blank=True)),
                ("ville", models.CharField(blank=True, max_length=120)),
                ("telephone", models.CharField(blank=True, max_length=32)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("site_web", models.URLField(blank=True, max_length=500)),
                ("representant_nom", models.CharField(blank=True, max_length=100)),
                ("representant_prenom", models.CharField(blank=True, max_length=100)),
                ("representant_fonction", models.CharField(blank=True, max_length=150)),
                ("logo", models.ImageField(blank=True, upload_to="companies/logos/", validators=[django.core.validators.FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])])),
                ("notes", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("ACTIVE", "Active"), ("INACTIVE", "Inactive")], default="ACTIVE", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "companies_company",
                "indexes": [models.Index(fields=["status"], name="companies_c_status_2407e4_idx"), models.Index(fields=["raison_sociale"], name="companies_c_raison__cbc158_idx")],
            },
        ),
        migrations.CreateModel(
            name="Membership",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("role", models.CharField(choices=[("OWNER", "Owner"), ("ADMIN", "Admin"), ("MEMBER", "Member")], max_length=20)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="memberships", to="companies.company")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "companies_membership",
                "indexes": [models.Index(fields=["user", "active"], name="companies_m_user_id_4ff7a9_idx"), models.Index(fields=["company", "active"], name="companies_m_company_55842b_idx")],
                "constraints": [models.UniqueConstraint(fields=("user", "company"), name="uniq_membership_user_company")],
            },
        ),
    ]
