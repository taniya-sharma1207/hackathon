"""Returns calculation: NPS (with tax benefit) and Index fund, compound interest, inflation."""
import math
from typing import Sequence

from app.models import (
    QPeriod,
    PPeriod,
    KPeriod,
    Transaction,
    TransactionWithTimestamp,
    SavingsByDates,
)


def _in_range(d, start, end) -> bool:
    return start <= d <= end


# Tax slabs (simplified): (upper_bound_exclusive, rate on amount above previous slab)
# 0–7L: 0%; 7L–10L: 10% on above 7L; 10L–12L: 15% on above 10L; 12L–15L: 20% on above 12L; >15L: 30% on above 15L
def _tax(income: float) -> float:
    """Tax on income (simplified slabs, standard deduction 50k not applied per spec)."""
    if income <= 0:
        return 0.0
    # Slabs: 0-7L=0, 7-10L=10%, 10-12L=15%, 12-15L=20%, >15L=30%
    tax_val = 0.0
    if income > 15_00_000:
        tax_val += (income - 15_00_000) * 0.30
        income = 15_00_000
    if income > 12_00_000:
        tax_val += (income - 12_00_000) * 0.20
        income = 12_00_000
    if income > 10_00_000:
        tax_val += (income - 10_00_000) * 0.15
        income = 10_00_000
    if income > 7_00_000:
        tax_val += (income - 7_00_000) * 0.10
    return round(tax_val, 2)


def _years_to_retirement(age: int) -> int:
    """Years until 60; if age >= 60 use 5."""
    if age >= 60:
        return 5
    return 60 - age


def _compound(P: float, r: float, t: int) -> float:
    """A = P * (1+r)^t (annual compounding)."""
    if t <= 0:
        return P
    return P * math.pow(1 + r, t)


def _inflation_adjust(A: float, inflation: float, t: int) -> float:
    """A_real = A / (1+inflation)^t."""
    if t <= 0:
        return A
    return A / math.pow(1 + inflation, t)


def _apply_q_p_to_transactions(
    transactions: list[TransactionWithTimestamp],
    q: Sequence[QPeriod],
    p: Sequence[PPeriod],
) -> list[Transaction]:
    """Reuse filter logic to get effective remanent per transaction."""
    from app.services.filter import apply_temporal_constraints
    valid, _ = apply_temporal_constraints(q, p, transactions)
    return valid


def compute_nps_returns(
    age: int,
    wage: float,
    inflation: float,
    q: list[QPeriod],
    p: list[PPeriod],
    k: list[KPeriod],
    transactions: list[TransactionWithTimestamp],
) -> tuple[float, float, list[SavingsByDates]]:
    """
    NPS: 7.11% compounded, tax benefit on min(invested, 10% of annual income, 2L).
    Returns (transactionsTotalAmount, transactionsTotalCeiling, savingsByDates).
    """
    RATE = 0.0711
    NPS_CAP = 200_000
    valid = _apply_q_p_to_transactions(transactions, q, p)
    total_amount = sum(t.amount for t in valid)
    total_ceiling = sum(t.ceiling for t in valid)
    annual_income = wage * 12
    t_years = _years_to_retirement(age)
    savings_by_dates = []

    for i, kp in enumerate(k):
        amount = sum(t.remanent for t in valid if _in_range(t.date, kp.start, kp.end))
        amount = round(amount, 2)
        A = _compound(amount, RATE, t_years)
        A_real = _inflation_adjust(A, inflation, t_years)
        profits = round(A_real - amount, 2)  # real profit

        nps_deduction = min(amount, annual_income * 0.10, NPS_CAP)
        tax_benefit = round(
            _tax(annual_income) - _tax(annual_income - nps_deduction), 2
        )

        savings_by_dates.append(
            SavingsByDates(
                start=kp.start,
                end=kp.end,
                amount=amount,
                profits=round(profits, 2),
                taxBenefit=tax_benefit,
            )
        )

    return total_amount, total_ceiling, savings_by_dates


def compute_index_returns(
    age: int,
    wage: float,
    inflation: float,
    q: list[QPeriod],
    p: list[PPeriod],
    k: list[KPeriod],
    transactions: list[TransactionWithTimestamp],
) -> tuple[float, float, list[SavingsByDates]]:
    """
    Index fund: 14.49% compounded, no tax benefit.
    Returns (transactionsTotalAmount, transactionsTotalCeiling, savingsByDates).
    """
    RATE = 0.1449
    valid = _apply_q_p_to_transactions(transactions, q, p)
    total_amount = sum(t.amount for t in valid)
    total_ceiling = sum(t.ceiling for t in valid)
    t_years = _years_to_retirement(age)
    savings_by_dates = []

    for kp in k:
        amount = sum(t.remanent for t in valid if _in_range(t.date, kp.start, kp.end))
        amount = round(amount, 2)
        A = _compound(amount, RATE, t_years)
        A_real = _inflation_adjust(A, inflation, t_years)
        savings_by_dates.append(
            SavingsByDates(
                start=kp.start,
                end=kp.end,
                amount=amount,
                profits=round(A_real, 2),  # index output is "return" = real value
                taxBenefit=0.0,
            )
        )

    return total_amount, total_ceiling, savings_by_dates
