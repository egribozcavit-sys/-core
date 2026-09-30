# PayCore — Production Payment Engine

High-performance payment infrastructure with idempotency, audit logging, and Redis Streams.

## Features

- ✅ Idempotent transactions (no double-spending)
- ✅ JWT authentication & authorization
- ✅ Redis Streams for durable queuing (consumer groups)
- ✅ Full audit logging
- ✅ Rate limiting (1000 req/min)
- ✅ PostgreSQL with timezone-aware timestamps
- ✅ Decimal-safe (integer cents, no float)
- ✅ Row-level locking (with_for_update)
- ✅ Health checks & structured logging
- ✅ Email validation
- ✅ Password strength validation

## Quick Start

```bash
git clone [https://github.com/yourusername/paycore.git](https://github.com/yourusername/paycore.git)
cd paycore
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set SECRET_KEY (min 32 chars)
uvicorn app.main:app --host 0.0.0.0 --port 8000
