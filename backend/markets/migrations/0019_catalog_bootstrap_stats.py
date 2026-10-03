from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("markets", "0018_official_resolution_audit")]
    operations = [
        migrations.AddField(model_name="indexsourcedocument", name="extracted_cells", field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="indexsourcedocument", name="extracted_rows", field=models.PositiveIntegerField(default=0)),
    ]
