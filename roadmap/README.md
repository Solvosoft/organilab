# Roadmap — Organilab sobre djgentelella 0.6.0

Rama de trabajo: `dj060`. Biblioteca: checkout `~/Desktop/desarrollo/django-gentelella-widgets`,
rama `development` (instalación editable durante el desarrollo; mecanismo de CI pendiente de decidir).

**Entorno:** venv `~/entornos/organilab`. OJO: una reinstalación desde requirements puede pisar
la editable con la djgentelella de PyPI (pasó el 2026-08-29: faltaba `djgentelella.async_notification`,
que solo existe en 0.6.0); se restaura con `pip install -e ~/Desktop/desarrollo/django-gentelella-widgets`.

| Etapa | Documento | Contenido | Riesgo | Estado |
|---|---|---|---|---|
| 0 | `00_ANALISIS_DJGENTELELLA_060.md` + `BASELINE.md` | Análisis de la biblioteca, baseline de pruebas (891/891 OK), backups | — | hecha |
| — | `INVENTARIO_VISTAS.md` | Impacto vista por vista (métrica de cambios) | — | hecho |
| 1 | `01_ETAPA_LIMPIEZA.md` | Limpieza compatible con 0.5.9 (alias, blog, DataTables vendorizado, tests perdidos) | bajo | hecha |
| 2 | `02_ETAPA_DJANGO_AJAX.md` | django_ajax: dependencia asumida + JS vendorizado (salida total → etapa 10) | medio | hecha |
| 3 | `03_ETAPA_ASYNC_NOTIFICATION.md` | Correos → djgentelella.async_notification (+ salida de markitup) | **alto** | hecha |
| 4 | `04_ETAPA_SUBIDA_060.md` | Instalación 0.6.0 (editable, adelantada a la 3), migraciones, arranque | medio | hecha |
| 5 | `05_ETAPA_ICHECK.md` | iCheck/switchery → inputs nativos | **alto** | hecha y validada |
| 6 | `06_ETAPA_DATATABLES2.md` | DataTables 1→2 (dom→layout, clases, hook selenium) | **alto** | hecha y validada |
| 7 | `07_ETAPA_CHARTJS4.md` | Chart.js 2→4 (+ fix genérico min/max en la lib) | medio | hecha |
| 8 | `08_ETAPA_OVERRIDES.md` | Overrides de la lib: 11 borrados, sidebar/navbar adaptados | medio-alto | hecha |
| 9 | `09_ETAPA_AJUSTES.md` | TinyMCE 8, recordsTotal, moment locale, misc | bajo | hecha |
| 10 | `10_ETAPA_MODERNIZACION.md` | Modales, formularios y tablas a mano → widgets (completa) | medio | hecha — 10a/10b/10c/10d ejecutadas; diferidos como proyectos aparte: labview (salida total de django_ajax) e history/Trash |
| 11 | `11_ETAPA_SELENIUM.md` | Mejoras menores de la infraestructura selenium | bajo | hecha — 3 tests rescatados en verde (30/30), bugs de producto corregidos de paso |
| 12 | `12_ETAPA_VALIDACION.md` | Validación final completa | — | hecha salvo smoke manual — unit 902/902, selenium ≈213/213, lint 0, migrate limpio |
| 13 | `13_HISTORY_TRASH.md` + `13D_FASE_D_PAPELERA.md` | history/Trash: relaciones + extras JSON y papelera org-scoped (proyecto diferido de la 10) | medio | hecha y cerrada (2026-08-30) — fases A, B y C, más limpieza de residuos y el arreglo de la fuga de papelera del `ProtocolViewSet`; la fase D queda diseñada, sin implementar |
| 14 | `14_ETAPA_LABVIEW.md` + `14_ARQUITECTURA_LABVIEW.md` + `14_labview_prototipo.svg` | labview: mapa digital del laboratorio sobre API, overlay de riesgo y salida total de django_ajax (proyecto diferido de la 2 y la 10) | **alto** | en curso — F0 (documentación y prototipo) hecha |

## Cambios hechos a djgentelella durante la migración (para su changelog/release)

