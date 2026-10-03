from datetime import date
from collections import Counter
from decimal import Decimal
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch
from unittest import skipUnless

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from companies.models import Company, Membership

from .index_importer import AMBIGUOUS, STRUCTURAL_MATCH, DocumentResult, RawRow, resolve_extracted_code
from .models import FormulaTerm, IndexDefinition, IndexPublication, IndexSourceDocument, IndexValidationAudit, Market, MarketFormula, MonthlyIndexValue, MonthlyWorkAllocation, OfficialDiscoveryCheck, OfficialExtractedValue, RevisionGroup, Statement
from .official_ingestion import OfficialIngestionError, Provenance, _preview, check_official_publications, create_official_definition, ingest_official_bareme, validate_official_bareme
from .services import resolve_calculation_index, resolve_index
from .statement_services import calculate_statement_preview


class OfficialIngestionTests(TestCase):
    def setUp(self):
        self.definition, _ = IndexDefinition.objects.get_or_create(code="BAT3", defaults={"designation": "Électricité", "domain": "BAT"})

    def fake_result(self, path, value="351.4", code="BAT3", ambiguity=""):
        row = RawRow(1, code, "Électricité", value, "1", "DEFINITIVE", "NATIVE_TEXT", "0.99", ambiguity, code, value, "DEFINITIVE")
        return DocumentResult(path.name, "unused", path.stat().st_size, 1, ["2026-05"], "NATIVE_TEXT", "PROCESSED", [row], source_reference=str(path))

    def pdf(self, name="Bareme-mai-2026.pdf"):
        stream = NamedTemporaryFile(suffix=name)
        stream.write(b"%PDF-1.7\nplaceholder")
        stream.flush()
        self.addCleanup(stream.close)
        return Path(stream.name)

    def test_short_code_resolution_uses_designation_structure(self):
        py, _ = IndexDefinition.objects.get_or_create(code="Py", defaults={"designation": "Polyester en plaques", "domain": "OFFICIAL"})
        pv, _ = IndexDefinition.objects.get_or_create(code="Pv", defaults={"designation": "Peinture-Vitrerie", "domain": "OFFICIAL"})
        resolution = resolve_extracted_code("Py", "VI Penn VIRE", [py, pv])
        self.assertEqual(resolution.code, "Pv")
        self.assertEqual(resolution.method, STRUCTURAL_MATCH)

    def test_short_code_tie_remains_ambiguous(self):
        py = IndexDefinition.objects.create(code="Pxa", designation="Produit court", domain="OFFICIAL")
        pv = IndexDefinition.objects.create(code="Pxb", designation="Produit court", domain="OFFICIAL")
        resolution = resolve_extracted_code("P?", "Produit court", [py, pv])
        self.assertEqual(resolution.method, AMBIGUOUS)
        self.assertEqual(set(resolution.candidates), {"Pxa", "Pxb"})

    def test_manual_resolution_is_audited_and_never_reextracts(self):
        first = IndexDefinition.objects.create(code="Pxa", designation="Produit court", domain="OFFICIAL")
        IndexDefinition.objects.create(code="Pxb", designation="Produit court", domain="OFFICIAL")
        path = self.pdf()
        row = RawRow(1, "P?", "Produit court", "12,3", "1", "PENDING_VALIDATION", "OCR", "0.50", "CODE_AMBIGUOUS", "", "12.3", "PENDING_VALIDATION")
        result = DocumentResult(path.name, "unused", path.stat().st_size, 1, ["2026-05"], "OCR", "PENDING_VALIDATION", [row], source_reference=str(path))
        with patch("markets.official_ingestion.analyse_pdf", return_value=result):
            imported = ingest_official_bareme(path)
        user = get_user_model().objects.create_user("resolver@example.com", "password-123")
        company = Company.objects.create(raison_sociale="Resolver Company")
        Membership.objects.create(user=user, company=company, role=Membership.Role.OWNER)
        client = APIClient(); client.force_authenticate(user)
        row_id = imported["preview"]["rows"][0]["id"]
        response = client.post(f"/api/indices/official-imports/{imported['preview']['document_id']}/rows/{row_id}/resolve/", {"index_definition": str(first.id)}, format="json")
        self.assertEqual(response.status_code, 200)
        resolved = OfficialExtractedValue.objects.get(pk=row_id)
        self.assertEqual(resolved.resolution_method, "MANUAL")
        self.assertEqual(resolved.resolved_index_definition_id, first.id)
        self.assertEqual(resolved.resolved_by_id, user.id)
        self.assertIsNotNone(resolved.resolved_at)
        validated = validate_official_bareme(imported["preview"]["document_id"], actor=user)
        self.assertEqual(validated["validation_status"], "VALIDATED")

    def test_new_official_code_requires_confirmation_then_is_created_transactionally(self):
        path = self.pdf()
        row = RawRow(1, "Aa", "", "12,3", "1", "DEFINITIVE", "OCR", "0.99", "", "Aa", "12.3", "DEFINITIVE")
        result = DocumentResult(path.name, "unused", path.stat().st_size, 1, ["2026-05"], "OCR", "PENDING_VALIDATION", [row], source_reference=str(path))
        with patch("markets.official_ingestion.analyse_pdf", return_value=result):
            imported = ingest_official_bareme(path)
        self.assertEqual(imported["preview"]["rows"][0]["status"], "NEW_OFFICIAL_CODE")
        self.assertFalse(IndexDefinition.objects.filter(code="Aa").exists())
        user = get_user_model().objects.create_user("catalogue@example.com", "password-123")
        company = Company.objects.create(raison_sociale="Catalogue Company")
        Membership.objects.create(user=user, company=company, role=Membership.Role.OWNER)
        client = APIClient(); client.force_authenticate(user)
        row_id = imported["preview"]["rows"][0]["id"]
        response = client.post(f"/api/indices/official-imports/{imported['preview']['document_id']}/rows/{row_id}/create-definition/", {"designation": ""}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(IndexDefinition.objects.filter(code="Aa", designation="").exists())
        validated = validate_official_bareme(imported["preview"]["document_id"], actor=user)
        self.assertEqual(validated["validation_status"], "VALIDATED")
        value = MonthlyIndexValue.objects.get(index_definition__code="Aa", year=2026, month=5)
        self.assertEqual(value.status, MonthlyIndexValue.Status.DEFINITIVE)

    @skipUnless(Path("/tmp/Bareme-mai-2026.pdf").exists(), "PDF officiel mai non monté")
    def test_real_may_pdf_bootstraps_catalogue_in_test_database(self):
        imported = ingest_official_bareme(Path("/tmp/Bareme-mai-2026.pdf"))
        preview = imported["preview"]
        for row in preview["rows"]:
            if row["status"] == "NEW_OFFICIAL_CODE":
                create_official_definition(preview["document_id"], row["id"], row["designation"])
            elif row["status"] == "AMBIGUOUS":
                corrected = {"BATI": "BAT1", "BATS": "BAT5"}.get(row["raw_extracted_code"])
                self.assertIsNotNone(corrected, row)
                create_official_definition(preview["document_id"], row["id"], row["designation"], code=corrected)
        refreshed = _preview(IndexSourceDocument.objects.get(pk=preview["document_id"]))
        self.assertEqual(refreshed["blocking_issues"], 0, refreshed)
        validated = validate_official_bareme(preview["document_id"])
        self.assertEqual(validated["validation_status"], "VALIDATED")
        self.assertEqual(MonthlyIndexValue.objects.get(index_definition__code="BAT3", year=2026, month=5).value, Decimal("348.5"))

    @skipUnless(Path("/tmp/Bareme-mai-2026.pdf").exists() and Path("/tmp/Bareme-avril-2026.pdf").exists(), "PDF officiels non montés")
    def test_real_april_reuses_catalogue_after_may(self):
        may = ingest_official_bareme(Path("/tmp/Bareme-mai-2026.pdf"))["preview"]
        print("MAY_PREVIEW_COUNTS", {key: may[key] for key in ("cells_detected", "rows_detected", "valid_index_value_pairs", "unique_index_codes", "blocking_issues")})
        print("MAY_STATUS_COUNTS", dict(Counter(row["status"] for row in may["rows"])))
        for row in may["rows"]:
            if row["status"] == "NEW_OFFICIAL_CODE":
                create_official_definition(may["document_id"], row["id"], row["designation"])
            elif row["status"] == "AMBIGUOUS":
                create_official_definition(may["document_id"], row["id"], row["designation"], code={"BATI": "BAT1", "BATS": "BAT5"}[row["raw_extracted_code"]])
            elif row["status"] == "CONFLICT":
                create_official_definition(may["document_id"], row["id"], row["designation"], code=row["code"])
        validate_official_bareme(may["document_id"])
        april = ingest_official_bareme(Path("/tmp/Bareme-avril-2026.pdf"))["preview"]
        print("APRIL_PREVIEW_AFTER_MAY_COUNTS", {key: april[key] for key in ("cells_detected", "rows_detected", "valid_index_value_pairs", "unique_index_codes", "blocking_issues")})
        print("APRIL_STATUS_COUNTS", dict(Counter(row["status"] for row in april["rows"])))
        for row in april["rows"]:
            if row["status"] == "NEW_OFFICIAL_CODE":
                create_official_definition(april["document_id"], row["id"], row["designation"])
            elif row["status"] == "AMBIGUOUS":
                corrected = {"BATI": "BAT1", "BATS": "BAT5"}.get(row["raw_extracted_code"], row["code"])
                self.assertTrue(corrected, row)
                create_official_definition(april["document_id"], row["id"], row["designation"], code=corrected)
            elif row["status"] == "CONFLICT":
                create_official_definition(april["document_id"], row["id"], row["designation"], code=row["code"])
        april_after = _preview(IndexSourceDocument.objects.get(pk=april["document_id"]))
        print("APRIL_AFTER_MAY_BLOCKERS", [row for row in april_after["rows"] if row["status"] in {"AMBIGUOUS", "UNKNOWN_CODE", "NEW_OFFICIAL_CODE", "CONFLICT"}])
        validated = validate_official_bareme(april["document_id"])
        print("APRIL_MAY_COUNTS", {"april_values": MonthlyIndexValue.objects.filter(year=2026, month=4).count(), "april_definitions": IndexDefinition.objects.count(), "may_values": MonthlyIndexValue.objects.filter(year=2026, month=5).count(), "may_definitive": MonthlyIndexValue.objects.filter(year=2026, month=5, status=MonthlyIndexValue.Status.DEFINITIVE).count(), "may_bat3": resolve_index("BAT3", 2026, 5), "april_bat3": resolve_index("BAT3", 2026, 4)})
        self.assertEqual(validated["validation_status"], "VALIDATED")

    @skipUnless(Path("/tmp/Bareme-mai-2026.pdf").exists() and Path("/tmp/Bareme-avril-2026.pdf").exists(), "PDF officiels non montés")
    def test_real_april_then_may_bootstraps_and_reuses_catalogue(self):
        april = ingest_official_bareme(Path("/tmp/Bareme-avril-2026.pdf"))["preview"]
        print("APRIL_FIRST_PREVIEW_COUNTS", {key: april[key] for key in ("cells_detected", "rows_detected", "valid_index_value_pairs", "unique_index_codes", "blocking_issues")})
        print("APRIL_FIRST_STATUS_COUNTS", dict(Counter(row["status"] for row in april["rows"])))
        for row in april["rows"]:
            if row["status"] == "NEW_OFFICIAL_CODE":
                create_official_definition(april["document_id"], row["id"], row["designation"])
            elif row["status"] == "AMBIGUOUS":
                create_official_definition(april["document_id"], row["id"], row["designation"], code={"BATI": "BAT1", "BATS": "BAT5"}[row["raw_extracted_code"]])
        april_after = _preview(IndexSourceDocument.objects.get(pk=april["document_id"]))
        print("APRIL_FIRST_AFTER_RESOLUTION", {"blocking_issues": april_after["blocking_issues"], "definitions": IndexDefinition.objects.count()})
        validate_official_bareme(april["document_id"])

        may = ingest_official_bareme(Path("/tmp/Bareme-mai-2026.pdf"))["preview"]
        print("MAY_AFTER_APRIL_PREVIEW_COUNTS", {key: may[key] for key in ("cells_detected", "rows_detected", "valid_index_value_pairs", "unique_index_codes", "blocking_issues")})
        print("MAY_AFTER_APRIL_STATUS_COUNTS", dict(Counter(row["status"] for row in may["rows"])))
        print("MAY_AFTER_APRIL_AMBIGUOUS_ROWS", [(row["raw_extracted_code"], row["code"], row.get("resolution_candidates"), row["designation"], row["value"]) for row in may["rows"] if row["status"] == "AMBIGUOUS"])
        for row in may["rows"]:
            if row["status"] == "NEW_OFFICIAL_CODE":
                create_official_definition(may["document_id"], row["id"], row["designation"])
            elif row["status"] == "AMBIGUOUS":
                corrected = {"cf": "cf", "Hb": "Hb", "Cv": "Cv", "Biv": "Biv", "Cy": "Cy", "Smr": "Smr", "Ck": "Ck", "Mtn": "Mtn", "Mes": "Mes", "Ale": "Ale", "Em": "Em", "BATI": "BAT1", "BATS": "BAT5", "CEPI": "CEP1"}.get(row["raw_extracted_code"])
                if corrected is None:
                    candidates = row.get("resolution_candidates") or []
                    self.fail(f"No explicit manual fixture for ambiguous row: {row}; candidates={candidates}")
                create_official_definition(may["document_id"], row["id"], row["designation"], code=corrected)
        may_after = _preview(IndexSourceDocument.objects.get(pk=may["document_id"]))
        print("APRIL_MAY_FORWARD_COUNTS", {"april_values": MonthlyIndexValue.objects.filter(year=2026, month=4).count(), "may_blocking": may_after["blocking_issues"], "may_values": MonthlyIndexValue.objects.filter(year=2026, month=5).count()})
        validate_official_bareme(may["document_id"])
        print("APRIL_MAY_FORWARD_RESOLVED", {"definitions": IndexDefinition.objects.count(), "april_values": MonthlyIndexValue.objects.filter(year=2026, month=4).count(), "may_values": MonthlyIndexValue.objects.filter(year=2026, month=5).count(), "april_bat3": resolve_index("BAT3", 2026, 4), "may_bat3": resolve_index("BAT3", 2026, 5)})

    @skipUnless(Path("/tmp/Bareme-avril-2026.pdf").exists(), "PDF officiel avril non monté")
    def test_real_april_diagnostics(self):
        preview = ingest_official_bareme(Path("/tmp/Bareme-avril-2026.pdf"))["preview"]
        for row in preview["rows"]:
            if row["status"] == "NEW_OFFICIAL_CODE":
                create_official_definition(preview["document_id"], row["id"], row["designation"])
        refreshed = _preview(IndexSourceDocument.objects.get(pk=preview["document_id"]))
        print("APRIL_DIAGNOSTICS", {key: refreshed[key] for key in ("cells_detected", "rows_detected", "unique_index_codes", "valid_index_value_pairs", "blocking_issues")})
        print("APRIL_BLOCKERS", [row for row in refreshed["rows"] if row["status"] in {"AMBIGUOUS", "UNKNOWN_CODE", "NEW_OFFICIAL_CODE", "CONFLICT"}])
        for row in refreshed["rows"]:
            if row["status"] == "AMBIGUOUS":
                create_official_definition(preview["document_id"], row["id"], row["designation"], code={"BATI": "BAT1", "BATS": "BAT5"}[row["raw_extracted_code"]])
        validated = validate_official_bareme(preview["document_id"])
        print("APRIL_VALIDATED", {"definitions": IndexDefinition.objects.count(), "values": MonthlyIndexValue.objects.filter(year=2026, month=4).count(), "definitive": MonthlyIndexValue.objects.filter(year=2026, month=4, status=MonthlyIndexValue.Status.DEFINITIVE).count(), "audits": IndexValidationAudit.objects.filter(publication__year=2026, publication__month=4).count(), "bat3": resolve_index("BAT3", 2026, 4)})

    def test_manual_upload_preview_stays_pending_and_hash_is_recorded(self):
        path = self.pdf()
        with patch("markets.official_ingestion.analyse_pdf", side_effect=lambda path, source_reference="": self.fake_result(path)):
            outcome = ingest_official_bareme(path)
        self.assertEqual(outcome["event"], "PENDING_VALIDATION")
        document = IndexSourceDocument.objects.get()
        self.assertEqual(document.validation_status, "PENDING_VALIDATION")
        self.assertEqual(document.import_method, "MANUAL")
        self.assertEqual(len(outcome["preview"]["sha256"]), 64)
        self.assertEqual(outcome["preview"]["rows"][0]["status"], "OK")

    def test_all_recognized_indices_are_kept_as_decimal_candidates(self):
        IndexDefinition.objects.get_or_create(code="BAT6", defaults={"designation": "Main-d'œuvre", "domain": "BAT"})
        path = self.pdf()
        def result(path, source_reference=""):
            rows = [
                RawRow(1, "BAT3", "Électricité", "351,4", "1", "DEFINITIVE", "NATIVE_TEXT", "0.99", "", "BAT3", "351.4", "DEFINITIVE"),
                RawRow(1, "BAT6", "Main-d'œuvre", "212,7", "1", "DEFINITIVE", "NATIVE_TEXT", "0.99", "", "BAT6", "212.7", "DEFINITIVE"),
            ]
            return DocumentResult(path.name, "unused", path.stat().st_size, 1, ["2026-05"], "NATIVE_TEXT", "PROCESSED", rows, source_reference=str(path))
        with patch("markets.official_ingestion.analyse_pdf", side_effect=result):
            outcome = ingest_official_bareme(path)
        self.assertEqual(outcome["preview"]["count"], 2)
        self.assertEqual({row["code"] for row in outcome["preview"]["rows"]}, {"BAT3", "BAT6"})
        self.assertEqual(Decimal("212.7"), outcome["preview"]["rows"][1]["value"] and Decimal(outcome["preview"]["rows"][1]["value"]))

    def test_invalid_pdf_is_rejected(self):
        with NamedTemporaryFile(suffix=".pdf") as stream:
            stream.write(b"not a pdf")
            stream.flush()
            with self.assertRaises(OfficialIngestionError) as raised:
                ingest_official_bareme(Path(stream.name))
        self.assertEqual(raised.exception.code, "INVALID_PDF")

    def test_same_hash_is_noop_and_same_period_different_hash_is_conflict(self):
        path = self.pdf()
        with patch("markets.official_ingestion.analyse_pdf", side_effect=lambda path, source_reference="": self.fake_result(path)):
            first = ingest_official_bareme(path)
            duplicate = ingest_official_bareme(path)
        self.assertEqual(first["event"], "PENDING_VALIDATION")
        self.assertEqual(duplicate["event"], "DOCUMENT_ALREADY_IMPORTED")
        second = self.pdf()
        second.write_bytes(b"%PDF-1.7\nsecond-version")
        with patch("markets.official_ingestion.analyse_pdf", side_effect=lambda path, source_reference="": self.fake_result(path)):
            version = ingest_official_bareme(second)
        self.assertEqual(version["preview"]["blocking_issues"], 1)
        self.assertEqual(IndexSourceDocument.objects.count(), 2)

    def test_validation_is_transactional_and_makes_value_eligible(self):
        path = self.pdf()
        with patch("markets.official_ingestion.analyse_pdf", side_effect=lambda path, source_reference="": self.fake_result(path)):
            outcome = ingest_official_bareme(path)
        document_id = outcome["preview"]["document_id"]
        validated = validate_official_bareme(document_id, confirm_conflicts=False)
        self.assertEqual(validated["validation_status"], "VALIDATED")
        value = MonthlyIndexValue.objects.get(index_definition=self.definition, year=2026, month=5)
        self.assertEqual(value.value, Decimal("351.4"))
        self.assertEqual(value.status, MonthlyIndexValue.Status.DEFINITIVE)
        self.assertEqual(IndexPublication.objects.get(pk=validated["publication_id"]).status, IndexPublication.Status.VALIDATED)

    def test_unknown_code_is_proposed_but_not_automatically_created(self):
        path = self.pdf()
        with patch("markets.official_ingestion.analyse_pdf", side_effect=lambda path, source_reference="": self.fake_result(path, code="UNKNOWN")):
            outcome = ingest_official_bareme(path)
        self.assertEqual(outcome["preview"]["rows"][0]["status"], "NEW_OFFICIAL_CODE")
        with self.assertRaises(OfficialIngestionError):
            validate_official_bareme(outcome["preview"]["document_id"])
        self.assertFalse(MonthlyIndexValue.objects.filter(year=2026, month=5).exists())

    @patch("markets.official_ingestion._fetch")
    def test_official_discovery_uses_same_pipeline_and_stays_pending(self, fetch):
        page = b'<a href="/docs/Bareme-mai-2026.pdf">PDF</a>'
        fetch.side_effect = [page, b"%PDF-1.7 official"]
        with patch("markets.official_ingestion.analyse_pdf", side_effect=lambda path, source_reference="": self.fake_result(path)):
            result = check_official_publications()
        self.assertEqual(result["status"], OfficialDiscoveryCheck.Status.AVAILABLE)
        document = IndexSourceDocument.objects.get()
        self.assertEqual(document.import_method, "OFFICIAL_AUTO")
        self.assertEqual(document.validation_status, "PENDING_VALIDATION")

    @patch("markets.official_ingestion._fetch", side_effect=OSError("timeout"))
    def test_official_source_unavailable_does_not_use_external_data(self, fetch):
        result = check_official_publications()
        self.assertEqual(result["status"], OfficialDiscoveryCheck.Status.UNAVAILABLE)
        self.assertFalse(MonthlyIndexValue.objects.filter(year=2026, month=5).exists())

    def test_resolver_ignores_external_publication(self):
        publication = IndexPublication.objects.create(year=2026, month=5, source_type=IndexPublication.SourceType.EXTERNAL_SECONDARY, document_reference="legacy", status=IndexPublication.Status.VALIDATED)
        MonthlyIndexValue.objects.create(index_definition=self.definition, publication=publication, year=2026, month=5, value=Decimal("351.4"), status=MonthlyIndexValue.Status.DEFINITIVE)
        result = resolve_calculation_index("BAT3", 2026, 5)
        self.assertFalse(result["available_for_calculation"])
        self.assertEqual(result["reason"], "INDEX_NOT_AVAILABLE")

    def test_database_first_survives_source_file_removal_for_api_resolver_and_calculation(self):
        user = get_user_model().objects.create_user("database-first@example.com", "password-123")
        company = Company.objects.create(raison_sociale="Database First Company")
        Membership.objects.create(user=user, company=company, role=Membership.Role.OWNER)
        market = Market.objects.create(company=company, market_number="DB-FIRST-001", contracting_authority="Test", subject="Travaux", date_limite_remise_offres=date(2025, 11, 19), formula_structure=Market.FormulaStructure.SINGLE)
        group = RevisionGroup.objects.create(market=market, code="BAT3", name="Électricité")
        formula = MarketFormula.objects.create(revision_group=group, version_number=1, label="BAT3", constant_term=Decimal("0.15"), created_by=user)
        FormulaTerm.objects.create(formula=formula, position=1, coefficient=Decimal("0.85"), index_code="BAT3", base_value=Decimal("337.8"))
        market.global_revision_group = group; market.revision_application_mode = Market.RevisionApplicationMode.GLOBAL_FORMULA; market.save()
        base_publication = IndexPublication.objects.create(year=2025, month=11, source_type=IndexPublication.SourceType.OFFICIAL, document_reference="Base novembre 2025", status=IndexPublication.Status.VALIDATED)
        MonthlyIndexValue.objects.update_or_create(index_definition=self.definition, year=2025, month=11, defaults={"publication": base_publication, "value": Decimal("337.8"), "status": MonthlyIndexValue.Status.DEFINITIVE})
        path = self.pdf("Bareme-mai-2026.pdf")
        with patch("markets.official_ingestion.analyse_pdf", side_effect=lambda path, source_reference="": self.fake_result(path)):
            imported = ingest_official_bareme(path)
        validate_official_bareme(imported["preview"]["document_id"], actor=user)
        stored_file = Path(IndexSourceDocument.objects.get(pk=imported["preview"]["document_id"]).stored_file)
        self.assertTrue(stored_file.exists())
        path.unlink()
        stored_file.unlink()
        response = APIClient().get("/api/indices/values/?code=BAT3&year=2026&month=5")
        self.assertEqual(response.status_code, 401)
        client = APIClient(); client.force_authenticate(user)
        response = client.get("/api/indices/values/?code=BAT3&year=2026&month=5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["value"], "351.40000000")
        resolved = resolve_index("BAT3", 2026, 5)
        self.assertEqual(resolved["value"], "351.40000000")
        statement = Statement.objects.create(market=market, number=1, date=date(2026, 5, 31), amount_ht=Decimal("1000.00"))
        MonthlyWorkAllocation.objects.create(statement=statement, year=2026, month=5, work_days=Decimal("1"))
        calculation = calculate_statement_preview(statement)
        self.assertEqual(calculation["monthly_results"][0]["current_index"], Decimal("351.40000000"))
        self.assertEqual(calculation["calculation_status"], "CALCULABLE_PREVIEW")
