from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("markets", "0010_externalindexstaging")]

    operations = [
        migrations.AddField(model_name="externalindexstaging", name="previous_raw_value", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="externalindexstaging", name="previous_normalized_value", field=models.DecimalField(blank=True, decimal_places=8, max_digits=18, null=True)),
        migrations.AddField(model_name="externalindexstaging", name="previous_raw_payload_hash", field=models.CharField(blank=True, max_length=64)),
        migrations.AddField(model_name="externalindexstaging", name="source_changed", field=models.BooleanField(default=False)),
    ]
