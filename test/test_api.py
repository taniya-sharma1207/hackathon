# Test type: Integration / API
# Validation: Transaction parse, validator, filter, returns (NPS/Index), performance endpoints
# Command: pytest test/test_api.py -v
# Alternative: python -m pytest test/test_api.py -v

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_transactions_parse():
    expenses = [
        {"timestamp": "2023-10-12T20:15:00", "amount": 250},
        {"timestamp": "2023-02-28T15:49:00", "amount": 375},
        {"timestamp": "2023-07-01T21:59:00", "amount": 620},
        {"timestamp": "2023-12-17T08:09:00", "amount": 480},
    ]
    r = client.post("/blackrock/challenge/v1/transactions:parse", json=expenses)
    assert r.status_code == 200
    data = r.json()
    assert len(data["transactions"]) == 4
    assert data["totalRemanent"] == 175.0  # 50+25+80+20
    # 250->300 rem 50, 375->400 rem 25, 620->700 rem 80, 480->500 rem 20
    assert data["transactions"][0]["remanent"] == 50
    assert data["transactions"][1]["remanent"] == 25
    assert data["transactions"][2]["remanent"] == 80
    assert data["transactions"][3]["remanent"] == 20


def test_transactions_validator():
    transactions = [
        {"date": "2023-10-12T20:15:00", "amount": 250, "ceiling": 300, "remanent": 50},
        {"date": "2023-02-28T15:49:00", "amount": 375, "ceiling": 400, "remanent": 25},
    ]
    r = client.post(
        "/blackrock/challenge/v1/transactions:validator",
        json={"wage": 50000, "transactions": transactions},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["valid"]) == 2
    assert len(data["invalid"]) == 0
    assert len(data["duplicate"]) == 0


def test_validator_rejects_invalid_remanent():
    transactions = [
        {"date": "2023-10-12T20:15:00", "amount": 250, "ceiling": 300, "remanent": 99},
    ]
    r = client.post(
        "/blackrock/challenge/v1/transactions:validator",
        json={"wage": 50000, "transactions": transactions},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["invalid"]) == 1
    assert "remanent" in data["invalid"][0]["message"].lower() or "ceiling" in data["invalid"][0]["message"].lower()


def test_validator_marks_duplicate():
    # Two valid transactions with same date -> one valid, one duplicate
    transactions = [
        {"date": "2023-10-12T20:15:00", "amount": 250, "ceiling": 300, "remanent": 50},
        {"date": "2023-10-12T20:15:00", "amount": 250, "ceiling": 300, "remanent": 50},
    ]
    r = client.post(
        "/blackrock/challenge/v1/transactions:validator",
        json={"wage": 50000, "transactions": transactions},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["valid"]) == 1
    assert len(data["duplicate"]) == 1


def test_transactions_filter():
    transactions = [
        {"timestamp": "2023-10-12T20:15:00", "amount": 250, "ceiling": 300, "remanent": 50},
        {"timestamp": "2023-02-28T15:49:00", "amount": 375, "ceiling": 400, "remanent": 25},
        {"timestamp": "2023-07-01T21:59:00", "amount": 620, "ceiling": 700, "remanent": 80},
        {"timestamp": "2023-12-17T08:09:00", "amount": 480, "ceiling": 500, "remanent": 20},
    ]
    q = [{"fixed": 0, "start": "2023-07-01T00:00:00", "end": "2023-07-31T23:59:00"}]
    p = [{"extra": 25, "start": "2023-10-01T08:00:00", "end": "2023-12-31T19:59:00"}]
    k = [
        {"start": "2023-03-01T00:00:00", "end": "2023-11-30T23:59:00"},
        {"start": "2023-01-01T00:00:00", "end": "2023-12-31T23:59:00"},
    ]
    r = client.post(
        "/blackrock/challenge/v1/transactions:filter",
        json={"q": q, "p": p, "k": k, "transactions": transactions},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["valid"]) == 4
    # After q: July expense remanent = 0. After p: Oct +25 -> 75, Dec +25 -> 45
    assert any("2023-07-01" in t["date"] and t["remanent"] == 0 for t in data["valid"])
    assert any(t["remanent"] == 75 for t in data["valid"])
    assert any(t["remanent"] == 45 for t in data["valid"])
    assert sum(t["remanent"] for t in data["valid"]) == 145.0  # 25+0+75+45


def test_returns_nps_example():
    transactions = [
        {"timestamp": "2023-10-12T20:15:00", "amount": 250, "ceiling": 300, "remanent": 50},
        {"timestamp": "2023-02-28T15:49:00", "amount": 375, "ceiling": 400, "remanent": 25},
        {"timestamp": "2023-07-01T21:59:00", "amount": 620, "ceiling": 700, "remanent": 80},
        {"timestamp": "2023-12-17T08:09:00", "amount": 480, "ceiling": 500, "remanent": 20},
    ]
    q = [{"fixed": 0, "start": "2023-07-01T00:00:00", "end": "2023-07-31T23:59:00"}]
    p = [{"extra": 25, "start": "2023-10-01T08:00:00", "end": "2023-12-31T19:59:00"}]
    k = [
        {"start": "2023-03-01T00:00:00", "end": "2023-11-30T23:59:00"},
        {"start": "2023-01-01T00:00:00", "end": "2023-12-31T23:59:00"},
    ]
    body = {
        "age": 29,
        "wage": 50000,
        "inflation": 0.055,
        "q": q,
        "p": p,
        "k": k,
        "transactions": transactions,
    }
    r = client.post("/blackrock/challenge/v1/returns:nps", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["transactionsTotalAmount"] == 1725.0
    assert data["transactionsTotalCeiling"] == 1900.0
    assert len(data["savingsByDates"]) == 2
    # Full year amount = 145 (25+0+75+45); Mar-Nov = 75
    amounts = sorted([s["amount"] for s in data["savingsByDates"]])
    assert amounts == [75.0, 145.0]
    full_year = next(s for s in data["savingsByDates"] if s["amount"] == 145.0)
    assert full_year["taxBenefit"] == 0  # salary 6L in 0% slab


def test_returns_index():
    transactions = [
        {"timestamp": "2023-01-15T12:00:00", "amount": 150, "ceiling": 200, "remanent": 50},
    ]
    k = [{"start": "2023-01-01T00:00:00", "end": "2023-12-31T23:59:00"}]
    body = {
        "age": 29,
        "wage": 50000,
        "inflation": 0.055,
        "q": [],
        "p": [],
        "k": k,
        "transactions": transactions,
    }
    r = client.post("/blackrock/challenge/v1/returns:index", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["savingsByDates"][0]["amount"] == 50.0
    assert data["savingsByDates"][0]["taxBenefit"] == 0.0


def test_performance():
    r = client.get("/blackrock/challenge/v1/performance")
    assert r.status_code == 200
    data = r.json()
    assert "time" in data
    assert "memory" in data
    assert "threads" in data
    assert isinstance(data["threads"], int)
    assert "MB" in data["memory"]
