# Fase 01 — Setup inicial del proyecto

> Estado: Implementada
> Commit: ver `git log` (scaffolding base previo a `apps/branches`)

## 1. Objetivo y alcance

Esta fase deja lista la **base del proyecto** sobre la que se construirán todas las demás:

- Proyecto Django 5 + DRF 3.15 con settings split (`base`/`dev`/`prod`).
- API versionada en `/api/v1/`.
- Autenticación JWT (`djangorestframework-simplejwt`).
- Documentación OpenAPI/Swagger con `drf-spectacular` (`/api/docs/`, `/api/redoc/`, `/api/schema/`).
- PostgreSQL 16 como base de datos.
- Redis 7 listo para Celery (worker comentado en `docker-compose.yml`).
- `django-storages` + `boto3` configurados condicionalmente para AWS S3 (fallback a `FileSystemStorage` cuando no hay credenciales).
- Stack de testing: `pytest-django`, `factory-boy`, `faker`, `moto[s3]`.
- Linting/formatter con `ruff`.
- Docker Compose con servicios `db`, `redis`, `web`.

**Out of scope:**

- Apps de dominio (Branches, Equipment, Maintenance, etc.).
- Worker Celery activo (queda comentado, se habilita en fase 05).
- Pipeline CI/CD.
- Configuración real de S3 (solo el wiring; las credenciales son placeholders).

## 2. Stack y dependencias específicas

### 2.1 Python (`requirements/base.txt`)

```
Django==5.0.6
djangorestframework==3.15.1
django-environ==0.11.2
django-cors-headers==4.3.1
django-filter==24.2

djangorestframework-simplejwt==5.3.1
drf-spectacular==0.27.2

psycopg[binary]==3.1.19

django-storages==1.14.3
boto3==1.34.106

qrcode[pil]==7.4.2
Pillow==10.3.0

celery==5.4.0
redis==5.0.4

gunicorn==22.0.0
```

### 2.2 `requirements/dev.txt`

Hereda de `base.txt` y añade testing y tooling:

```
-r base.txt

pytest==8.2.1
pytest-django==4.8.0
pytest-cov==5.0.0
factory-boy==3.3.0
faker==25.2.0

moto[s3]==5.0.7

django-debug-toolbar==4.3.0
ruff==0.4.4
ipython==8.24.0
```

### 2.3 `requirements/prod.txt`

```
-r base.txt
sentry-sdk==2.2.1
```

### 2.4 Variables de entorno (`.env.example`)

