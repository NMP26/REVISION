"""Pure Decimal helpers for the V1 statement allocation/revision preview."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import Iterable, Mapping


CENT = Decimal("0.01")
FOUR_DECIMALS = Decimal("0.0001")


class CalculationInputError(ValueError):
    pass


@dataclass(frozen=True)
class AllocationInput:
    year: int
    month: int
    work_days: Decimal


def decimal(value) -> Decimal:
    if isinstance(value, float):
        raise CalculationInputError("Les calculs V1 refusent les float.")
    try:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    except Exception as exc:
        raise CalculationInputError("Valeur Decimal invalide.") from exc


def round_money(value: Decimal) -> Decimal:
    """Technical preview rounding; regulatory mode remains pending validation."""
    return decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def allocate_amount(amount: Decimal, allocations: Iterable[AllocationInput]) -> tuple[Decimal, list[dict]]:
    amount = decimal(amount)
    rows = list(allocations)
    if amount < 0:
        raise CalculationInputError("Le montant HT ne peut pas être négatif.")
    if any(row.work_days < 0 for row in rows):
        raise CalculationInputError("Le nombre de jours ne peut pas être négatif.")
    total_days = sum((decimal(row.work_days) for row in rows), Decimal("0"))
    if amount > 0 and total_days == 0:
        raise CalculationInputError("Aucun jour de travaux n'a été renseigné pour ce décompte.")
    if total_days == 0:
        return total_days, [{"year": row.year, "month": row.month, "work_days": decimal(row.work_days), "monthly_amount": Decimal("0.00")} for row in rows]

    result = []
    positive_indexes = [index for index, row in enumerate(rows) if row.work_days > 0]
    last_positive = positive_indexes[-1]
    with localcontext() as context:
        context.prec = 40
        for index, row in enumerate(rows):
            raw = amount * decimal(row.work_days) / total_days
            result.append({"year": row.year, "month": row.month, "work_days": decimal(row.work_days), "monthly_amount": round_money(raw), "raw_monthly_amount": raw})
    allocated = sum((row["monthly_amount"] for row in result), Decimal("0.00"))
    result[last_positive]["monthly_amount"] += amount.quantize(CENT) - allocated
    for row in result:
        row.pop("raw_monthly_amount", None)
    return total_days, result


def evaluate_simple_formula(*, constant: Decimal, coefficient: Decimal, base_index: Decimal, current_index: Decimal) -> dict:
    constant = decimal(constant)
    coefficient = decimal(coefficient)
    base_index = decimal(base_index)
    current_index = decimal(current_index)
    if base_index <= 0 or current_index <= 0:
        raise CalculationInputError("Les indices doivent être strictement positifs.")
    with localcontext() as context:
        context.prec = 40
        ratio = current_index / base_index
        k = constant + coefficient * ratio
    return {
        "ratio": ratio,
        "K": k,
        "K_minus_1": k - Decimal("1"),
        "rounding_status": "ROUNDING_POLICY_PENDING",
    }


def formula_parameters(formula, term) -> tuple[Decimal, Decimal, str]:
    """Read formula data; no business code is embedded here."""
    if formula is None or term is None or formula.constant_term is None:
        raise CalculationInputError("Formule simple indisponible ou incomplète.")
    return decimal(formula.constant_term), decimal(term.coefficient), term.index_code
