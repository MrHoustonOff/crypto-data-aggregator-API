# Crypto Data Aggregator API

> An asynchronous backend service for aggregating cryptocurrency quotes and delivering webhook notifications based on user-defined price alerts.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.13-FF6600?style=flat-square&logo=rabbitmq&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)

---
*Также доступно на русском: [README](docs/README.ru.md)*
## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [User Flow](#user-flow)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Tests](#tests)
- [Project Goals](#project-goals)
- [Planned Improvements](#planned-improvements)

---

## Overview

The service addresses the problem of real-time cryptocurrency price monitoring and asynchronous notification delivery.

**What the system can do:**

- Aggregates prices for 5 tickers (`BTC`, `ETH`, `DOGE`, `SOL`, `BNB`) from two sources — **Binance** and **CoinGecko** — in parallel, via an adapter layer.
- Provides a REST API with API key authentication for managing price alerts.
- When an alert is triggered, places a task in a RabbitMQ queue and reliably delivers an HTTP webhook to the user's URL — with retry logic (up to 4 attempts, exponential backoff).
- Logs every delivery attempt to PostgreSQL.
- Caches authentication and quotes in Redis to minimize database load.

---

## Architecture

The system is built on the principle of separation of concerns: the HTTP API, three independent background workers, and the infrastructure layer run as separate processes within a single Docker network.

### C4 — Context Diagram

<div align="center">
<img width="707" height="866" alt="С4 Context" src="https://github.com/user-attachments/assets/b427446a-d6ac-4a96-b06f-dc3304c2a60c" />
</div>

### C4 — Container Diagram

<div align="center">
<img width="8191" height="5917" alt="с4 сontainer" src="https://github.com/user-attachments/assets/b91c9c3d-28c9-4200-9017-e6eb004a1ae1" />
</div>

### Component Descriptions

| Component | Role |
|---|---|
| **API (FastAPI)** | HTTP interface: registration, alert management, quote retrieval |
| **Parser Worker** | Polls Binance and CoinGecko every 10 seconds, stores prices in Redis |
| **Checker Worker** | Reads alerts from PostgreSQL and prices from Redis every 10 seconds, triggers fired alerts |
| **Sender Worker** | RabbitMQ consumer: delivers webhooks, logs results to PostgreSQL |
| **PostgreSQL** | Storage for users, alerts, and delivery logs |
| **Redis** | Quote cache (TTL 15s), authentication cache (TTL 1h), rate-limit counters |
| **RabbitMQ** | Persistent `webhooks_queue` between Checker and Sender |

---

## Technology Stack

| Category | Technology |
|---|---|
| **Language** | Python 3.13 |
| **Web Framework** | FastAPI |
| **ASGI Server** | Uvicorn |
| **ORM** | SQLAlchemy (async) |
| **Migrations** | Alembic |
| **Database** | PostgreSQL 16 |
| **Cache / Rate Limit** | Redis 7 (aioredis) |
| **Message Broker** | RabbitMQ 3 (aio-pika) |
| **HTTP Client** | httpx (async) |
| **Retry** | Tenacity |
| **Validation** | Pydantic v2 + pydantic-settings |
| **Package Manager** | uv |
| **Containerization** | Docker + Docker Compose |
| **Tests** | pytest + pytest-asyncio |

---

## Project Structure

```
crypto-data-aggregator-API/
├── app/
│   ├── core/
│   │   ├── config.py          # Environment settings (pydantic-settings)
│   │   └── rate_limit.py      # Fixed Window Rate Limiter (Redis)
│   ├── database/
│   │   ├── base.py            # SQLAlchemy Base + model registry
│   │   ├── session.py         # Async engine + get_db dependency
│   │   ├── redis.py           # Redis client + get_redis dependency
│   │   └── rabbitmq.py        # RabbitMQ client (aio-pika)
│   ├── modules/
│   │   ├── alerts/            # Alert CRUD (model, schema, repo, service, router)
│   │   ├── rates/             # Quote proxy from Redis
│   │   └── users/             # Registration, API key authentication
│   ├── workers/
│   │   ├── parser/            # Price aggregator (Binance + CoinGecko adapters)
│   │   ├── checker/           # Alert condition evaluation engine
│   │   └── sender/            # Webhook dispatcher (RabbitMQ consumer)
│   └── main.py                # FastAPI entrypoint, lifespan, error handlers
├── migrations/                # Alembic migrations
├── tests/                     # pytest tests
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── alembic.ini
```

---

## API Reference

All endpoints are available under the `/api/v1/` prefix.
Authentication is performed via the `X-API-Key` header.

### - Healthcheck

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | no | Service status |

**Response:**
```json
{
  "status": "ok",
  "version": "0.0.1"
}
```

---

### - Users

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/users/register` | no | 2 req / 10s (by IP) | Registration, returns API key |
| `GET` | `/api/v1/users/me` | yes | 5 req / 10s (by user) | Current user data |

1. **`POST /api/v1/users/register`**

Request:
```json
{
  "email": "user@example.com"
}
```

Response `201`:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "api_key": "sk_live_<token>"
}
```

> The API key is returned **only once**. _**Store it in a safe place.**_

Errors: `400 Bad Request` — email is already registered.

---

2. **`GET /api/v1/users/me`**

Response `200`:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

### - Rates

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/rates/` | yes | 5 req / 10s (by IP) | Current quotes from cache |

**`GET /api/v1/rates/`**

Response `200`:
```json
{
  "BTC": 65420.15,
  "ETH": 3100.50,
  "DOGE": 0.1423,
  "SOL": 142.80,
  "BNB": 580.00
}
```

Errors: `503 Service Unavailable` — the parser has not yet populated the cache (first launch).

---

### - Alerts

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/alerts/` | yes | 5 req / 10s | Create an alert |
| `GET` | `/api/v1/alerts/` | yes | 5 req / 10s | List of active alerts |
| `DELETE` | `/api/v1/alerts/{id}` | yes | 5 req / 10s | Delete an alert |

1. **`POST /api/v1/alerts/`**

Request:
```json
{
  "ticker": "BTC",
  "target_price": 70000.00,
  "condition": "gt",
  "webhook_url": "https://your-server.com/webhook"
}
```

| Field | Type | Description |
|---|---|---|
| `ticker` | string | One of: `BTC`, `ETH`, `DOGE`, `SOL`, `BNB` |
| `target_price` | float | Target price (`> 0`) |
| `condition` | enum | `gt` — price rose above, `lt` — price fell below |
| `webhook_url` | string | URL for the POST notification |

Response `201`:
```json
{
  "id": "uuid",
  "ticker": "BTC",
  "target_price": 70000.00,
  "condition": "gt",
  "webhook_url": "https://your-server.com/webhook",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

Errors: `409 Conflict` — an identical active alert already exists.

---

2. **`GET /api/v1/alerts/`**

Response `200`: an array of alert objects belonging to the current user.

---

**`DELETE /api/v1/alerts/{id}`**

Response `204 No Content`.

Errors: `404 Not Found` — alert not found or belongs to another user.

---

### Error Format

All errors follow a unified format:

```json
{
  "error": "HTTPException",
  "detail": "Error description",
  "code": 404
}
```

---

## User Flow

```
1. Registration
   POST /users/register  →  receive sk_live_... (save it!)

2. Check quotes
   GET /rates/  (X-API-Key: sk_live_...)  →  current prices

3. Create an alert
   POST /alerts/  →  alert created, is_active = true

4. Wait
   Checker Worker compares prices against alerts every 10 seconds.
   Once the condition is met:
     → alert is marked is_active = false
     → task is placed in RabbitMQ

5. Notification delivery
   Sender Worker picks up the task from the queue.
   POST <webhook_url> with payload:
   {
     "alert_id": "uuid",
     "ticker": "BTC",
     "triggered_price": 70100.00
   }
   On failure — up to 4 attempts with exponential backoff (10s → 600s).

6. View history
   GET /alerts/  →  alert is present with is_active = false
```

---

## Quick Start

### Prerequisites

- Docker >= 24
- Docker Compose >= 2.20

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/crypto-data-aggregator-API.git
cd crypto-data-aggregator-API
```

### 2. Create the environment file

```bash
cp .env.example .env
```

Fill in `.env` (see the [Environment Variables](#environment-variables) section).

### 3. Start all services

```bash
docker compose up --build -d
```

This command will bring up: `api`, `parser`, `checker`, `sender`, `postgres`, `redis`, `rabbitmq`.

### 4. Apply migrations

```bash
docker compose exec api alembic upgrade head
```

### 5. Check the status

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.0.1"}
```

Swagger UI is available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### Stopping

```bash
docker compose down
```

For a full cleanup (including volumes):

```bash
docker compose down -v
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
# PostgreSQL
DB_USER=postgres
DB_PASS=postgres
DB_HOST=postgres
DB_PORT=5432
DB_NAME=crypto_db

# Redis
REDIS_URL=redis://redis:6379

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

> For local development outside of Docker, replace the hostnames with `localhost`.

---

## Tests

Tests are run inside the Docker environment:

```bash
docker compose exec api pytest
```

Or locally (with an activated venv):

```bash
pytest
```

Coverage:

| Module | Tests |
|---|---|
| `test_users.py` | Registration, duplicate email, profile retrieval |
| `test_alerts.py` | Creation, duplication, deletion, 404 on another user's alert |
| `test_rate_limit.py` | HTTP 429 when the rate limit is exceeded |

---

## Project Goals

The project was created as a demonstration of backend system design and development skills, featuring an asynchronous architecture, a message broker, and a distributed cache.

**Achieved:**

- Multi-component event-driven architecture (API + 3 independent workers)
- Adapter pattern for data sources with the ability to scale the number of exchanges
- Two-level authentication cache (Redis + PostgreSQL)
- Guaranteed webhook delivery via a persistent RabbitMQ queue with retry (Tenacity, exponential backoff)
- Unique partial indexes in PostgreSQL for deduplication of active alerts
- Fixed Window Rate Limiter on Redis with no external dependencies
- Containerization of all services, multi-stage Dockerfile (builder / runtime), unprivileged user
- Alembic migrations with schema versioning
- Unified error response format via global exception handlers

**Not implemented / in progress:**

- Health check with real dependency pings (currently a stub)
- Retry logic in Parser Worker (currently silently swallows exchange errors)
- Protection against Cloudflare HTML stubs in adapters
- Delivery attempt counter in `DispatchLog` (currently hardcoded to `1`)
- `SSL verify=False` in Sender — acceptable for development only

---

## Planned Improvements

| Priority | Task | Description |
|---|---|---|
| High | Replace O(N) alert iteration | Use Redis Sorted Sets: store alerts as `ZADD ticker SCORE alert_id`, check condition via `ZRANGEBYSCORE` — O(log N) instead of O(N) |
| High | Tenacity in Parser Worker | Exponential backoff on 429 and network errors from exchanges |
| High | Real Health Check | Ping PostgreSQL, Redis, RabbitMQ and return an aggregated status |
| Medium | Metrics | Prometheus + Grafana: endpoint latency, queue size, delivery throughput |
| Medium | Dispatch attempt counter | Count actual retry attempts via Tenacity callback, write to `DispatchLog` |
| Medium | SSL verify in Sender | Enable in production, configurable via environment variable |
| Low | Ticker expansion | Move the list of supported tickers to configuration, remove hardcoding |
| Low | Token-bucket Rate Limiter | A fairer algorithm to replace Fixed Window |
| Low | WebSocket endpoint | Stream real-time quotes on top of the REST API |

---

## License

[MIT](./LICENSE)
