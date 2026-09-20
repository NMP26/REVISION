from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("companies", "0001_initial")]
    operations = [migrations.AddField(
        model_name="company",
        name="rc_city",
        field=models.CharField(blank=True, max_length=120),
    )]
