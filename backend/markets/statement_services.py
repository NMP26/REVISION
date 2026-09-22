"""Django adapter around the pure V1 allocation and calculation engine."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError

from .calculation_engine import AllocationInput, CalculationInputError, allocate_amount, evaluate_simple_formula, formula_parameters
from .models import MarketFormula, MonthlyIndexValue, Statement
from .services import resolve_base_index, resolve_index


def v1_formula_for_market(market):
    if market.formula_structure != market.FormulaStructure.SINGLE or not market.global_revision_group_id:
        return None
    formulas = list(market.global_revision_group.formulas.prefetch_related("terms").exclude(status=MarketFormula.Status.INACTIVE).order_by("-version_number"))
    return formulas[0] if len(formulas) == 1 else None


def _source(index):
    source = index.get("source") or {}
    return {
        "publication": source.get("document_reference"),
        "source_type": source.get("source_type"),
        "source_reference": source.get("source_reference") or source.get("document_reference"),
    }


def calculate_statement_preview(statement: Statement) -> dict:
    market = statement.market
    formula = v1_formula_for_market(market)
    allocations = list(statement.monthly_allocations.order_by("year", "month"))
    total_days = sum((row.work_days for row in allocations), Decimal("0"))
    base = resolve_base_index(market, formula)
    base_value = Decimal(base["base_index_value"]) if base.get("base_index_value") else None
    base_status = base.get("base_index_status")
    result = {
        "statement_id": str(statement.pk),
        "statement_amount_ht": statement.amount_ht,
        "allocation_method": statement.allocation_method,
        "total_work_days": total_days,
        "total_allocated_amount": Decimal("0.00"),
        "total_revision": Decimal("0.00"),
        "calculation_status": "CALCULABLE_PREVIEW",
        "rounding_status": "ROUNDING_POLICY_PENDING",
        "base_index": base_value,
        "base_index_status": base_status,
        "base_index_source": base.get("base_index_publication") or base.get("base_index_source"),
        "index_code": base.get("base_index_code"),
        "formula": {
            "constant": formula.constant_term if formula else None,
            "coefficient": None,
            "index_code": None,
        },
        "monthly_results": [],
    }
    if formula is None:
        result["calculation_status"] = "FORMULA_NOT_AVAILABLE"
    elif len(formula.terms.all()) != 1:
        result["calculation_status"] = "FORMULA_NOT_SUPPORTED_V1"
    else:
        constant, coefficient, index_code = formula_parameters(formula, formula.terms.all()[0])
        result["formula"].update({"constant": constant, "coefficient": coefficient, "index_code": index_code})
        result["index_code"] = index_code

    if statement.amount_ht > 0 and total_days == 0:
        result["calculation_status"] = "NO_WORK_DAYS"
        result["message"] = "Aucun jour de travaux n'a été renseigné pour ce décompte."
        return result

    try:
        _, allocated = allocate_amount(statement.amount_ht, [AllocationInput(row.year, row.month, row.work_days) for row in allocations])
    except CalculationInputError as exc:
        raise ValidationError({"allocations": str(exc)}) from exc

    for allocation, amount in zip(allocations, allocated):
        current = resolve_index(result["index_code"], allocation.year, allocation.month) if result["index_code"] else {"status": "INDEX_NOT_AVAILABLE"}
        current_value = Decimal(current["value"]) if current.get("value") else None
        row = {
            "year": allocation.year,
            "month": allocation.month,
            "work_days": allocation.work_days,
            "monthly_amount": amount["monthly_amount"],
            "amount_to_revise": amount["monthly_amount"],
            "index_code": result["index_code"],
            "base_index": base_value,
            "current_index": current_value,
            "index_status": current.get("status", "INDEX_NOT_AVAILABLE"),
            "index_source": _source(current),
            "ratio": None,
            "K": None,
            "K_minus_1": None,
            "revision_amount": None,
            "calculation_status": "INDEX_NOT_AVAILABLE",
        }
        if amount["monthly_amount"] == 0:
            # Financial allocation is complete before index availability is
            # evaluated. A zero-work month therefore always has a zero
            # revision amount, while its index/coefficient fields remain
            # informative when the index is available.
            row["revision_amount"] = Decimal("0.00")
            if base_value is None or base_status != MonthlyIndexValue.Status.DEFINITIVE:
                row["calculation_status"] = "INDEX_NOT_AVAILABLE" if base_status == "INDEX_NOT_AVAILABLE" else "PENDING_INDEX"
            elif current_value is None:
                row["calculation_status"] = "INDEX_NOT_AVAILABLE"
            elif current.get("status") != MonthlyIndexValue.Status.DEFINITIVE:
                row["calculation_status"] = "PENDING_INDEX"
            else:
                formula_values = evaluate_simple_formula(constant=result["formula"]["constant"], coefficient=result["formula"]["coefficient"], base_index=base_value, current_index=current_value)
                row.update(formula_values)
                row["revision_amount"] = Decimal("0.00")
                row["calculation_status"] = "CALCULABLE_PREVIEW"
            result["monthly_results"].append(row)
            continue
        if base_value is None or base_status != MonthlyIndexValue.Status.DEFINITIVE:
            row["calculation_status"] = "INDEX_NOT_AVAILABLE" if base_status == "INDEX_NOT_AVAILABLE" else "PENDING_INDEX"
        elif current_value is None:
            row["calculation_status"] = "INDEX_NOT_AVAILABLE"
        elif current.get("status") != MonthlyIndexValue.Status.DEFINITIVE:
            row["calculation_status"] = "PENDING_INDEX"
        else:
            formula_values = evaluate_simple_formula(constant=result["formula"]["constant"], coefficient=result["formula"]["coefficient"], base_index=base_value, current_index=current_value)
            row.update(formula_values)
            row["revision_amount"] = amount["monthly_amount"] * row["K_minus_1"]
            row["calculation_status"] = "CALCULABLE_PREVIEW"
        result["monthly_results"].append(row)

    result["total_allocated_amount"] = sum((row["monthly_amount"] for row in result["monthly_results"]), Decimal("0.00"))
    usable = [row for row in result["monthly_results"] if row["monthly_amount"] > 0]
    if any(row["calculation_status"] == "INDEX_NOT_AVAILABLE" for row in usable):
        result["calculation_status"] = "INDEX_NOT_AVAILABLE"
        result["total_revision"] = None
    elif any(row["calculation_status"] == "PENDING_INDEX" for row in usable):
        result["calculation_status"] = "PENDING_INDEX"
        result["total_revision"] = None
    else:
        result["total_revision"] = sum(((row["revision_amount"] or Decimal("0")) for row in result["monthly_results"]), Decimal("0"))
    return result
