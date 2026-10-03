"""Single ingestion path for manual and official-auto index PDFs.

Discovery only downloads documents.  It never validates values; promotion to
the local calculation repository is an explicit, transactional action.
"""

from __future__ import annotations

import re
import shutil
import tempfile
from dataclasses import dataclass
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .index_importer import AMBIGUOUS, EXACT_MATCH, NEW_OFFICIAL_CODE, STRUCTURAL_MATCH, analyse_pdf, resolve_extracted_code, sha256_file
from .models import (
    IndexDefinition,
    IndexPublication,
    IndexSourceDocument,
    IndexValidationAudit,
    IndexValidationComparison,
    MonthlyIndexValue,
    OfficialDiscoveryCheck,
    OfficialExtractedValue,
)
from .official_validation import nominal_period


class OfficialIngestionError(Exception):
    def __init__(self, code, message, *, status=400):
        super().__init__(message)
        self.code = code
        self.status = status


class _PdfLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href", "")
        if href:
            self.links.append(href)


@dataclass(frozen=True)
class Provenance:
    source_page_url: str = ""
    source_pdf_url: str = ""
    import_method: str = IndexSourceDocument.ImportMethod.MANUAL


def _configured_source():
    value = getattr(settings, "OFFICIAL_INDEX_PUBLICATION_URL", "").strip()
    if not value:
        raise OfficialIngestionError("OFFICIAL_SOURCE_NOT_CONFIGURED", "La source officielle n'est pas configurée.", status=503)
    return value


def _validate_pdf(path: Path):
    if path.suffix.lower() != ".pdf":
        raise OfficialIngestionError("INVALID_PDF", "Seuls les fichiers PDF sont acceptés.")
    try:
        if path.stat().st_size == 0 or path.read_bytes()[:5] != b"%PDF-":
            raise OfficialIngestionError("INVALID_PDF", "Le fichier n'est pas un PDF valide.")
    except OSError as exc:
        raise OfficialIngestionError("INVALID_PDF", "Le fichier PDF est inaccessible.") from exc


def _period_for_row(row, year, month, periods):
    if row.source_column.isdigit() and year and month:
        offset = int(row.source_column) - 1
        if 0 <= offset <= 2:
            absolute = month + offset
            return year + (absolute - 1) // 12, ((absolute - 1) % 12) + 1
    if len(periods) == 1:
        value = periods[0]
        return int(value[:4]), int(value[5:7])
    return None


def _row_status(row, definition, local):
    if row.ambiguity and row.ambiguity not in {"UNKNOWN_CODE", "CONFLICT", "ALREADY_EXISTS"}:
        return "AMBIGUOUS"
    if not row.normalized_value:
        return "AMBIGUOUS"
    if definition is None:
        return "UNKNOWN_CODE"
    if local is None:
        return "OK"
    if local.value == Decimal(str(row.normalized_value)):
        return "ALREADY_EXISTS"
    return "CONFLICT"


def _blocking(status):
    return status in {"UNKNOWN_CODE", "NEW_OFFICIAL_CODE", "AMBIGUOUS", "CONFLICT"}


