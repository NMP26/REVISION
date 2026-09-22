from datetime import date, datetime, timezone
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase

from companies.models import Company

from .models import ExternalIndexStaging, IndexDefinition, IndexPublication, Market, MarketFormula, MonthlyIndexValue, RevisionGroup, FormulaTerm
from .promotion import IndexPromotionService, normalize_code
from .services import resolve_base_index, resolve_index


def staged(code="BAT3", value="337.8", year=2025, month=11, designation=None, comparison="MISSING_LOCAL"):
    return ExternalIndexStaging.objects.create(
        source_endpoint=f"/api/indices?year={year}",
        retrieved_at=datetime(2026, 9, 22, tzinfo=timezone.utc),
        external_code=code,
        external_designation=designation,
        year=year,
        month=month,
        raw_value=value,
        normalized_value=Decimal(value) if value is not None else None,
        raw_payload_hash=(code + str(year) + str(month) + str(value or ""))[:64].ljust(64, "0"),
        comparison_status=comparison,
    )


class IndexPromotionTests(TestCase):
    def setUp(self):
        self.definition, _ = IndexDefinition.objects.get_or_create(code="BAT3", defaults={"designation": "Électricité", "domain": "BAT"})
        self.publication, _ = IndexPublication.objects.get_or_create(year=2025, month=11, source_type=IndexPublication.SourceType.OFFICIAL, defaults={"document_reference": "Contrôle local", "status": IndexPublication.Status.PENDING_VALIDATION})
        self.local, _ = MonthlyIndexValue.objects.get_or_create(
            index_definition=self.definition, year=2025, month=11,
            defaults={"publication": self.publication, "value": Decimal("337.8"), "status": MonthlyIndexValue.Status.PENDING_VALIDATION},
        )
        if self.local.status != MonthlyIndexValue.Status.PENDING_VALIDATION:
            self.local.status = MonthlyIndexValue.Status.PENDING_VALIDATION
            self.local.save(update_fields=["status", "updated_at"])

    def test_normalize_code_only_trims_and_applies_case(self):
        self.assertEqual(normalize_code(" BAT3 "), "BAT3")
        self.assertEqual(normalize_code("b4t3"), "B4T3")

    def test_dry_run_does_not_write_and_identical_value_is_no_change(self):
        row = staged()
        before = MonthlyIndexValue.objects.count()
        plan = IndexPromotionService(year=2025, code="BAT3").plan()
        self.assertEqual(len(plan.values_already_identical), 1)
        self.assertEqual(len(plan.values_to_create), 0)
        self.assertEqual(MonthlyIndexValue.objects.count(), before)
        self.assertEqual(ExternalIndexStaging.objects.get(pk=row.pk).normalized_value, Decimal("337.8"))

    def test_conflict_is_never_overwritten(self):
        staged(value="340.1", comparison="CONFLICT")
        plan = IndexPromotionService(year=2025, code="BAT3").plan()
        self.assertEqual(len(plan.conflicts), 1)
        self.assertEqual(self.local.value, Decimal("337.8"))

    def test_candidate_definition_and_pending_secondary_value_are_idempotent(self):
        ExternalIndexStaging.objects.create(
            source_endpoint="/api/indices/names", retrieved_at=datetime(2026, 9, 22, tzinfo=timezone.utc),
            external_code="NEW1", external_designation="Nouvel indice", raw_payload_hash="1" * 64,
        )
        staged(code="NEW1", value="12.30", year=2026, month=1, designation="Nouvel indice")
        service = IndexPromotionService(year=2026, code="NEW1")
        plan = service.plan()
        self.assertEqual(plan.summary["index_definitions_to_create"], 1)
        self.assertEqual(plan.summary["values_to_create"], 0)
        plan, applied = service.apply()
        self.assertEqual(applied, {"index_definitions_created": 1, "monthly_values_created": 1})
        value = MonthlyIndexValue.objects.get(index_definition__code="NEW1", year=2026, month=1)
        self.assertEqual(value.value, Decimal("12.30"))
        self.assertEqual(value.status, MonthlyIndexValue.Status.PENDING_VALIDATION)
        self.assertEqual(value.publication.source_type, IndexPublication.SourceType.EXTERNAL_SECONDARY)
        self.assertIn("staging=", value.source_reference)
        _, reapplied = service.apply()
        self.assertEqual(reapplied, {"index_definitions_created": 0, "monthly_values_created": 0})
        self.assertEqual(MonthlyIndexValue.objects.filter(index_definition__code="NEW1").count(), 1)

    def test_missing_month_has_no_fallback(self):
        staged(code="BAT3", value="340.0", year=2026, month=1)
        self.assertEqual(resolve_index("BAT3", 2026, 2)["status"], "INDEX_NOT_AVAILABLE")

    def test_base_index_reports_pending_status_without_hardcoding(self):
        user = get_user_model().objects.create_user("idx-owner@example.com", "password-123")
        company = Company.objects.create(raison_sociale="Société test")
        market = Market.objects.create(company=company, market_number="10006299/4500004338", contracting_authority="Agadir", subject="Travaux", date_limite_remise_offres=date(2025, 11, 19), formula_structure=Market.FormulaStructure.SINGLE)
        group = RevisionGroup.objects.create(market=market, code="BAT3", name="Électricité")
        formula = MarketFormula.objects.create(revision_group=group, version_number=1, label="BAT3", constant_term=Decimal("0.15"), created_by=user)
        FormulaTerm.objects.create(formula=formula, position=1, coefficient=Decimal("0.85"), index_code="BAT3")
        result = resolve_base_index(market, formula)
        self.assertEqual(result["base_month"], "2025-11")
        self.assertEqual(result["base_index_value"], "337.80000000")
        self.assertEqual(result["base_index_status"], MonthlyIndexValue.Status.PENDING_VALIDATION)
