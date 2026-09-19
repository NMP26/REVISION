from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("markets", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="market",
            constraint=models.CheckConstraint(
                condition=models.Q(contract_duration_value__isnull=True)
                | models.Q(contract_duration_value__gt=0),
                name="market_duration_value_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="market",
            constraint=models.CheckConstraint(
                condition=models.Q(contract_duration_unit__isnull=True)
                | models.Q(contract_duration_unit__in=["DAYS", "MONTHS"]),
                name="market_duration_unit_allowed",
            ),
        ),
        migrations.AddConstraint(
            model_name="market",
            constraint=models.CheckConstraint(
                condition=models.Q(market_number__regex=r"\S"),
                name="market_number_not_blank",
            ),
        ),
        migrations.AddConstraint(
            model_name="market",
            constraint=models.CheckConstraint(
                condition=models.Q(contracting_authority__regex=r"\S"),
                name="market_contracting_authority_not_blank",
            ),
        ),
        migrations.AddConstraint(
            model_name="market",
            constraint=models.CheckConstraint(
                condition=models.Q(subject__regex=r"\S"),
                name="market_subject_not_blank",
            ),
        ),
        migrations.AddConstraint(
            model_name="marketlot",
            constraint=models.CheckConstraint(
                condition=models.Q(lot_number__regex=r"\S"),
                name="marketlot_number_not_blank",
            ),
        ),
        migrations.AddConstraint(
            model_name="marketlot",
            constraint=models.CheckConstraint(
                condition=models.Q(title__regex=r"\S"),
                name="marketlot_title_not_blank",
            ),
        ),
    ]