def _preview(document):
    first_value = document.official_values.select_related("publication").first()
    publication = first_value.publication if first_value else None
    rows = []
    for extracted in document.official_values.select_related("publication").all():
        definition = extracted.resolved_index_definition or IndexDefinition.objects.filter(code=extracted.normalized_code).first()
        local = None
        if definition:
            local = MonthlyIndexValue.objects.filter(index_definition=definition, year=extracted.year, month=extracted.month).first()
        if extracted.resolution_method in {EXACT_MATCH, STRUCTURAL_MATCH}:
            status = "AMBIGUOUS" if extracted.status == OfficialExtractedValue.Status.CONFLICT and "DUPLICATE_CODE_FOR_PERIOD" in extracted.ambiguity else ("OK" if extracted.status != OfficialExtractedValue.Status.CONFLICT else "CONFLICT")
        elif extracted.resolution_method == AMBIGUOUS and "CANDIDATES:" in extracted.ambiguity:
            status = "AMBIGUOUS"
        elif extracted.resolution_method == NEW_OFFICIAL_CODE:
            status = NEW_OFFICIAL_CODE
        else:
            status = extracted.ambiguity or extracted.status
        if extracted.resolution_method not in {EXACT_MATCH, STRUCTURAL_MATCH} and status in {"PENDING_VALIDATION", "EXTRACTED", "CONFLICT"}:
            status = _row_status(
                type("Row", (), {"ambiguity": extracted.ambiguity, "normalized_value": extracted.normalized_value})(),
                definition,
                local,
            )
        rows.append({
            "id": str(extracted.id),
            "code": extracted.normalized_code,
            "raw_extracted_code": extracted.raw_code,
            "designation": extracted.raw_designation,
            "value": str(extracted.normalized_value) if extracted.normalized_value is not None else None,
            "local_value": str(local.value) if local else None,
            "status": status,
            "resolution_method": extracted.resolution_method or None,
            "resolution_candidates": [candidate for candidate in (extracted.ambiguity or "").split("CANDIDATES:")[-1].split(",") if candidate] if "CANDIDATES:" in extracted.ambiguity else [],
            "resolved_by": str(extracted.resolved_by_id) if extracted.resolved_by_id else None,
            "resolved_at": extracted.resolved_at,
            "year": extracted.year,
            "month": extracted.month,
        })
    period_conflict = document.notes.startswith("CONFLICT:")
    if period_conflict and rows and not any(_blocking(row["status"]) for row in rows):
        rows[0]["status"] = "CONFLICT"
    return {
        "document_id": str(document.id),
        "publication_id": str(publication.id) if publication else None,
        "filename": document.original_filename,
        "sha256": document.sha256,
        "source": "Ministère de l'Équipement",
        "source_page_url": document.source_page_url,
        "source_pdf_url": document.source_pdf_url,
        "year": document.nominal_year,
        "month": document.nominal_month,
        "validation_status": document.validation_status,
        "rows": rows,
        "count": len(rows),
        "cells_detected": document.extracted_cells,
        "rows_detected": document.extracted_rows,
        "unique_index_codes": len({row["code"] for row in rows if row["code"]}),
        "valid_index_value_pairs": sum(1 for row in rows if row["status"] not in {"UNKNOWN_CODE", "NEW_OFFICIAL_CODE", "AMBIGUOUS", "CONFLICT"} and row["value"] is not None),
        "period_conflict": period_conflict,
        "blocking_issues": sum(_blocking(row["status"]) for row in rows),
    }