| Variable                                | Default                                     | Propósito                                    |
| --------------------------------------- | ------------------------------------------- | -------------------------------------------- |
| `DJANGO_SETTINGS_MODULE`                | `config.settings.dev`                       | Selector de settings                         |
| `DJANGO_SECRET_KEY`                     | `change-me-in-production`                   | Clave secreta de Django                      |
| `DJANGO_DEBUG`                          | `True`                                      | Modo debug                                   |
| `DJANGO_ALLOWED_HOSTS`                  | `localhost,127.0.0.1,0.0.0.0`               | Hosts permitidos                             |
| `POSTGRES_DB`                           | `biometric_db`                              | Nombre de la BD                              |
| `POSTGRES_USER`                         | `biometric_user`                            | Usuario de la BD                             |
| `POSTGRES_PASSWORD`                     | `biometric_pass`                            | Password de la BD                            |
| `POSTGRES_HOST`                         | `db`                                        | Host de la BD (servicio docker)              |
| `POSTGRES_PORT`                         | `5432`                                      | Puerto de la BD                              |
| `REDIS_URL`                             | `redis://redis:6379/0`                      | URL de Redis                                 |
| `CELERY_BROKER_URL`                     | `redis://redis:6379/0`                      | Broker de Celery                             |
| `CELERY_RESULT_BACKEND`                 | `redis://redis:6379/1`                      | Backend de resultados                        |
| `CELERY_TASK_ALWAYS_EAGER`              | `False`                                     | Si `True`, Celery corre síncrono en dev      |
| `AWS_ACCESS_KEY_ID`                     | (vacío)                                     | Credencial S3                                |
| `AWS_SECRET_ACCESS_KEY`                 | (vacío)                                     | Credencial S3                                |
| `AWS_STORAGE_BUCKET_NAME`               | `biometric-api-bucket`                      | Bucket S3                                    |
| `AWS_S3_REGION_NAME`                    | `us-east-1`                                 | Región S3                                    |
| `AWS_S3_CUSTOM_DOMAIN`                  | (vacío)                                     | Dominio CDN custom                           |
| `AWS_QUERYSTRING_AUTH`                  | `True`                                      | Firmar URLs                                  |
| `FRONTEND_BASE_URL`                     | `http://localhost:3000`                     | URL para los QR (apunta al frontend)         |
| `EMAIL_BACKEND`                         | `django.core.mail.backends.console.EmailBackend` | Backend de email (consola en dev)            |
| `EMAIL_HOST`                            | `smtp.gmail.com`                            | SMTP host                                    |
| `EMAIL_PORT`                            | `587`                                       | SMTP port                                    |
| `EMAIL_USE_TLS`                         | `True`                                      | TLS para SMTP                                |
| `EMAIL_HOST_USER`                       | (vacío)                                     | Usuario SMTP                                 |
| `EMAIL_HOST_PASSWORD`                   | (vacío)                                     | Password SMTP                                |
| `DEFAULT_FROM_EMAIL`                    | `Biometric API <noreply@biometric.local>`   | Remitente por defecto                        |
| `CORS_ALLOWED_ORIGINS`                  | `http://localhost:3000,http://127.0.0.1:3000` | CORS                                         |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`     | `60`                                        | Vida del access token                        |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS`       | `7`                                         | Vida del refresh token                       |

## 3. Modelo de datos

No aplica en esta fase: solo se configura `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"` y la conexión a Postgres. No hay modelos propios todavía.

## 4. Capa API

### 4.1 Endpoints incluidos en el scaffolding

| Método | Path                          | Descripción                          | Permisos |
| ------ | ----------------------------- | ------------------------------------ | -------- |
| POST   | `/api/v1/auth/token/`         | Obtiene `access` + `refresh` JWT     | Pública  |
| POST   | `/api/v1/auth/token/refresh/` | Refresca el `access` token           | Pública  |
| POST   | `/api/v1/auth/token/verify/`  | Verifica un token                    | Pública  |
| GET    | `/api/schema/`                | Esquema OpenAPI (YAML)               | Pública  |
| GET    | `/api/docs/`                  | Swagger UI                           | Pública  |
| GET    | `/api/redoc/`                 | Redoc                                | Pública  |
| GET    | `/admin/`                     | Django admin                         | Staff    |

### 4.2 Configuración global de DRF (`config/settings/base.py`)

- Autenticación por defecto: `JWTAuthentication`.
- Permiso por defecto: `IsAuthenticated` (todas las rutas son privadas hasta declarar lo contrario).
- Filtros por defecto: `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter`.
- Paginación por defecto: `PageNumberPagination` con `PAGE_SIZE = 20`.
- Schema: `drf_spectacular.openapi.AutoSchema`.

## 5. Reglas de negocio (de plataforma)

- Todo el código va en **inglés** (nombres de clases, funciones, variables, fields).
- Solo el contenido visible al usuario va en **español** vía `gettext_lazy as _`: `verbose_name`, `help_text`, labels de `TextChoices`, mensajes de error de validación.
- Las URLs versionan bajo `/api/v1/` y cada app de dominio se monta en `api/v1/urls.py`.
- `LANGUAGE_CODE = "es-co"`, `TIME_ZONE = "America/Bogota"`.
- `STORAGES` se decide en runtime: si hay credenciales S3 → `S3Storage`, si no → `FileSystemStorage`. Esto hace que dev sin AWS funcione sin tocar settings.
- En `dev.py`, `CORS_ALLOW_ALL_ORIGINS = True` para no bloquear pruebas.
- En `prod.py`, hardening: `SECURE_SSL_REDIRECT`, HSTS 30d, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `X_FRAME_OPTIONS = "DENY"`.

