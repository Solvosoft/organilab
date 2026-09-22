# Consumos y residuos — implementado salvo la importación masiva

> **Qué es esto.** App `src/ambiental/` (no `environment`, para no confundirla) para registrar
> **cuánto consume y desecha** cada edificio (agua, electricidad, combustible, gas, papel, residuos
> sólidos, peligrosos y especiales), convertirlo en **indicadores normalizados** (por persona, por m²)
> y **alertar consumos atípicos**. La versión larga del diseño con flujos de pantalla está en git
> (`git show fdd5de217:plans/ENVIRONMENT_PLAN.md`). Viene de [`SIGMA_GAP_ANALYSIS.md`](SIGMA_GAP_ANALYSIS.md).
>
> **Estado (2026-09-16):** pasos 1–6, 8 y 9 hechos en la rama `regenteambiental`. Falta el paso 7
> (importación masiva) y lo de §4.

---

## 1. Decisiones

- **App nueva `ambiental`**; modelos y clases en inglés como el resto del repo.
- **El registro es por edificio** (medidor y recibo reales). La unidad de registro es el
  **punto de medición**, que pertenece a un edificio y opcionalmente a varios laboratorios
  (informativo: no hay prorrateo).
- **Un solo modelo de registro** con `extra_data` validado por recurso; un residuo es un registro con
  `is_waste=True` (lo fuerza el recurso).
- **Período**: en reportes, indicadores y alertas un registro cuenta en el mes de `period_end`
  (mes facturado); no se prorratea por días.
- **Unidades**: catálogo propio `ambiental_measure_unit`; unidades distintas de un mismo recurso no se
  suman ni se convierten (se marca «unidades mezcladas»).
- **Gestor autorizado de residuos**: FK a `laboratory.Provider` (proveedores de los laboratorios de la
  organización más los globales).
- **Alertas** sobre la plataforma genérica (`AlertRule`, ver [`PLATFORM_ADMIN_PLAN.md`](PLATFORM_ADMIN_PLAN.md)).
- **djgentelella como base**: ObjectCRUD, `BaseViewSetWithLogs`, `DeletedWithTrash`, chunked upload,
  select2 con `data-s2filter-*`, `chartjs`, `async_notification`.

### Acceso por edificio

- Un rol ambiental asignado **en la organización** cubre todos sus edificios; asignado **sobre un
  edificio** (`ProfilePermission` con content type `risk_management.Buildings`) cubre solo ese
  edificio, y cada permiso se evalúa contra el rol de ese edificio (se puede ser administrador en
  uno y analista en otro). No se hereda de roles de laboratorio ni del «Responsable» del edificio.
- `ProfileMiddleware` suma los roles de edificio de la organización de la URL
  (`profile_permission_scope_query`) solo para dejar entrar a las pantallas. Lo que autoriza cada
  objeto es `src/ambiental/access.py` `BuildingAccess`: APIs, selects, reportes (con el acceso de
  quien pidió el reporte), panel, gráficos y destinatarios de alertas.
- La plataforma (parámetros, correos, reglas) exige roles de organización
  (`organization_permissions`), no de edificio.
- Pantalla `ambiental:building_access_list` (permiso `manage_building_access`): un administrador de
  edificio solo da acceso a su edificio. Sacar a la persona de la organización o borrar el edificio
  borra sus accesos.

## 2. Dónde está cada cosa

| Pieza | Archivo |
|-------|---------|
| Catálogos y metadatos por recurso | `src/ambiental/ambiental_defaults.py` (migración `0002`, comando `seed_ambiental_catalog`) |
| Modelos | `src/ambiental/models.py`: `MeasurementPoint`, `ConsumptionRecord`, `NormalizationBase`, `ConsumptionAlert` |
| APIs (org de la URL, bitácora y papelera) | `src/ambiental/api/viewsets.py` sobre `presentation/api_mixins.py` `OrganizationLogsViewSet` |
| Precarga de bases (área del edificio, jornadas sin doble conteo) | `src/ambiental/normalization.py` |
| Indicadores y comparación de períodos | `src/ambiental/indicators.py` |
| Reportes (detalle, consolidado, costos, indicadores, comparación, residuos) | `src/ambiental/reports.py`, registrados en `src/report/register.py` |
| Panel y gráficos | `src/ambiental/views.py` `AmbientalDashboard`, `src/ambiental/gtcharts.py` |
| Alertas | `src/ambiental/alerts.py`, tarea `src/ambiental/tasks.py` (`CELERYBEAT_SCHEDULE`, día 2 de cada mes) |
| Roles | `update_roles.py` `update_ambiental_roles`: Administrador ambiental, Encargado de registro ambiental, Analista ambiental |
| Acceso por edificio | `src/ambiental/access.py`, `src/ambiental/api/building_access.py` |
| Catálogo de funcionalidades | `src/presentation/features/ambiental.py` (AMB-01 a AMB-09) |

Parámetros que usa (`presentation/parameters.py`): `ambiental.require_document`,
`ambiental.alert_window_months`.

## 3. Pasos

| # | Entregable | Estado |
|---|-----------|--------|
| 1 | App + catálogos + `MeasurementPoint` + CRUD | Hecho |
| 2 | `ConsumptionRecord` + formulario adaptable por recurso + anti-traslape + adjunto obligatorio configurable | Hecho |
| 3 | `NormalizationBase` + precarga | Hecho |
| 4 | Reportes detalle, consolidado, costos | Hecho |
| 5 | Indicadores + comparación entre períodos | Hecho |
| 6 | Panel con gráficos y tarjetas | Hecho |
| 7 | Importación masiva CSV/Excel con mapeo de columnas y previsualización | **Pendiente** |
| 8 | `ConsumptionAlert` + tarea mensual + pantalla «Marcar como revisada» | Hecho |
| 9 | Residuos y reporte de manifiestos | Hecho |

## 4. Pendientes

- **Paso 7**: importación masiva (`source="import"` ya existe en el modelo).
- **Nunca visto en navegador**: las pantallas solo tienen pruebas de cliente y de API. Falta el smoke
  manual (modales ObjectCRUD, select2 filtrado por edificio, campos que se ocultan según el recurso,
  gráficos) y pruebas Selenium.
- **Geolocalización y ubicación del punto** (provincia/cantón/distrito) quedaron fuera: el punto usa la
  del edificio.
- `Structure.area` no se usa en la precarga (solo `Buildings.area`, que no guarda unidad y se asume m²).
- Sin factor de emisión ni huella de carbono.
- Los roles ambientales reciben `laboratory.do_report` porque la cola común de reportes lo exige; eso
  también les abre los demás reportes de la organización.
- [`MANAGEMENT_PLANS_PLAN.md`](MANAGEMENT_PLANS_PLAN.md): acciones con `resource_type` que abran el
  formulario de consumo precargado.
