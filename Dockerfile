# CPU-only runtime for the FastAPI + FAISS application.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEVICE=cpu

WORKDIR /app

# libgomp is required by FAISS and common PyTorch CPU builds.
RUN apt-get update \
    && apt-get install --no-install-recommends -y libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . ./

# The Compose bind mounts persist these paths outside the container.
RUN addgroup --system appuser \
    && adduser --system --ingroup appuser appuser \
    && mkdir -p /app/data/vector_db /app/data/users /app/logs \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
