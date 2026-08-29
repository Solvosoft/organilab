# Etapa 4 — Subida oficial a 0.6.0 (arranque)

**Objetivo:** el entorno de trabajo corre el checkout `development` completo (no el snapshot viejo
de `cleanup` que hay hoy en el venv) y organilab arranca y migra.
**Estado: HECHA (2026-08-29) — se adelantó a la etapa 3** porque `djgentelella.async_notification`
no existe en el snapshot viejo: sin el swap, la etapa 3 no podía ni importarse.

## Resultado

- `pip install -e ~/Desktop/desarrollo/django-gentelella-widgets` (bundles ya generados en el
  checkout el 28-ago; no hizo falta `make loadstatic/basejs/assets`).
- `manage.py check`: OK. Suite completa ANTES de la etapa 3: **889/891** — los únicos 2 fallos
  fueron `risk_management.tests.test_incident` (asserts que codificaban el bug viejo de
  `recordsTotal`; corregidos a la semántica nueva: cuenta el queryset filtrado por URL).
- Los paquetes viejos (`django-markitup`, `async-notifications`) se desinstalaron en la etapa 3.

## Contexto

El `.venv` tiene un 0.6.0 viejo (rama `cleanup`: aún con `inline_crud.py`, iCheck, sin
`async_notification`) más `django-markitup`/`djangoajax` instalados aparte. Decisión: instalación
**editable local** por ahora; CI se decide después (no bloquear).

## Tareas

- [ ] En el checkout: `make loadstatic && make basejs && make assets` (en ese orden — `assets` sin
      `basejs` previo no escribe nada y no avisa).
- [ ] `pip uninstall djgentelella django-markitup djangoajax async-notifications` +
      `pip install -e ~/Desktop/desarrollo/django-gentelella-widgets[firmador,celery]`.
- [ ] `requirements.txt:1`: anotar (comentario) que el release requiere djgentelella>=0.6.0
      publicado; mientras tanto editable. NO subir el pin todavía si rompe CI.
- [ ] Verificar migraciones que referencian la lib:
      `sga/migrations/0066` (dep `djgentelella.0017_alter_chunkedupload_status` — ¿sigue existiendo?),
      `auth_and_perms/migrations/0014` (MenuItem, dep `0010_menuitem_position`),
      `presentation/migrations/0005` (ruta `djgentelella.notification.widgets.NotificationMenu`).
- [ ] `python manage.py check` + `migrate` (BD de desarrollo y BD limpia) + `collectstatic`.
- [ ] Smoke: `runserver`, login, home, una lista con DataTable (aunque esté fea hasta la etapa 6).
- [ ] Documentar en README/Makefile cómo instalar para desarrollar.

## Pruebas

- `make test` (sin selenium) — se esperan fallos de las áreas de etapas 5-8 (anotarlos como
  "pendiente de etapa N" en este documento), pero NO fallos nuevos en áreas sin relación.

## Notas / hallazgos

(al cerrar la etapa)
