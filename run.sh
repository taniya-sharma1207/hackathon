#!/bin/bash
# Run the API from the project root: ./run.sh
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 5477
