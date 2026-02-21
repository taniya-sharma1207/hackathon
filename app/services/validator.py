"""Validate transactions: valid, invalid (with message), duplicates."""
from collections import defaultdict
from datetime import datetime

from app.models import Transaction, InvalidTransaction


def validate_transactions(
    wage: float,
    transactions: list[Transaction],
) -> tuple[list[Transaction], list[InvalidTransaction], list[Transaction]]:
    """
    Validate transactions. Returns (valid, invalid, duplicate).
    Duplicates: same date (and possibly amount); invalid: constraint violations.
    """
    valid: list[Transaction] = []
    invalid: list[InvalidTransaction] = []
    duplicate: list[Transaction] = []
    seen_dates: set[datetime] = set()
    date_to_first: dict[datetime, Transaction] = {}

    for t in transactions:
        msgs = []

        # Amount < 5e5
        if t.amount >= 5e5:
            msgs.append("amount must be less than 500000")
        if t.ceiling >= 5e5:
            msgs.append("ceiling must be less than 500000")
        if t.remanent >= 5e5:
            msgs.append("remanent must be less than 500000")

        # Remanent = ceiling - amount
        expected_remanent = round(t.ceiling - t.amount, 2)
        if abs(t.remanent - expected_remanent) > 1e-6:
            msgs.append(
                f"remanent must equal ceiling - amount (expected {expected_remanent})"
            )

        # Ceiling is next multiple of 100
        import math
        expected_ceiling = math.ceil(t.amount / 100) * 100 if t.amount > 0 else 100
        if abs(t.ceiling - expected_ceiling) > 1e-6:
            msgs.append(
                f"ceiling must be next multiple of 100 for amount {t.amount} (expected {expected_ceiling})"
            )

        if msgs:
            invalid.append(
                InvalidTransaction(
                    date=t.date,
                    amount=t.amount,
                    ceiling=t.ceiling,
                    remanent=t.remanent,
                    message="; ".join(msgs),
                )
            )
            continue

        # Duplicate: same date (t_i != t_j in spec means unique timestamps)
        if t.date in seen_dates:
            duplicate.append(t)
            continue
        seen_dates.add(t.date)
        date_to_first[t.date] = t
        valid.append(t)

    return valid, invalid, duplicate
