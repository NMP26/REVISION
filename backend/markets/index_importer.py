"""Safe, reviewable extraction pipeline for official index PDFs.

This module deliberately stops before database import.  It produces raw rows and
normalised candidates so a later approval step can decide what becomes official.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
import unicodedata
from difflib import SequenceMatcher
from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


MONTHS = {
    "janvier": 1, "fevrier": 2, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "aout": 8, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12, "décembre": 12,
}
MONTH_NAMES = {value: key for key, value in MONTHS.items() if len(key) <= 8}
METHOD_NATIVE = "NATIVE_TEXT"
METHOD_TABLE = "TABLE_EXTRACTION"
METHOD_OCR = "OCR"
METHOD_MANUAL = "MANUAL_REVIEW_REQUIRED"

EXACT_MATCH = "EXACT_MATCH"
STRUCTURAL_MATCH = "STRUCTURAL_MATCH"
AMBIGUOUS = "AMBIGUOUS"
NEW_OFFICIAL_CODE = "NEW_OFFICIAL_CODE"


@dataclass(frozen=True)
class CodeResolution:
    code: str = ""
    method: str = AMBIGUOUS
    candidates: tuple[str, ...] = ()


def _words(value: str) -> set[str]:
    folded = unicodedata.normalize("NFKD", value.lower()).encode("ascii", "ignore").decode()
    return {word for word in re.findall(r"[a-z0-9]+", folded) if len(word) > 2}


def resolve_extracted_code(raw_code: str, raw_designation: str, definitions) -> CodeResolution:
    """Resolve a short extracted code against the catalogue without guessing.

    An exact catalogue code is accepted unless the row's designation is a
    stronger structural match for another catalogue entry.  Ties and weak
    evidence remain explicitly ambiguous; OCR character similarity is never a
    resolution rule.
    """
    catalogue = {str(item.code).upper(): item for item in definitions}
    extracted = (raw_code or "").strip()
    case_matches = [item for item in definitions if str(item.code).upper() == extracted.upper()]
    if len(case_matches) > 1 and not any(str(item.code) == extracted for item in case_matches):
        return CodeResolution("", AMBIGUOUS, tuple(str(item.code) for item in case_matches))
    exact = next((item for item in case_matches if str(item.code) == extracted), None) or (case_matches[0] if len(case_matches) == 1 else None)
    row_words = _words(raw_designation)
    scored = []
    for code, definition in catalogue.items():
        # Structure may disambiguate a short OCR token only among nearby
        # catalogue codes; it cannot turn an unrelated unknown token into a
        # valid index merely because the designation happens to overlap.
        if extracted and (code[:1] != extracted[:1].upper() or abs(len(code) - len(extracted)) > 1):
            continue
        definition_words = _words(getattr(definition, "designation", ""))
        overlap = len(row_words & definition_words)
        fuzzy = sum(1 for row_word in row_words for definition_word in definition_words if SequenceMatcher(None, row_word, definition_word).ratio() >= 0.64)
        structural_score = overlap * 2 + min(fuzzy, 2)
        if structural_score:
            scored.append((structural_score, code))
    scored.sort(reverse=True)
    if not exact and extracted:
        prefix_candidates = [item.code for item in definitions if len(extracted) == len(str(item.code)) and len(re.match(r"^[A-Za-z]+", extracted).group(0)) >= 3 and str(item.code).upper().startswith(extracted[:3].upper())]
        if prefix_candidates:
            return CodeResolution("", AMBIGUOUS, tuple(prefix_candidates))
    if exact and not scored:
        return CodeResolution(exact.code, EXACT_MATCH, (exact.code,))
    if exact and scored:
        best_score, best_code = scored[0]
        second_score = scored[1][0] if len(scored) > 1 else 0
        if best_code == extracted.upper() and best_score > second_score:
            return CodeResolution(exact.code, EXACT_MATCH, (exact.code,))
        if best_code != extracted.upper() and best_score > 0 and best_score > second_score:
            return CodeResolution(catalogue[best_code].code, STRUCTURAL_MATCH, (catalogue[best_code].code, exact.code))
    if exact and len(scored) == 1:
        return CodeResolution(catalogue[scored[0][1]].code, STRUCTURAL_MATCH, (catalogue[scored[0][1]].code,))
    # A syntactically valid code absent from the catalogue is unknown, not a
    # guessed match.  Only catalogue-backed alternatives are offered.
    candidates = tuple(dict.fromkeys([*(catalogue[code].code for _, code in scored), *( [exact.code] if exact else [])]))
    return CodeResolution("", AMBIGUOUS, candidates)


@dataclass
class RawRow:
    page: int | None
    raw_code: str
    raw_designation: str
    raw_value: str
    source_column: str
    raw_status: str
    extraction_method: str
    confidence: str | None = None
    ambiguity: str = ""
    normalized_code: str = ""
    normalized_value: str | None = None
    validation_status: str = "PENDING_VALIDATION"


@dataclass
class DocumentResult:
    filename: str
    sha256: str
    file_size: int
    pages: int | None
    periods: list[str]
    extractor: str
    extraction_status: str
    raw_rows: list[RawRow] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    source_reference: str = ""
    page_details: list[dict] = field(default_factory=list)

    def as_dict(self):
        result = asdict(self)
        result["raw_rows"] = [asdict(row) for row in self.raw_rows]
        return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _run(command: list[str], *, text=True, timeout=None) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, capture_output=True, text=text, timeout=timeout)


def page_count(path: Path) -> int | None:
    try:
        output = _run(["pdfinfo", str(path)]).stdout
        match = re.search(r"^Pages:\s*(\d+)", output, re.MULTILINE)
        return int(match.group(1)) if match else None
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def native_text(path: Path) -> str:
    try:
        return _run(["pdftotext", "-layout", str(path), "-"]).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""


def native_text_pages(path: Path) -> list[tuple[int, str]]:
    """Extract native text page by page so image-only pages can be isolated."""
    total = page_count(path)
    if not total:
        return []
    pages = []
    for number in range(1, total + 1):
        try:
            text = _run(["pdftotext", "-layout", "-f", str(number), "-l", str(number), str(path), "-"]).stdout
        except (FileNotFoundError, subprocess.CalledProcessError):
            text = ""
        pages.append((number, text))
    return pages


def _page_has_useful_text(text: str) -> bool:
    return len(re.sub(r"\s", "", text)) >= 20


def _page_detail(number: int, text: str) -> dict:
    codes = sorted({match.group(0).upper() for match in re.finditer(r"\b(?:BAT[1-9]\d*|[A-Za-z]{1,4}\d?(?:bis)?)\b", text)})
    return {"page": number, "text_chars": len(text), "index_codes_detected": codes}


def ocr_text(path: Path, page_numbers: list[int] | None = None) -> tuple[str, str, list[str], list[dict]]:
    """OCR only selected pages, with an independent timeout and partial results."""
    warnings = []
    page_details = []
    timeout = int(os.environ.get("IDX_OCR_PAGE_TIMEOUT_SECONDS", "20"))
    render_timeout = int(os.environ.get("IDX_OCR_RENDER_TIMEOUT_SECONDS", "20"))
    selected = page_numbers or list(range(1, (page_count(path) or 0) + 1))
    try:
        with tempfile.TemporaryDirectory(prefix="index-ocr-") as temp:
            chunks = []
            for number in selected:
                prefix = Path(temp) / f"page-{number}"
                try:
                    # Render only this page.  200 DPI avoids the old full-document
                    # rasterization while retaining the scan's table glyphs.
                    _run(["pdftoppm", "-f", str(number), "-l", str(number), "-singlefile", "-jpeg", "-r", "200", str(path), str(prefix)], text=False, timeout=render_timeout)
                    image = prefix.with_suffix(".jpg")
                    if not image.exists():
                        warnings.append(f"OCR_PAGE_RENDER_FAILED:{number}")
                        continue
                    text = _run(["tesseract", str(image), "stdout", "-l", "fra+eng", "--psm", "6"], timeout=timeout).stdout
                    chunks.append(f"--- page-{number} ---\n{text}")
                    page_details.append(_page_detail(number, text))
                except subprocess.TimeoutExpired:
                    warnings.append(f"OCR_TIMEOUT_PAGE:{number}")
                except (FileNotFoundError, subprocess.CalledProcessError) as exc:
                    warnings.append(f"OCR_PAGE_ERROR:{number}:{exc}")
            return "\n".join(chunks), METHOD_OCR if chunks else METHOD_MANUAL, warnings, page_details
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        return "", METHOD_MANUAL, [f"Outils OCR indisponibles: {exc}"], page_details


def _month_periods(text: str, filename: str) -> tuple[list[str], list[str]]:
    """Content is authoritative; filename is only a secondary signal."""
    folded = text.lower()
    found = []
    for match in re.finditer(
        r"(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(20\d{2})",
        folded,
    ):
        period = f"{int(match.group(2)):04d}-{MONTHS[match.group(1)] :02d}"
        if period not in found:
            found.append(period)
    # The heading is the authoritative tri-month declaration.  Other pages
    # mention historical comparison months and must not expand the publication.
    heading = re.search(r"POUR\s+LES\s+MOIS(.{0,180})", folded, re.S)
    if heading:
        heading_matches = re.findall(
            r"(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(20\d{2})",
            heading.group(1),
        )
        heading_periods = [f"{int(year):04d}-{MONTHS[name]:02d}" for name, year in heading_matches]
        found = list(dict.fromkeys(heading_periods))
    filename_periods = []
    filename_folded = filename.lower()
    for name, month in MONTHS.items():
        match = re.search(rf"{re.escape(name)}[-_ ]*(20\d{{2}})", filename_folded)
        if match:
            filename_periods.append(f"{int(match.group(1)):04d}-{month:02d}")
    flags = []
    if filename_periods and found and filename_periods[0] not in found:
        flags.append("CONTRADICTORY_MONTH_METADATA")
    if not found:
        found = filename_periods
    return found, flags


_CODE = r"[A-Za-z][A-Za-z0-9]*(?:bis)?"
_NUMBER = r"[+-]?(?:\d[\d .]*[,.]\d+|\d+[,.]\d+|\d+)"
_ROW_RE = re.compile(rf"(?P<designation>.*?)\s+(?P<code>{_CODE})\s+(?P<v1>{_NUMBER})\s+(?P<v2>{_NUMBER})\s+(?P<v3>{_NUMBER})\s*$")
_SAFE_CODES = re.compile(r"^(?:BAT[1-6]|OA[1-5]|SF[1-6]|CEP[1-3]|REP|TR\d(?:bis)?|GO[AB]|MQ|PS(?:/C[alMRI])?|ET|EL[IB]|PV|BPI)$", re.I)


def parse_decimal(raw: str) -> tuple[Decimal | None, str]:
    value = raw.strip().replace(" ", "").replace("\u00a0", "")
    if not re.fullmatch(r"[+-]?\d+(?:[,.]\d+)?", value):
        return None, "FORMAT_AMBIGUOUS"
    try:
        return Decimal(value.replace(",", ".")), ""
    except InvalidOperation:
        return None, "DECIMAL_INVALID"


def _normalise_code(raw: str) -> tuple[str, str]:
    code = raw.strip()
    # The database remains authoritative for UNKNOWN_CODE classification.  The
    # extractor must not silently discard a syntactically valid official code
    # merely because the seed catalogue has not seen it yet.
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*(?:bis)?", code):
        return "", "CODE_AMBIGUOUS"
    return code, ""


def extract_rows(text: str, method: str, periods: list[str]) -> list[RawRow]:
    rows: list[RawRow] = []
    current_page = None
    for line in text.splitlines():
        page_match = re.search(r"page-(\d+)", line, re.I)
        if page_match:
            current_page = int(page_match.group(1))
        match = _ROW_RE.search(line.strip())
        if not match:
            continue
        code_raw = match.group("code")
        designation = re.sub(r"^[^\wÀ-ÿ]+", "", match.group("designation")).strip()
        code, code_error = _normalise_code(code_raw)
        for column, key in enumerate(("v1", "v2", "v3"), start=1):
            raw_value = match.group(key)
            value, value_error = parse_decimal(raw_value)
            ambiguity = ";".join(filter(None, [code_error, value_error]))
            # OCR frequently drops a decimal separator (e.g. 3378).  Never infer it.
            if method == METHOD_OCR and "," not in raw_value and "." not in raw_value:
                ambiguity = ";".join(filter(None, [ambiguity, "OCR_DECIMAL_SEPARATOR_MISSING"]))
                value = None
            status = "DEFINITIVE" if column == 1 else "PROVISIONAL"
            if ambiguity or value is None or not code:
                status = "PENDING_VALIDATION"
            rows.append(RawRow(
                page=current_page,
                raw_code=code_raw,
                raw_designation=designation,
                raw_value=raw_value,
                source_column=str(column),
                raw_status=status,
                extraction_method=method,
                confidence="0.99" if not ambiguity else "0.50",
                ambiguity=ambiguity,
                normalized_code=code,
                normalized_value=str(value) if value is not None else None,
                validation_status=status,
            ))
    return rows


def analyse_pdf(path: Path, source_reference: str = "") -> DocumentResult:
    digest = sha256_file(path)
    native_pages = native_text_pages(path)
    useful_native_pages = [number for number, text in native_pages if _page_has_useful_text(text)]
    missing_pages = [number for number, text in native_pages if not _page_has_useful_text(text)]
    if not native_pages:
        text = native_text(path)
        useful_native_pages = [1] if _page_has_useful_text(text) else []
        missing_pages = [] if useful_native_pages else list(range(1, (page_count(path) or 0) + 1))
        native_pages = [(1, text)] if text else []
    native_chunks = [f"--- page-{number} ---\n{text}" for number, text in native_pages if _page_has_useful_text(text)]
    text = "\n".join(native_chunks)
    method = METHOD_NATIVE if useful_native_pages and not missing_pages else (METHOD_TABLE if useful_native_pages else "")
    warnings = []
    page_details = [_page_detail(number, page_text) for number, page_text in native_pages]
    if missing_pages:
        ocr_output, ocr_method, ocr_warnings, ocr_details = ocr_text(path, missing_pages)
        if ocr_output:
            text = "\n".join(filter(None, [text, ocr_output]))
            method = METHOD_OCR if not useful_native_pages else METHOD_TABLE
        elif not useful_native_pages:
            method = METHOD_MANUAL
        warnings.extend(ocr_warnings)
        page_details = [detail for detail in page_details if detail["page"] not in missing_pages]
        page_details.extend(ocr_details)
    elif not text:
        method = METHOD_MANUAL
    periods, month_flags = _month_periods(text, path.name)
    flags = list(month_flags)
    flags.extend(warnings)
    if any("CORRIG" in line.upper() or "RECTIFIC" in line.upper() for line in text.splitlines()):
        flags.append("CORRECTION_DETECTED")
    rows = extract_rows(text, method, periods)
    if not periods:
        flags.append("MONTH_NOT_DETECTED")
    if not rows:
        flags.append("NO_INDEX_ROWS_DETECTED")
    if method == METHOD_MANUAL:
        status = "ERROR" if warnings else "PENDING_VALIDATION"
    else:
        status = "PENDING_VALIDATION" if flags or any(row.validation_status == "PENDING_VALIDATION" for row in rows) else "PROCESSED"
    return DocumentResult(
        filename=path.name,
        sha256=digest,
        file_size=path.stat().st_size,
        pages=page_count(path),
        periods=periods,
        extractor=method,
        extraction_status=status,
        raw_rows=rows,
        errors=warnings,
        flags=flags,
        source_reference=source_reference or str(path),
        page_details=sorted(page_details, key=lambda item: item["page"]),
    )


def safe_zip_members(archive: Path) -> list[tuple[str, bytes]]:
    with zipfile.ZipFile(archive) as source:
        members = []
        for info in source.infolist():
            if info.is_dir():
                continue
            target = Path(info.filename)
            if target.is_absolute() or ".." in target.parts:
                raise ValueError(f"Chemin ZIP dangereux: {info.filename}")
            members.append((info.filename, source.read(info)))
        return members


def analyse_archive(archive: Path) -> list[DocumentResult]:
    results = []
    with tempfile.TemporaryDirectory(prefix="index-archive-") as temp:
        root = Path(temp)
        for name, content in safe_zip_members(archive):
            if not name.lower().endswith(".pdf"):
                continue
            target = root / Path(name).name
            target.write_bytes(content)
            results.append(analyse_pdf(target, source_reference=f"{archive}!{name}"))
    return sorted(results, key=lambda item: (item.periods[0] if item.periods else "9999-99", item.filename))
