# Administración de plataforma — pendientes

> **Qué es esto.** Seis funciones transversales: bitácora consultable (A), justificación de cambios
> (B), parámetros por organización (C), notificaciones administrables (D), alertas configurables (E)
> y ayuda en línea (F). Resumen de lo que falta; la versión larga con los flujos de interacción está
> en git (antes del 2026-09-16). Viene de [`SIGMA_GAP_ANALYSIS.md`](SIGMA_GAP_ANALYSIS.md).
> [`MANAGEMENT_PLANS_PLAN.md`](MANAGEMENT_PLANS_PLAN.md) y [`ENVIRONMENT_PLAN.md`](ENVIRONMENT_PLAN.md)
> dependen de B, C y E.
>
> **Estado:** paso 0 (djgentelella 0.6.0) hecho. C, D y E hechos en la rama `regenteambiental`. A parcial. B y F sin empezar.

**Principios que se mantienen:** sin app nueva (ayuda/config en `presentation`, bitácora/justificación
en `laboratory`); la bitácora sigue sobre `django.contrib.admin.LogEntry` + `HistoryRelation`, se amplía
la consulta y no la captura; justificación opt-in por modelo; catálogos con `Catalog` +
`djgentelella.fields.catalog.GTForeignKey`; correos con `djgentelella.async_notification`; borrado
lógico con `DeletedWithTrash`.

---

## A. Bitácora de auditoría — PARCIAL

**Hecho:** `LogEntryViewSet(HistoryViewSet)` acotado por org + sus labs con `recordsTotal` correcto
(`src/laboratory/api/views.py:338`); papelera `OrganizationTrashViewSet` + `trash_list`; tests
`test_logentry_history.py`, `test_trash.py`.

**Falta:**
- Extender el alcance a **organizaciones descendientes** (`TreeNode`).
- Permiso `laboratory.view_full_audit_log` (hoy `views/logentry.py` no exige permiso; `a8f5558f0` lo
  dejó así a propósito — ver decisiones).
- Filtro por módulo/tipo: `content_type__app_label` / `content_type__model` en `LogEntryFilterSet`
  (`api/filterset.py:111`) + selector `GTForm` con apps etiquetadas en español.
- **Valor anterior → nuevo:** `get_field_diffs(old_values, instance)` en `laboratory/utils.py`;
  `organilab_logentry()` serializa `[{"changed": {"fields": [...], "diffs": {...}}}]` (sin tocar las
  ≈280 llamadas). Serializer que exponga `diffs` y `justification`.
- Pantalla: badge de color por acción, panel lateral antes/después, últimos 30 días por defecto.
- Botón "Ver historial" en registros = bitácora pre-filtrada.
- Exportación `report_audit_log` en `report/register.py` (`html/pdf/xls/xlsx/ods`), form en
  `report/forms.py`, vista `report/views/audit.py` clonada de `object_changes.py`.
- Tests: cobertura multi-app, diffs en serializer, exportación.

## B. Justificación de cambios sensibles — NO INICIADO

- Modelo `ChangeJustification(log_entry OneToOne admin.LogEntry, justification, affected_records)`.
- `JustifiedUpdateMixin` en `laboratory/views/djgeneric.py`: la vista implementa
  `get_dependents(obj)`; si hay dependientes, exige justificación, crea `ChangeJustification` tras
  `organilab_logentry` y lanza `create_pending_task()` a los responsables afectados.
- Endpoint `…/dependents/` → `{"count", "detail"}` para el modal (si es `@action`, declararlo en `perms`).
- Aplica a parámetros (C), alertas (E) y programas/ejes/componentes/acciones. **No** a inventario.

## C. Parámetros del sistema por organización — HECHO (rama `regenteambiental`)

- `presentation.models.SystemParameter` guarda solo el valor propio (`key`, `raw_value`); tipo,
  valor por defecto, textos y permiso para cambiarlo los declara `presentation/parameters.py`
  (`PARAMETERS`).
- `get_parameter(org, key, request=None)` / `resolve_parameter`: org → ancestro más cercano →
  defecto (no lee `settings`), con caché por petición.
