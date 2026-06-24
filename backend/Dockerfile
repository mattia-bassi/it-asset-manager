FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# deps
COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir . && \
    (pip freeze | grep -qi bcrypt && (echo "ERROR: bcrypt found in installed packages!" && exit 1) || echo "OK: bcrypt not found")

# app
COPY . /app

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
