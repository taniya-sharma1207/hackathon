"""
Blackrock retirement auto-saving challenge API.
Production-grade APIs for expense-based micro-investments and returns calculation.
"""
import os
import sys
import time
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    ExpenseInput,
    ParseResponse,
    ValidatorInput,
    ValidatorOutput,
    FilterInput,
    FilterOutput,
    ReturnsInput,
    ReturnsOutput,
    PerformanceOutput,
)
from app.services.transactions import parse_expenses, totals
from app.services.validator import validate_transactions
from app.services.filter import apply_temporal_constraints
from app.services.returns import compute_nps_returns, compute_index_returns

# Track request count / start time for performance (optional)
_start_time = time.perf_counter()
_request_count = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _start_time
    _start_time = time.perf_counter()
    yield
    # shutdown if needed
    pass


app = FastAPI(
    title="Retirement Auto-Saving API",
    description="APIs for automated retirement savings through expense-based micro-investments",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 1. Transaction Builder ---
@app.post("/blackrock/challenge/v1/transactions:parse", response_model=ParseResponse)
def transactions_parse(expenses: list[ExpenseInput]):
    """
    Receives a list of Expenses and returns transactions enriched with ceiling and remanent.
    """
    transactions = parse_expenses(expenses)
    total_amount, total_ceiling, total_remanent = totals(transactions)
    return ParseResponse(
        transactions=transactions,
        totalAmount=round(total_amount, 2),
        totalCeiling=round(total_ceiling, 2),
        totalRemanent=round(total_remanent, 2),
    )


# --- 2. Transaction Validator ---
@app.post("/blackrock/challenge/v1/transactions:validator", response_model=ValidatorOutput)
def transactions_validator(body: ValidatorInput):
    """
    Validates transactions based on wage and constraints. Returns valid, invalid, and duplicate.
    """
    valid, invalid, duplicate = validate_transactions(body.wage, body.transactions)
    return ValidatorOutput(valid=valid, invalid=invalid, duplicate=duplicate)


# --- 3. Temporal Constraints Validator ---
@app.post("/blackrock/challenge/v1/transactions:filter", response_model=FilterOutput)
def transactions_filter(body: FilterInput):
    """
    Applies q (fixed override), p (extra amount) rules and returns valid/invalid transactions.
    """
    valid, invalid = apply_temporal_constraints(
        body.q, body.p, body.transactions
    )
    return FilterOutput(valid=valid, invalid=invalid)


# --- 4a. Returns NPS ---
@app.post("/blackrock/challenge/v1/returns:nps", response_model=ReturnsOutput)
def returns_nps(body: ReturnsInput):
    """
    Calculates NPS returns with tax benefit (7.11% compounded, deduction up to 10% salary or 2L).
    """
    total_amount, total_ceiling, savings_by_dates = compute_nps_returns(
        body.age,
        body.wage,
        body.inflation,
        body.q,
        body.p,
        body.k,
        body.transactions,
    )
    return ReturnsOutput(
        transactionsTotalAmount=round(total_amount, 2),
        transactionsTotalCeiling=round(total_ceiling, 2),
        savingsByDates=savings_by_dates,
    )


# --- 4b. Returns Index ---
@app.post("/blackrock/challenge/v1/returns:index", response_model=ReturnsOutput)
def returns_index(body: ReturnsInput):
    """
    Calculates Index fund returns (14.49% compounded, no tax benefit).
    """
    total_amount, total_ceiling, savings_by_dates = compute_index_returns(
        body.age,
        body.wage,
        body.inflation,
        body.q,
        body.p,
        body.k,
        body.transactions,
    )
    return ReturnsOutput(
        transactionsTotalAmount=round(total_amount, 2),
        transactionsTotalCeiling=round(total_ceiling, 2),
        savingsByDates=savings_by_dates,
    )


# --- 5. Performance Report ---
@app.get("/blackrock/challenge/v1/performance", response_model=PerformanceOutput)
def performance():
    """
    Reports response time (since process start), memory usage, and thread count.
    """
    elapsed = time.perf_counter() - _start_time
    hours = int(elapsed // 3600)
    mins = int((elapsed % 3600) // 60)
    secs = elapsed % 60
    time_str = f"{hours:02d}:{mins:02d}:{secs:06.3f}"

    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss: macOS = bytes, Linux = KB
        if sys.platform == "darwin":
            mem_mb = (usage.ru_maxrss or 0) / (1024 * 1024)
        else:
            mem_mb = (usage.ru_maxrss or 0) / 1024
    except Exception:
        mem_mb = 0.0
    memory_str = f"{mem_mb:.2f} MB"

    threads = threading.active_count()

    return PerformanceOutput(
        time=time_str,
        memory=memory_str,
        threads=threads,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5477))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
