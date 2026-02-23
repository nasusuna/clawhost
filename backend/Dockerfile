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

# Run API: migrations then server. Use uvicorn for fast startup (Railway); bind to $PORT.
RUN pip install --no-cache-dir gunicorn
CMD ["sh", "-c", "set -e; alembic upgrade head; exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
