# Baseline de pruebas — antes de la migración

**Fecha:** 2026-08-29 · **Rama:** `dj060` (== punta de `predevelopment`, commit `f10d482c`)

## Entorno del baseline

- `.venv` con **djgentelella 0.6.0 snapshot viejo (rama `cleanup`)**: aún contiene
  `cruds/inline_crud.py`, vendors iCheck/flag-icon-css, y NO contiene `async_notification`.
- Instalados aparte (transitivas del 0.5.9 histórico): `django-markitup 4.1.0`, `djangoajax 3.3`,
  `async_notifications 0.2`, `Markdown 3.10`.
- Es decir: el punto de partida ya es un híbrido pre-"Unreleased"; el salto pendiente es al
  checkout `development` (`d7bc6f9`).

## Resultado

```
make test   (manage.py test --no-input --exclude-tag=selenium, settings=organilab.test_settings)
Found 891 test(s).
Ran 891 tests in 113.735s
OK
```

**891/891 en verde. Cualquier fallo que aparezca durante la migración es nuestro.**

Ruido esperado en la salida (no son fallos): mensajes de comandos de mantenimiento
(`clean_orphaned_profilepermissions`, indicaciones de peligro, frases de prudencia) y prints de
notificaciones (`['sitio@organilab.org'] ###...`).

## Selenium

No corrido como baseline global (1-2 h). Estrategia: baseline puntual por etapa de riesgo
(manage_organizations antes de la etapa 5; una pantalla con tabla antes de la etapa 6) usando
`make test-selenium-single-fast TEST=...`. Corrida completa una sola vez en la etapa 12.

Dato de las notas de memoria del proyecto: con `--parallel`, un fallo con excepciones encadenadas
aborta la suite entera si no está `tblib` instalado; y `--keepdb` deja la BD selenium sin permisos
(loaddata revienta en setUpClass). Preferir corridas sin `--keepdb` y considerar añadir `tblib`.

## Validación tras las etapas 1-9 (2026-08-29, misma sesión)

| Corrida | Resultado |
|---|---|
| `make test` (unit, con djgentelella `development` editable) | **891/891 OK** (idéntico al baseline) |
| Selenium `manage_organizations` (sensible a iCheck/DataTables/permisos) | **28/28 OK** |
| Selenium `capacitacion` (navegación completa por el menú nuevo) | **40/40 OK** |
| Tests de djgentelella (`ChartJS_Test`, con el fix genérico min/max) | **19/19 OK** |
| `make trans` | OK (estaba ROTO en el repo: 9 msgids duplicados pre-existentes en `djangojs.po` es, deduplicados con msguniq) |
| `make lint` | 41 avisos, todos pre-existentes (mismo resultado con y sin estos cambios) |

Los `.po` se regeneraron con `make messages` (no se corría desde 2024-07: el diff grande es la
re-extracción atrasada, convención del propio Makefile con `--no-obsolete`).
Pendiente de la etapa 12: suite selenium COMPLETA (1-2 h) y smoke manual.
