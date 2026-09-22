from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("markets", "0011_externalindexstaging_change_trace")]

    operations = [
        migrations.AddField(
            model_name="indexpublication",
            name="source_type",
            field=models.CharField(
                choices=[
                    ("OFFICIAL", "Officielle"),
                    ("EXTERNAL_SECONDARY", "Source externe secondaire"),
                    ("MANUAL_VALIDATED", "Validation manuelle"),
                ],
                default="OFFICIAL",
                max_length=32,
            ),
        ),
        migrations.RemoveConstraint(model_name="indexpublication", name="uniq_indexpublication_month"),
        migrations.AddConstraint(
            model_name="indexpublication",
            constraint=models.UniqueConstraint(fields=("year", "month", "source_type"), name="uniq_indexpublication_period_source"),
        ),
    ]
