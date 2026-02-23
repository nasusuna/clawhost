# ClawHost backend — production image
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application
COPY alembic ./alembic
COPY alembic.ini .
COPY app ./app

# Run API: migrations then gunicorn. Bind to $PORT (Railway) or 8000.
RUN pip install --no-cache-dir gunicorn
# Echo steps so Railway captures logs; exec so gunicorn gets signals.
CMD ["sh", "-c", "set -e; echo '[ClawHost] Running migrations...'; alembic upgrade head; echo '[ClawHost] Starting gunicorn on port ${PORT:-8000}'; exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:${PORT:-8000}"]
