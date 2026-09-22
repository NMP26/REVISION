from decimal import Decimal
import uuid

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


def seed_validated_bat3(apps, schema_editor):
    """Seed only the validated dataset explicitly available to this release."""
    IndexDefinition = apps.get_model("markets", "IndexDefinition")
    IndexPublication = apps.get_model("markets", "IndexPublication")
    MonthlyIndexValue = apps.get_model("markets", "MonthlyIndexValue")
    definition, _ = IndexDefinition.objects.get_or_create(
        code="BAT3",
        defaults={"designation": "Électricité", "domain": "BAT", "active": True},
    )
    publication, _ = IndexPublication.objects.get_or_create(
        year=2025,
        month=11,
        defaults={
            "document_reference": "Barème novembre 2025",
            "status": "VALIDATED",
        },
    )
    MonthlyIndexValue.objects.get_or_create(
        index_definition=definition,
        year=2025,
        month=11,
        defaults={
            "publication": publication,
            "value": Decimal("337.8"),
            "status": "DEFINITIVE",
            "source_document": "Barème novembre 2025",
        },
    )


class Migration(migrations.Migration):
    dependencies = [("markets", "0007_product_owner_formula_catalog")]

    operations = [
        migrations.CreateModel(
            name="IndexDefinition",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("code", models.CharField(max_length=120, unique=True)),
                ("designation", models.CharField(max_length=255)),
                ("domain", models.CharField(blank=True, max_length=120)),
                ("active", models.BooleanField(default=True)),
            ],
            options={"db_table": "markets_indexdefinition", "ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="IndexPublication",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("year", models.PositiveSmallIntegerField()),
                ("month", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
                ("publication_date", models.DateField(blank=True, null=True)),
                ("source_url", models.URLField(blank=True, max_length=500)),
                ("document_reference", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("IMPORTED", "Importée"), ("VALIDATED", "Validée"), ("PENDING_VALIDATION", "Validation en attente")], default="IMPORTED", max_length=30)),
                ("imported_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "markets_indexpublication", "ordering": ["-year", "-month"]},
        ),
        migrations.CreateModel(
            name="MonthlyIndexValue",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("year", models.PositiveSmallIntegerField()),
                ("month", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
                ("value", models.DecimalField(decimal_places=8, max_digits=18)),
                ("status", models.CharField(choices=[("DEFINITIVE", "Définitive"), ("PROVISIONAL", "Provisoire"), ("PENDING_VALIDATION", "Validation en attente")], default="PENDING_VALIDATION", max_length=30)),
                ("source_url", models.URLField(blank=True, max_length=500)),
                ("source_document", models.CharField(blank=True, max_length=255)),
                ("validated_at", models.DateTimeField(blank=True, null=True)),
                ("source_reference", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("index_definition", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="monthly_values", to="markets.indexdefinition")),
                ("publication", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="values", to="markets.indexpublication")),
            ],
            options={"db_table": "markets_monthlyindexvalue", "ordering": ["-year", "-month", "index_definition__code"]},
        ),
        migrations.AddConstraint(model_name="indexpublication", constraint=models.UniqueConstraint(fields=("year", "month"), name="uniq_indexpublication_month")),
        migrations.AddConstraint(model_name="monthlyindexvalue", constraint=models.UniqueConstraint(fields=("index_definition", "year", "month"), name="uniq_monthlyindex_definition_month")),
        migrations.AddConstraint(model_name="monthlyindexvalue", constraint=models.CheckConstraint(condition=models.Q(("value__gt", 0)), name="monthlyindexvalue_positive")),
        migrations.AddIndex(model_name="monthlyindexvalue", index=models.Index(fields=["index_definition", "year", "month", "status"], name="monthlyindex_lookup_idx")),
        migrations.RunPython(seed_validated_bat3, migrations.RunPython.noop),
    ]
