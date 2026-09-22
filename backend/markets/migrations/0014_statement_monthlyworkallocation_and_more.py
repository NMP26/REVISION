import uuid
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("markets", "0013_official_index_validation")]

    operations = [
        migrations.CreateModel(
            name="Statement",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("number", models.PositiveIntegerField()),
                ("date", models.DateField()),
                ("amount_ht", models.DecimalField(decimal_places=2, max_digits=18, validators=[django.core.validators.MinValueValidator(Decimal("0"))])),
                ("observation", models.TextField(blank=True)),
                ("allocation_method", models.CharField(choices=[("ACTUAL_EXECUTION", "Jours d'exécution saisis"), ("CALENDAR_DAY_PRORATA", "Prorata de jours calendaires")], default="ACTUAL_EXECUTION", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("market", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="statements", to="markets.market")),
            ],
            options={"db_table": "markets_statement", "ordering": ["number"]},
        ),
        migrations.CreateModel(
            name="MonthlyWorkAllocation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("year", models.PositiveSmallIntegerField()),
                ("month", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
                ("work_days", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0"))])),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("statement", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="monthly_allocations", to="markets.statement")),
            ],
            options={"db_table": "markets_monthlyworkallocation", "ordering": ["year", "month"]},
        ),
        migrations.AddConstraint(model_name="statement", constraint=models.UniqueConstraint(fields=("market", "number"), name="uniq_statement_market_number")),
        migrations.AddConstraint(model_name="monthlyworkallocation", constraint=models.UniqueConstraint(fields=("statement", "year", "month"), name="uniq_work_allocation_statement_month")),
    ]
