# IPER — Guía de implementación (para el agente implementador)

> **Qué es esto.** Guía técnica para implementar el módulo IPER en `src/risk_management/`. Léela
> junto a [`IPER_DESIGN.md`](IPER_DESIGN.md) (qué hace + catálogos INTE T55) y
> [`AGENT_BRIEFING.md`](AGENT_BRIEFING.md) (arquitectura de Organilab).
>
> **Principio rector: reutilizar, no reinventar.** Casi todo tiene un patrón gemelo ya en este app
> (`IncidentReport`, `RiskZone`/`ZoneDashboard`, `Workday`, `create_pending_task`,
> `riskmanagement_menu.html`). Clonar y adaptar.

---

## 0. Decisiones ya tomadas (no re-litigar)

- **Modelos dedicados** (no derb/Formio), el IPER vive **por laboratorio**.
- **Metodología: réplica exacta de IPER-CL / INTE T55** (catálogos en `IPER_DESIGN.md` §3). Las
  listas (categorías de peligro, probabilidad, consecuencia, niveles) **reutilizan el modelo
  `Catalog` de organilab** (global, `key`+`description`) vía `GTForeignKey` — **no** se crean modelos
  de catálogo propios. Editar/agregar valores IPER se **restringe a la org raíz** (permiso). La
  **matriz P×C→nivel** es el único modelo nuevo (`IPERRiskMatrix`); los atributos fijos (prioridad,
  color, acción, emoji, ejemplos) son constantes en `iper_defaults.py` (ver §1 y §9).
- **Rol Analista**: lectura global + dashboard + solicitar llenado por zona. Sin flujo de aprobación, pero permitiendo poner observaciones en esta primera etapa.
- **Periodicidad configurable** (12 meses por defecto) + bajo demanda; cada actualización crea una
  nueva versión precargada con la anterior, y tiene una opción de iniciar en limpio que quita los datos precargados.

---

## 1. Catálogos con el modelo `Catalog` de organilab + `iper_defaults.py`

Las listas IPER **reutilizan el modelo `Catalog`** (`src/laboratory/models.py`: `key` + `description`,
**global**, sin scoping por org) en vez de modelos propios. Se declaran en `IPERHazard` con
`GTForeignKey` (`src/laboratory/catalog/utils.py`), igual que `Structure.type_structure`/
`measuerement_unit`. `key` por catálogo:

- `iper_hazard_category` — las 6 categorías de peligro.
- `iper_probability` — `B/M/A`.
- `iper_consequence` — `LD/D/ED`.
- `iper_risk_level` — Trivial / Tolerable / Moderado / Importante / Intolerable.

**Lo que NO cabe en `Catalog`** (solo guarda `key`/`description`):
- La **matriz P×C→nivel** → único modelo nuevo `IPERRiskMatrix` (ver §2.4), 9 filas con `GTForeignKey`
  a `Catalog` (probabilidad, consecuencia, nivel).
- Atributos fijos (prioridad 1-5, color/badge, acción, emoji por categoría, ejemplos de ayuda) →
  **constantes en `src/risk_management/iper_defaults.py`**, indexadas por el `description` sembrado
  (estándar INTE T55, no cambia). Mantener los textos sembrados estables; etiquetas con `gettext`.

`def compute_risk_level(probability, consequence)`: consulta
`IPERRiskMatrix.objects.get(probability=…, consequence=…).risk_level` y devuelve la entrada `Catalog`
del nivel; la `priority` sale de las constantes (`iper_defaults.py`).

**Edición restringida a la org raíz**: como `Catalog` es global, agregar/editar valores IPER se hace
solo desde una org raíz (`parent=Null`), gateado por permiso (ver §7). El `SelectWithAdd` de “agregar”
se muestra solo a usuarios de org raíz; los demás solo seleccionan.

**Semilla + migración** (ver también §8 y la nota del usuario): una **data migration**
(`migrations.RunPython`) — y un management command `seed_iper_catalog` espejo para re-cargar — que:
1. crea las entradas `Catalog` de los 4 `key` desde `iper_defaults.py` si no existen (patrón
   `create_catalog()` / `load_common_catalogs` de `laboratory`);
