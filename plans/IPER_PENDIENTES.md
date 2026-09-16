# IPER — pendientes

> **Qué es esto.** Lo que falta del módulo IPER (riesgo INTE T55) en `src/risk_management/`.
> Sustituye a `IPER_DESIGN.md`, `IPER_IMPLEMENTATION_PLAN.md` y `plan-iper-duplicate.md`, ya
> borrados (siguen en el historial de git). Verificado contra el código el 2026-09-16.
>
> **Ya hecho (no rehacer):** modelos `IPERAssessment`/`IPERHazard`/`IPERConfig`/`IPERRiskMatrix`/
> `IPERObservation` (`models.py:391-660`, migraciones `0032`–`0035`); catálogos INTE T55 en
> `iper_defaults.py` sembrados por `0033_seed_iper.py` y `seed_iper_catalog`; CRUD, detalle,
> historial con Excel/PDF, dashboard, clonar (`?clean=1`), duplicar a otro lab, observaciones,
> ayuda del lab, toggles de estado/anónimo (`iper_views.py`); `IPERAssessmentViewSet`; tarea
> `send_iper_update_reminders` en `CELERYBEAT_SCHEDULE`; roles "Auditor IPER" y "Administrador
> IPER" (`update_roles.py`); tests en `tests/test_iper.py` + flujo Selenium `selenium_tests/iper/`.

---

## 1. Funcional

| # | Pendiente | Estado / evidencia |
|---|-----------|--------------------|
| 1 | `IPERHazardViewSet` + serializer DataTable | No existe |
| 2 | Filtros API en `api/filterseet.py` (categoría, nivel, rango de fechas con `DateFromToRangeFilter`) | El historial filtra con un form plano |
| 3 | `IPERRiskTrendChart`: evolución de niveles entre versiones de un lab (el diferenciador del diseño) | No existe |
| 4 | Métricas: peligros Importante/Intolerable abiertos, prioridad promedio | No existen |
| 5 | Lista de responsables que no han llenado su IPER | `IPERComplianceChart` (`gtcharts.py:1216`) solo da conteos |
| 6 | Alcance de gráficos: incluir orgs hijas y contar solo la última versión por lab | Filtran `organization__pk` exacto y cuentan todas las versiones |
| 7 | Filtros de gráficos por `risk_zone[]`/`buildings[]` + selects en `gtselects.py` | No hecho |
| 8 | Editar `IPERRiskMatrix` (solo org raíz) | Sin vista; modelos no están en `admin.py` |
| 9 | "Agregar valor" (`SelectWithAdd`) visible solo a org raíz | `iper_catalog_add` existe pero nada lo llama; `IPERHazardForm` usa `Select` |
| 10 | Editar un peligro desde el detalle | Ruta `iper_hazard_update` existe; la plantilla solo tiene agregar/borrar |
| 11 | Categorías como tarjetas con emoji | Hoy `Select` + panel de ayuda (`static/js/iper_hazard_help.js`) |
| 12 | Sugerir descripciones químicas/biológicas desde el inventario | El panel lista ítems y códigos H, sin enlazar con la descripción |
| 13 | Ayuda del lab con pictogramas, precursor y CAS | `iper_lab_help` devuelve nombre, tipo, `is_dangerous`, códigos H |
| 14 | Breadcrumb org→lab en detalle, historial y PDF; columna "Escuela" en historial | Solo `laboratory.organization` |

## 2. Recordatorios (`tasks.py:39-80`)

- Labs **sin ninguna evaluación** no reciben recordatorio.
- No hay deduplicación: dentro de la ventana crea una `PendingTask` nueva cada día.
- No verifica si ya existe una evaluación vigente más nueva.
- El `link` va a `iper_list`, no a la actualización del lab.
- (Opcional) marcar vencidas como `obsolete`.

## 3. Solicitud por zona

- `iper_request_for_zone` existe pero **no hay botón** en `riskzone_detail.html`.
- Nunca se usa `source=ZONE_REQUEST` (solo crea tareas).
- Sin protección contra solicitudes duplicadas.

## 4. Menú y roles

- Falta entrada "Historial IPER (todos los labs)" gated por `view_all_iper` en
  `riskmanagement_menu.html` (hoy solo se llega por botón desde la lista).
- No hay un rol "Analista de Riesgo" exacto: "Auditor IPER" no tiene `request_iper`.

## 5. Clonar / duplicar

- `iper_clone_for_update` **rechaza evaluaciones completadas** (`iper_views.py:524`) y el botón se
  oculta: hay que reabrir como borrador para versionar, al revés del diseño.
- El clon no copia `is_anonymous`.
- Duplicar: las observaciones copiadas quedan con el usuario que duplica como autor, y `responsible`
  es `request.user` y no el responsable del lab destino.

## 6. Tests faltantes

- **Duplicar** (`iper_duplicate`): no completada → 400; GET → 405; copia con versión 1 y sin
  `previous`; copia hazards, `related_shelfobjects` y observaciones; crea `IPERConfig` si falta;
  original intacto; `actions.duplicate` en la API solo para completadas.
- Observaciones, solicitud por zona, alta de catálogo (raíz vs. hija), charts del dashboard,
  gating por permisos, toggle de estado.

## 7. Decisiones abiertas

1. ¿Una versión nueva sale de una evaluación **completada** (diseño) o solo de un borrador (código)?
2. ¿Los gráficos incluyen orgs hijas y solo la última versión por lab?
3. ¿Cómo deduplicar recordatorios (una `PendingTask` abierta por lab/período)? ¿Avisar a labs sin IPER?
4. ¿La solicitud por zona crea un borrador con `source=zone_request` o solo la tarea?
5. ¿La matriz se edita en el admin de Django o en una pantalla de org raíz?
6. ¿Rol formal "Analista de Riesgo" o bastan Auditor/Administrador IPER?
7. Al duplicar: ¿conservar autor original de observaciones y usar el responsable del lab destino?

## Referencias

- `src/presentation/features/riskmanagement.py:210` apunta `doc="plans/IPER_DESIGN.md"` (borrado);
  actualizar la referencia cuando se toque ese código.
- Catálogos INTE T55 (categorías, P, C, matriz, acciones): fuente de verdad en `iper_defaults.py`.
