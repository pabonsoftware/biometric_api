# =========================================================
# Dockerfile multi-stage: sirve dev y producción.
#   - dev  : runserver (Daphne-backed vía channels), requirements/dev.txt
#   - prod : daphne (ASGI), requirements/prod.txt, usuario sin privilegios
# Build prod:  docker build -f docker/Dockerfile --target prod .
# =========================================================

# ---------- base: Python + variables comunes ----------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ---------- builder: compila las wheels con toolchain ----------
FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ /app/requirements/
ARG REQUIREMENTS=dev
RUN pip install --upgrade pip \
    && pip wheel --wheel-dir /wheels -r requirements/${REQUIREMENTS}.txt

# ---------- runtime: instala wheels sin toolchain de compilación ----------
FROM base AS runtime

# Solo librerías de runtime (psycopg, Pillow, qrcode) — sin build-essential.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
        zlib1g \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
COPY --from=builder /app/requirements /app/requirements
ARG REQUIREMENTS=dev
RUN pip install --no-index --find-links=/wheels -r requirements/${REQUIREMENTS}.txt \
    && rm -rf /wheels

COPY docker/entrypoint.sh /entrypoint.sh
# chmod 755 (no "+x"): el archivo del host es 0400, así que "+x" daría 0500
# (solo root). La imagen prod corre como usuario "django" y necesita leerlo.
RUN chmod 755 /entrypoint.sh

COPY . /app/

# ---------- prod: daphne como usuario sin privilegios ----------
# Daphne reemplaza a gunicorn-WSGI porque la app habla ASGI (HTTP + WebSocket).
# Mantener gunicorn dejaría /ws/notifications/ caído en producción.
FROM runtime AS prod

# Usuario no-root y directorios escribibles para static/media.
RUN groupadd --system django \
    && useradd --system --gid django --home /app django \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R django:django /app

USER django

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", \
     "--access-log", "-", \
     "config.asgi:application"]

# ---------- dev: runserver (stage por defecto del build) ----------
FROM runtime AS dev

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