2. crea las 9 filas de `IPERRiskMatrix`;
3. crea una `IPERConfig` por defecto **para cada organización raíz** (`OrganizationStructure` con
   `parent=Null`). Los `Catalog`/matriz son globales (una sola vez); `IPERConfig` se crea por cada
   org raíz.

---

## 2. Modelos — `src/risk_management/models.py` (+ migración)

Heredan `AbstractOrganizationRef` (de `src/presentation/models.py`): aporta `organization`,
`created_by`, `creation_date`, `last_update`. Seguir el estilo de `RiskZone`/`IncidentReport`.

### 2.1 `IPERAssessment` (cabecera, versionada por laboratorio)
- `laboratory` → FK `laboratory.Laboratory`.
- `assessment_date` → `DateField`.
- `responsible` → FK `User` (normalmente `laboratory.responsible`).
- `status` → choices `draft` / `completed` / `obsolete`.
- `version` → `PositiveIntegerField` (1, 2, 3… por laboratorio).
- `previous` → self-FK nullable (cadena de versiones).
- `due_date` → `DateField` nullable (próxima actualización; calculada con el período de `IPERConfig`).
- `source` → choices `periodic` / `on_demand` / `zone_request`.
- Conteos por nivel para el dashboard: calcular en propiedades o cachear en campos al guardar
  (decisión del implementador; preferir caché si el dashboard lo pide seguido).
- `Meta.permissions` (extra a los auto CRUD): `view_all_iper`, `request_iper`, `view_iper_dashboard`.

### 2.2 `IPERHazard` (fila de peligro)
- `assessment` → FK `IPERAssessment`, `related_name="hazards"`.
- `category` → `GTForeignKey(Catalog, key_name="key", key_value="iper_hazard_category")`.
- `description` → `TextField`.
- `location` → `CharField`.
- `probability` → `GTForeignKey(Catalog, …, key_value="iper_probability")`;
  `consequence` → `GTForeignKey(Catalog, …, key_value="iper_consequence")`.
- `risk_level` → `GTForeignKey(Catalog, …, key_value="iper_risk_level")` **resuelto en `save()`** con
  `compute_risk_level(probability, consequence)` (lee `IPERRiskMatrix`); desnormalizado para
  filtrar/contar.
- `risk_priority` → `SmallIntegerField` (1–5, de las constantes de `iper_defaults.py`, para
  ordenar/promediar).
- `controls` → `TextField` ("Controles implementados").
- *(opcional)* `recommended_controls` → `TextField`.
- *(opcional, trazabilidad)* `related_shelfobjects` M2M a `laboratory.ShelfObject`.

### 2.3 `IPERConfig` (periodicidad configurable)
- `organization` (del mixin), `period_months` (default 12), `reminder_days_before` (ej. 30),
  `is_active`.
- `laboratory` nullable → si existe, override del período para ese lab; si no, aplica a toda la org.
- La config "vive" en la org raíz: resolver subiendo el árbol (helper `get_iper_config(org)`) salvo
  override por laboratorio. Se crea una por org raíz en la migración (§1).

### 2.4 `IPERRiskMatrix` (único modelo de catálogo)

La matriz P×C→nivel; no hereda org (es global, espeja al `Catalog` global). 9 filas sembradas.
- `probability` → `GTForeignKey(Catalog, …, key_value="iper_probability")`.
- `consequence` → `GTForeignKey(Catalog, …, key_value="iper_consequence")`.
- `risk_level` → `GTForeignKey(Catalog, …, key_value="iper_risk_level")`.
- `Meta.unique_together = ("probability", "consequence")`.

Las **listas** (categorías, P, C, niveles) son entradas de `Catalog` (no modelos), y los **atributos
fijos** (prioridad/color/acción/emoji/ejemplos) son constantes en `iper_defaults.py` (§1).

### 2.5 `IPERObservation` (observaciones del analista)
- `assessment` → FK `IPERAssessment`, `related_name="observations"`.
- `author` → FK `User` (el analista), `text` → `TextField`, `creation_date` (auto).
- Permite que el analista deje comentarios sin un flujo de aprobación formal. El form del
  responsable las muestra como solo-lectura.

