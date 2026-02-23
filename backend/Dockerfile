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
CMD ["sh", "-c", "alembic upgrade head && gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:${PORT:-8000}"]
