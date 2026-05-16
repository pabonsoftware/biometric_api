# Biometric API

API REST para la administración de equipos biomédicos de una clínica: sedes, equipos, mantenimientos (programados e historial), fallas y generación de códigos QR.

## Stack

- **Python 3.12** + **Django 5.0** + **Django REST Framework 3.15**
- **PostgreSQL 16** como base de datos
- **Redis 7** + **Celery 5** para tareas async (envío de emails)
- **AWS S3** (vía `django-storages`) para almacenar PDFs y QRs
- **JWT** (`djangorestframework-simplejwt`) para autenticación
- **drf-spectacular** para documentación OpenAPI / Swagger
- **Docker** + **docker-compose** para desarrollo

## Estructura del proyecto

```
biometric_api/
├── config/             # Proyecto Django (settings split: base/dev/prod)
├── apps/               # Apps de dominio (sites, equipment, maintenance, failures, core)
├── api/v1/             # Aglutinador de URLs de la v1
├── docker/             # Dockerfile + entrypoint
├── requirements/       # Requirements separados por entorno
└── docs/               # Documentación y postman_collection.json
```

## Levantar el proyecto con Docker

### 1. Clonar y preparar variables de entorno

```bash
git clone <repo-url> biometric_api
cd biometric_api
cp .env.example .env
```

Edita `.env` y completa al menos:
- `DJANGO_SECRET_KEY` (cualquier cadena aleatoria larga para desarrollo)
- Las credenciales de S3 si vas a probar la subida de archivos (opcional en dev)

### 2. Construir y levantar los contenedores

```bash
docker-compose up --build
```

Esto levanta:
- `biometric_db` — PostgreSQL en `localhost:5432`
- `biometric_redis` — Redis en `localhost:6379`
- `biometric_web` — Django dev server en `localhost:8000`

El `entrypoint.sh` espera a que Postgres esté listo y corre `migrate` automáticamente.

### 3. Verificar que está corriendo

- API root: http://localhost:8000/api/v1/
- Swagger UI: http://localhost:8000/api/docs/
- Redoc: http://localhost:8000/api/redoc/
- Admin: http://localhost:8000/admin/

### 4. Crear superusuario (opcional)

```bash
docker-compose exec web python manage.py createsuperuser
```

### 5. Detener

```bash
docker-compose down            # Detiene los contenedores
docker-compose down -v         # Adicionalmente borra el volumen de datos de Postgres
```

## Comandos útiles

```bash
# Migraciones
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Shell de Django
docker-compose exec web python manage.py shell

# Tests
docker-compose exec web pytest

# Linter
docker-compose exec web ruff check .
docker-compose exec web ruff format .
```

## Autenticación

La API usa JWT. Para obtener un token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "adminpass"}'
```

Y para usar el token en endpoints protegidos:

```bash
curl http://localhost:8000/api/v1/sites/ \
  -H "Authorization: Bearer <access_token>"
```

## Variables de entorno

Ver [`.env.example`](./.env.example) para la lista completa con descripciones.

## Estado actual

Este repositorio está en construcción incremental. El scaffolding base está listo y los siguientes módulos se irán añadiendo en commits separados:

- [x] Setup inicial (Docker, Django, DRF, settings split, JWT, Swagger)
- [ ] Sedes (CRUD)
- [ ] Equipos biomédicos (CRUD + QR)
- [ ] Historial de mantenimientos (CRUD + PDF en S3)
- [ ] Programación de mantenimientos (CRUD + email async)
- [ ] Historial de fallas (CRUD)
- [ ] Colección Postman
- [ ] Suite completa de tests