> **Historial/tendencia**: NO usar `EstablishmentLogs` (es del flujo de clasificación de
> establecimiento por sustancias, `utils_risk.py`, otro sistema). El historial IPER sale de
> recorrer la cadena `IPERAssessment.previous` por laboratorio, **ordenado por fecha**. Al actualizar
> se **clona** la evaluación, así cada `IPERHazard` queda inmutable en su versión.

---

## 3. Vistas — `src/risk_management/iper_views.py` (nuevo) o ampliar `views.py`

- Heredar las CBV base de `src/laboratory/views/djgeneric.py` (`ListView`, `CreateView`,
  `UpdateView`, `DetailView`): ya extraen `org_pk`/`lab_pk` y validan acceso
  (`user_is_allowed_on_organization`, `organization_can_change_laboratory`).
- Decoradores como el código actual:
  `@method_decorator(permission_required("risk_management.<perm>", raise_exception=True), name="dispatch")`.
- Vistas:
  - `IPERAssessmentList` / `Create` / `Update` / `Detail` — CRUD por laboratorio; el form de
    peligros es inline (mirar cómo `ZoneDetail` maneja `IncidentReportForm`, `views.py:232`).
  - `IPERHistory` — tabla **ordenada por fecha** + contadores + filtros + export PDF (WeasyPrint) y
    Excel (`django_excel`), siguiendo `report_incidentreport` en `incidents.py:202` y la plantilla
    `incidentreport_pdf.html`. Mostrar la **cadena org→lab** (breadcrumb del árbol
    `OrganizationStructure`) en lugar de un texto libre "Escuela".
  - `IPERAnalystDashboard` — `TemplateView` que agrega URLs de charts, patrón de `ZoneDashboard`
    (`views.py:401`), gated por `view_iper_dashboard`.
  - `clone_for_update` — crea `version+1` copiando cabecera + `IPERHazard`, enlaza `previous`,
    marca la anterior `obsolete`. Acepta un flag **"iniciar en limpio"** que crea la nueva versión
    **sin** copiar los `IPERHazard` (datos precargados vacíos).
  - `IPERObservation` create/list — el analista deja observaciones sobre una evaluación
    (gated por un permiso del analista; ver §7).
  - **Agregar valores de `Catalog`** (categorías, P, C, niveles) y editar `IPERRiskMatrix`: **solo
    para la org raíz**; reutilizar el patrón `add_catalog` AJAX + `CatalogForm` + `SelectWithAdd` de
    `laboratory`, pero gateado por permiso de org raíz (bloquear si `organization.parent` no es Null).
  - `request_iper_for_zone(risk_zone)` — itera labs de la zona, llama a `create_pending_task`
    (ver §6). Gated por `request_iper`.

Usar `organilab_logentry(user, obj, ADDITION/CHANGE/DELETION)` para auditoría, como hace el código
actual.

---

## 4. API — `src/risk_management/api/`

- `IPERAssessmentViewSet`, `IPERHazardViewSet` extendiendo `AuthAllPermBaseObjectManagement`
  (patrón de `IncidentViewSet`/`WorkdaysViewSet` en `api/viewset.py`).
- Serializers DataTable (patrón `*DataTableSerializer` en `api/serializer.py`).
- Filtros en `api/filterseet.py`: por `category`, `risk_level`, rango de fechas (reusar
  `DateFromToRangeFilter`, como `IncidentReportFilter`).
- Endpoint de **ayuda contextual** (§5 de design): `iper_lab_help/<lab_pk>/` → inventario + peligros
  SGA del laboratorio para sugerir descripciones. Consumido por el JS del formulario.
- Registrar con `DefaultRouter` en `urls.py` (namespace `riskmanagement`).

---

## 5. Charts y selects del dashboard

- `gtcharts.py` — añadir, siguiendo el patrón existente (`BaseChart`/`HorizontalBarChart`,
  `@register_lookups`, `LaboratoryPermission`, `get_extra_filters` con `risk_zone[]`/`buildings[]`):
  - `IPERRiskLevelDistributionChart` — peligros por nivel (última evaluación).
  - `IPERRiskTrendChart` — evolución del nivel de riesgo entre versiones (línea temporal).
  - `IPERHazardByCategoryChart` — peligros por categoría.
  - `IPERComplianceChart` — labs con IPER vigente / vencido / nunca llenado.
