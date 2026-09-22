from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from django.test import TestCase

from .index_importer import DocumentResult, RawRow, extract_rows, parse_decimal, sha256_file
from .models import ExternalIndexStaging, IndexDefinition, IndexPublication, IndexSourceDocument, IndexValidationAudit, MonthlyIndexValue, OfficialExtractedValue
from .official_validation import OfficialIndexValidationService, comparison_status
from .services import resolve_index


class OfficialIndexValidationTests(TestCase):
    def setUp(self):
        self.definition, _ = IndexDefinition.objects.get_or_create(code="BAT3", defaults={"designation": "Électricité", "domain": "BAT"})
        self.publication = IndexPublication.objects.create(year=2025, month=11, source_type=IndexPublication.SourceType.EXTERNAL_SECONDARY, document_reference="API secondaire", status=IndexPublication.Status.PENDING_VALIDATION)
        self.official_publication, _ = IndexPublication.objects.get_or_create(year=2025, month=11, source_type=IndexPublication.SourceType.OFFICIAL, defaults={"document_reference": "Barème novembre 2025", "status": IndexPublication.Status.PENDING_VALIDATION})
        self.seed_local, _ = MonthlyIndexValue.objects.get_or_create(index_definition=self.definition, year=2025, month=11, defaults={"publication": self.official_publication, "value": Decimal("337.8"), "status": MonthlyIndexValue.Status.PENDING_VALIDATION})
        ExternalIndexStaging.objects.create(source_endpoint="/indices?year=2025", retrieved_at="2026-09-22T00:00:00Z", external_code="BAT3", year=2025, month=11, raw_value="337.8", normalized_value=Decimal("337.8"), raw_payload_hash="a" * 64)

    def row(self, value="337,8", code="BAT3", ambiguity=""):
        return RawRow(8, code, "Electricité", value, "1", "DEFINITIVE" if not ambiguity else "PENDING_VALIDATION", "NATIVE_TEXT", "0.99", ambiguity, code if code == "BAT3" else "", str(Decimal(value.replace(",", "."))) if not ambiguity else None, "DEFINITIVE" if not ambiguity else "PENDING_VALIDATION")

    def result(self, path, row=None):
        return DocumentResult(path.name, "b" * 64, path.stat().st_size, 8, ["2025-11", "2025-12", "2026-01"], "NATIVE_TEXT", "PROCESSED", [row or self.row()], source_reference=str(path))

    def test_native_text_extracts_decimal_and_all_columns(self):
        rows = extract_rows("Electricité BAT3 337,8 337,8 340,0\nAcier BATX 1,2 1,3 1,4", "NATIVE_TEXT", ["2025-11", "2025-12", "2026-01"])
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0].normalized_value, "337.8")
        self.assertEqual(rows[0].validation_status, "DEFINITIVE")
        self.assertEqual(rows[3].validation_status, "PENDING_VALIDATION")

    def test_sha256_is_stable(self):
        with NamedTemporaryFile() as stream:
            stream.write(b"official pdf bytes")
            stream.flush()
            self.assertEqual(sha256_file(Path(stream.name)), sha256_file(Path(stream.name)))

    def test_triple_comparison_classifications(self):
        self.assertEqual(comparison_status(Decimal("1"), Decimal("1"), Decimal("1")), "ALL_MATCH")
        self.assertEqual(comparison_status(Decimal("1"), Decimal("1"), None), "OFFICIAL_API_MATCH_LOCAL_MISSING")
        self.assertEqual(comparison_status(Decimal("1"), Decimal("2"), Decimal("1")), "OFFICIAL_LOCAL_MATCH_API_CONFLICT")
        self.assertEqual(comparison_status(Decimal("1"), Decimal("2"), Decimal("3")), "OFFICIAL_API_CONFLICT")
        self.assertEqual(comparison_status(None, Decimal("1"), Decimal("1"), pending=True), "PENDING_VALIDATION")

    def test_apply_promotes_existing_pending_without_recreating_and_audits(self):
        local = MonthlyIndexValue.objects.get(index_definition=self.definition, year=2025, month=11)
        local.publication = self.publication
        local.value = Decimal("337.8")
        local.status = MonthlyIndexValue.Status.PENDING_VALIDATION
        local.save(update_fields=["publication", "value", "status", "updated_at"])
        with NamedTemporaryFile(suffix="-novembre-2025.pdf") as stream, patch.dict("os.environ", {"DJANGO_ENV": "test"}), patch("markets.official_validation.analyse_pdf") as analyse:
            stream.write(b"pdf")
            stream.flush()
            analyse.return_value = self.result(Path(stream.name))
            plan, outcome = OfficialIndexValidationService(Path(stream.name)).apply()
        self.assertEqual(outcome["event"], "APPLIED")
        local.refresh_from_db()
        self.assertEqual(local.status, MonthlyIndexValue.Status.DEFINITIVE)
        resolved = resolve_index("BAT3", 2025, 11)
        self.assertEqual(resolved["status"], MonthlyIndexValue.Status.DEFINITIVE)
        self.assertEqual(resolved["source_type"], IndexPublication.SourceType.OFFICIAL)
        self.assertEqual(resolved["value"], "337.80000000")
        self.assertEqual(MonthlyIndexValue.objects.filter(pk=local.pk).count(), 1)
        self.assertEqual(IndexValidationAudit.objects.filter(monthly_value=local).count(), 1)
        self.assertEqual(IndexPublication.objects.filter(source_type=IndexPublication.SourceType.OFFICIAL, year=2025, month=11).count(), 1)

    def test_duplicate_document_is_noop(self):
        IndexSourceDocument.objects.create(sha256="b" * 64, original_filename="old.pdf", nominal_year=2025, nominal_month=11, file_size=3, source_reference="old", extraction_method="NATIVE_TEXT", extraction_status="PROCESSED")
        with NamedTemporaryFile(suffix="-novembre-2025.pdf") as stream, patch.dict("os.environ", {"DJANGO_ENV": "test"}), patch("markets.official_validation.sha256_file", return_value="b" * 64), patch("markets.official_validation.analyse_pdf") as analyse:
            analyse.return_value = self.result(Path(stream.name))
            _, outcome = OfficialIndexValidationService(Path(stream.name)).apply()
        self.assertEqual(outcome["event"], "DOCUMENT_DUPLICATE_DETECTED")
        self.assertEqual(IndexPublication.objects.filter(source_type=IndexPublication.SourceType.OFFICIAL).count(), 1)

    def test_local_conflict_never_updates_value(self):
        local = MonthlyIndexValue.objects.get(index_definition=self.definition, year=2025, month=11)
        local.publication = self.publication
        local.value = Decimal("338.0")
        local.status = MonthlyIndexValue.Status.PENDING_VALIDATION
        local.save(update_fields=["publication", "value", "status", "updated_at"])
        with NamedTemporaryFile(suffix="-novembre-2025.pdf") as stream, patch.dict("os.environ", {"DJANGO_ENV": "test"}), patch("markets.official_validation.analyse_pdf") as analyse:
            stream.write(b"pdf")
            stream.flush()
            analyse.return_value = self.result(Path(stream.name))
            OfficialIndexValidationService(Path(stream.name)).apply()
        local.refresh_from_db()
        self.assertEqual(local.value, Decimal("338.0"))
        self.assertEqual(local.status, MonthlyIndexValue.Status.PENDING_VALIDATION)
