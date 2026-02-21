# Retirement Auto-Saving API (Blackrock Challenge)

Production-grade APIs for **automated retirement savings** through expense-based micro-investments. The system supports rounding up expenses to the next multiple of 100, temporal rules (fixed/extra amounts), evaluation periods, and return calculations for NPS and Index funds with inflation adjustment.

## Features

- **Transaction Builder** – Parse expenses into transactions with ceiling and remanent (round-up to next 100).
- **Transaction Validator** – Validate transactions (constraints, duplicates).
- **Temporal Filter** – Apply q (fixed amount override), p (extra amount) rules; output valid/invalid.
- **Returns** – NPS (7.11%, tax benefit up to 10% salary / ₹2L) and Index (14.49%), compound interest and inflation-adjusted.
- **Performance** – Report uptime, memory, and thread count.

## Requirements

- Python 3.10+
- Docker (optional, for containerized run)

## Configuration and Run

### Local (no Docker)

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server (port **5477**):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 5477
   ```
   Or:
   ```bash
   python -m app.main
   ```

4. API base: `http://localhost:5477`  
   - Health: `GET /health`  
   - Swagger UI: `GET /docs`  
   - OpenAPI JSON: `GET /openapi.json`  
   - **Standalone contract:** `openapi.yaml` (OpenAPI 3.0) in the project root for import into Postman, API gateways, or codegen.

### Docker

1. Build the image (image name per convention):
   ```bash
   docker build -t blk-hacking-ind-taniya-sharma .
   ```

2. Run the container with port mapping:
   ```bash
   docker run -d -p 5477:5477 blk-hacking-ind-taniya-sharma
   ```

### Docker Compose

```bash
docker compose up --build
```

The API will be available at `http://localhost:5477`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/blackrock/challenge/v1/transactions:parse` | Parse expenses → transactions (ceiling, remanent) |
| POST | `/blackrock/challenge/v1/transactions:validator` | Validate transactions (valid, invalid, duplicate) |
| POST | `/blackrock/challenge/v1/transactions:filter` | Apply q/p periods → valid/invalid transactions |
| POST | `/blackrock/challenge/v1/returns:nps` | NPS returns (7.11%, tax benefit) |
| POST | `/blackrock/challenge/v1/returns:index` | Index fund returns (14.49%) |
| GET | `/blackrock/challenge/v1/performance` | Execution metrics (time, memory, threads) |

### Example: Parse

```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/transactions:parse \
  -H "Content-Type: application/json" \
  -d '[
    {"timestamp": "2023-10-12T20:15:00", "amount": 250},
    {"timestamp": "2023-02-28T15:49:00", "amount": 375}
  ]'
```

### Example: Returns (NPS)

```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/returns:nps \
  -H "Content-Type: application/json" \
  -d '{
    "age": 29,
    "wage": 50000,
    "inflation": 0.055,
    "q": [{"fixed": 0, "start": "2023-07-01T00:00:00", "end": "2023-07-31T23:59:00"}],
    "p": [{"extra": 25, "start": "2023-10-01T08:00:00", "end": "2023-12-31T19:59:00"}],
    "k": [{"start": "2023-01-01T00:00:00", "end": "2023-12-31T23:59:00"}],
    "transactions": [
      {"timestamp": "2023-10-12T20:15:00", "amount": 250, "ceiling": 300, "remanent": 50},
      {"timestamp": "2023-02-28T15:49:00", "amount": 375, "ceiling": 400, "remanent": 25},
      {"timestamp": "2023-07-01T21:59:00", "amount": 620, "ceiling": 700, "remanent": 80},
      {"timestamp": "2023-12-17T08:09:00", "amount": 480, "ceiling": 500, "remanent": 20}
    ]
  }'
```

## Testing

Tests are under the `test/` folder.

- **Test type:** Integration / API  
- **Validation:** All challenge endpoints (parse, validator, filter, returns:nps, returns:index, performance)  
- **Command:**
  ```bash
  pytest test/test_api.py -v
  ```
  Or with venv:
  ```bash
  .venv/bin/python -m pytest test/test_api.py -v
  ```

## Project Structure

```
├── app/
│   ├── main.py           # FastAPI app and routes
│   ├── models.py         # Pydantic request/response models
│   └── services/
│       ├── transactions.py  # Parse, ceiling/remanent
│       ├── validator.py     # Valid/invalid/duplicate
│       ├── filter.py        # q, p temporal rules
│       └── returns.py       # NPS, Index, compound, tax, inflation
├── test/
│   └── test_api.py       # API integration tests
├── requirements.txt
├── Dockerfile
├── compose.yaml
└── README.md
```

## Business Rules Summary

- **Ceiling:** Next multiple of 100 above expense amount; **remanent** = ceiling − amount.
- **q periods:** Replace remanent with `fixed` when transaction date ∈ [start, end]. If multiple q match, use the one with **latest start** (then first in list).
- **p periods:** Add `extra` to remanent for each matching p (all matching p are summed).
- **k periods:** For each k, sum remanent of transactions with date in [start, end] (inclusive).
- **NPS:** 7.11% compounded; tax benefit on `min(invested, 10% of annual income, ₹2,00,000)`.
- **Index:** 14.49% compounded; no tax benefit. Final value adjusted for inflation: `A_real = A / (1+inflation)^t`.

## License

Part of the Blackrock code challenge. Use as per challenge terms.
