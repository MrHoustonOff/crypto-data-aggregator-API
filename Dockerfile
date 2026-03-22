FROM python:3.12-slim AS builder

RUN pip install uv

WORKDIR /build
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

FROM python:3.12-slim

RUN useradd --no-create-home appuser

WORKDIR /app

COPY --from=builder /build/.venv /app/.venv

COPY app/ /app/app/

RUN chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]