- `gtselects.py` — reusar/extender `RiskLaboratory`, `RiskBuildings` para filtros del dashboard.

---

## 6. Tareas pendientes y Celery

- Crear tareas con `create_pending_task()` de `src/pending_tasks/utils.py`
  (`created_by, name, rols, description="", status=PendingTask.PENDING, profile=None, link="", notify=False`).
  - Recordatorio/vencimiento: `profile=lab.responsible.profile`, `notify=True`, `link` a la URL de
    actualización del IPER del lab.
  - Solicitud por zona: una tarea por responsable de los labs de la `RiskZone`.
- `src/risk_management/tasks.py` — nueva tarea `send_iper_update_reminders()`:
  - Calcula vencimiento con `IPERConfig.period_months` sobre la última `IPERAssessment.assessment_date`.
  - Si `due_date - reminder_days_before <= hoy` y no hay evaluación vigente → crea `PendingTask`.
  - (Opcional) marca evaluaciones vencidas como `obsolete`.
- `src/organilab/settings.py` — añadir a `CELERYBEAT_SCHEDULE` (patrón de `create_establishment_logs`):
  ```python
  "send_iper_update_reminders": {
      "task": "risk_management.tasks.send_iper_update_reminders",
      "schedule": crontab(minute=0, hour=8),  # diario; la lógica decide a quién toca hoy
  },
  ```

---

## 7. URLs, templates, menú, permisos

- **URLs** (`src/risk_management/urls.py`, namespace `riskmanagement`, bajo `/<int:org_pk>/...`):
  `iper/list/`, `iper/create/`, `iper/<pk>/detail/`, `iper/<pk>/update/` (acepta `?clean=1` para
  iniciar en limpio), `iper/<pk>/history/`, `iper/<pk>/observation/`, `iper/dashboard/`,
  `iper/zone/<risk_pk>/request/`, `iper/catalog/...` (solo org raíz), + rutas API.
- **Templates** (`src/risk_management/templates/risk_management/`): `iper_form.html` (tarjetas de
  categoría con emoji + ejemplos; panel de ayuda lateral con inventario), `iper_list.html`,
  `iper_detail.html`, `iper_history.html` (tabla + contadores + filtros + Excel/PDF),
  `iper_dashboard.html` (iframes de charts, como `risk_graphics.html`), `iper_pdf.html`.
- **Menú** (`src/presentation/templates/partials/riskmanagement_menu.html`), entradas gated:
  - `{% if perms.risk_management.add_iperassessment %}` → "Evaluación IPER".
  - `{% if perms.risk_management.view_iper_dashboard %}` → "Dashboard de Riesgo (Analista)".
  - `{% if perms.risk_management.view_all_iper %}` → "Historial IPER (todos los labs)".
- **Permisos / rol Analista**:
  - Declarar permisos extra en `IPERAssessment.Meta.permissions` (§2.1): `view_all_iper`,
    `request_iper`, `view_iper_dashboard`, `add_iperobservation` (observaciones del analista), y
    `manage_iper_catalog` (agregar valores `Catalog` IPER + editar `IPERRiskMatrix`). La vista exige
    además que la org sea raíz (`parent=Null`).
  - Registrar URL-permissions en
    `src/auth_and_perms/management/commands/urlname_permissions.py` (categoría "Risk Management"),
    luego `python manage.py load_urlname_permissions`.
  - Rol **Analista de Riesgo** como `Rol` con `view_all_iper`, `view_iper_dashboard`, `request_iper`,
    `add_iperobservation`, `view_iperassessment`, `view_iperhazard`; asignar vía `ProfilePermission`
    por organización. Opcional: management command/fixture que cree el rol por defecto.

---

## 8. Archivos a crear / modificar

**Crear:** `iper_defaults.py` (constantes: textos de `Catalog`, matriz, atributos fijos),
`management/commands/seed_iper_catalog.py`, `iper_views.py` (o ampliar `views.py`),
viewsets/serializers/filters IPER en `api/`, templates `iper_*.html`, `tests/test_iper.py`.

