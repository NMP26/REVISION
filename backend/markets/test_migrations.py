from decimal import Decimal
from datetime import date

from django.db import connection
from django.test import TransactionTestCase
from django.db.migrations.executor import MigrationExecutor


class MarketHolderMigrationTests(TransactionTestCase):
    migrate_from = [("companies", "0001_initial"), ("markets", "0002_market_invariants")]
    migrate_to = [("companies", "0002_company_rc_city"), ("markets", "0003_market_holders_authority")]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.executor = MigrationExecutor(connection)
        cls.executor.migrate(cls.migrate_from)
        cls.old_apps = cls.executor.loader.project_state(cls.migrate_from).apps
        User = cls.old_apps.get_model("accounts", "User")
        Company = cls.old_apps.get_model("companies", "Company")
        Membership = cls.old_apps.get_model("companies", "Membership")
        Market = cls.old_apps.get_model("markets", "Market")
        cls.user = User.objects.create(email="migration@example.com", password="not-a-real-password")
        cls.company = Company.objects.create(raison_sociale="NAXU")
        Membership.objects.create(user=cls.user, company=cls.company, role="OWNER", active=True)
        cls.market = Market.objects.create(
            company=cls.company,
            market_number="10006299/4500004338",
            contracting_authority="Société Régionale Multiservices Souss-Massa",
            subject="Remplacement des câbles souterrains HTA en papier imprégné dégradé au centre-ville d’Agadir (Préfecture Agadir Ida Outanane)",
            amount_ht=Decimal("6603156.00"),
            vat_rate=Decimal("20.0000"),
            date_limite_remise_offres=date(2025, 11, 19),
            date_ouverture_plis=date(2025, 11, 19),
            date_signature=None,
            date_os_commencement=date(2026, 4, 23),
            contract_duration_value=365,
            contract_duration_unit="DAYS",
            formula_structure="SINGLE",
            status="ACTIVE",
            notes="Données historiques de migration.",
        )
        cls.company_count_before = Company.objects.count()
        cls.market_count_before = Market.objects.count()
        cls.before = {
            "user_id": cls.user.pk,
            "company_id": cls.company.pk,
            "market_id": cls.market.pk,
            "market_number": cls.market.market_number,
            "contracting_authority": cls.market.contracting_authority,
            "subject": cls.market.subject,
            "amount_ht": cls.market.amount_ht,
            "vat_rate": cls.market.vat_rate,
            "date_limite_remise_offres": cls.market.date_limite_remise_offres,
            "date_ouverture_plis": cls.market.date_ouverture_plis,
            "date_signature": cls.market.date_signature,
            "date_os_commencement": cls.market.date_os_commencement,
            "contract_duration_value": cls.market.contract_duration_value,
            "contract_duration_unit": cls.market.contract_duration_unit,
            "formula_structure": cls.market.formula_structure,
            "status": cls.market.status,
            "notes": cls.market.notes,
        }
        cls.executor = MigrationExecutor(connection)
        cls.executor.migrate(cls.migrate_to)
        cls.apps = cls.executor.loader.project_state(cls.migrate_to).apps

    @classmethod
    def tearDownClass(cls):
        cls.executor = MigrationExecutor(connection)
        cls.executor.migrate(cls.executor.loader.graph.leaf_nodes())
        connection.close()
        super().tearDownClass()

    def test_existing_market_identity_and_values_survive_progressive_migration(self):
        Company = self.apps.get_model("companies", "Company")
        Market = self.apps.get_model("markets", "Market")
        Authority = self.apps.get_model("authorities", "ContractingAuthority")
        Consortium = self.apps.get_model("consortia", "Consortium")
        company = Company.objects.get(pk=self.before["company_id"])
        market = Market.objects.get(pk=self.before["market_id"])
        def invariant(label, condition):
            print(f"{'PASS' if condition else 'FAIL'} {label}")
            self.assertTrue(condition, label)

        invariant("Company NAXU conservée", company.raison_sociale == "NAXU")
        invariant("UUID Company conservé", company.pk == self.before["company_id"])
        invariant("Market conservé", Market.objects.filter(pk=self.before["market_id"]).exists())
        invariant("UUID Market conservé", market.pk == self.before["market_id"])
        invariant("numéro conservé", market.market_number == self.before["market_number"])
        invariant("montant_ht conservé", market.amount_ht == Decimal("6603156.00") == self.before["amount_ht"])
        invariant("TVA conservée", market.vat_rate == Decimal("20.0000") == self.before["vat_rate"])
        invariant("objet strictement inchangé", market.subject == self.before["subject"])
        invariant("date limite conservée", market.date_limite_remise_offres == date(2025, 11, 19) == self.before["date_limite_remise_offres"])
        invariant("ouverture plis conservée", market.date_ouverture_plis == date(2025, 11, 19) == self.before["date_ouverture_plis"])
        invariant("OS commencement conservé", market.date_os_commencement == date(2026, 4, 23) == self.before["date_os_commencement"])
        invariant("signature NULL conservée", market.date_signature is None and self.before["date_signature"] is None)
        invariant("délai conservé", (market.contract_duration_value, market.contract_duration_unit) == (self.before["contract_duration_value"], self.before["contract_duration_unit"]))
        invariant("structure conservée", market.formula_structure == self.before["formula_structure"])
        invariant("statut conservé", market.status == self.before["status"])
        invariant("notes conservées", market.notes == self.before["notes"])
        invariant("titulaire historique NAXU conservé", market.holder_type == "SOLE_COMPANY" and market.holder_company_id == company.pk)
        invariant("aucun groupement fictif créé", Consortium.objects.count() == 0 and market.consortium_id is None)
        invariant("maître d’ouvrage historique conservé", market.contracting_authority == self.before["contracting_authority"])
        authority = Authority.objects.get(pk=market.authority_id)
        invariant("autorité référencée sans perte d’historique", authority.name == self.before["contracting_authority"])
        invariant("aucune Company fictive créée", Company.objects.filter(raison_sociale="Groupement INGC/NAXU").count() == 0)
        invariant("aucune donnée Company perdue", Company.objects.count() == self.company_count_before)
        invariant("aucune donnée Market perdue", Market.objects.count() == self.market_count_before)
