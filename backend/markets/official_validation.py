"""Official PDF extraction, triple comparison and controlled validation."""

from __future__ import annotations

import os
import re
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from django.db import connection, transaction
from django.utils import timezone

from .index_importer import MONTHS, DocumentResult, analyse_pdf, sha256_file
from .models import (
    ExternalIndexStaging,
    IndexDefinition,
    IndexPublication,
    IndexSourceDocument,
    IndexValidationAudit,
    IndexValidationComparison,
    MonthlyIndexValue,
    OfficialExtractedValue,
    RawIndexExtraction,
)


def nominal_period(filename: str, periods: list[str]) -> tuple[int | None, int | None]:
    folded = filename.lower()
    for name, month in MONTHS.items():
        match = re.search(rf"{re.escape(name)}[-_ .]*(20\d{{2}})", folded)
        if match:
            return int(match.group(1)), month
    if len(periods) == 1:
        year, month = periods[0].split("-")
        return int(year), int(month)
    return None, None


def comparison_status(official: Decimal | None, api: Decimal | None, local: Decimal | None, pending=False) -> str:
    if pending or official is None:
        return IndexValidationComparison.Status.PENDING_VALIDATION
    if api is None and local is None:
        return IndexValidationComparison.Status.API_MISSING
    if api is None:
        return IndexValidationComparison.Status.API_MISSING
    if local is None:
        return IndexValidationComparison.Status.OFFICIAL_API_MATCH_LOCAL_MISSING if official == api else IndexValidationComparison.Status.OFFICIAL_API_CONFLICT
    if official == api == local:
        return IndexValidationComparison.Status.ALL_MATCH
    if official == api and local != official:
        return IndexValidationComparison.Status.OFFICIAL_LOCAL_CONFLICT
    if official == local and api != official:
        return IndexValidationComparison.Status.OFFICIAL_LOCAL_MATCH_API_CONFLICT
    return IndexValidationComparison.Status.OFFICIAL_API_CONFLICT


@dataclass
class ValidationPlan:
    result: object
    nominal_year: int | None
    nominal_month: int | None
    comparisons: list[dict]
    duplicate: bool = False

    @property
    def summary(self):
        counts = Counter(item["status"] for item in self.comparisons)
        return {key: counts.get(key, 0) for key in IndexValidationComparison.Status.values}