## 6. Snippets clave de implementación

### 6.1 `Dockerfile` (`docker/Dockerfile`)

```dockerfile
# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps for psycopg, Pillow, qrcode
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev libjpeg-dev zlib1g-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements/ /app/requirements/
ARG REQUIREMENTS=dev
RUN pip install --upgrade pip && pip install -r requirements/${REQUIREMENTS}.txt

COPY . /app/

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### 6.2 `entrypoint.sh` (`docker/entrypoint.sh`)

```bash
#!/usr/bin/env bash
set -e

# Wait for Postgres
if [ -n "$POSTGRES_HOST" ]; then
    echo "Esperando a PostgreSQL en ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."
    until python -c "import socket,sys; s=socket.socket(); \
        s.settimeout(2); \
        sys.exit(0) if s.connect_ex(('${POSTGRES_HOST}', int('${POSTGRES_PORT:-5432}'))) == 0 else sys.exit(1)" 2>/dev/null; do
        sleep 1
    done
    echo "PostgreSQL listo."
fi

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    python manage.py migrate --noinput
fi

if [ "${COLLECT_STATIC:-false}" = "true" ]; then
    python manage.py collectstatic --noinput || true
fi

exec "$@"
```

### 6.3 `docker-compose.yml`

```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: biometric_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-biometric_db}
      POSTGRES_USER: ${POSTGRES_USER:-biometric_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-biometric_pass}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-biometric_user} -d ${POSTGRES_DB:-biometric_db}"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: biometric_redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

  web:
    build:
      context: .
      dockerfile: docker/Dockerfile
      args:
        REQUIREMENTS: dev
    container_name: biometric_web
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      db: {condition: service_healthy}
      redis: {condition: service_healthy}
    command: python manage.py runserver 0.0.0.0:8000

  # celery_worker (descomentar en fase 05 con maintenance scheduling):
  # celery_worker:
  #   build: { context: ., dockerfile: docker/Dockerfile, args: { REQUIREMENTS: dev } }
  #   env_file: [.env]
  #   volumes: [".:/app"]
  #   depends_on: { db: {condition: service_healthy}, redis: {condition: service_healthy} }
  #   command: celery -A config worker -l info

volumes:
  postgres_data:
```

### 6.4 `config/settings/base.py` — bloques clave

```python
from datetime import timedelta
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, []),
    CELERY_TASK_ALWAYS_EAGER=(bool, False),
    EMAIL_USE_TLS=(bool, True),
    AWS_QUERYSTRING_AUTH=(bool, True),
)
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

INSTALLED_APPS = (
    [  # Django
        "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
        "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    ]
    + [  # Third-party
        "rest_framework", "rest_framework_simplejwt", "django_filters",
        "corsheaders", "drf_spectacular", "storages",
    ]
    + [  # Local (se va llenando incrementalmente)
        "apps.branches",
    ]
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7)),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Storage condicional: S3 si hay credenciales, FileSystem en otro caso
if AWS_ACCESS_KEY_ID and AWS_STORAGE_BUCKET_NAME:
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", default="http://localhost:3000")
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True
```

### 6.5 `config/settings/dev.py`

```python
from .base import *  # noqa
from .base import INSTALLED_APPS, MIDDLEWARE

DEBUG = True

try:
    import debug_toolbar  # noqa
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
    INTERNAL_IPS = ["127.0.0.1", "localhost"]
except ImportError:
    pass

CORS_ALLOW_ALL_ORIGINS = True
```

### 6.6 `config/settings/prod.py`

```python
from .base import *  # noqa

DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
```

### 6.7 `config/urls.py`

```python
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.v1.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
```

### 6.8 `api/v1/urls.py` (estado inicial, se va creciendo)

```python
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView, TokenVerifyView,
)

app_name = "v1"

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    # Las rutas por dominio se incluyen aquí a medida que se crean.
]
```

### 6.9 `pytest.ini`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.dev
python_files = tests.py test_*.py *_tests.py
addopts = -ra --strict-markers
testpaths = apps
```

### 6.10 `pyproject.toml` (ruff)

