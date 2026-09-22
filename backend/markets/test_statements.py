from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from companies.models import Company, Membership

from .models import FormulaTerm, IndexDefinition, IndexPublication, Market, MarketFormula, MonthlyIndexValue, MonthlyWorkAllocation, RevisionGroup, Statement
from .statement_services import calculate_statement_preview


class V1StatementCalculationTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("v1-statement@example.com", "password-123")
        self.user = user
        self.client = APIClient()
        self.client.force_authenticate(user)
        company = Company.objects.create(raison_sociale="V1 Statement Company")
        Membership.objects.create(user=user, company=company, role=Membership.Role.OWNER)
        self.market = Market.objects.create(company=company, market_number="10006299/4500004338", contracting_authority="SRM-SM", subject="Travaux", date_limite_remise_offres=date(2025, 11, 19), date_os_commencement=date(2026, 4, 23), formula_structure=Market.FormulaStructure.SINGLE)
        group = RevisionGroup.objects.create(market=self.market, code="BAT3", name="Électricité")
        self.formula = MarketFormula.objects.create(revision_group=group, version_number=1, label="Électricité", constant_term=Decimal("0.15"), created_by=user)
        FormulaTerm.objects.create(formula=self.formula, position=1, coefficient=Decimal("0.85"), index_code="BAT3", base_value=Decimal("337.8"))
        self.market.global_revision_group = group
        self.market.revision_application_mode = Market.RevisionApplicationMode.GLOBAL_FORMULA
        self.market.save()
        definition = IndexDefinition.objects.filter(code="BAT3").first() or IndexDefinition.objects.create(code="BAT3", designation="Électricité", domain="BAT")
        self.definition = definition
        publication = IndexPublication.objects.get_or_create(year=2025, month=11, source_type=IndexPublication.SourceType.OFFICIAL, defaults={"document_reference": "Barème novembre 2025", "status": IndexPublication.Status.VALIDATED})[0]
        MonthlyIndexValue.objects.update_or_create(index_definition=definition, year=2025, month=11, defaults={"publication": publication, "value": Decimal("337.8"), "status": MonthlyIndexValue.Status.DEFINITIVE, "source_document": "Barème novembre 2025"})

    def make_statement(self, amount="535776.00"):
        return Statement.objects.create(market=self.market, number=1, date=date(2026, 8, 31), amount_ht=Decimal(amount))

    def add_month(self, statement, year, month, days="0"):
        return MonthlyWorkAllocation.objects.create(statement=statement, year=year, month=month, work_days=Decimal(days))

    def test_statement_number_unique_per_market_and_reusable_between_markets(self):
        first = self.make_statement("1.00")
        with self.assertRaises(Exception):
            Statement.objects.create(market=self.market, number=1, date=date(2026, 9, 1), amount_ht=Decimal("2.00"))
        other = Market.objects.create(company=self.market.company, market_number="OTHER-1", contracting_authority="SRM-SM", subject="Autres travaux", formula_structure=Market.FormulaStructure.SINGLE)
        self.assertEqual(Statement.objects.create(market=other, number=1, date=date(2026, 9, 1), amount_ht=Decimal("2.00")).number, first.number)

    def test_allocation_rejects_negative_and_duplicate_month(self):
        statement = self.make_statement()
        with self.assertRaises(ValidationError):
            MonthlyWorkAllocation.objects.create(statement=statement, year=2026, month=8, work_days=Decimal("-1"))
        self.add_month(statement, 2026, 8, "1")
        with self.assertRaises(Exception):
            self.add_month(statement, 2026, 8, "2")

    def test_real_market_one_month_scenario_conserves_amount(self):
        statement = self.make_statement()
        for month in range(4, 9):
            self.add_month(statement, 2026, month, "30" if month == 8 else "0")
        publication = IndexPublication.objects.get_or_create(year=2026, month=8, source_type=IndexPublication.SourceType.OFFICIAL, defaults={"document_reference": "Barème août 2026", "status": IndexPublication.Status.VALIDATED})[0]
        MonthlyIndexValue.objects.create(index_definition=self.definition, year=2026, month=8, publication=publication, value=Decimal("348.7"), status=MonthlyIndexValue.Status.DEFINITIVE)
        result = calculate_statement_preview(statement)
        self.assertEqual(result["total_work_days"], Decimal("30.00"))
        self.assertEqual(result["total_allocated_amount"], Decimal("535776.00"))
        self.assertEqual([row["monthly_amount"] for row in result["monthly_results"]], [Decimal("0.00")] * 4 + [Decimal("535776.00")])
        self.assertEqual(result["base_index"], Decimal("337.80000000"))
        self.assertEqual(result["monthly_results"][-1]["current_index"], Decimal("348.70000000"))
        self.assertEqual(result["calculation_status"], "CALCULABLE_PREVIEW")

    def test_missing_august_index_has_no_fallback(self):
        statement = self.make_statement()
        for month in range(4, 9):
            self.add_month(statement, 2026, month, "30" if month == 8 else "0")
        result = calculate_statement_preview(statement)
        self.assertEqual(result["calculation_status"], "INDEX_NOT_AVAILABLE")
        self.assertEqual(result["total_work_days"], Decimal("30.00"))
        self.assertEqual(result["total_allocated_amount"], Decimal("535776.00"))
        self.assertEqual([row["monthly_amount"] for row in result["monthly_results"]], [Decimal("0.00")] * 4 + [Decimal("535776.00")])
        self.assertEqual([row["amount_to_revise"] for row in result["monthly_results"]], [Decimal("0.00")] * 4 + [Decimal("535776.00")])
        self.assertIsNone(result["monthly_results"][-1]["current_index"])
        self.assertIsNone(result["monthly_results"][-1]["revision_amount"])
        self.assertIsNone(result["total_revision"])

    def test_zero_work_month_keeps_zero_revision_and_uses_available_index_coefficients(self):
        statement = self.make_statement()
        for month in range(4, 9):
            self.add_month(statement, 2026, month, "30" if month == 8 else "0")
        publication = IndexPublication.objects.get_or_create(year=2026, month=4, source_type=IndexPublication.SourceType.OFFICIAL, defaults={"document_reference": "Barème avril 2026", "status": IndexPublication.Status.VALIDATED})[0]
        MonthlyIndexValue.objects.create(index_definition=self.definition, year=2026, month=4, publication=publication, value=Decimal("348.7"), status=MonthlyIndexValue.Status.DEFINITIVE)
        result = calculate_statement_preview(statement)
        april = result["monthly_results"][0]
        self.assertEqual(april["monthly_amount"], Decimal("0.00"))
        self.assertEqual(april["amount_to_revise"], Decimal("0.00"))
        self.assertEqual(april["current_index"], Decimal("348.70000000"))
        self.assertIsNotNone(april["ratio"])
        self.assertEqual(april["revision_amount"], Decimal("0.00"))

    def test_zero_total_blocks_calculation(self):
        statement = self.make_statement()
        self.add_month(statement, 2026, 8, "0")
        result = calculate_statement_preview(statement)
        self.assertEqual(result["calculation_status"], "NO_WORK_DAYS")
        self.assertEqual(result["message"], "Aucun jour de travaux n'a été renseigné pour ce décompte.")

    def test_api_simple_statement_allocation_and_calculation_do_not_require_bdp(self):
        response = self.client.post(f"/api/markets/{self.market.id}/statements/", {"number": 1, "date": "2026-08-31", "amount_ht": "535776.00", "observation": "V1"}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        statement_id = response.data["id"]
        for month in range(4, 9):
            allocation = self.client.post(f"/api/markets/{self.market.id}/statements/{statement_id}/allocations/", {"year": 2026, "month": month, "work_days": "30.00" if month == 8 else "0.00"}, format="json")
            self.assertEqual(allocation.status_code, 201, allocation.data)
        calculation = self.client.get(f"/api/markets/{self.market.id}/statements/{statement_id}/calculation/")
        self.assertEqual(calculation.status_code, 200, calculation.data)
        self.assertEqual(calculation.data["total_allocated_amount"], Decimal("535776.00"))
        self.assertEqual(calculation.data["monthly_results"][-1]["monthly_amount"], Decimal("535776.00"))

    def test_api_requires_market_permission_for_statement_creation(self):
        member = get_user_model().objects.create_user("v1-statement-member@example.com", "password-123")
        Membership.objects.create(user=member, company=self.market.company, role=Membership.Role.MEMBER)
        client = APIClient()
        client.force_authenticate(member)
        response = client.post(f"/api/markets/{self.market.id}/statements/", {"number": 1, "date": "2026-08-31", "amount_ht": "1.00"}, format="json")
        self.assertEqual(response.status_code, 403)