class OfficialIndexValidationService:
    def __init__(self, path: Path, *, source_url="", document_reference="", publication_date=None):
        self.path = Path(path)
        self.source_url = source_url
        self.document_reference = document_reference or self.path.name
        self.publication_date = publication_date

    def plan(self) -> ValidationPlan:
        digest = sha256_file(self.path)
        existing = IndexSourceDocument.objects.filter(sha256=digest).first()
        if existing:
            duplicate_result = DocumentResult(
                filename=self.path.name, sha256=digest, file_size=self.path.stat().st_size,
                pages=existing.page_count, periods=existing.detected_periods,
                extractor=existing.extraction_method, extraction_status=existing.extraction_status,
            )
            return ValidationPlan(duplicate_result, existing.nominal_year, existing.nominal_month, [], True)
        result = analyse_pdf(self.path, source_reference=str(self.path))
        year, month = nominal_period(result.filename, result.periods)
        comparisons = []
        for position, row in enumerate(result.raw_rows):
            period = result.periods[int(row.source_column) - 1] if row.source_column.isdigit() and int(row.source_column) <= len(result.periods) else None
            row_year, row_month = (period.split("-") if period else (None, None))
            if row_year is None or row_month is None or (year and month and (int(row_year), int(row_month)) != (year, month)):
                continue
            code = row.normalized_code
            definition = IndexDefinition.objects.filter(code=code).first() if code else None
            official = Decimal(row.normalized_value) if row.normalized_value else None
            api = None
            if code:
                api = ExternalIndexStaging.objects.filter(external_code=code, year=int(row_year), month=int(row_month), normalized_value__isnull=False).order_by("-retrieved_at").values_list("normalized_value", flat=True).first()
            local = None
            if definition:
                local = MonthlyIndexValue.objects.filter(index_definition=definition, year=int(row_year), month=int(row_month)).values_list("value", flat=True).first()
            comparisons.append({"position": position, "row": row, "definition": definition, "official": official, "api": api, "local": local, "status": comparison_status(official, api, local, pending=bool(row.ambiguity or not period or not definition))})
        return ValidationPlan(result, year, month, comparisons)

    @staticmethod
    def _apply_allowed():
        db_name = str(connection.settings_dict.get("NAME", ""))
        return os.environ.get("DJANGO_ENV", "").lower() == "test" or db_name.startswith("test_")

    @transaction.atomic
    def apply(self, *, actor=None):
        if not self._apply_allowed():
            raise RuntimeError("SECURITY: --apply est autorisé uniquement sur TEST_DATABASE.")
        plan = self.plan()
        if plan.duplicate:
            return plan, {"event": "DOCUMENT_DUPLICATE_DETECTED"}
        result = plan.result
        document = IndexSourceDocument.objects.create(
            sha256=result.sha256, original_filename=result.filename, nominal_year=plan.nominal_year,
            nominal_month=plan.nominal_month, file_size=result.file_size, page_count=result.pages,
            detected_periods=result.periods, source_reference=result.source_reference, source_url=self.source_url,
            extraction_method=result.extractor, extraction_status=result.extraction_status,
            notes="; ".join(result.flags + result.errors),
        )
        for row in result.raw_rows:
            RawIndexExtraction.objects.create(
                source_document=document, page_number=row.page, raw_code=row.raw_code,
                raw_designation=row.raw_designation, raw_value=row.raw_value, source_column=row.source_column,
                raw_status=row.raw_status, extraction_method=row.extraction_method,
                confidence=Decimal(row.confidence) if row.confidence else None, ambiguity=row.ambiguity,
                normalized_code=row.normalized_code, normalized_value=Decimal(row.normalized_value) if row.normalized_value else None,
                validation_status=row.validation_status,
            )
        if not plan.nominal_year or not plan.nominal_month:
            return plan, {"event": "PENDING_VALIDATION", "document_id": str(document.pk)}
        publication, _ = IndexPublication.objects.get_or_create(
            year=plan.nominal_year, month=plan.nominal_month, source_type=IndexPublication.SourceType.OFFICIAL,
            defaults={"document_reference": self.document_reference, "source_url": self.source_url, "document_hash": result.sha256, "publication_date": self.publication_date, "status": IndexPublication.Status.PENDING_VALIDATION},
        )
        if publication.document_hash and publication.document_hash != result.sha256:
            return plan, {"event": "OFFICIAL_PUBLICATION_CONFLICT", "publication_id": str(publication.pk)}
        if not publication.document_hash:
            publication.document_hash = result.sha256
            publication.save(update_fields=["document_hash"])
        for item in plan.comparisons:
            row = item["row"]
            period = result.periods[int(row.source_column) - 1]
            row_year, row_month = map(int, period.split("-"))
            extracted, _ = OfficialExtractedValue.objects.update_or_create(
                source_document=document, year=row_year, month=row_month,
                normalized_code=row.normalized_code or row.raw_code.strip().upper(),
                defaults={"publication": publication, "raw_code": row.raw_code, "raw_designation": row.raw_designation, "raw_value": row.raw_value, "normalized_value": item["official"], "confidence": Decimal(row.confidence) if row.confidence else None, "status": OfficialExtractedValue.Status.PENDING_VALIDATION, "extraction_method": row.extraction_method, "page_number": row.page, "source_reference": result.source_reference, "ambiguity": row.ambiguity},
            )
            status = item["status"]
            definition = item["definition"]
            comparison, _ = IndexValidationComparison.objects.update_or_create(
                official_value=extracted, index_definition=definition,
                defaults={"year": row_year, "month": row_month, "api_value": item["api"], "local_value": item["local"], "status": status, "resolved": status in {IndexValidationComparison.Status.ALL_MATCH, IndexValidationComparison.Status.OFFICIAL_API_MATCH_LOCAL_MISSING}},
            )
            if row_year != plan.nominal_year or row_month != plan.nominal_month:
                continue
            if status in {IndexValidationComparison.Status.ALL_MATCH, IndexValidationComparison.Status.OFFICIAL_API_MATCH_LOCAL_MISSING} and definition:
                local = MonthlyIndexValue.objects.select_for_update().filter(index_definition=definition, year=row_year, month=row_month).first()
                if local and local.status == MonthlyIndexValue.Status.DEFINITIVE:
                    extracted.status = OfficialExtractedValue.Status.VALIDATED
                    extracted.save(update_fields=["status"])
                    continue
                before_value, before_status = (local.value, local.status) if local else (None, "")
                if local is None:
                    local = MonthlyIndexValue.objects.create(index_definition=definition, publication=publication, year=row_year, month=row_month, value=item["official"], status=MonthlyIndexValue.Status.DEFINITIVE, source_url=self.source_url, source_document=self.document_reference, source_reference=result.source_reference, validated_at=timezone.now())
                elif local.value == item["official"] and local.status == MonthlyIndexValue.Status.PENDING_VALIDATION:
                    local.publication = publication
                    local.status = MonthlyIndexValue.Status.DEFINITIVE
                    local.source_url = self.source_url
                    local.source_document = self.document_reference
                    local.source_reference = result.source_reference
                    local.validated_at = timezone.now()
                    local.save(update_fields=["publication", "status", "source_url", "source_document", "source_reference", "validated_at", "updated_at"])
                else:
                    continue
                IndexValidationAudit.objects.create(monthly_value=local, value_before=before_value, status_before=before_status, value_after=local.value, status_after=local.status, publication=publication, document_hash=result.sha256, method="OFFICIAL_PDF_VALIDATION", actor=actor)
                extracted.status = OfficialExtractedValue.Status.VALIDATED
                extracted.save(update_fields=["status"])
            elif status in {IndexValidationComparison.Status.OFFICIAL_API_CONFLICT, IndexValidationComparison.Status.OFFICIAL_LOCAL_CONFLICT, IndexValidationComparison.Status.OFFICIAL_LOCAL_MATCH_API_CONFLICT}:
                extracted.status = OfficialExtractedValue.Status.CONFLICT
                extracted.save(update_fields=["status"])
        if any(item["status"] in {IndexValidationComparison.Status.OFFICIAL_API_CONFLICT, IndexValidationComparison.Status.OFFICIAL_LOCAL_CONFLICT, IndexValidationComparison.Status.PENDING_VALIDATION, IndexValidationComparison.Status.API_MISSING} for item in plan.comparisons):
            publication.status = IndexPublication.Status.PENDING_VALIDATION
        else:
            publication.status = IndexPublication.Status.VALIDATED
            publication.validated_at = timezone.now()
        publication.save(update_fields=["status", "validated_at"])
        return plan, {"event": "APPLIED", "document_id": str(document.pk), "publication_id": str(publication.pk)}
