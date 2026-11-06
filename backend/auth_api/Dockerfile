FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY packages/launchpad_shared /app/packages/launchpad_shared
COPY backend/auth_api /app/backend/auth_api
WORKDIR /app
RUN pip install --no-cache-dir -e packages/launchpad_shared
WORKDIR /app/backend/auth_api
RUN pip install --no-cache-dir -e .

FROM base AS development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

FROM base AS production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]