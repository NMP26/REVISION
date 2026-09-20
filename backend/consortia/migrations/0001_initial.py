from django.db import migrations, models
import django.db.models.deletion
import uuid
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):
    initial = True
    dependencies = [("accounts", "0001_initial"), ("companies", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Consortium",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("consortium_type", models.CharField(blank=True, max_length=80)),
                ("active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_consortia", to="accounts.user")),
                ("owner_company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="owned_consortia", to="companies.company")),
            ],
            options={"db_table": "consortia_consortium", "constraints": [models.CheckConstraint(condition=models.Q(name__regex=r"\S"), name="consortium_name_not_blank")]},
        ),
        migrations.CreateModel(
            name="ConsortiumMember",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("role", models.CharField(choices=[("MANDATAIRE", "Mandataire"), ("MEMBER", "Membre")], max_length=20)),
                ("share_percent", models.DecimalField(blank=True, decimal_places=4, max_digits=7, null=True, validators=[django.core.validators.MinValueValidator(Decimal("0.0001")), django.core.validators.MaxValueValidator(Decimal("100"))])),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="consortium_memberships", to="companies.company")),
                ("consortium", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="members", to="consortia.consortium")),
            ],
            options={"db_table": "consortia_consortiummember", "constraints": [models.UniqueConstraint(fields=("consortium", "company"), name="uniq_consortium_company"), models.CheckConstraint(condition=models.Q(share_percent__isnull=True) | models.Q(share_percent__gt=0, share_percent__lte=100), name="consortium_share_percent_range")]},
        ),
    ]