@transaction.atomic
def ingest_official_bareme(path: Path, provenance: Provenance = Provenance()):
    """Ingest one PDF into the reviewable official repository, never definitive."""
    path = Path(path)
    _validate_pdf(path)
    digest = sha256_file(path)
    known = IndexSourceDocument.objects.filter(sha256=digest).first()
    if known is None:
        known_publication = IndexPublication.objects.filter(document_hash=digest).first()
        if known_publication:
            raise OfficialIngestionError("DOCUMENT_ALREADY_IMPORTED", "Ce document officiel a déjà été importé.", status=409)
    if known:
        return {"event": "DOCUMENT_ALREADY_IMPORTED", "preview": _preview(known)}

    result = analyse_pdf(path, source_reference=provenance.source_pdf_url or str(path))
    year, month = nominal_period(result.filename, result.periods)
    if not year or not month:
        raise OfficialIngestionError("PERIOD_NOT_IDENTIFIED", "La période du barème n'a pas pu être identifiée.")

    archive_dir = Path(settings.MEDIA_ROOT) / "official-indexes"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"{digest}.pdf"
    if path.resolve() != archive_path.resolve():
        shutil.copyfile(path, archive_path)

    conflict = (
        IndexSourceDocument.objects.filter(nominal_year=year, nominal_month=month).exclude(sha256=digest).exists()
        or IndexPublication.objects.filter(year=year, month=month, source_type=IndexPublication.SourceType.OFFICIAL).exclude(document_hash=digest).exists()
    )
    source_document = IndexSourceDocument.objects.create(
        sha256=digest,
        original_filename=path.name,
        nominal_year=year,
        nominal_month=month,
        file_size=path.stat().st_size,
        page_count=result.pages,
        detected_periods=result.periods,
        source_reference=provenance.source_pdf_url or str(archive_path),
        stored_file=str(archive_path),
        source_url=provenance.source_pdf_url,
        source_page_url=provenance.source_page_url,
        source_pdf_url=provenance.source_pdf_url,
        import_method=provenance.import_method,
        extraction_method=result.extractor,
        extraction_status=IndexSourceDocument.ExtractionStatus.PENDING_VALIDATION,
        validation_status="PENDING_VALIDATION",
        extracted_cells=len(result.raw_rows),
        notes="CONFLICT: nouvelle version pour la même période" if conflict else "",
    )
    publication = IndexPublication.objects.create(
        year=year,
        month=month,
        source_url=provenance.source_pdf_url,
        source_page_url=provenance.source_page_url,
        source_pdf_url=provenance.source_pdf_url,
        document_reference=path.name,
        document_hash=digest,
        source_type=IndexPublication.SourceType.OFFICIAL,
        import_method=provenance.import_method,
        status=IndexPublication.Status.PENDING_VALIDATION,
    )

    position = 0
    seen_period_codes = set()
    duplicate_codes = []
    for row in result.raw_rows:
        period = _period_for_row(row, year, month, result.periods)
        if period is None or period != (year, month):
            continue
        definitions = list(IndexDefinition.objects.filter(active=True))
        resolution = resolve_extracted_code(row.raw_code, row.raw_designation, definitions)
        normalized_code = resolution.code
        ambiguity = row.ambiguity
        prefix_ambiguous = not any(character.isdigit() for character in row.normalized_code) and any(
            len(row.normalized_code) == len(definition.code)
            and row.normalized_code[:3].upper() == definition.code[:3].upper()
            for definition in definitions
            if len(row.normalized_code) >= 3
        )
        if resolution.method == AMBIGUOUS and row.normalized_code and not prefix_ambiguous and not ambiguity:
            resolution = type(resolution)(row.normalized_code, NEW_OFFICIAL_CODE, (row.normalized_code,))
        elif resolution.method == AMBIGUOUS and resolution.candidates:
            ambiguity = ";".join(filter(None, [ambiguity, "CODE_AMBIGUOUS", "CANDIDATES:" + ",".join(resolution.candidates)]))
        elif resolution.method == STRUCTURAL_MATCH:
            ambiguity = ";".join(filter(None, [ambiguity, "STRUCTURAL_MATCH"]))
        row_code = normalized_code or row.normalized_code or f"UNKNOWN_{position + 1}"
        row_key = (year, month, row_code)
        if row_key in seen_period_codes:
            duplicate_codes.append(row_code)
            existing = OfficialExtractedValue.objects.filter(
                source_document=source_document, year=year, month=month, normalized_code=row_code,
            ).first()
            if existing:
                existing.ambiguity = ";".join(filter(None, [existing.ambiguity, "DUPLICATE_CODE_FOR_PERIOD"]))
                existing.status = OfficialExtractedValue.Status.CONFLICT
                existing.save(update_fields=["ambiguity", "status"])
            continue
        seen_period_codes.add(row_key)
        position += 1
        definition = IndexDefinition.objects.filter(code=normalized_code).first()
        value = row.normalized_value
        status = _row_status(row, definition, None)
        if definition and value:
            local = MonthlyIndexValue.objects.filter(index_definition=definition, year=year, month=month).first()
            status = _row_status(row, definition, local)
        OfficialExtractedValue.objects.create(
            publication=publication,
            source_document=source_document,
            year=year,
            month=month,
            raw_code=row.raw_code or f"UNKNOWN_{position}",
            raw_designation=row.raw_designation,
            normalized_code=normalized_code or row.normalized_code or f"UNKNOWN_{position}",
            raw_value=row.raw_value,
            normalized_value=value,
            confidence=row.confidence,
            status=OfficialExtractedValue.Status.CONFLICT if status == "CONFLICT" else OfficialExtractedValue.Status.PENDING_VALIDATION,
            extraction_method=row.extraction_method,
            page_number=row.page,
            source_reference=provenance.source_pdf_url or str(path),
            ambiguity=ambiguity or (status if status not in {"OK", "ALREADY_EXISTS"} else ""),
            resolution_method=resolution.method,
        )
    if position == 0:
        source_document.extraction_status = IndexSourceDocument.ExtractionStatus.ERROR
        source_document.notes = "Aucune ligne d'indice exploitable pour la période identifiée."
        source_document.save(update_fields=["extraction_status", "notes"])
        raise OfficialIngestionError("NO_INDEX_ROWS", source_document.notes)
    if duplicate_codes:
        source_document.notes = "; ".join(filter(None, [source_document.notes, "AMBIGUOUS_DUPLICATE_CODES:" + ",".join(sorted(set(duplicate_codes)))]))
        source_document.save(update_fields=["notes"])
    source_document.extracted_rows = position
    source_document.save(update_fields=["extracted_rows"])
    return {"event": "PENDING_VALIDATION", "preview": _preview(source_document)}


