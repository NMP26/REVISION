from django.db import migrations, models
import django.db.models.deletion


def seed_short_code_catalogue(apps, schema_editor):
    IndexDefinition = apps.get_model("markets", "IndexDefinition")
    IndexDefinition.objects.get_or_create(code="Py", defaults={"designation": "Polyester en plaques", "domain": "OFFICIAL", "active": True})
    IndexDefinition.objects.get_or_create(code="Pv", defaults={"designation": "Peinture-Vitrerie", "domain": "OFFICIAL", "active": True})


class Migration(migrations.Migration):
    dependencies = [("markets", "0017_indexsourcedocument_stored_file")]

    operations = [
        migrations.AddField(
            model_name="officialextractedvalue",
            name="resolved_index_definition",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="manually_resolved_official_values", to="markets.indexdefinition"),
        ),
        migrations.AddField(model_name="officialextractedvalue", name="resolution_method", field=models.CharField(blank=True, max_length=32)),
        migrations.AddField(
            model_name="officialextractedvalue",
            name="resolved_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="official_index_resolutions", to="accounts.user"),
        ),
        migrations.AddField(model_name="officialextractedvalue", name="resolved_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.RunPython(seed_short_code_catalogue, migrations.RunPython.noop),
    ]
