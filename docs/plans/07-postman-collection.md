# Fase 07 — Colección Postman

> Estado: Pendiente
> Commit: pendiente

## 1. Objetivo y alcance

Producir una **colección Postman exportable** (formato Collection v2.1) con todos los endpoints de las fases 01–06, organizada por carpetas, con variables de entorno reusables, **pre-request scripts** para refrescar el JWT automáticamente, y **tests post-respuesta** que persisten IDs (`branch_id`, `equipment_id`, etc.) en variables de entorno para encadenar requests.

Incluye también el `environment.json` correspondiente y la documentación para correrlo con **Newman** desde CLI / CI.

**Out of scope:**

- Documentación interactiva tipo Postman API Network publishing.
- Mocks de Postman (la API real cubre los casos).
- Pruebas de carga (Newman puede correr `--iteration-count` pero no es el objetivo aquí).
- Sincronización con OpenAPI auto-generado por `drf-spectacular` (decisión: la colección es a mano para tener control exacto sobre tests/scripts).

## 2. Stack y dependencias específicas

**Cliente / dev:**

- [Postman](https://www.postman.com/downloads/) (UI) o [Newman](https://github.com/postmanlabs/newman) (CLI).
- Newman se instala vía npm:
  ```bash
  npm install -g newman
  ```

**Archivos a producir:**

- `docs/postman/biometric_api.postman_collection.json` — la colección.
- `docs/postman/biometric_api.postman_environment.json` — el environment.
- `docs/postman/README.md` (opcional) — instrucciones rápidas.

No introduce dependencias Python.

## 3. Modelo de datos

No aplica: esta fase no toca la base de datos.

## 4. Estructura de la colección

### 4.1 Carpetas (folders)

```
Biometric API
├── 00 Auth
│   ├── Obtain token
│   ├── Refresh token
│   └── Verify token
├── 01 Branches
│   ├── List
│   ├── Create
│   ├── Retrieve
│   ├── Update (PUT)
│   ├── Patch
│   └── Delete
├── 02 Equipment
│   ├── List
│   ├── Create
│   ├── Retrieve
│   ├── By asset tag
│   ├── Regenerate QR
│   ├── History (action)
│   ├── Update (PUT)
│   ├── Patch
│   └── Delete
├── 03 Maintenance History
│   ├── List
│   ├── Create (JSON)
│   ├── Create with PDF (form-data)
│   ├── Retrieve
│   ├── Patch (replace PDF)
│   └── Delete
├── 04 Maintenance Scheduling
│   ├── List
│   ├── Create
│   ├── Retrieve
│   ├── Complete (action)
│   ├── Notify (action)
│   ├── Patch
│   └── Delete
└── 05 Failures
    ├── List
    ├── Create
    ├── Retrieve
    ├── Resolve (action)
    ├── Patch
    └── Delete
```

### 4.2 Variables del Environment

| Variable                      | Valor inicial                  | Tipo      | Descripción                                                    |
| ----------------------------- | ------------------------------ | --------- | -------------------------------------------------------------- |
| `base_url`                    | `http://localhost:8000`        | default   | Host de la API                                                 |
| `username`                    | `admin`                        | default   | Usuario para login                                             |
| `password`                    | `adminpass`                    | secret    | Password                                                       |
| `access_token`                | (vacío)                        | secret    | JWT access (lo llenan los scripts)                             |
| `refresh_token`               | (vacío)                        | secret    | JWT refresh (lo llenan los scripts)                            |
| `access_token_expires_at`     | (vacío)                        | default   | Timestamp ms cuando expira el access (para auto-refresh)       |
| `branch_id`                   | (vacío)                        | default   | Se setea tras crear branch                                     |
| `equipment_id`                | (vacío)                        | default   | Se setea tras crear equipment                                  |
| `asset_tag_sample`            | `EQ-0001`                      | default   | Tag para `by-asset-tag`                                        |
| `maintenance_record_id`       | (vacío)                        | default   | Se setea tras crear MaintenanceRecord                          |
| `schedule_id`                 | (vacío)                        | default   | Se setea tras crear MaintenanceSchedule                        |
| `failure_id`                  | (vacío)                        | default   | Se setea tras crear FailureRecord                              |
| `sample_pdf_path`             | (file path local)              | default   | Path absoluto al PDF de prueba                                 |

### 4.3 Pre-request scripts globales (collection-level)

A nivel de la colección (`Pre-request Scripts` tab):

```js
// Auto-login: si el access_token está vacío o expirado, obtener uno nuevo
const baseUrl = pm.environment.get("base_url");
const accessToken = pm.environment.get("access_token");
const expiresAt = parseInt(pm.environment.get("access_token_expires_at") || "0", 10);
const now = Date.now();

const needLogin = !accessToken || now >= expiresAt;

if (needLogin) {
  pm.sendRequest({
    url: `${baseUrl}/api/v1/auth/token/`,
    method: "POST",
    header: { "Content-Type": "application/json" },
    body: {
      mode: "raw",
      raw: JSON.stringify({
        username: pm.environment.get("username"),
        password: pm.environment.get("password"),
      }),
    },
  }, (err, res) => {
    if (err) {
      console.error("Login failed:", err);
      return;
    }
    if (res.code !== 200) {
      console.error("Login non-200:", res.code, res.text());
      return;
    }
    const body = res.json();
    pm.environment.set("access_token", body.access);
    pm.environment.set("refresh_token", body.refresh);
    // Marcar expiración 5 minutos antes del lifetime real (60 min - 5 min)
    pm.environment.set(
      "access_token_expires_at",
      (Date.now() + 55 * 60 * 1000).toString()
    );
  });
}
```

> Nota: el endpoint `auth/token/` no requiere el header de Authorization, así que el bucle de auto-login funciona sin recursión.

### 4.4 Authorization a nivel de colección

`Authorization` tab → `Bearer Token` → `{{access_token}}`. Heredado por todas las requests excepto las de `00 Auth` (que están como `No Auth`).

### 4.5 Tests post-respuesta (por request)

Cada request tiene un test que:

1. Verifica el status code esperado.
2. Si crea un recurso, persiste su `id` en la variable de environment correspondiente.

Ejemplos:

**Auth → Obtain token:**

```js
pm.test("status is 200", () => pm.response.to.have.status(200));
const body = pm.response.json();
pm.environment.set("access_token", body.access);
pm.environment.set("refresh_token", body.refresh);
pm.environment.set("access_token_expires_at", (Date.now() + 55 * 60 * 1000).toString());
```

**Branches → Create:**

```js
pm.test("status is 201", () => pm.response.to.have.status(201));
const body = pm.response.json();
pm.expect(body).to.have.property("id");
pm.environment.set("branch_id", body.id);
```

**Equipment → Create:**

```js
pm.test("status is 201", () => pm.response.to.have.status(201));
const body = pm.response.json();
pm.environment.set("equipment_id", body.id);
pm.test("qr_code_url present", () => pm.expect(body.qr_code_url).to.be.a("string").and.not.empty);
```

**Maintenance → Create (JSON):**

```js
pm.test("status is 201", () => pm.response.to.have.status(201));
pm.environment.set("maintenance_record_id", pm.response.json().id);
```

**Scheduling → Create:**

```js
pm.test("status is 201", () => pm.response.to.have.status(201));
pm.environment.set("schedule_id", pm.response.json().id);
```

**Failures → Create:**

```js
pm.test("status is 201", () => pm.response.to.have.status(201));
pm.environment.set("failure_id", pm.response.json().id);
```

**Failures → Resolve:**

```js
pm.test("status is 200", () => pm.response.to.have.status(200));
pm.test("now resolved", () => pm.expect(pm.response.json().resolved).to.eql(true));
```

## 5. Reglas para construir la colección

- **Orden importante:** dentro de cada folder, el primer request del CRUD es siempre `Create` o `List` para sembrar datos. Las posteriores reusan `{{...}}_id`.
- **No autenticar** los requests del folder `00 Auth` (cada uno usa `No Auth` explícitamente para evitar el auto-login global recursivo). Igualmente, el pre-request global hace su propio fetch que no respeta esa regla, pero el endpoint funciona sin token.
- **Idempotencia:** los requests `Patch` y `Update` deben funcionar tras un `Create` previo, sin requerir reordenar manualmente.
- **Form-data para PDF:** la request "Create with PDF" debe usar `Body → form-data`. Los keys de tipo `Text` no deben tener content type explícito; el de tipo `File` apunta a `{{sample_pdf_path}}`.
- **Variables tipo secret:** marcar `password`, `access_token`, `refresh_token` como `secret` para que se enmascaren en logs/UI.
- **Tests defensivos:** además de validar el status, validar al menos un campo del body para detectar regresiones de schema.

## 6. Snippets clave

### 6.1 Esquema mínimo del archivo `biometric_api.postman_collection.json` (Collection v2.1)

```json
{
  "info": {
    "_postman_id": "00000000-0000-0000-0000-000000000000",
    "name": "Biometric API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    "description": "API para administración de equipos biomédicos. Cubre Auth, Branches, Equipment, Maintenance History, Scheduling y Failures."
  },
  "auth": {
    "type": "bearer",
    "bearer": [{ "key": "token", "value": "{{access_token}}", "type": "string" }]
  },
  "event": [
    {
      "listen": "prerequest",
      "script": {
        "type": "text/javascript",
        "exec": [
          "// Auto-login global: ver fase 07 §4.3"
        ]
      }
    }
  ],
  "variable": [
    { "key": "base_url", "value": "http://localhost:8000" }
  ],
  "item": [
    {
      "name": "00 Auth",
      "item": [
        {
          "name": "Obtain token",
          "request": {
            "auth": { "type": "noauth" },
            "method": "POST",
            "header": [{ "key": "Content-Type", "value": "application/json" }],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"username\": \"{{username}}\",\n  \"password\": \"{{password}}\"\n}"
            },
            "url": "{{base_url}}/api/v1/auth/token/"
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('status 200', () => pm.response.to.have.status(200));",
                  "const body = pm.response.json();",
                  "pm.environment.set('access_token', body.access);",
                  "pm.environment.set('refresh_token', body.refresh);"
                ],
                "type": "text/javascript"
              }
            }
          ]
        }
      ]
    },
    {
      "name": "01 Branches",
      "item": [
        {
          "name": "Create",
          "request": {
            "method": "POST",
            "header": [{ "key": "Content-Type", "value": "application/json" }],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"name\": \"Sede Norte\",\n  \"address\": \"Calle 100 #15-20\",\n  \"city\": \"Bogota\",\n  \"phone\": \"+57 300 555 1234\",\n  \"email\": \"norte@clinic.test\",\n  \"is_active\": true\n}"
            },
            "url": "{{base_url}}/api/v1/branches/"
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('201', () => pm.response.to.have.status(201));",
                  "pm.environment.set('branch_id', pm.response.json().id);"
                ]
              }
            }
          ]
        }
      ]
    }
  ]
}
```

> El armador del archivo replica la estructura para cada folder. Para Maintenance "Create with PDF", el `body` cambia a:
>
> ```json
> "body": {
>   "mode": "formdata",
>   "formdata": [
>     {"key": "equipment", "value": "{{equipment_id}}", "type": "text"},
>     {"key": "kind", "value": "CORRECTIVE", "type": "text"},
>     {"key": "date", "value": "2026-04-20", "type": "text"},
>     {"key": "description", "value": "Cambio de batería", "type": "text"},
>     {"key": "pdf_file", "type": "file", "src": "{{sample_pdf_path}}"}
>   ]
> }
> ```

### 6.2 Esquema mínimo del archivo `biometric_api.postman_environment.json`

```json
{
  "id": "00000000-0000-0000-0000-000000000001",
  "name": "Biometric API - Local",
  "values": [
    {"key": "base_url", "value": "http://localhost:8000", "type": "default", "enabled": true},
    {"key": "username", "value": "admin", "type": "default", "enabled": true},
    {"key": "password", "value": "adminpass", "type": "secret", "enabled": true},
    {"key": "access_token", "value": "", "type": "secret", "enabled": true},
    {"key": "refresh_token", "value": "", "type": "secret", "enabled": true},
    {"key": "access_token_expires_at", "value": "0", "type": "default", "enabled": true},
    {"key": "branch_id", "value": "", "type": "default", "enabled": true},
    {"key": "equipment_id", "value": "", "type": "default", "enabled": true},
    {"key": "asset_tag_sample", "value": "EQ-0001", "type": "default", "enabled": true},
    {"key": "maintenance_record_id", "value": "", "type": "default", "enabled": true},
    {"key": "schedule_id", "value": "", "type": "default", "enabled": true},
    {"key": "failure_id", "value": "", "type": "default", "enabled": true},
    {"key": "sample_pdf_path", "value": "/tmp/sample.pdf", "type": "default", "enabled": true}
  ],
  "_postman_variable_scope": "environment",
  "_postman_exported_using": "Postman/10.x"
}
```

### 6.3 Cómo armar el JSON (recomendación operativa)

1. **Construir manualmente desde la UI de Postman** y exportar (`File → Export → Collection v2.1`). Esta es la ruta más robusta porque Postman valida el schema. Pegar los pre-request y test scripts en cada request.
2. Una vez exportado, mover el archivo a `docs/postman/biometric_api.postman_collection.json`.
3. Lo mismo para el environment: crear en la UI, exportar a `biometric_api.postman_environment.json`.
4. Versionar ambos archivos en git (no incluir `secret` reales — dejar `password=adminpass` solo si es la cred del docker dev).

## 7. Tests (validar la colección)

### 7.1 Validar con Newman localmente

```bash
# Instalar Newman
npm install -g newman

# Levantar la API
docker compose up -d
docker compose exec web python manage.py createsuperuser
# (admin / adminpass / cualquier email)

# Sembrar datos mínimos opcionalmente:
docker compose exec web python manage.py shell <<'EOF'
from apps.branches.models import Branch
Branch.objects.get_or_create(
    name="Sede Norte", defaults={
        "address": "Calle 100 #15-20", "city": "Bogota",
        "phone": "+57 300 555 1234", "email": "norte@clinic.test",
    },
)
EOF

# Correr la colección
newman run docs/postman/biometric_api.postman_collection.json \
  -e docs/postman/biometric_api.postman_environment.json \
  --reporters cli,html \
  --reporter-html-export newman-report.html
```

### 7.2 Validar en CI

GitHub Actions snippet (referencia, no a implementar en esta fase):

```yaml
- name: Run Postman collection
  run: |
    npm install -g newman
    newman run docs/postman/biometric_api.postman_collection.json \
      -e docs/postman/biometric_api.postman_environment.json \
      --env-var "base_url=http://localhost:8000" \
      --env-var "password=${{ secrets.POSTMAN_TEST_PASSWORD }}"
```

### 7.3 Casos a verificar en una corrida limpia

- [ ] `00 Auth → Obtain token` 200, llena `access_token`.
- [ ] `01 Branches → Create` 201, llena `branch_id`.
- [ ] `01 Branches → List` 200, count >= 1.
- [ ] `02 Equipment → Create` 201, llena `equipment_id`, `qr_code_url` no vacío.
- [ ] `02 Equipment → By asset tag` 200.
- [ ] `02 Equipment → Regenerate QR` 200.
- [ ] `02 Equipment → History` 200 (lista vacía o paginada).
- [ ] `03 Maintenance History → Create` 201.
- [ ] `03 Maintenance History → Create with PDF` 201 (requiere `sample_pdf_path` válido en environment).
- [ ] `04 Maintenance Scheduling → Create` 201, dispara email (verificar logs del backend o mailpit).
- [ ] `04 Maintenance Scheduling → Complete` 200, `is_completed=true`.
- [ ] `05 Failures → Create` 201.
- [ ] `05 Failures → Resolve` 200, `resolved=true`, `resolved_at` poblado.
- [ ] Cleanup (DELETE de cada recurso) 204.

## 8. Pruebas manuales con Postman

### 8.1 Importar en Postman UI

1. `File → Import → biometric_api.postman_collection.json`.
2. `Environments → Import → biometric_api.postman_environment.json`.
3. Seleccionar el environment `Biometric API - Local` en el dropdown superior derecho.
4. Editar `username`/`password` si tu superuser tiene otras credenciales.
5. (Opcional) Editar `sample_pdf_path` apuntando a un PDF local válido para los requests de maintenance.

### 8.2 Flujo completo manual

1. Abrir `00 Auth → Obtain token` → Send. Verificar que `access_token` queda poblado en el environment.
2. Abrir `01 Branches → Create` → Send. Confirmar 201 y que `branch_id` se llena.
3. Abrir `02 Equipment → Create` → Send. Confirmar 201, `qr_code_url` no nulo.
4. (Opcional) Abrir `02 Equipment → Regenerate QR` → Send → 200.
5. Abrir `03 Maintenance History → Create with PDF` (form-data). Asegurar que en `pdf_file` esté seleccionado el archivo. Send → 201.
6. Abrir `04 Maintenance Scheduling → Create` → Send → 201. Revisar logs del backend para ver el email impreso.
7. Abrir `05 Failures → Create` → Send → 201.
8. Abrir `05 Failures → Resolve` → Send → 200.

### 8.3 Encadenado (Runner)

Postman → `Runner` → seleccionar la colección y el environment → `Run Biometric API`.

Resultado esperado: todas las requests pasan en el orden definido (los IDs se propagan vía environment).

## 9. Checklist de verificación

- [ ] `docs/postman/biometric_api.postman_collection.json` existe y es Collection v2.1 válida.
- [ ] `docs/postman/biometric_api.postman_environment.json` existe.
- [ ] Pre-request global hace auto-login si `access_token` está vacío o expirado.
- [ ] Cada folder tiene un Create que llena su variable `*_id` correspondiente.
- [ ] Cada request tiene un test que valida el status code.
- [ ] Las requests del folder `00 Auth` están con `No Auth` explícito.
- [ ] Newman corre la colección entera sin fallos en una API limpia con superuser sembrado.
- [ ] La request "Create with PDF" usa `form-data` y referencia `{{sample_pdf_path}}`.
- [ ] La acción `regenerate-qr` y `resolve` están en sus folders.
- [ ] Variables `password`, `access_token`, `refresh_token` marcadas como `secret`.

## 10. Posibles extensiones futuras / TODO

- **Auto-generar la colección** desde el schema OpenAPI (`drf-spectacular` → `openapi.json` → herramienta tipo `openapi-to-postman`). Decisión: en esta fase la mantenemos a mano para tener control sobre tests/scripts.
- **Mocks de Postman** para que el frontend pueda desarrollar sin backend.
- **Workspace público** en Postman API Network (con sanitización de credenciales).
- **Escenarios negativos** explícitos como folders separados (`Auth Errors`, `Validation Errors`) para ejercitar los 400/401/404.
- **Snapshots de respuesta** con `chai-json-schema` para detectar drifts en el contrato.
- **Variables data-driven** (Newman `--iteration-data data.csv`) para correr el CRUD con N branches/equipos.
- **`--reporter junit`** para integrar el resultado de Newman al pipeline de CI con métricas.
- **Tokens rotativos** (refresh token) en el pre-request para entornos con access lifetime corto.
