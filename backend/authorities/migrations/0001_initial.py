from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = [("companies", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="ContractingAuthority",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("normalized_name", models.CharField(editable=False, max_length=255, unique=True)),
                ("short_name", models.CharField(blank=True, max_length=120)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "authorities_contractingauthority", "indexes": [models.Index(fields=["active", "normalized_name"], name="authorities_active_e702f8_idx")]},
        ),
        migrations.CreateModel(
            name="AuthorityAlias",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("alias", models.CharField(max_length=255)),
                ("normalized_alias", models.CharField(editable=False, max_length=255, unique=True)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("authority", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="aliases", to="authorities.contractingauthority")),
            ],
        ),
        migrations.CreateModel(
            name="CompanyAuthority",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("authority", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="company_links", to="authorities.contractingauthority")),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="authority_links", to="companies.company")),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("company", "authority"), name="uniq_company_authority")]},
        ),
    ]
