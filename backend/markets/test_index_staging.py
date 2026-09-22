from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from companies.models import Company, Membership

from .models import ExternalIndexStaging, IndexDefinition, IndexPublication, MonthlyIndexValue
from .revisiondesprix_client import ExternalIndexEvolutionPoint, ExternalIndexName, ExternalIndexValue
from .staging import compare_evolution, stage_catalogue, stage_year


def external(code="BAT3", value="337.8", year=2025, month=11):
    return ExternalIndexValue(1, date(year, month, 1), code, Decimal(value), month, year, 3, True, datetime(2026, 5, 6, tzinfo=timezone.utc))


class ExternalIndexStagingTests(TestCase):
    def setUp(self):
        self.definition, _ = IndexDefinition.objects.get_or_create(code="BAT3", defaults={"designation": "Électricité", "domain": "BAT"})
        self.publication, _ = IndexPublication.objects.get_or_create(year=2025, month=11, defaults={"document_reference": "Local contrôlé", "status": "VALIDATED"})
        self.local, _ = MonthlyIndexValue.objects.get_or_create(index_definition=self.definition, year=2025, month=11, defaults={"publication": self.publication, "value": Decimal("337.8"), "status": "PENDING_VALIDATION"})
        self.client = Mock()
        self.client.get_index_names.return_value = [ExternalIndexName("BAT3"), ExternalIndexName("UNKNOWN")]
        self.client.get_indices_for_year.return_value = [external(), external("UNKNOWN", "12.3")]

    def test_catalogue_stages_matched_and_missing_without_creating_definition(self):
        result = stage_catalogue(self.client)
        self.assertEqual(result["matched"], 1)
        self.assertEqual(result["missing_local"], 1)
        self.assertFalse(IndexDefinition.objects.filter(code="UNKNOWN").exists())
        self.assertEqual(ExternalIndexStaging.objects.count(), 2)

    def test_year_match_is_decimal_and_does_not_write_official_value(self):
        before = MonthlyIndexValue.objects.count()
        result = stage_year(self.client, 2025)
        self.assertEqual(result["matched"], 1)
        self.assertEqual(result["missing_local"], 1)
        self.assertEqual(MonthlyIndexValue.objects.count(), before)
        row = ExternalIndexStaging.objects.get(external_code="BAT3", year=2025, month=11)
        self.assertEqual(row.normalized_value, Decimal("337.8"))
        self.assertEqual(row.comparison_status, "MATCHED")
        self.assertEqual(row.validation_status, "PENDING_VALIDATION")

    def test_conflict_and_idempotence(self):
        stage_year(self.client, 2025)
        self.client.get_indices_for_year.return_value = [external(value="338.0")]
        stage_year(self.client, 2025)
        row = ExternalIndexStaging.objects.get(external_code="BAT3", year=2025, month=11)
        self.assertEqual(row.comparison_status, "CONFLICT")
        self.assertTrue(row.source_changed)
        self.assertEqual(row.previous_normalized_value, Decimal("337.8"))
        stage_year(self.client, 2025)
        self.assertEqual(ExternalIndexStaging.objects.filter(external_code="BAT3", year=2025, month=11).count(), 1)

    def test_dry_run_writes_nothing(self):
        result = stage_year(self.client, 2025, dry_run=True)
        self.assertEqual(result["values"], 2)
        self.assertEqual(ExternalIndexStaging.objects.count(), 0)
        self.assertEqual(MonthlyIndexValue.objects.count(), 1)

    def test_evolution_comparison_reports_conflict_and_missing_endpoint(self):
        self.client.get_index_evolution.return_value = [ExternalIndexEvolutionPoint(date(2025, 11, 1), Decimal("337.8"), "11/2025")]
        result = compare_evolution(self.client, year_values=[external(), external("BAT3", "340.0", 2025, 12)], code="BAT3")
        self.assertEqual([item["status"] for item in result], ["MATCHED", "MISSING_EVOLUTION_ENDPOINT"])

    def test_command_dry_run_does_not_write_database(self):
        fake = Mock()
        fake.get_index_names.return_value = [ExternalIndexName("BAT3")]
        fake.get_indices_for_year.return_value = [external()]
        fake.get_index_evolution.return_value = [ExternalIndexEvolutionPoint(date(2025, 11, 1), Decimal("337.8"), "11/2025")]
        with patch("markets.management.commands.sync_revision_indices.RevisionDesPrixApiClient", return_value=fake):
            call_command("sync_revision_indices", "--dry-run", "--year", "2025", "--code", "BAT3")
        self.assertEqual(ExternalIndexStaging.objects.count(), 0)
        self.assertEqual(MonthlyIndexValue.objects.count(), 1)

    def test_staging_api_requires_authentication_and_active_membership(self):
        self.assertEqual(APIClient().get("/api/indices/staging/").status_code, 401)
        user = get_user_model().objects.create_user("staging@example.com", "password-123")
        company = Company.objects.create(raison_sociale="Staging Company")
        Membership.objects.create(user=user, company=company, role=Membership.Role.MEMBER)
        client = APIClient()
        client.force_authenticate(user)
        response = client.get("/api/indices/staging/?page=1&page_size=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["page_size"], 1)
        self.assertEqual(response.data["count"], 0)
        self.assertFalse(response.data["has_next"])
