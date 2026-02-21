"""Transaction parsing: ceiling to next multiple of 100, remanent = ceiling - amount."""
import math
from datetime import datetime

from app.models import ExpenseInput, Transaction


def ceiling_to_100(amount: float) -> float:
    """Round up to next multiple of 100."""
    if amount <= 0:
        return 100.0
    return math.ceil(amount / 100) * 100


def parse_expenses(expenses: list[ExpenseInput]) -> list[Transaction]:
    """Build transactions from expenses with ceiling and remanent."""
    result = []
    for e in expenses:
        ceiling = ceiling_to_100(e.amount)
        remanent = ceiling - e.amount
        result.append(
            Transaction(
                date=e.timestamp,
                amount=e.amount,
                ceiling=ceiling,
                remanent=remanent,
            )
        )
    return result


def totals(transactions: list[Transaction]) -> tuple[float, float, float]:
    """Return (total amount, total ceiling, total remanent)."""
    total_amount = sum(t.amount for t in transactions)
    total_ceiling = sum(t.ceiling for t in transactions)
    total_remanent = sum(t.remanent for t in transactions)
    return total_amount, total_ceiling, total_remanent
