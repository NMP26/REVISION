from decimal import Decimal, localcontext
from unittest import TestCase

from .calculation_engine import AllocationInput, CalculationInputError, allocate_amount, evaluate_simple_formula


class CalculationEngineTests(TestCase):
    def test_one_month_allocation(self):
        total, rows = allocate_amount(Decimal("535776.00"), [AllocationInput(2026, 8, Decimal("30"))])
        self.assertEqual(total, Decimal("30"))
        self.assertEqual(rows[0]["monthly_amount"], Decimal("535776.00"))

    def test_zero_months_remain_and_residual_is_assigned_to_last_positive_month(self):
        total, rows = allocate_amount(Decimal("100.01"), [AllocationInput(2026, 4, Decimal("0")), AllocationInput(2026, 5, Decimal("1")), AllocationInput(2026, 6, Decimal("2"))])
        self.assertEqual(total, Decimal("3"))
        self.assertEqual([row["monthly_amount"] for row in rows], [Decimal("0.00"), Decimal("33.34"), Decimal("66.67")])
        self.assertEqual(sum((row["monthly_amount"] for row in rows), Decimal("0")), Decimal("100.01"))

    def test_zero_total_is_blocked_for_positive_amount(self):
        with self.assertRaises(CalculationInputError):
            allocate_amount(Decimal("1.00"), [AllocationInput(2026, 8, Decimal("0"))])

    def test_formula_is_decimal_and_has_no_embedded_business_code(self):
        result = evaluate_simple_formula(constant=Decimal("0.15"), coefficient=Decimal("0.85"), base_index=Decimal("337.8"), current_index=Decimal("348.7"))
        with localcontext() as context:
            context.prec = 40
            self.assertEqual(result["ratio"], Decimal("348.7") / Decimal("337.8"))
        self.assertEqual(result["rounding_status"], "ROUNDING_POLICY_PENDING")

    def test_float_is_rejected(self):
        with self.assertRaises(CalculationInputError):
            evaluate_simple_formula(constant=0.15, coefficient=Decimal("0.85"), base_index=Decimal("1"), current_index=Decimal("1"))
