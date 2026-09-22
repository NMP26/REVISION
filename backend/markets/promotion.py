"""Controlled promotion from external staging to the local index repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from django.db import transaction

from .models import ExternalIndexStaging, IndexDefinition, IndexPublication, MonthlyIndexValue


def normalize_code(code: str) -> str:
    return str(code or "").strip().upper()


@dataclass
class PromotionPlan:
    definition_decisions: list[dict] = field(default_factory=list)
    definitions_to_create: list[dict] = field(default_factory=list)
    values_to_create: list[dict] = field(default_factory=list)
    values_already_identical: list[dict] = field(default_factory=list)
    conflicts: list[dict] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)
    pending_validation: list[dict] = field(default_factory=list)

    @property
    def summary(self):
        return {
            "index_definitions_to_create": len(self.definitions_to_create),
            "values_to_create": len(self.values_to_create),
            "values_already_identical": len(self.values_already_identical),
            "conflicts": len(self.conflicts),
            "rejected": len(self.rejected),
            "pending_validation": len(self.pending_validation),
        }


class IndexPromotionService:
    """Plan/apply explicit staging promotion without overwriting local values."""

    def __init__(self, *, year=None, code=None):
        self.year = year
        self.code = normalize_code(code) if code else None

    def _catalogue_rows(self):
        rows = ExternalIndexStaging.objects.filter(year__isnull=True, month__isnull=True)
        if self.code:
            rows = rows.filter(external_code=self.code)
        return rows.order_by("external_code")

    def _value_rows(self):
        rows = ExternalIndexStaging.objects.filter(year__isnull=False, month__isnull=False)
        if self.year:
            rows = rows.filter(year=self.year)
        if self.code:
            rows = rows.filter(external_code=self.code)
        return rows.order_by("external_code", "year", "month")

    def plan(self) -> PromotionPlan:
        plan = PromotionPlan()
        definitions = {normalize_code(definition.code): definition for definition in IndexDefinition.objects.all()}
        candidates = {}

        for row in self._catalogue_rows():
            normalized = normalize_code(row.external_code)
            local = definitions.get(normalized)
            if local is not None:
                decision = "MATCH_EXISTING"
            elif row.external_designation:
                decision = "CREATE_CANDIDATE"
                candidates[normalized] = row
            else:
                decision = "REJECT"
            if local is not None and row.external_designation and local.designation.strip() != row.external_designation.strip():
                decision = "DESIGNATION_CONFLICT"
            item = {
                "external_code": row.external_code,
                "external_designation": row.external_designation,
                "local_match": str(local.id) if local else None,
                "decision": decision,
            }
            plan.definition_decisions.append(item)
            if decision == "CREATE_CANDIDATE":
                plan.definitions_to_create.append(item)

        for row in self._value_rows():
            normalized = normalize_code(row.external_code)
            definition = definitions.get(normalized)
            candidate = candidates.get(normalized)
            item = {"code": normalized, "year": row.year, "month": row.month, "external_value": row.normalized_value, "staging_id": str(row.id)}
            if row.normalized_value is None or not (1 <= row.month <= 12):
                item["reason"] = "INVALID_VALUE_OR_MONTH"
                plan.rejected.append(item)
                continue
            if definition is None and candidate is None:
                item["reason"] = "INDEX_DEFINITION_MISSING"
                plan.rejected.append(item)
                continue
            if definition is None:
                item["reason"] = "INDEX_DEFINITION_CANDIDATE_NOT_APPLIED"
                plan.rejected.append(item)
                continue
            local = MonthlyIndexValue.objects.filter(index_definition=definition, year=row.year, month=row.month).first()
            if local is None:
                if row.validation_status == ExternalIndexStaging.ValidationStatus.INVALID or row.comparison_status in {
                    ExternalIndexStaging.ComparisonStatus.CONFLICT,
                    ExternalIndexStaging.ComparisonStatus.INVALID,
                }:
                    item["reason"] = "STAGING_NOT_PROMOTABLE"
                    plan.rejected.append(item)
                    continue
                item["status"] = MonthlyIndexValue.Status.PENDING_VALIDATION
                plan.values_to_create.append(item)
                plan.pending_validation.append(item)
            elif local.value == row.normalized_value:
                item["local_value"] = local.value
                plan.values_already_identical.append(item)
            else:
                item["local_value"] = local.value
                plan.conflicts.append(item)
        return plan

    @transaction.atomic
    def apply(self) -> tuple[PromotionPlan, dict]:
        initial = self.plan()
        definitions_created = 0
        for item in initial.definitions_to_create:
            row = ExternalIndexStaging.objects.select_for_update().get(
                external_code=item["external_code"], year__isnull=True, month__isnull=True,
            )
            _, created = IndexDefinition.objects.get_or_create(
                code=normalize_code(item["external_code"]),
                defaults={"designation": row.external_designation.strip(), "domain": "", "active": True},
            )
            definitions_created += int(created)

        plan = self.plan()
        values_created = 0
        for item in plan.values_to_create:
            definition = IndexDefinition.objects.get(code=item["code"])
            row = ExternalIndexStaging.objects.select_for_update().get(pk=item["staging_id"])
            publication, _ = IndexPublication.objects.get_or_create(
                year=row.year,
                month=row.month,
                source_type=IndexPublication.SourceType.EXTERNAL_SECONDARY,
                defaults={
                    "document_reference": f"Source secondaire — {row.source_provider}",
                    "source_url": "https://revisiondesprix.ma",
                    "status": IndexPublication.Status.PENDING_VALIDATION,
                },
            )
            MonthlyIndexValue.objects.create(
                index_definition=definition,
                publication=publication,
                year=row.year,
                month=row.month,
                value=Decimal(row.normalized_value),
                status=MonthlyIndexValue.Status.PENDING_VALIDATION,
                source_url="https://revisiondesprix.ma",
                source_document=f"Source secondaire — {row.source_provider}",
                source_reference=f"{row.source_endpoint} | staging={row.id} | récupéré={row.retrieved_at.isoformat()}",
            )
            values_created += 1
        return plan, {"index_definitions_created": definitions_created, "monthly_values_created": values_created}