- Pantalla `/platform/<org_pk>/parameters/` (namespace `platform`, no `/perms/`): columna Origen y
  «Restaurar valor heredado»; se edita el valor como texto (sin widget por tipo). Solo lista los
  parámetros cuyo permiso tiene el usuario.
- **Pendiente:** registrar parámetros de otras apps; `IPERConfig` sigue como está.

## D. Notificaciones administrables — HECHO (rama `regenteambiental`)

- `presentation.models.NotificationSetting` (`code`, `is_active`, `override_subject`,
  `override_message`), heredable a organizaciones hijas.
- `presentation.notifications.send_process_email(org, code, context, recipients)` (en
  `notifications.py`, no en `utils.py`).
- Pantalla `/platform/<org_pk>/notifications/` con los procesos registrados y enlace a las
  plantillas globales de la biblioteca.
- **Pendiente:** registrar los procesos que aún no lo estén y que los envíos existentes
  (`send_email_from_template` directo) pasen por `send_process_email`.

## E. Alertas configurables — HECHO (rama `regenteambiental`)

- `presentation.models.AlertRule` + `AlertEvent` (historial de disparos); disparadores sembrados en
  `Catalog key="alert_trigger"`.
- `presentation/alerts.py`: las apps registran sus procesos (`register_alert_process`, con evaluador,
  disparadores válidos y permiso), `fire_alert` (evento + `send_process_email` + tarea pendiente +
  campana si es crítica) y `run_alert_rules`.
- Pantalla `/platform/<org_pk>/alerts/` con pestañas de reglas e historial (formulario único en vez de
  asistente de 3 pasos).
- Primer proceso: `ambiental.consumption` ([`ENVIRONMENT_PLAN.md`](ENVIRONMENT_PLAN.md)).
- **Pendiente:** migrar el vencimiento de `ShelfObject` (`laboratory/limit_shelfobject.py`) y las
  demás tareas de `CELERYBEAT_SCHEDULE`, una por una con test.

## F. Ayuda en línea — NO INICIADO

- Manual con video: agregar `video_url` y `section` a `Tutorial` (`presentation/models.py:79`) y
  `video_url` a `TutorialStep`; listado por capítulo filtrado por rol con botón "Hacerlo paso a paso".
- `FAQ(AbstractRegistry, DeletedWithTrash)`: `question`, `answer` (TinyMCE), `category`
  (`Catalog key="faq_category"`), `order`, `target_roles`; CRUD + página `/faq/` con búsqueda.
- Vista `about`: versión leída de `src/organilab/__init__.py`, textos como `SystemParameter`.
- (De SIGMA) expiración de sesión configurable: no hay `SESSION_COOKIE_AGE`.

---

## Orden

| Paso | Entregable | Depende de |
|------|-----------|-----------|
| 1 | A: descendientes + filtro por módulo + diffs + permiso | — |
| 2 | A: exportación + "Ver historial" | 1 |
| 3 | C: `SystemParameter` + registro + pantalla | — |
| 4 | B: justificación + modal | 1 |
| 5 | F: FAQ + Acerca de + video | — |
| 6 | D: `NotificationSetting` + `send_process_email` + menú | 3 |
| 7 | E: `AlertRule` + asistente + migrar vencimientos | 6 |

1–2, 3 y 5 son paralelizables.

## Decisiones abiertas

- `video_url`: URL o `FileField`.
- Menús: parciales en `presentation/templates/partials/` o `MenuItem` (aplica a todo el proyecto).
- Qué modelos declarar en `GT_HISTORY_ALLOWED_MODELS` (opcional, ya no rompe sin él).
- ¿La bitácora tiene permiso propio y entra al catálogo de roles?
- ¿`IPERConfig` se migra algún día a `SystemParameter`?

## Checklist transversal

- Modelos org-scoped con `AbstractOrganizationRef`; vistas HTML desde `laboratory/views/djgeneric.py`.
- Viewsets `BaseViewSetWithLogs` **con `models_log` declarado** y `perform_destroy` pasando
  `user=self.request.user`; toda `@action` en el dict `perms` (si no, 403).
- `DeletedWithTrash`: formularios excluyen `is_deleted`; borrar con `related_objects=[org, lab]`.
- Permisos en `Meta.permissions` + `load_urlname_permissions` + `update_roles`.
- `gettext` + `make messages && make trans`; tests + `make lint`.
