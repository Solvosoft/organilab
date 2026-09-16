# Administración de plataforma — pendientes

> **Qué es esto.** Seis funciones transversales: bitácora consultable (A), justificación de cambios
> (B), parámetros por organización (C), notificaciones administrables (D), alertas configurables (E)
> y ayuda en línea (F). Resumen de lo que falta; la versión larga con los flujos de interacción está
> en git (antes del 2026-09-16). Viene de [`SIGMA_GAP_ANALYSIS.md`](SIGMA_GAP_ANALYSIS.md).
> [`MANAGEMENT_PLANS_PLAN.md`](MANAGEMENT_PLANS_PLAN.md) y [`ENVIRONMENT_PLAN.md`](ENVIRONMENT_PLAN.md)
> dependen de B, C y E.
>
> **Estado:** paso 0 (djgentelella 0.6.0) hecho. A y D parciales. B, C, E y F sin empezar.

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

## C. Parámetros del sistema por organización — NO INICIADO

- `SystemParameter(AbstractOrganizationRef)`: `key`, `description`, `data_type`
  (int/float/bool/str/date/json), `raw_value`, `is_editable`; `unique_together (organization, key)`;
  `clean()` valida tipo, `value` castea.
- `get_parameter(org, key, default)` en `presentation/utils.py`: org → ancestros → `settings`, con
  caché por request.
- Registro declarativo por app en `presentation/parameters.py` (análogo a `REPORT_FORMS`).
- Pantalla `/perms/<org_pk>/parameters/`: columna **Origen** (propio / heredado / defecto), edición en
  línea por tipo, "Restaurar valor heredado".
- `IPERConfig` queda como está.

## D. Notificaciones administrables — PARCIAL

**Hecho:** procesos registrados con `register_context` (`laboratory/apps.py:10-47`,
`authentication/apps.py:8`); envío con `send_email_from_template`. La UI (`EmailTemplate`, árbol de
variables, preview, TinyMCE) la trae la biblioteca.

**Falta:**
- `NotificationSetting(AbstractOrganizationRef)`: `code`, `is_active`, `override_subject`,
  `override_message` (la plantilla de la lib es global).
- `presentation.utils.send_process_email(org, code, context, recipients)` que aplique estado y
  overrides y delegue en la lib.
- Entrada de menú de administración a la pantalla de plantillas.
- Registrar los procesos que aún no lo estén.

## E. Alertas configurables — NO INICIADO

- `AlertRule(AbstractOrganizationRef)`: `process` (código de `register_context`), `trigger`
  (`Catalog key="alert_trigger"`), `threshold` JSON, `notification_code`, `notify_roles` M2M `Rol`,
  `notify_responsible`, `create_task`, `is_active`.
- Pantalla `ObjectCRUD` + `BaseViewSetWithLogs` con asistente de 3 pasos (qué vigilar / cuándo / a
  quién) y pestaña de historial de disparos.
- Al disparar: `send_process_email()` + `create_pending_task()` + `create_notification()` si amerita.
- Migrar **primero solo** el vencimiento de `ShelfObject` (`laboratory/limit_shelfobject.py`); las
  demás tareas de `CELERYBEAT_SCHEDULE` después, una por una con test.

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
