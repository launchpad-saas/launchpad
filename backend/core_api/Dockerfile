FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY packages/launchpad_shared /app/packages/launchpad_shared
COPY backend/core_api /app/backend/core_api
WORKDIR /app
RUN pip install --no-cache-dir -e packages/launchpad_shared
WORKDIR /app/backend/core_api
RUN pip install --no-cache-dir -e .

FROM base AS development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]