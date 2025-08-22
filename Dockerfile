# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 1) Dependencias Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 2) Copia del proyecto
COPY . .

EXPOSE 8000

# Ajusta main:app si tu objeto ASGI tiene otro nombre
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
