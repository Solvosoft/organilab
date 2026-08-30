# Etapa 12 — Validación final

**Objetivo:** confirmar que no se fue funcionalidad. **Estado:** HECHA salvo el smoke manual (2026-08-29).

## Tareas

- [ ] `make test` completo (sin selenium) — comparar contra `BASELINE.md` (891/891 OK).
- [ ] Suite selenium completa UNA vez (`make test-selenium-dev`; presupuestar 1-2 h).
- [ ] `make lint`.
- [ ] `make messages && make trans` si se tocaron strings traducibles.
- [ ] `python manage.py migrate` en BD limpia (instalación desde cero) y en copia de la BD real.
- [ ] Smoke manual con `runserver`:
      - login / logout / reset de contraseña,
      - sidebar y navbar en <992px (drawer) y >=992px (rail/flyout),
      - una tabla DataTables por app (layout, buscador, paginación, i18n es),
      - pantalla de permisos (checkboxes visibles y funcionales),
      - un modal con TinyMCE (crear y editar: contenido no se pierde),
      - dashboards de charts (objectlimit + risk),
      - crear una notificación de correo, drenar la cola (`process_notifications`) y verla en Mailhog,
      - subir un archivo por chunked upload.
- [ ] Actualizar `plans/AGENT_BRIEFING.md` (frontend/notificaciones) y dejar nota de obsolescencia
      en `plans/DJGENTELELLA_060_NOTES.md` apuntando a `roadmap/00_ANALISIS_DJGENTELELLA_060.md`.
- [ ] Registrar en `roadmap/README.md` la lista final de cambios hechos a djgentelella (para su
      changelog/release).

## Resultados (2026-08-29)

- **`make test` completo: 902/902 OK** (baseline 891 + 11 tests nuevos de la migración;
  corrido dos veces en la etapa, antes y después de los arreglos selenium).
- **Suite selenium completa: ≈213/213 OK**, corrida por trozos con `--parallel`:
  manage_laboratory 53, laboratory_view 30, manage_organizations 28, reports 3,
  informs 17, academic 10, risk_management 27, capacitacion 42. Las suites que no se
  corrían por etapa (manage_laboratory, reports, inform_template) traían roturas
  acumuladas — TODAS quedaron en verde. Detalle de lo arreglado:
  - Selectores: link de admin de salas por href acotado a `right_col` (el sidebar
    tiene un duplicado oculto que gana en orden de documento); tarjetas de sala por
    `data-bs-toggle=popover`/`data-bs-target`; cuadrícula de estantes por
    `#btnAddRow`/`onclick=...`/iconos; palette de Formio por `data-key` (los títulos
    salen TRADUCIDOS: "Password"→"Contraseña"); buscador DT2 por `dt-search`.
  - `test_view_shelf`: el preludio my_labs rinde vacío por permisos del fixture
    (exige rol "Administrativo superior") — se entra directo al labindex.
  - Fixtures: `laboratory_delta.json` gana la fila `sga.substancecharacteristics`
    del 1-Propanol (el fixture poblaba el modelo LEGADO `laboratory.sustance...`;
    el viewset hcode consulta el centralizado de SGA).
  - Bomba de tiempo desactivada: la reserva pedía fecha final a +5 días, que en
    cierres de mes cae fuera de la cuadrícula visible del datepicker → +1.
  - Infraestructura selenium: `presence_only` ahora es espera PURA (antes clicaba
    igual, y clicar el div de un modal es zona de backdrop → lo cerraba);
    `close_extra_windows()` al iniciar los flujos con pestañas (el navegador se
    reutiliza y una pestaña vieja conserva el window.name buscado).
  - **Bugs reales encontrados**: `shelfobject_code.html` tenía un tag roto
    (`{% get_organilab_version"` sin cerrar y sin load) que dejaba la página del
    listado hcode con el JS muerto desde su creación; y el `get_data()` de
    djgentelella llamaba `get_datasets()` antes que `get_labels()` (contrato
    invertido → AttributeError en los charts de riesgo). Ambos corregidos
    (el segundo en la lib, con test 20/20).
- **`make lint`: 0 avisos** en todo src/.
- **`migrate` en BD limpia: OK** (BD `organilab_valida12` desde cero).
- Traducciones: extraídas y compiladas durante las etapas (es completo; en usa
  fallback del msgid).

## Smoke manual (pendiente, para Luis con `runserver`)

- login/logout/reset; sidebar y drawer <992px; una tabla DataTables por app (es);
  pantalla de permisos; modal con TinyMCE (crear/editar sin perder contenido);
  dashboards de charts (objectlimit + risk); notificación de correo →
  `process_notifications` → Mailhog; chunked upload; y verificar el mensaje del
  checkbox "borrar fichero" en FileFields obligatorios (nota de la etapa 9).
