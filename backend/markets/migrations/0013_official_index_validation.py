import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("markets", "0012_indexpublication_source_type")]

    operations = [
        migrations.AddField(
            model_name="indexpublication",
            name="document_hash",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="indexpublication",
            name="validated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(model_name="indexsourcedocument", name="nominal_year", field=models.PositiveSmallIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="indexsourcedocument", name="nominal_month", field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
        migrations.AddField(model_name="indexsourcedocument", name="source_url", field=models.URLField(blank=True, max_length=500)),
        migrations.AddField(model_name="indexsourcedocument", name="retrieved_at", field=models.DateTimeField(auto_now_add=True, null=True)),
        migrations.CreateModel(
            name="OfficialExtractedValue",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("year", models.PositiveSmallIntegerField()),
                ("month", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
                ("raw_code", models.CharField(max_length=120)),
                ("raw_designation", models.TextField(blank=True)),
                ("normalized_code", models.CharField(blank=True, max_length=120)),
                ("raw_value", models.CharField(max_length=120)),
                ("normalized_value", models.DecimalField(blank=True, decimal_places=8, max_digits=18, null=True)),
                ("confidence", models.DecimalField(blank=True, decimal_places=4, max_digits=5, null=True)),
                ("status", models.CharField(choices=[("EXTRACTED", "Extraite"), ("PENDING_VALIDATION", "Validation en attente"), ("VALIDATED", "Validée"), ("CONFLICT", "Conflit")], default="PENDING_VALIDATION", max_length=32)),
                ("extraction_method", models.CharField(max_length=32)),
                ("page_number", models.PositiveIntegerField(blank=True, null=True)),
                ("source_reference", models.CharField(blank=True, max_length=1000)),
                ("ambiguity", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("publication", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="official_values", to="markets.indexpublication")),
                ("source_document", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="official_values", to="markets.indexsourcedocument")),
            ],
            options={"db_table": "markets_officialextractedvalue"},
        ),
        migrations.AddConstraint(model_name="officialextractedvalue", constraint=models.UniqueConstraint(fields=("source_document", "year", "month", "normalized_code"), name="uniq_official_extracted_document_period_code")),
        migrations.AddIndex(model_name="officialextractedvalue", index=models.Index(fields=("year", "month", "normalized_code"), name="official_value_period_code_idx")),
        migrations.CreateModel(
            name="IndexValidationComparison",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("year", models.PositiveSmallIntegerField()),
                ("month", models.PositiveSmallIntegerField()),
                ("api_value", models.DecimalField(blank=True, decimal_places=8, max_digits=18, null=True)),
                ("local_value", models.DecimalField(blank=True, decimal_places=8, max_digits=18, null=True)),
                ("status", models.CharField(choices=[("ALL_MATCH", "Toutes les sources concordent"), ("OFFICIAL_API_MATCH_LOCAL_MISSING", "Officiel/API concordants, local absent"), ("OFFICIAL_LOCAL_MATCH_API_CONFLICT", "Officiel/local concordants, API en conflit"), ("OFFICIAL_API_CONFLICT", "Officiel/API en conflit"), ("OFFICIAL_LOCAL_CONFLICT", "Officiel/local en conflit"), ("LOCAL_MISSING", "Local absent"), ("API_MISSING", "API absente"), ("PENDING_VALIDATION", "Validation en attente")], max_length=48)),
                ("resolved", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("official_value", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="comparisons", to="markets.officialextractedvalue")),
                ("index_definition", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="validation_comparisons", to="markets.indexdefinition")),
            ],
            options={"db_table": "markets_indexvalidationcomparison"},
        ),
        migrations.AddConstraint(model_name="indexvalidationcomparison", constraint=models.UniqueConstraint(fields=("official_value", "index_definition"), name="uniq_index_validation_comparison")),
        migrations.CreateModel(
            name="IndexValidationAudit",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("value_before", models.DecimalField(blank=True, decimal_places=8, max_digits=18, null=True)),
                ("status_before", models.CharField(blank=True, max_length=30)),
                ("value_after", models.DecimalField(blank=True, decimal_places=8, max_digits=18, null=True)),
                ("status_after", models.CharField(max_length=30)),
                ("document_hash", models.CharField(blank=True, max_length=64)),
                ("method", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="index_validation_audits", to=settings.AUTH_USER_MODEL)),
                ("monthly_value", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="validation_audits", to="markets.monthlyindexvalue")),
                ("publication", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="validation_audits", to="markets.indexpublication")),
            ],
            options={"db_table": "markets_indexvalidationaudit", "ordering": ["created_at"]},
        ),
    ]