```toml
[tool.ruff]
line-length = 100
target-version = "py312"
extend-exclude = ["migrations", "staticfiles"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP", "DJ"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["apps", "config", "api"]
```

## 7. Tests

En esta fase no hay tests propios: solo se valida que la infraestructura levante. Las apps de dominio sí tendrán tests.

**Smoke test manual:**

```bash
docker compose up --build
# En otra terminal:
curl -i http://localhost:8000/api/docs/        # Swagger UI
curl -i http://localhost:8000/api/schema/      # OpenAPI YAML
curl -i http://localhost:8000/api/v1/auth/token/   # Debe responder 405 (sin POST)
```

## 8. Pruebas manuales con Postman

### 8.1 Variables de entorno Postman

| Nombre         | Valor inicial               | Descripción                              |
| -------------- | --------------------------- | ---------------------------------------- |
| `base_url`     | `http://localhost:8000`     | Host base                                |
| `username`     | `admin`                     | Usuario para obtener JWT                 |
| `password`     | `adminpass`                 | Password                                 |
| `access_token` | (vacío, se llena con login) | Bearer token                             |
| `refresh_token`| (vacío, se llena con login) | Refresh token                            |

### 8.2 Setup — crear superusuario y obtener JWT

```bash
docker compose exec web python manage.py createsuperuser
# username: admin / password: adminpass
```

Request Postman:

```http
POST {{base_url}}/api/v1/auth/token/
Content-Type: application/json

{"username": "{{username}}", "password": "{{password}}"}
```

Response (200):

```json
{
  "refresh": "eyJhbGciOi...",
  "access": "eyJhbGciOi..."
}
```

Test script (Postman → Tests):

```js
const body = pm.response.json();
pm.test("status is 200", () => pm.response.to.have.status(200));
pm.environment.set("access_token", body.access);
pm.environment.set("refresh_token", body.refresh);
```

### 8.3 Refresh token

```http
POST {{base_url}}/api/v1/auth/token/refresh/
Content-Type: application/json

{"refresh": "{{refresh_token}}"}
```

Response (200):

```json
{"access": "eyJhbGciOi..."}
```

### 8.4 Verify token

```http
POST {{base_url}}/api/v1/auth/token/verify/
Content-Type: application/json

{"token": "{{access_token}}"}
```

Response (200): `{}` (vacío). Si inválido: 401 con `{"detail": "Token is invalid or expired", "code": "token_not_valid"}`.

### 8.5 Casos especiales

- **Login con credenciales inválidas → 401:**
  ```json
  {"detail": "No active account found with the given credentials"}
  ```

- **Verificación visual del Swagger:** abrir `http://localhost:8000/api/docs/` en el navegador. Debe listar al menos los endpoints de `auth/`.

## 9. Checklist de verificación

- [ ] `docker compose up --build` levanta `db`, `redis`, `web` sin errores.
- [ ] `migrate` se ejecuta automáticamente (se ven las migraciones de Django builtin: `auth`, `admin`, `contenttypes`, etc.).
- [ ] `http://localhost:8000/api/docs/` responde 200 con Swagger.
- [ ] `http://localhost:8000/admin/` responde 200.
- [ ] `POST /api/v1/auth/token/` con superuser válido devuelve `access` y `refresh`.
- [ ] `pytest` corre (sin tests todavía pero sin errores de configuración).
- [ ] `ruff check .` no falla.

## 10. Posibles extensiones futuras / TODO

- Habilitar el worker Celery en `docker-compose.yml` (actualmente comentado).
- Añadir un servicio `mailpit` o `mailhog` para inspeccionar emails en dev en lugar del `console` backend.
- Configurar `pytest-cov` con un threshold mínimo (`--cov-fail-under=85`).
- GitHub Actions para CI: lint + tests en PRs.
- `docker-compose.override.yml.example` con bind-mount opcional para hot reload.
- Healthcheck del servicio `web` (curl al `/api/schema/`).
- Configurar `LOGGING` con formato JSON para producción.
- Definir un módulo `apps.core` con base abstracta `TimeStampedModel` para no repetir `created_at`/`updated_at`.
