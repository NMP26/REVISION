from decimal import Decimal
import uuid

from django.db import migrations


CATALOG_SOURCE_TITLE = "Catalogue des formules fourni par le propriétaire produit"
CATALOG_SOURCE_REFERENCE = "PRODUCT_OWNER_FORMULA_CATALOG_2026-09-21"
CATALOG_NAMESPACE = uuid.UUID("6f12b5a9-82c9-4f39-8a58-4c8e6cae6df2")


FORMULAS = [
    ("BAT1", "Gros œuvre, revêtement, étanchéité", "Bâtiment"),
    ("BAT2", "Menuiserie", "Bâtiment"),
    ("BAT3", "Électricité", "Bâtiment"),
    ("BAT4", "Plomberie sanitaire", "Bâtiment"),
    ("BAT5", "Peinture vitrerie", "Bâtiment"),
    ("BAT6", "Bâtiment tous corps d'état", "Bâtiment"),
    ("SF1", "Reconnaissances géologiques et forages d'eau", "Sondages & forages"),
    ("SF2", "Sondages de reconnaissances hydrogéologiques", "Sondages & forages"),
    ("SF3", "Forages d'essai et d'exploitation", "Sondages & forages"),
    ("SF4", "Forages profonds", "Sondages & forages"),
    ("SF5", "Fonçage de puits", "Sondages & forages"),
    ("SF6", "Sondages et forages", "Sondages & forages"),
    ("OA1", "Travaux de réalisation de fondations profondes", "Ouvrages d'art"),
    ("OA2", "Construction du tablier en béton armé y compris équipements", "Ouvrages d'art"),
    ("OA3", "Construction du tablier en béton précontraint y compris équipements", "Ouvrages d'art"),
    ("OA4", "Ouvrage d'art en béton armé (avec fondations profondes ou superficielles)", "Ouvrages d'art"),
    ("OA5", "Ouvrage d'art en béton précontraint (avec fondations profondes ou superficielles)", "Ouvrages d'art"),
    ("CEP1", "Conduites amiante ciment", "Conduites eau potable"),
    ("CEP2", "Conduites en béton armé ou précontraint", "Conduites eau potable"),
    ("CEP3", "Conduites en fonte", "Conduites eau potable"),
    ("REP", "Réservoirs d'eau potable", "Conduites eau potable"),
    ("TR1", "Terrassements", "Travaux routiers"),
    ("TR2", "Assainissement et soutènement", "Travaux routiers"),
    ("TR3", "Construction de route avec enduit superficiel (fourniture de liant non comprise)", "Travaux routiers"),
    ("TR3bis", "Construction de route avec enduit superficiel (y compris fourniture de liant)", "Travaux routiers"),
    ("TR4", "Renforcement ou construction de chaussée avec enduit superficiel (fourniture de liant non comprise)", "Travaux routiers"),
    ("TR4bis", "Renforcement ou construction de chaussée avec enduit superficiel (y compris fourniture de liant)", "Travaux routiers"),
    ("TR5", "Construction ou renforcement de chaussée avec matériaux traités au liant hydrocarboné (liant non compris)", "Travaux routiers"),
    ("TR5bis", "Construction ou renforcement de chaussée avec matériaux traités au liant hydrocarboné (y compris liant)", "Travaux routiers"),
    ("TR6", "Couche de roulement en enduit superficiel (fourniture de liant non comprise)", "Travaux routiers"),
    ("TR6bis", "Couche de roulement en enduit superficiel (y compris fourniture de liant)", "Travaux routiers"),
]

def expression(code):
    return f"P = P₀ × [0,15 + 0,85 × {code}/{code}₀]"


def seed_catalog(apps, schema_editor):
    FormulaTemplate = apps.get_model("markets", "FormulaTemplate")
    FormulaTemplateTerm = apps.get_model("markets", "FormulaTemplateTerm")
    verified_at = __import__("django.utils.timezone", fromlist=["now"]).now()

    for code, designation, domain in FORMULAS:
        template, created = FormulaTemplate.objects.get_or_create(
            scope="GLOBAL", code=code, version_number=1,
            defaults={
                "family_key": uuid.uuid5(CATALOG_NAMESPACE, code),
                "designation": designation,
                "domain": domain,
                "expression_display": expression(code),
                "constant_term": Decimal("0.15"),
                "status": "VERIFIED",
                "source_type": "OFFICIAL",
                "source_title": CATALOG_SOURCE_TITLE,
                "source_reference": CATALOG_SOURCE_REFERENCE,
                "verification_status": "PRODUCT_OWNER_APPROVED",
                "verified_at": verified_at,
                "notes": "Expression et métadonnées fournies explicitement par le propriétaire produit.",
            },
        )
        if not created:
            expected = {
                "designation": designation,
                "domain": domain,
                "expression_display": expression(code),
                "constant_term": Decimal("0.15"),
                "status": "VERIFIED",
                "source_type": "OFFICIAL",
                "source_title": CATALOG_SOURCE_TITLE,
                "source_reference": CATALOG_SOURCE_REFERENCE,
            }
            differences = [field for field, value in expected.items() if getattr(template, field) != value]
            term = template.terms.first()
            if term is None or term.coefficient != Decimal("0.85") or term.index_code != code or template.terms.count() != 1:
                differences.append("terms")
            if differences:
                raise RuntimeError(f"Catalogue existant contradictoire pour {code}: {', '.join(differences)}")
            continue
        FormulaTemplateTerm.objects.create(
            template=template, position=1, coefficient=Decimal("0.85"),
            term_type="INDEX_RATIO", index_code=code,
        )

class Migration(migrations.Migration):
    dependencies = [("markets", "0006_priceitem_priceschedule_market_global_revision_group_and_more")]
    operations = [migrations.RunPython(seed_catalog, migrations.RunPython.noop)]
