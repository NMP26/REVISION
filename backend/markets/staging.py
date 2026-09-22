"""Staging-only synchronization for revisiondesprix.ma."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import ExternalIndexStaging, IndexDefinition, MonthlyIndexValue
from .revisiondesprix_client import ExternalIndexValue, RevisionDesPrixApiClient


YEARS_AUDITED = (2021, 2022, 2023, 2024, 2025, 2026)


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"payload non sérialisable: {type(value)!r}")


def payload_hash(payload) -> str:
    encoded = json.dumps(payload, default=_json_default, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def compare_external_value(item: ExternalIndexValue, *, definition, local_value):
    if definition is None or local_value is None:
        return ExternalIndexStaging.ComparisonStatus.MISSING_LOCAL
    if local_value.value == item.value:
        return ExternalIndexStaging.ComparisonStatus.MATCHED
    return ExternalIndexStaging.ComparisonStatus.CONFLICT


@transaction.atomic
def stage_catalogue(client, *, dry_run=False, retrieved_at=None):
    retrieved_at = retrieved_at or timezone.now()
    names = client.get_index_names()
    definitions = {item.code: item for item in IndexDefinition.objects.all()}
    external_codes = {item.code for item in names}
    matched = missing = 0
    for item in names:
        definition = definitions.get(item.code)
        status = ExternalIndexStaging.ComparisonStatus.MATCHED if definition else ExternalIndexStaging.ComparisonStatus.MISSING_LOCAL
        matched += status == ExternalIndexStaging.ComparisonStatus.MATCHED
        missing += status == ExternalIndexStaging.ComparisonStatus.MISSING_LOCAL
        if not dry_run:
            ExternalIndexStaging.objects.update_or_create(
                source_provider=ExternalIndexStaging.SOURCE_PROVIDER,
                source_endpoint="/indices/names",
                external_code=item.code,
                year=None,
                month=None,
                defaults={
                    "retrieved_at": retrieved_at,
                    "raw_value": "",
                    "normalized_value": None,
                    "raw_payload_hash": payload_hash({"code": item.code, "endpoint": "/indices/names"}),
                    "comparison_status": status,
                    "validation_status": ExternalIndexStaging.ValidationStatus.PENDING_VALIDATION,
                    "matched_index_definition": definition,
                    "local_value": None,
                },
            )
    return {"total": len(names), "matched": matched, "missing_local": missing, "local_only": sorted(set(definitions) - external_codes)}


@transaction.atomic
def stage_year(client, year: int, *, code=None, dry_run=False, retrieved_at=None):
    retrieved_at = retrieved_at or timezone.now()
    values = client.get_indices_for_year(year)
    if code:
        values = [item for item in values if item.index_name == code]
    counts = {key: 0 for key in ("values", "normalized", "matched", "conflict", "missing_local", "invalid", "pending")}
    for item in values:
        definition = IndexDefinition.objects.filter(code=item.index_name).first()
        local = None
        if definition:
            local = MonthlyIndexValue.objects.filter(index_definition=definition, year=item.year, month=item.month).first()
        status = compare_external_value(item, definition=definition, local_value=local)
        counts["values"] += 1
        counts["normalized"] += 1
        counts[status.lower()] += 1 if status.lower() in counts else 0
        counts["pending"] += 1
        if not dry_run:
            defaults = {
                "retrieved_at": retrieved_at,
                "raw_value": str(item.value),
                "normalized_value": item.value,
                "raw_payload_hash": payload_hash(asdict(item)),
                "comparison_status": status,
                "validation_status": ExternalIndexStaging.ValidationStatus.PENDING_VALIDATION,
                "matched_index_definition": definition,
                "local_value": local.value if local else None,
                "pdf_comparison_status": "PDF_NOT_CHECKED",
            }
            staged, created = ExternalIndexStaging.objects.get_or_create(
                source_provider=ExternalIndexStaging.SOURCE_PROVIDER,
                source_endpoint=f"/indices?year={year}",
                external_code=item.index_name,
                year=item.year,
                month=item.month,
                defaults=defaults,
            )
            if not created:
                new_hash = defaults["raw_payload_hash"]
                if staged.raw_payload_hash != new_hash:
                    staged.previous_raw_value = staged.raw_value
                    staged.previous_normalized_value = staged.normalized_value
                    staged.previous_raw_payload_hash = staged.raw_payload_hash
                    staged.source_changed = True
                for field, value in defaults.items():
                    setattr(staged, field, value)
                staged.save()
    return counts


def compare_evolution(client, *, year_values, code: str):
    year_map = {item.date: item.value for item in year_values if item.index_name == code}
    evolution_map = {item.date: item.value for item in client.get_index_evolution(code)}
    result = []
    for item_date in sorted(set(year_map) | set(evolution_map)):
        year_value = year_map.get(item_date)
        evolution_value = evolution_map.get(item_date)
        if year_value is None:
            status = "MISSING_YEAR_ENDPOINT"
        elif evolution_value is None:
            status = "MISSING_EVOLUTION_ENDPOINT"
        elif year_value == evolution_value:
            status = "MATCHED"
        else:
            status = "CONFLICT"
        result.append({"code": code, "date": item_date, "year_value": year_value, "evolution_value": evolution_value, "status": status})
    return result
