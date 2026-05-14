# WSO2 IS + Organilab — Entorno local

Integración OIDC Authorization Code Flow entre Organilab y WSO2 Identity Server 7.0.0.

> **Hostnames:**
> - Browser → WSO2: `https://localhost:9443` (cert SSL de WSO2 es para `localhost`)
> - Contenedor Django → WSO2: `wso2is:9443` vía Docker DNS interno (automático, sin config en host)

## Requisitos previos

- Docker + Docker Compose v2.4+
- Imagen de Organilab construida (`make build_docker` desde la raíz)
- Puerto 9443 libre en el host

---

## Servicios disponibles

| Servicio | URL | Credenciales |
|---------|-----|-------------|
| Organilab | http://localhost:8001 | según BD |
| WSO2 IS Console | https://localhost:9443/console | `admin` / `admin` |
| pgAdmin | http://localhost:5050 | `admin@local.dev` / `admin` |
| MailHog | http://localhost:8025 | — |

---

## Paso 1 — Construir imagen de Organilab

Desde la raíz del proyecto:

```bash
make build_docker
```

---

## Paso 2 — Levantar servicios

Desde este directorio (`docker/wso2-local/`):

```bash
cd docker/wso2-local && docker compose up -d
```

Esperar a que WSO2 IS esté disponible (puede tardar 2-3 minutos):

```bash
 cd docker/wso2-local && docker compose logs -f wso2is
# Buscar: "WSO2 Identity Server started"
```

Admin UI: **https://localhost:9443/console** — login `admin` / `admin`
(el browser advertirá certificado no seguro — aceptar y continuar)

---

## Paso 3 — Crear aplicación OIDC en WSO2 IS

### 3.1 Crear nueva aplicación

1. Menú lateral → **Applications** → **New Application**
2. Seleccionar **Standard-Based Application**
3. Completar:
   - **Name:** `Organilab Local`
   - **Protocol:** `OpenID Connect`
4. Click **Register**

Client id
6qfwgV942Qt2yVfAz6RlWQB85xsa
client secret
kdYum6vnDgvw9HLNJ55ajaLI0gMKHzorMhhKv3BokfMa

### 3.2 Configurar la aplicación

En la pestaña **Protocol**:

| Campo | Valor |
|-------|-------|
| Allowed grant types | ✅ Code, ✅ Refresh Token |
| Callback URLs | `http://localhost:8001/oidc/callback/` |
| Allowed origins | `http://localhost:8001` |
| Logout URL | `http://localhost:8001/` |
| Access Token → Token type | `JWT` |
| ID Token → Response signing algorithm | `SHA256withRSA` |

Click **Update**.

### 3.3 Configurar atributos de usuario

En la pestaña **User Attributes** → sección **User Attribute Selection**, marcar los siguientes scopes:

| Scope / Atributo | Descripción |
|------------------|-------------|
| ✅ `email` | Email del usuario — **obligatorio** para identificar al usuario en Organilab |
| ✅ `profile` | Nombre y apellido (`given_name`, `family_name`) |
| ✅ `address` | Dirección del usuario |
| ✅ `phone` | Teléfono del usuario |
| ✅ `username` | Username de WSO2 — usado como username en Django |
| ✅ `preferred_username` | Nombre de usuario preferido (fallback de username) |

> `username` y `preferred_username` no aparecen en la lista por defecto — buscarlos con el buscador de la sección **User Attribute Selection**.

Click **Update**.

> **Crítico:** Sin marcar `email`, WSO2 IS solo devuelve `sub` en el userinfo — Organilab no puede identificar al usuario y falla la autenticación.

### 3.4 Obtener credenciales

En la pestaña **Protocol**, copiar:
- **Client ID**
- **Client Secret** (click en el ojo para revelar)

---

## Paso 4 — Configurar variables de entorno

Editar `docker/wso2-local/organilab.env` y completar:

```env
OIDC_RP_CLIENT_ID=<client_id_copiado>
OIDC_RP_CLIENT_SECRET=<client_secret_copiado>
```

