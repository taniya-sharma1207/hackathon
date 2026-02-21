"""Pydantic models for the retirement auto-saving API."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Expense / Transaction inputs ---
class ExpenseInput(BaseModel):
    """Raw expense as received (timestamp + amount)."""
    timestamp: datetime
    amount: float = Field(..., lt=5e5)


class Transaction(BaseModel):
    """Parsed transaction with ceiling and remanent."""
    date: datetime
    amount: float
    ceiling: float
    remanent: float


class InvalidTransaction(Transaction):
    """Transaction with validation error message."""
    message: str


# --- Period definitions ---
class QPeriod(BaseModel):
    """Fixed amount override period."""
    fixed: float = Field(..., lt=5e5)
    start: datetime
    end: datetime


class PPeriod(BaseModel):
    """Extra amount addition period."""
    extra: float = Field(..., lt=5e5)
    start: datetime
    end: datetime


class KPeriod(BaseModel):
    """Evaluation grouping period (start/end only)."""
    start: datetime
    end: datetime


# --- Parse response ---
class ParseResponse(BaseModel):
    """Response from transaction parse endpoint."""
    transactions: list[Transaction]
    totalAmount: Optional[float] = None
    totalCeiling: Optional[float] = None
    totalRemanent: Optional[float] = None


# --- Validator input/output ---
class ValidatorInput(BaseModel):
    wage: float
    transactions: list[Transaction]


class ValidatorOutput(BaseModel):
    valid: list[Transaction]
    invalid: list[InvalidTransaction]
    duplicate: list[Transaction] = Field(default_factory=list)


# --- Filter input (transactions use timestamp per spec) ---
class TransactionWithTimestamp(BaseModel):
    timestamp: datetime
    amount: float
    ceiling: float
    remanent: float


class FilterInput(BaseModel):
    q: list[QPeriod] = Field(default_factory=list)
    p: list[PPeriod] = Field(default_factory=list)
    k: list[KPeriod] = Field(default_factory=list)
    transactions: list[TransactionWithTimestamp]


class FilterOutput(BaseModel):
    valid: list[Transaction]
    invalid: list[InvalidTransaction]


# --- Returns input ---
class ReturnsInput(BaseModel):
    age: int
    wage: float
    inflation: float
    q: list[QPeriod] = Field(default_factory=list)
    p: list[PPeriod] = Field(default_factory=list)
    k: list[KPeriod] = Field(default_factory=list)
    transactions: list[TransactionWithTimestamp]


class SavingsByDates(BaseModel):
    start: datetime
    end: datetime
    amount: float
    profits: float
    taxBenefit: float = 0.0


class ReturnsOutput(BaseModel):
    transactionsTotalAmount: float
    transactionsTotalCeiling: float
    savingsByDates: list[SavingsByDates]


# --- Performance ---
class PerformanceOutput(BaseModel):
    time: str  # HH:mm:ss.SSS or duration ms
    memory: str  # XXX.XX MB
    threads: int
