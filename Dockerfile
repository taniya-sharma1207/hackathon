# docker build -t blk-hacking-ind-taniya-sharma .
# OS: Alpine Linux (minimal, secure); Linux base as required.
FROM python:3.12-alpine3.19

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY app/ ./app/

# Run on port 5477 as required
EXPOSE 5477

ENV PORT=5477
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5477"]
