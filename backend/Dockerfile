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

# Bust cache so CMD is from current Dockerfile (remove after deploy works)
ARG CACHEBUST=
RUN echo "Build ${CACHEBUST:-no-arg}"

# Run API. Listen on $PORT so Railway marks the container as started.
# If you set Custom Start Command in Railway, it overrides this — clear it to use the Dockerfile.
CMD ["sh", "-c", "echo \"[ClawHost] Starting port=${PORT:-8000}\" && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
