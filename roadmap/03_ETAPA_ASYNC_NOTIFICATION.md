# Etapa 3 — Correos: async_notifications 0.2 → djgentelella.async_notification (+ salida de markitup)

**Objetivo:** migrar los correos al módulo interno de la biblioteca manteniendo la semántica actual
(cola + drenado programado). Incluye la salida de markitup, cuyos últimos usos son los widgets de
correo. **Riesgo: ALTO. Estado: HECHA (2026-08-29)** — ver "Cómo quedó" al final.

## Decisiones

- Semántica: `enqueued=True` + tarea beat que drena la cola (`process_notifications`), NO envío
  inmediato. Backend: `CeleryBackend` (extra `djgentelella[celery]`).
- La rama `origin/async_notifications` (`b199f51d`) se usa SOLO como mapa (ver
  `00_ANALISIS...md` §9: línea corrupta, prints, deps de migración rotas, contextos comentados,
  DBNAME accidental, cobertura incompleta).

## Tareas

### Settings/urls
- [ ] `settings.py:88` `"async_notifications"` → `"djgentelella.async_notification"`.
- [ ] `ASYNC_NOTIFICATION_BACKEND = "djgentelella.async_notification.backends.celery.CeleryBackend"`.
- [ ] `CELERYBEAT_SCHEDULE`: reemplazar `send_daily_emails` (`async_notifications.tasks.send_daily`,
      settings.py:306) por el drenado de la lib (tarea/comando `process_notifications`) con la misma
      periodicidad.
- [ ] Quitar `ASYNC_NOTIFICATION_TEXT_AREA_WIDGET` (:300), `ASYNC_NEWSLETTER_WIDGET` (:348),
      `MARKITUP_FILTER`/`MARKITUP_SET` (:349-350), `"markitup"` (:91).
- [ ] Evaluar settings de branding: `ASYNC_NOTIFICATION_BASE_TEMPLATES/_BRAND/_BASE_URL/...`.
- [ ] `urls.py:89` quitar `markitup.urls`; `urls.py:91` `async_notifications.urls` →
      `djgentelella.async_notification` con namespace.

### Contextos (update_template_context → registry.register_context)
- [ ] `src/laboratory/apps.py:11-12` — "Shelf object in limit" (+DummyContextObject: existe en
      `djgentelella/async_notification/preview.py`).
- [ ] `src/authentication/apps.py:8` + `views.py:3` — "new user", "New feedback", "Request demo".
- [ ] Contexto de expiring-reactives y lab_or_org_request si lo tienen.
- Firma nueva: `register_context(code, subject, models={alias: 'app.Model'}, exclude=, extra_variables=, depth=2, preview_provider=)`.

### Emisores (verificar firma de send_email_from_template en cada uno)
- [ ] `src/laboratory/signals.py:89` (shelf-object-in-limit)
- [ ] `src/laboratory/tasks.py` (expiring-reactives)
- [ ] `src/laboratory/limit_shelfobject.py` (llamada hoy comentada — reescribir limpia, SIN el
      pegote de la rama vieja)
- [ ] `src/laboratory/lab_or_org_request_notifications.py`
- [ ] `src/presentation/views.py:275` (new-feedback)
- [ ] `src/sga/utils.py:6,25`

### Migraciones
- [ ] Data migrations nuevas que crean cada `EmailTemplate` por `code` con dependencia
      `('async_notification', '0008_...')` o `__latest__` (verificar el nombre real en el checkout).
- [ ] Traspaso de datos: plantillas ya editadas en producción (tablas de async_notifications 0.2)
      → nuevas tablas; documentar el mapping.
- [ ] Neutralizar las 10 migraciones históricas que hacen `apps.get_model('async_notifications',...)`
      para instalación limpia: laboratory 0040-0044, 0171, 0203-0205; authentication 0007.
      (try/except o guard por app instalada; NO reescribir historia aplicada.)

### Tests y requirements
- [ ] `src/sga/tests/test_substance_flow.py:3` — `EmailNotification` del paquete nuevo.
- [ ] `requirements.txt`: quitar `async-notifications==0.2`; evaluar quitar `Markdown==3.10`
      (0 imports propios); NO declarar django-markitup.

## Pruebas

- ANTES de codificar: correr los tests que cubren correos (signals, tasks, substance_flow) y anotar
  comportamiento esperado.
- Después: mismos tests + `migrate` en BD limpia + crear notificación y drenar cola manualmente
  (`process_notifications`) contra Mailhog.

## Cómo quedó (2026-08-29)

- **Settings**: `djgentelella.async_notification` en INSTALLED_APPS (markitup y async_notifications
  fuera); `ASYNC_NOTIFICATION_BACKEND = CeleryBackend`; beat `send_daily_emails` ahora apunta a
  `presentation.tasks.process_email_notifications` (nueva, llama `call_command("process_notifications")`),
  misma periodicidad. Se eliminaron `ASYNC_*_WIDGET`, `MARKITUP_*` y `JQUERY_URL` (era de markitup).
- **URLs**: `async_notification/` → `djgentelella.async_notification.urls` (namespace propio del
  módulo); `markitup/` eliminado.
- **Códigos normalizados a slug** (el campo `code` nuevo es SlugField unique):
  `Shelf object in limit`→`shelf-object-in-limit`, `New feedback`→`new-feedback`,
  `new user`→`new-user`, `Request demo`→`request-demo`, `Expiring reactives`→`expiring-reactives`;
  `lab_or_org_request_*` ya eran válidos.
- **Contextos** con `register_context`: laboratory/apps.py (shelf-object-in-limit,
  expiring-reactives, lab_or_org_request_*), authentication/apps.py (new-user, new-feedback),
  authentication/views.py (request-demo).
- **Emisores activos migrados (4)**: laboratory/signals.py, laboratory/lab_or_org_request_notifications.py,
  presentation/views.py, sga/utils.py (código compartido `lab_or_org_request_created`).
  laboratory/tasks.py tenía un import muerto (eliminado); limit_shelfobject.py conserva su bloque
  comentado, actualizado al import/código nuevos.
- **Hallazgo**: "Expiring reactives", "new user" y "Request demo" NO tienen emisor activo en el
  código actual — son plantillas huérfanas de flujos retirados. Se migran igual (por si se
  rehabilitan) pero no hay código que las envíe.
- **Migraciones**: `laboratory/0219_move_email_templates_to_djgentelella` crea las 7 plantillas
  (update_or_create por code) con defaults horneados desde la BD real; si la tabla vieja
  `async_notifications_emailtemplate` existe, su contenido gana (preserva ediciones de producción).
  Las 10 migraciones históricas quedaron con guard `try/except LookupError` y sin dependencias al
  app label eliminado.
- **Fixtures globales** (`fixtures/initial_data.json`, `initialdata.json`): eliminadas las entradas
  de emailtemplate/templatecontext, los 6 contenttypes y los 24 permisos del app viejo (ningún
  rol/grupo los referenciaba).
- **Tests**: sga/tests/test_substance_flow.py usa el modelo nuevo (`recipients` es JSONField lista:
  filtro `recipients__contains=[email]`).
- **requirements.txt**: fuera `async-notifications==0.2` y `Markdown==3.10` (sin imports propios).
  Paquetes desinstalados del venv.
- **Pendiente de validar en smoke (etapa 12)**: pantallas de plantillas/notificaciones del módulo
  nuevo con un usuario real, drenado contra Mailhog, y branding
  (`ASYNC_NOTIFICATION_BASE_TEMPLATES/_BRAND` quedan sin definir por ahora — correos salen sin
  wrapper, igual que antes).