@transaction.atomic
def validate_official_bareme(document_id, actor=None, confirm_conflicts=False):
    document = IndexSourceDocument.objects.select_for_update().get(pk=document_id)
    preview = _preview(document)
    blocking = [row for row in preview["rows"] if _blocking(row["status"])]
    unresolved = [row for row in blocking if row["status"] != "CONFLICT"]
    if unresolved or (blocking and not confirm_conflicts):
        raise OfficialIngestionError("VALIDATION_BLOCKED", "La validation est bloquée par des anomalies.")
    first_value = document.official_values.select_related("publication").first()
    publication = first_value.publication if first_value else None
    if publication is None:
        raise OfficialIngestionError("PUBLICATION_NOT_FOUND", "Publication introuvable.")
    for row in document.official_values.all():
        definition = row.resolved_index_definition or IndexDefinition.objects.filter(code=row.normalized_code).first()
        if not definition or row.normalized_value is None:
            continue
        local = MonthlyIndexValue.objects.filter(index_definition=definition, year=row.year, month=row.month).first()
        before_value = local.value if local else None
        before_status = local.status if local else ""
        local, _ = MonthlyIndexValue.objects.update_or_create(
            index_definition=definition,
            year=row.year,
            month=row.month,
            defaults={
                "publication": publication,
                "value": row.normalized_value,
                "status": MonthlyIndexValue.Status.DEFINITIVE,
                "source_url": document.source_pdf_url,
                "source_document": document.original_filename,
                "source_reference": document.source_pdf_url or document.source_reference,
                "validated_at": timezone.now(),
            },
        )
        IndexValidationComparison.objects.update_or_create(
            official_value=row,
            index_definition=definition,
            defaults={"year": row.year, "month": row.month, "local_value": before_value, "status": "ALL_MATCH" if before_value == row.normalized_value else "OFFICIAL_LOCAL_CONFLICT", "resolved": True},
        )
        IndexValidationAudit.objects.create(monthly_value=local, value_before=before_value, status_before=before_status, value_after=local.value, status_after=local.status, publication=publication, document_hash=document.sha256, method="OFFICIAL_INGESTION", actor=actor)
        row.status = OfficialExtractedValue.Status.VALIDATED
        row.save(update_fields=["status"])
    now = timezone.now()
    publication.status = IndexPublication.Status.VALIDATED
    publication.validated_at = now
    publication.validated_by = actor
    publication.save(update_fields=["status", "validated_at", "validated_by"])
    document.validation_status = "VALIDATED"
    document.validated_at = now
    document.validated_by = actor
    document.save(update_fields=["validation_status", "validated_at", "validated_by"])
    return _preview(document)


