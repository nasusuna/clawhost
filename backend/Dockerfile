# ClawHost backend — production image
FROM python:3.12-slim

# Unbuffered output so logs show up immediately in Railway
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application
COPY alembic ./alembic
COPY alembic.ini .
COPY app ./app

# Run API. Listen on $PORT immediately so Railway marks the container as started.
# Run migrations once via Railway CLI or one-off: railway run alembic upgrade head
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
