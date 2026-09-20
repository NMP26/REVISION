from django.db import migrations, models
import django.db.models.deletion
import unicodedata


def normalize_authority_name(value):
    value = " ".join((value or "").strip().split()).casefold()
    return "".join(char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char))


def backfill_holders(apps, schema_editor):
    Market = apps.get_model("markets", "Market")
    Market.objects.update(holder_type="SOLE_COMPANY")
    for market in Market.objects.all().iterator():
        market.holder_company_id = market.company_id
        market.save(update_fields=["holder_company"])


def backfill_authorities(apps, schema_editor):
    Market = apps.get_model("markets", "Market")
    Authority = apps.get_model("authorities", "ContractingAuthority")
    CompanyAuthority = apps.get_model("authorities", "CompanyAuthority")
    for market in Market.objects.exclude(contracting_authority="").iterator():
        name = " ".join(market.contracting_authority.strip().split())
        normalized = normalize_authority_name(name)
        authority, _ = Authority.objects.get_or_create(normalized_name=normalized, defaults={"name": name})
        CompanyAuthority.objects.get_or_create(company_id=market.company_id, authority_id=authority.id)
        Market.objects.filter(pk=market.pk).update(authority_id=authority.id)


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("markets", "0002_market_invariants"), ("authorities", "0001_initial"), ("consortia", "0002_consortium_invariants")]
    operations = [
        migrations.AddField(model_name="market", name="holder_type", field=models.CharField(choices=[("SOLE_COMPANY", "Société"), ("CONSORTIUM", "Groupement")], default="SOLE_COMPANY", max_length=20)),
        migrations.AddField(model_name="market", name="holder_company", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="held_markets", to="companies.company")),
        migrations.AddField(model_name="market", name="consortium", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="markets", to="consortia.consortium")),
        migrations.AddField(model_name="market", name="authority", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="markets", to="authorities.contractingauthority")),
        migrations.RunPython(backfill_holders, migrations.RunPython.noop),
        migrations.RunPython(backfill_authorities, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="market",
            constraint=models.CheckConstraint(condition=models.Q(consortium__isnull=True, holder_company__isnull=False, holder_type="SOLE_COMPANY") | models.Q(consortium__isnull=False, holder_company__isnull=True, holder_type="CONSORTIUM"), name="market_holder_exactly_one"),
        ),
    ]
