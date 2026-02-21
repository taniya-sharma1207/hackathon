"""Temporal constraints: apply q (fixed override), p (extra add), then group by k."""
from datetime import datetime
from typing import Sequence

from app.models import (
    QPeriod,
    PPeriod,
    KPeriod,
    Transaction,
    InvalidTransaction,
    TransactionWithTimestamp,
)


def _in_range(d: datetime, start: datetime, end: datetime) -> bool:
    """Inclusive range check."""
    return start <= d <= end


def _apply_q(
    transactions: list[TransactionWithTimestamp],
    q_periods: list[QPeriod],
) -> list[tuple[TransactionWithTimestamp, float]]:
    """
    For each transaction, apply q rules: replace remanent with fixed when in range.
    If multiple q match: use the one that starts latest; same start use first in list.
    Returns list of (transaction, effective_remanent after q).
    """
    result = []
    for t in transactions:
        rem = t.remanent
        # Find all q periods that contain t.timestamp
        matching = [
            (i, q)
            for i, q in enumerate(q_periods)
            if _in_range(t.timestamp, q.start, q.end)
        ]
        if matching:
            # Sort by start desc (latest first), then by index asc (first in list)
            matching.sort(key=lambda x: (-x[1].start.timestamp(), x[0]))
            rem = matching[0][1].fixed
        result.append((t, rem))
    return result


def _apply_p(
    tx_remanent: list[tuple[TransactionWithTimestamp, float]],
    p_periods: list[PPeriod],
) -> list[tuple[TransactionWithTimestamp, float]]:
    """
    Add extra from all matching p periods to each transaction's remanent.
    Returns list of (transaction, final_remanent).
    """
    result = []
    for t, rem in tx_remanent:
        for p in p_periods:
            if _in_range(t.timestamp, p.start, p.end):
                rem += p.extra
        result.append((t, rem))
    return result


def apply_temporal_constraints(
    q: list[QPeriod],
    p: list[PPeriod],
    transactions: list[TransactionWithTimestamp],
) -> tuple[list[Transaction], list[InvalidTransaction]]:
    """
    Apply q then p. Return valid transactions with updated remanent, and invalid list.
    """
    invalid: list[InvalidTransaction] = []
    after_q = _apply_q(transactions, q)
    after_p = _apply_p(after_q, p)
    valid = []
    for (t, rem) in after_p:
        if rem < 0:
            invalid.append(
                InvalidTransaction(
                    date=t.timestamp,
                    amount=t.amount,
                    ceiling=t.ceiling,
                    remanent=t.remanent,
                    message="remanent became negative after applying periods",
                )
            )
        else:
            valid.append(
                Transaction(
                    date=t.timestamp,
                    amount=t.amount,
                    ceiling=t.ceiling,
                    remanent=round(rem, 2),
                )
            )
    return valid, invalid


def compute_k_sums(
    k_periods: list[KPeriod],
    transactions: list[Transaction],
) -> list[float]:
    """
    For each k period, sum remanent of transactions whose date is in [start, end].
    Returns list of amounts (one per k period).
    """
    amounts = []
    for kp in k_periods:
        s = sum(
            t.remanent
            for t in transactions
            if _in_range(t.date, kp.start, kp.end)
        )
        amounts.append(round(s, 2))
    return amounts
