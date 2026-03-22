FROM python:3.13-slim AS builder

WORKDIR /app

# Устанавливаем uv
RUN pip install --no-cache-dir uv

# Копируем только файлы зависимостей
COPY pyproject.toml uv.lock ./

# Создаём venv и ставим зависимости
RUN uv sync --frozen --no-dev

# Проверка что всё встало
RUN /app/.venv/bin/python -c "import httpx; print('httpx OK')" && \
    ls /app/.venv/bin/uvicorn

# Stage 2: runtime
FROM python:3.13-slim AS runtime

RUN useradd --no-create-home appuser

WORKDIR /app

# Копируем venv из builder
COPY --from=builder /app/.venv /app/.venv

# Копируем код приложения
COPY app/ /app/app/
COPY alembic.ini /app/
COPY migrations/ /app/migrations/
COPY tests/ /app/tests/
COPY pytest.ini /app/

# Права
RUN chown -R appuser:appuser /app
USER appuser

# venv в PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]