@transaction.atomic
def create_official_definition(document_id, row_id, designation="", actor=None, code=""):
    document = IndexSourceDocument.objects.select_for_update().get(pk=document_id)
    row = document.official_values.select_for_update().get(pk=row_id)
    if row.resolution_method not in {NEW_OFFICIAL_CODE, AMBIGUOUS, "CONFLICT", EXACT_MATCH, STRUCTURAL_MATCH}:
        raise OfficialIngestionError("NEW_CODE_NOT_PENDING", "Cette ligne ne propose pas la création d'un nouveau code.")
    code = (code or row.normalized_code or "").strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*(?:bis)?", code):
        raise OfficialIngestionError("INVALID_OFFICIAL_CODE", "Le code officiel corrigé est invalide.")
    definition, created = IndexDefinition.objects.get_or_create(
        code=code,
        defaults={"designation": designation.strip(), "domain": "OFFICIAL", "active": True},
    )
    if not created and designation.strip() and not definition.designation:
        definition.designation = designation.strip()
        definition.save(update_fields=["designation"])
    row.resolved_index_definition = definition
    row.resolution_method = "MANUAL_CREATE" if created else "MANUAL"
    row.resolved_by = actor
    row.resolved_at = timezone.now()
    row.ambiguity = ""
    row.status = OfficialExtractedValue.Status.PENDING_VALIDATION
    row.save(update_fields=["resolved_index_definition", "resolution_method", "resolved_by", "resolved_at", "ambiguity", "status"])
    return _preview(document)


def _fetch(url):
    request = Request(url, headers={"User-Agent": "revision-prix-official-index-importer/1.0"})
    with urlopen(request, timeout=20) as response:
        return response.read()


def _official_pdf_links(page_url, html):
    parser = _PdfLinkParser()
    parser.feed(html.decode("utf-8", errors="replace"))
    page_host = urlparse(page_url).hostname or ""
    links = []
    for href in parser.links:
        url = urljoin(page_url, href)
        parsed = urlparse(url)
        if parsed.scheme != "https" or (parsed.hostname or "") != page_host:
            continue
        if not re.search(r"\.pdf(?:$|[?#])", parsed.path, re.I):
            continue
        if url not in links:
            links.append(url)
    return links


def check_official_publications():
    page_url = _configured_source()
    try:
        html = _fetch(page_url)
        links = _official_pdf_links(page_url, html)
        new_documents = []
        for pdf_url in links:
            if IndexSourceDocument.objects.filter(source_pdf_url=pdf_url).exists():
                continue
            payload = _fetch(pdf_url)
            filename = unquote(Path(urlparse(pdf_url).path).name) or "bareme-officiel.pdf"
            if not payload.startswith(b"%PDF-"):
                continue
            target_dir = Path(settings.MEDIA_ROOT) / "official-indexes"
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / filename
            target.write_bytes(payload)
            result = ingest_official_bareme(target, Provenance(page_url, pdf_url, IndexSourceDocument.ImportMethod.OFFICIAL_AUTO))
            new_documents.append(result["preview"]["document_id"])
        latest = IndexSourceDocument.objects.filter(pk__in=new_documents).order_by("-retrieved_at").first()
        check = OfficialDiscoveryCheck.objects.create(source_page_url=page_url, status=OfficialDiscoveryCheck.Status.AVAILABLE, new_documents_count=len(new_documents), latest_new_document=latest)
        return {"status": check.status, "checked_at": check.checked_at, "new_documents": len(new_documents), "latest_new_document": str(latest.id) if latest else None}
    except (HTTPError, URLError, TimeoutError, OSError, OfficialIngestionError) as exc:
        check = OfficialDiscoveryCheck.objects.create(source_page_url=page_url, status=OfficialDiscoveryCheck.Status.UNAVAILABLE, error_message=str(exc))
        return {"status": check.status, "checked_at": check.checked_at, "new_documents": 0, "latest_new_document": None, "error": str(exc)}