Variables opcionales con sus valores por defecto:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DEFAULT_ORG_PK` | `0` | PK de la organización asignada al nuevo usuario en el primer login |
| `DEFAULT_ROL_NAME` | `Estudiante` | Nombre del rol asignado al nuevo usuario |
| `OIDC_VERIFY_SSL` | `True` | Verificar SSL al contactar WSO2. Poner `False` en local (cert autofirmado) |
| `OIDC_USE_PKCE` | `False` | Activar PKCE en el flujo OIDC |

### Mapeo de claims WSO2 → Organilab

Al autenticar, los claims del userinfo se mapean automáticamente:

| Claim WSO2 (scope) | Campo Django |
|--------------------|-------------|
| `email` (email) | `User.email` — identificador principal |
| `given_name` (profile) | `User.first_name` |
| `family_name` (profile) | `User.last_name` |
| `phone_number` (phone) | `Profile.phone_number` |
| `address.formatted` (address) | `Profile.address` |

---

## Paso 5 — Reiniciar Organilab

```bash
docker compose restart organilab-web organilab-celery
```

---

## Paso 6 — Configurar email en usuario WSO2

Organilab identifica usuarios por **email**. El usuario WSO2 debe tener email configurado antes de autenticar.

Para el usuario `admin` (u otro usuario existente):

1. **User Management** → **Users** → clic en el usuario
2. Completar el campo **Email** (ej: `admin@localhost`)
3. Click **Update**

> Si el usuario no tiene email, la autenticación falla con "Claims verification failed" aunque el flujo OIDC complete correctamente.

---

## Paso 7 — Verificar

1. Ir a http://localhost:8001/oidc/authenticate/
2. Debe redirigir a la pantalla de login de WSO2 IS (`localhost:9443`)
3. Login con `admin` / `admin` (o un usuario WSO2 con email configurado)
4. Después de autenticar, redirige al dashboard de Organilab

Botón de login en cualquier template:
```html
<a href="{% url 'oidc_authentication_init' %}">Login con SSO</a>
```

---

## Paso 8 — Restaurar base de datos con pgAdmin

### 8.1 — Preparar el archivo de backup

El directorio `docker/wso2-local/backups/` está montado dentro del contenedor pgAdmin y está en `.gitignore` (los archivos no se suben al repo).

Copiar el archivo de backup ahí:

```bash
cp /ruta/a/tu/backup.dump docker/wso2-local/backups/
```

### 8.2 — Conectar pgAdmin a la base de datos

1. Abrir http://localhost:5050
2. Login: `admin@local.dev` / `admin`
3. **Add New Server:**
   - **Name:** `organilab-local` (cualquier nombre)
   - Pestaña **Connection:**

| Campo | Valor |
|-------|-------|
| Host | `postgresdb` |
| Port | `5432` |
| Database | `postgres` |
| Username | `organilab_user` |
| Password | `0rg4n1l4b` |

4. Click **Save**

### 8.3 — Restaurar

5. Clic derecho sobre la base de datos → **Restore...**
6. En **Filename**, click en el ícono de carpeta → navegar a **Storage** → seleccionar el archivo copiado en `backups/`
7. Click **Restore**

Después de restaurar, correr migraciones pendientes:

```bash
docker compose exec organilab-web python manage.py migrate
```

---

## Paso 9 — Crear usuarios de prueba en WSO2 IS (opcional)

En la consola WSO2:
**User Management** → **Users** → **Add User**

Configurar el campo **Email** — es el identificador que usa Organilab para vincular cuentas.

---

## Troubleshooting

### `redirect_uri mismatch`

La callback URL registrada en WSO2 debe ser exactamente:
```
http://localhost:8001/oidc/callback/
```
(con barra al final)

### Usuario sin Profile

Si el usuario autentica pero falla después, el backend `OrganiLabOIDCBackend.create_user` crea el `Profile` automáticamente en el primer login. Verificar logs del contenedor:
```bash
docker compose logs organilab-web | tail -30
```

### WSO2 no arranca

```bash
docker compose logs wso2is | tail -50
```

WSO2 IS 7.x requiere mínimo 2GB de RAM disponible para Docker.

---

## Endpoints OIDC de WSO2 IS (referencia)

| Quién accede | Endpoint | URL |
|---|----------|-----|
| Browser | Authorization | `https://localhost:9443/oauth2/authorize` |
| Django server | Token | `https://wso2is:9443/oauth2/token` |
| Django server | UserInfo | `https://wso2is:9443/oauth2/userinfo` |
| Django server | JWKS | `https://wso2is:9443/oauth2/jwks` |
| Browser | Logout | `https://localhost:9443/oidc/logout` |
| Cualquiera | Discovery | `https://localhost:9443/oauth2/token/.well-known/openid-configuration` |

---

## URLs de Organilab generadas por mozilla-django-oidc

| URL | Descripción |
|-----|-------------|
| `/oidc/authenticate/` | Inicia el flujo OIDC (redirige a WSO2) |
| `/oidc/callback/` | Callback — registrar esta URL en WSO2 |
| `/oidc/logout/` | Cierra sesión en Organilab y WSO2 |