Los cambios 1-4 quedaron sin commitear al cierre de la etapa 12; los del proyecto 13
(ítems 5 y 6) ya están commiteados en el checkout `development` (`ba63783`, `7645a4e`,
`94a568d`); su entrada de `CHANGELOG.rst` y sus 9 traducciones al español se
escribieron después (2026-08-30) y siguen sin commitear.

1. **`chartjs.py` + `tests/ChartJS_Test.py`** (etapa 7): fix genérico min/max de ejes —
   los valores configurados se propagan a Chart.js 4 (antes se perdían). Con test.
2. **`static/gentelella/js/obj_api_management.js`** (etapa 10c): `do_action()` soporta
   **acciones de navegación** en `object_actions` — `link: true` hace
   `window.location.assign(url)` en vez de fetch (caso "abrir la página de detalle de la
   fila"). Probado en el demo: `object_management.html` reemplazó su columna "Notes" con
   `<a>` a mano por una object_action `link:true`.
3. **`templates/forms/as_horizontal.html` y `as_plain.html`** (etapa 11): el help_text se
   rendía en `div.valid-feedback` (Bootstrap lo oculta salvo validación) → cualquier
   contenido interactivo embebido en help_text quedaba invisible. Ahora `div.form-text`
   (siempre visible, la clase correcta de BS5 para help).
4. **`chartjs.py` `get_data()`** (etapa 12): invocaba `get_datasets()` antes que
   `get_labels()`, invirtiendo el contrato histórico del que dependen las subclases
   (suelen calcular las series en `get_labels()`). Reordenado, con test de orden en
   `ChartJS_Test` (20/20).
5. **history/Trash (proyecto 13, fases A)**: nuevo modelo `HistoryRelation`
   (relaciones N por LogEntry + JSON `data`, migración 0019) con admin; `add_log`
   retorna el LogEntry y acepta `related_objects`/`extra` + centinela
   `GT_HISTORY_ANONYMOUS_USERNAME` (y ya no pisa un change_message custom en DELETE);
   `HistoryViewSet` con `scope_queryset()`, filtros `related_contenttype`/`related_id`
   y `extra` (1..n claves JSON), `recordsTotal` scoped y fix del TypeError sin
   `GT_HISTORY_ALLOWED_MODELS`; `BaseViewSetWithLogs` reparado (`models_log`
   inexistente → allowlist coherente, `delete(user=)`, `perform_update` por `source`,
   hooks + metadatos de request); Trash: restore vía `get_object()` (scoped),
   huérfanos 410/borrables, logs con el modelo real, permisos alineados, filtro
   `deleted_by`, bulk `delete(user=)` con filas Trash; `__init__.py` en history/ y
   trash/; docs ampliadas; demo sin override de `perform_destroy`. Tests:
   `History_Test.py` nuevo + `Trash_Test.py` ampliado.
6. **history/Trash (proyecto 13, fase C — papelera)**: nuevo modelo
   **`TrashRelation`** (contexto del borrado: FK Trash + GenericFK, migración
   0020) con admin; `DeletedWithTrash.delete(..., related_objects=)` y el
   `delete()` de queryset registran ese contexto (instancias solamente, pk
   pelado → ValueError; el primer borrado gana); `TrashViewSet` gana
   `scope_queryset()` (acota list/restore/destroy y recordsTotal) y los
   params `related_contenttype`/`related_id`; demo `Customer.delete` reenvía
   `**kwargs`; docs `trash.rst` con la sección multi-tenant; `Trash_Test.py`
   +8 tests.

Ya venían de etapas previas y quedaron registrados en su documento de etapa; los cambios
anteriores del checkout (rama `development`) se commitean en el repo de la lib con su
propio changelog.

## Principios

1. **djgentelella es genérica**: los arreglos que le hagamos van al checkout SIN conocimiento de
   organilab (con prueba en su demo). Lo específico de organilab (org-scope, multi-tenant) se
   implementa en organilab como subclases/configuración. Registrar cada cambio hecho a la
   biblioteca en la sección "Cambios en djgentelella" del documento de la etapa.
2. **Pruebas**: baseline antes de tocar; por etapa solo los tests del área
   (`make single-test` / `make test-selenium-single-fast TEST=...`); la corrida completa
   (unit + selenium, 1-2 h) UNA sola vez al final (etapa 12).
3. Cada etapa actualiza su documento (estado, hallazgos, desvíos) al cerrarse.
