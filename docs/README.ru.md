# Crypto Data Aggregator API

> Асинхронный backend-сервис для агрегации криптовалютных котировок и доставки webhook-уведомлений по пользовательским ценовым алертам.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.13-FF6600?style=flat-square&logo=rabbitmq&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)

---
*Also available in English: [README](../README.md)*
## Содержание

- [Обзор](#обзор)
- [Архитектура](#архитектура)
- [Стек технологий](#стек-технологий)
- [Структура проекта](#структура-проекта)
- [API Reference](#api-reference)
- [User Flow](#user-flow)
- [Быстрый старт](#быстрый-старт)
- [Переменные окружения](#переменные-окружения)
- [Тесты](#тесты)
- [Цели проекта](#цели-проекта)
- [Планы на улучшения](#планы-на-улучшения)

---

## Обзор

Сервис решает задачу мониторинга криптовалютных котировок в реальном времени и асинхронной доставки уведомлений.

**Что умеет система:**

- Агрегирует цены по 5 тикерам (`BTC`, `ETH`, `DOGE`, `SOL`, `BNB`) с двух источников - **Binance** и **CoinGecko** - параллельно, через адаптерный слой.
- Предоставляет REST API с аутентификацией по API-ключу для управления ценовыми алертами.
- При срабатывании алерта помещает задачу в очередь RabbitMQ и гарантированно доставляет HTTP webhook на URL пользователя - с retry-логикой (до 4 попыток, exponential backoff).
- Логирует каждую попытку доставки в PostgreSQL.
- Кэширует аутентификацию и котировки в Redis для минимизации нагрузки на БД.

---

## Архитектура

Система построена по принципу разделения ответственности: HTTP API, три независимых фоновых воркера и инфраструктурный слой работают как отдельные процессы внутри одной Docker-сети.

### C4 - Контекстная диаграмма

<div align="center">
<img width="707" height="866" alt="С4 Context" src="https://github.com/user-attachments/assets/b427446a-d6ac-4a96-b06f-dc3304c2a60c" />
</div>

### C4 - Диаграмма контейнеров

<div align="center">
<img width="8191" height="5917" alt="с4 сontainer" src="https://github.com/user-attachments/assets/b91c9c3d-28c9-4200-9017-e6eb004a1ae1" />
</div>

### Описание компонентов

| Компонент | Роль |
|---|---|
| **API (FastAPI)** | HTTP-интерфейс: регистрация, управление алертами, получение котировок |
| **Parser Worker** | Каждые 10 сек опрашивает Binance и CoinGecko, кладёт цены в Redis |
| **Checker Worker** | Каждые 10 сек читает алерты из PostgreSQL и цены из Redis, триггерит сработавшие |
| **Sender Worker** | Консюмер RabbitMQ: доставляет webhook, логирует результат в PostgreSQL |
| **PostgreSQL** | Хранение пользователей, алертов, логов доставки |
| **Redis** | Кэш котировок (TTL 15s), кэш аутентификации (TTL 1h), rate-limit счётчики |
| **RabbitMQ** | Persistent очередь `webhooks_queue` между Checker и Sender |

---

## Стек технологий

| Категория | Технология |
|---|---|
| **Язык** | Python 3.13 |
| **Web Framework** | FastAPI |
| **ASGI Server** | Uvicorn |
| **ORM** | SQLAlchemy (async) |
| **Миграции** | Alembic |
| **База данных** | PostgreSQL 16 |
| **Кэш / Rate Limit** | Redis 7 (aioredis) |
| **Message Broker** | RabbitMQ 3 (aio-pika) |
| **HTTP Client** | httpx (async) |
| **Retry** | Tenacity |
| **Валидация** | Pydantic v2 + pydantic-settings |
| **Пакетный менеджер** | uv |
| **Контейнеризация** | Docker + Docker Compose |
| **Тесты** | pytest + pytest-asyncio |

---

## Структура проекта

```
crypto-data-aggregator-API/
├── app/
│   ├── core/
│   │   ├── config.py          # Настройки окружения (pydantic-settings)
│   │   └── rate_limit.py      # Fixed Window Rate Limiter (Redis)
│   ├── database/
│   │   ├── base.py            # SQLAlchemy Base + реестр моделей
│   │   ├── session.py         # Async engine + get_db dependency
│   │   ├── redis.py           # Redis client + get_redis dependency
│   │   └── rabbitmq.py        # RabbitMQ client (aio-pika)
│   ├── modules/
│   │   ├── alerts/            # CRUD алертов (model, schema, repo, service, router)
│   │   ├── rates/             # Прокси котировок из Redis
│   │   └── users/             # Регистрация, аутентификация по API-ключу
│   ├── workers/
│   │   ├── parser/            # Агрегатор цен (Binance + CoinGecko адаптеры)
│   │   ├── checker/           # Движок проверки условий алертов
│   │   └── sender/            # Webhook dispatcher (RabbitMQ consumer)
│   └── main.py                # FastAPI entrypoint, lifespan, error handlers
├── migrations/                # Alembic миграции
├── tests/                     # pytest тесты
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── alembic.ini
```

---

## API Reference

Все эндпоинты доступны по префиксу `/api/v1/`.
Аутентификация - заголовок `X-API-Key`.

### - Healthcheck

| Метод | Путь | Auth | Описание |
|---|---|---|---|
| `GET` | `/health` | нет | Статус сервиса |

**Ответ:**
```json
{
  "status": "ok",
  "version": "0.0.1"
}
```

---

### - Users

| Метод | Путь | Auth | Rate Limit | Описание |
|---|---|---|---|---|
| `POST` | `/api/v1/users/register` | нет | 2 req / 10s (по IP) | Регистрация, возвращает API-ключ |
| `GET` | `/api/v1/users/me` | да | 5 req / 10s (по user) | Данные текущего пользователя |

1. **`POST /api/v1/users/register`**

Запрос:
```json
{
  "email": "user@example.com"
}
```

Ответ `201`:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "api_key": "sk_live_<token>"
}
```

> API-ключ возвращается **единожды**. _**Храните его в надёжном месте.**_

Ошибки: `400 Bad Request` - email уже зарегистрирован.

---

2. **`GET /api/v1/users/me`**

Ответ `200`:
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

| Метод | Путь | Auth | Rate Limit | Описание |
|---|---|---|---|---|
| `GET` | `/api/v1/rates/` | да | 5 req / 10s (по IP) | Текущие котировки из кэша |

**`GET /api/v1/rates/`**

Ответ `200`:
```json
{
  "BTC": 65420.15,
  "ETH": 3100.50,
  "DOGE": 0.1423,
  "SOL": 142.80,
  "BNB": 580.00
}
```

Ошибки: `503 Service Unavailable` - парсер ещё не заполнил кэш (первый запуск).

---

### - Alerts

| Метод | Путь | Auth | Rate Limit | Описание |
|---|---|---|---|---|
| `POST` | `/api/v1/alerts/` | да | 5 req / 10s | Создать алерт |
| `GET` | `/api/v1/alerts/` | да | 5 req / 10s | Список активных алертов |
| `DELETE` | `/api/v1/alerts/{id}` | да | 5 req / 10s | Удалить алерт |

1. **`POST /api/v1/alerts/`**

Запрос:
```json
{
  "ticker": "BTC",
  "target_price": 70000.00,
  "condition": "gt",
  "webhook_url": "https://your-server.com/webhook"
}
```

| Поле | Тип | Описание |
|---|---|---|
| `ticker` | string | Один из: `BTC`, `ETH`, `DOGE`, `SOL`, `BNB` |
| `target_price` | float | Целевая цена (`> 0`) |
| `condition` | enum | `gt` - цена выросла выше, `lt` - упала ниже |
| `webhook_url` | string | URL для POST-уведомления |

Ответ `201`:
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

Ошибки: `409 Conflict` - идентичный активный алерт уже существует.

---

2. **`GET /api/v1/alerts/`**

Ответ `200`: массив объектов алертов текущего пользователя.

---

**`DELETE /api/v1/alerts/{id}`**

Ответ `204 No Content`.

Ошибки: `404 Not Found` - алерт не найден или принадлежит другому пользователю.

---

### Формат ошибок

Все ошибки приведены к единому формату:

```json
{
  "error": "HTTPException",
  "detail": "Описание ошибки",
  "code": 404
}
```

---

## User Flow

```
1. Регистрация
   POST /users/register  →  получаете sk_live_... (сохраните!)

2. Проверка котировок
   GET /rates/  (X-API-Key: sk_live_...)  →  текущие цены

3. Создание алерта
   POST /alerts/  →  алерт создан, is_active = true

4. Ожидание
   Checker Worker каждые 10 сек сверяет цены с алертами.
   Как только условие выполнено:
     → алерт помечается is_active = false
     → задача попадает в RabbitMQ

5. Доставка уведомления
   Sender Worker берёт задачу из очереди.
   POST <webhook_url> с payload:
   {
     "alert_id": "uuid",
     "ticker": "BTC",
     "triggered_price": 70100.00
   }
   При неудаче - до 4 попыток с экспоненциальным откатом (10s → 600s).

6. Просмотр истории
   GET /alerts/  →  алерт присутствует с is_active = false
```

---

## Быстрый старт

### Предварительные требования

- Docker >= 24
- Docker Compose >= 2.20

### 1. Клонировать репозиторий

```bash
git clone https://github.com/<your-username>/crypto-data-aggregator-API.git
cd crypto-data-aggregator-API
```

### 2. Создать файл окружения

```bash
cp .env.example .env
```

Заполните `.env` (см. раздел [Переменные окружения](#переменные-окружения)).

### 3. Запустить все сервисы

```bash
docker compose up --build -d
```

Команда поднимет: `api`, `parser`, `checker`, `sender`, `postgres`, `redis`, `rabbitmq`.

### 4. Применить миграции

```bash
docker compose exec api alembic upgrade head
```

### 5. Проверить статус

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.0.1"}
```

Swagger UI доступен по адресу: [http://localhost:8000/docs](http://localhost:8000/docs)

### Остановка

```bash
docker compose down
```

Для полной очистки (включая volumes):

```bash
docker compose down -v
```

---

## Переменные окружения

Создайте файл `.env` в корне проекта:

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

> Для локального запуска вне Docker замените хосты на `localhost`.

---

## Тесты

Тесты запускаются внутри Docker-окружения:

```bash
docker compose exec api pytest
```

Или локально (при активированном venv):

```bash
pytest
```

Покрытие:

| Модуль | Тесты |
|---|---|
| `test_users.py` | Регистрация, дублирование email, получение профиля |
| `test_alerts.py` | Создание, дублирование, удаление, 404 на чужой алерт |
| `test_rate_limit.py` | HTTP 429 при превышении лимита |

---

## Цели проекта

Проект создан как демонстрация навыков проектирования и разработки backend-систем с асинхронной архитектурой, брокером сообщений и распределённым кэшем.

**Достигнуто:**

- Многокомпонентная event-driven архитектура (API + 3 независимых воркера)
- Адаптерный паттерн для источников данных с возможностью масштабирования числа бирж
- Двухуровневый кэш аутентификации (Redis + PostgreSQL)
- Гарантированная доставка webhook через persistent RabbitMQ очередь с retry (Tenacity, exponential backoff)
- Уникальные partial-индексы PostgreSQL для дедупликации активных алертов
- Fixed Window Rate Limiter на Redis без внешних зависимостей
- Контейнеризация всех сервисов, multi-stage Dockerfile (builder / runtime), непривилегированный пользователь
- Alembic-миграции с версионированием схемы
- Единый формат ответов об ошибках через глобальные exception handlers

**Не реализовано / в процессе:**

- Health check с реальными пингами зависимостей (сейчас заглушка)
- Retry-логика в Parser Worker (сейчас тихое поглощение ошибок от бирж)
- Защита от Cloudflare HTML-заглушек в адаптерах
- Счётчик попыток доставки в `DispatchLog` (сейчас хардкод `1`)
- `SSL verify=False` в Sender - допустимо только для разработки

---

## Планы на улучшения

| Приоритет | Задача | Описание |
|---|---|---|
| Высокий | Заменить O(N) перебор алертов | Использовать Redis Sorted Sets: хранить алерты как `ZADD ticker SCORE alert_id`, проверять условие через `ZRANGEBYSCORE` - O(log N) вместо O(N) |
| Высокий | Tenacity в Parser Worker | Экспоненциальный backoff при 429 и сетевых ошибках от бирж |
| Высокий | Реальный Health Check | Пинговать PostgreSQL, Redis, RabbitMQ и возвращать агрегированный статус |
| Средний | Метрики | Prometheus + Grafana: latency эндпоинтов, размер очереди, скорость доставки |
| Средний | Dispatch attempt counter | Считать реальное число попыток через Tenacity callback, писать в `DispatchLog` |
| Средний | SSL verify в Sender | Включить в production, настраивать через переменную окружения |
| Низкий | Расширение тикеров | Вынести список поддерживаемых тикеров в конфигурацию без хардкода |
| Низкий | Токен-bucket Rate Limiter | Более справедливый алгоритм вместо Fixed Window |
| Низкий | WebSocket endpoint | Стримить котировки в реальном времени поверх REST API |

---

## Лицензия

[MIT](./LICENSE)
