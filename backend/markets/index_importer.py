"""Safe, reviewable extraction pipeline for official index PDFs.

This module deliberately stops before database import.  It produces raw rows and
normalised candidates so a later approval step can decide what becomes official.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
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


def _run(command: list[str], *, text=True) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, capture_output=True, text=text)


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


def ocr_text(path: Path) -> tuple[str, str, list[str]]:
    """OCR only a document with no useful text layer."""
    warnings = []
    try:
        with tempfile.TemporaryDirectory(prefix="index-ocr-") as temp:
            prefix = Path(temp) / "page"
            _run(["pdftoppm", "-jpeg", "-r", "100", str(path), str(prefix)], text=False)
            pages = sorted(Path(temp).glob("page-*.jpg"))
            if not pages:
                return "", METHOD_MANUAL, ["Aucune page rasterisée"]
            chunks = []
            def read_page(item):
                number, image = item
                try:
                    text = _run(["tesseract", str(image), "stdout", "-l", "fra+eng", "--psm", "6"]).stdout
                    return number, f"--- page-{number}.jpg ---\n{text}", None
                except (FileNotFoundError, subprocess.CalledProcessError) as exc:
                    return number, "", f"OCR page {number}: {exc}"
            with ThreadPoolExecutor(max_workers=4) as pool:
                page_results = list(pool.map(read_page, enumerate(pages, start=1)))
            for number, text, warning in page_results:
                if warning:
                    warnings.append(warning)
                else:
                    chunks.append(text)
            return "\n".join(chunks), METHOD_OCR if chunks else METHOD_MANUAL, warnings
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        return "", METHOD_MANUAL, [f"Outils OCR indisponibles: {exc}"]


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
    if not _SAFE_CODES.fullmatch(code):
        return "", "CODE_AMBIGUOUS"
    return code.upper(), ""


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
    text = native_text(path)
    method = METHOD_NATIVE if len(re.sub(r"\s", "", text)) >= 100 else ""
    warnings = []
    if not method:
        text, method, warnings = ocr_text(path)
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
