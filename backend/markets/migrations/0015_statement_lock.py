from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("markets", "0014_statement_monthlyworkallocation_and_more")]

    operations = [
        migrations.AddField(
            model_name="statement",
            name="locked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="statement",
            name="lock_reason",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
