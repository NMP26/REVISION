from django.db import migrations, models
import django.db.models.deletion
import uuid
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ("markets", "0009_indexsourcedocument_rawindexextraction"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExternalIndexStaging",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("source_provider", models.CharField(default="revisiondesprix.ma", max_length=120)),
                ("source_endpoint", models.CharField(max_length=500)),
                ("retrieved_at", models.DateTimeField()),
                ("external_code", models.CharField(max_length=120)),
                ("external_designation", models.CharField(blank=True, max_length=255, null=True)),
                ("year", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("month", models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
                ("raw_value", models.CharField(blank=True, max_length=120)),
                ("normalized_value", models.DecimalField(blank=True, decimal_places=8, max_digits=18, null=True)),
                ("raw_payload_hash", models.CharField(max_length=64)),
                ("comparison_status", models.CharField(choices=[("NEW", "Nouveau"), ("MATCHED", "Correspondant"), ("CONFLICT", "Conflit"), ("MISSING_LOCAL", "Absent du référentiel local"), ("MISSING_SOURCE", "Absent de la source"), ("LOCAL_ONLY", "Présent uniquement en local"), ("DESIGNATION_CONFLICT", "Conflit de désignation"), ("INVALID", "Invalide")], default="NEW", max_length=32)),
                ("validation_status", models.CharField(choices=[("PENDING_VALIDATION", "Validation en attente"), ("VALIDATED", "Validé"), ("INVALID", "Invalide")], default="PENDING_VALIDATION", max_length=32)),
                ("local_value", models.DecimalField(blank=True, decimal_places=8, max_digits=18, null=True)),
                ("pdf_value", models.DecimalField(blank=True, decimal_places=8, max_digits=18, null=True)),
                ("pdf_comparison_status", models.CharField(default="PDF_NOT_CHECKED", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("matched_index_definition", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="external_staging_rows", to="markets.indexdefinition")),
            ],
            options={"db_table": "markets_externalindexstaging", "ordering": ["-retrieved_at", "external_code", "year", "month"]},
        ),
        migrations.AddConstraint(model_name="externalindexstaging", constraint=models.UniqueConstraint(fields=("source_provider", "source_endpoint", "external_code", "year", "month"), name="uniq_external_index_stage_source_period", nulls_distinct=False)),
        migrations.AddIndex(model_name="externalindexstaging", index=models.Index(fields=("year", "month", "external_code"), name="external_stage_period_code_idx")),
        migrations.AddIndex(model_name="externalindexstaging", index=models.Index(fields=("comparison_status",), name="external_stage_comparison_idx")),
    ]