**Modificar:** `models.py` (+ **migración con `RunPython`** que siembra los `Catalog` de los 4 `key`,
las 9 filas de `IPERRiskMatrix`, y una `IPERConfig` por **cada org raíz `parent=Null`**; modelos
nuevos: `IPERAssessment`, `IPERHazard`, `IPERConfig`, `IPERRiskMatrix`, `IPERObservation`),
`urls.py`, `gtcharts.py`, `gtselects.py`, `tasks.py`, `forms.py`,
`utils.py`/`models_utils.py` (`compute_risk_level`, `get_iper_config`),
`presentation/.../riskmanagement_menu.html`, `auth_and_perms/.../urlname_permissions.py`,
`organilab/settings.py`. i18n: `make messages` + `make trans`.

---

## 9. Notas / decisiones abiertas

- **Catálogos con `Catalog`**: las listas (categorías, P, C, niveles) son entradas del modelo
  `Catalog` global de organilab (vía `GTForeignKey`); **no** modelos propios. La matriz es el único
  modelo nuevo (`IPERRiskMatrix`); prioridad/color/acción/emoji/ejemplos son constantes en
  `iper_defaults.py`. Agregar/editar valores IPER se restringe a la org **raíz** (`parent=Null`) por
  permiso `manage_iper_catalog`. **Migración con `RunPython`** siembra `Catalog` + `IPERRiskMatrix`
  (globales, una vez) y crea una `IPERConfig` por **cada** org raíz.
- **Versionado**: al "actualizar", clonar cabecera + hazards a `version+1`, enlazar `previous`, la
  anterior pasa a `obsolete`. Hay opción de **iniciar en limpio** (sin precargar hazards). Historial
  y tendencia salen de recorrer la cadena, aunque se ordenan por fecha.
- **Escuela**: en IPER-CL es texto libre; aquí derivarla del árbol `OrganizationStructure` del lab y
  proveer la cadena de organización/lab (breadcrumb).
- **No** confundir con `EstablishmentLogs`/`utils_risk.py` (clasificación de establecimiento por
  sustancias del decreto): sistema distinto, aunque comparta el app.

---

## 10. Verificación (end-to-end)

1. **Migraciones + semilla**: `make migrate` ejecuta la `RunPython` que crea las entradas `Catalog`
   (4 `key`), las 9 filas de `IPERRiskMatrix` y una `IPERConfig` por cada org raíz (`parent=Null`).
   `python manage.py seed_iper_catalog` re-carga idempotente. Verificar que los 4 catálogos existen y
   que cada org raíz tiene su `IPERConfig`.
2. **Catálogo (org raíz)**: agregar un valor `Catalog` IPER o editar una celda de `IPERRiskMatrix`
   desde una org raíz (permiso `manage_iper_catalog`); confirmar que desde una org hija no se permite
   (no aparece el `SelectWithAdd`/bloqueo por `parent`).
3. **Permisos**: `python manage.py load_urlname_permissions`; crear rol Analista; el menú muestra/
   oculta según permisos.
4. **Formulario**: como responsable, crear `IPERAssessment` con varios `IPERHazard`; verificar que
   `risk_level` se resuelve desde `IPERRiskMatrix` (ej. `A`+`ED` → Intolerable) y que el panel de
   ayuda lista inventario/peligros SGA del lab.
5. **Observaciones**: como analista, dejar una observación en una evaluación; el responsable la ve
   como solo-lectura.
6. **Historial/export**: orden por fecha, contadores por nivel, filtros y export Excel + PDF;
   breadcrumb org→lab visible.
7. **Versionado**: actualizar bajo demanda → nueva versión precargada (y probar "iniciar en limpio");
   anterior `obsolete`; la tendencia del dashboard muestra el cambio.
8. **Solicitud por zona**: como analista, "Solicitar IPER" en una `RiskZone` → `PendingTask` +
   notificaciones a los responsables (verificar en `pending_tasks` y Mailhog del docker-compose).
9. **Tarea periódica**: ejecutar `send_iper_update_reminders` (eager en tests) → genera `PendingTask`
   para labs con IPER por vencer según `IPERConfig.period_months`.
10. **Tests/lint**: `make single-test TEST=risk_management.tests.test_iper` y `make lint`.
