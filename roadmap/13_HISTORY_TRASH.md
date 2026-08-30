# Proyecto history/Trash — estado y traspaso (2026-08-30)

Plan aprobado completo en `~/.claude/plans/vamos-a-revisar-roadmap-composed-cookie.md`
(fases A/B/C con decisiones de Luis). Este documento es el traspaso operativo.

## Decisiones ya tomadas por Luis (NO re-preguntar)

- `LabOrgLogEntry` se migró y DROPEÓ en el mismo cambio (hecho).
- Logs sin usuario autenticado → setting `GT_HISTORY_ANONYMOUS_USERNAME` de la lib;
  organilab la apunta al centinela `DELETED_USER_SENTINEL_USERNAME` (hecho).
- Extras por entrada: JSONField filtrable por 1..n campos + metadatos del request
  (navegador/IP/método/ruta) capturados automáticamente (hecho).
- Pilotos de papelera (Fase C): **Protocol y Procedure**; los flags booleanos
  artesanales NO se migran en esa fase.

## HECHO — Fase A (lib, checkout `~/Desktop/desarrollo/django-gentelella-widgets`, SIN commitear)

- `djgentelella/models.py`: modelo **`HistoryRelation`** (FK LogEntry
  `related_name='gt_relations'` + GenericFK nullable + `data` JSONField +
  CheckConstraint + índice ct/object_id) y migración `0019_historyrelation`.
  `Trash.hard_delete` borra filas huérfanas (con fallback sin mixin).
- `djgentelella/history/utils.py`: `add_log(..., related_objects=None, extra=None)
  -> LogEntry` (retorna; instancias o tuplas `(inst, data)`; pk pelado → ValueError;
  anónimo → centinela por setting o ValueError claro; un change_message custom en
  DELETE ya NO se reemplaza).
- `djgentelella/history/api.py`: `BaseViewSetWithLogs` con `models_log`
  (None=todo, lista `app.model`), `perform_destroy` sin el AttributeError y con
  `delete(user=)` para `DeletedWithTrash`, `perform_update` robusto (fields por
  `source`), hooks `get_log_related_objects`/`get_log_extra` + metadatos request
  (`log_request_metadata=True`). `HistoryViewSet` con `scope_queryset()` overridable,
  params `related_contenttype`/`related_id`, `recordsTotal` scoped, fix del
  TypeError sin `GT_HISTORY_ALLOWED_MODELS`.
- `djgentelella/history/filterset.py`: filtro `?extra={"k":v,...}` — 1..n claves
  encadenadas sobre la MISMA fila de relación (portable a SQLite).
- `djgentelella/history/serializers.py`: `get_actions` overridable +
  `HistoryRelationsMixin` (expone relations/extra).
- `djgentelella/trash/`: restore vía `self.get_object()` (respeta subclases
  scoped), huérfano→410, logs con el modelo real, permisos restore alineados a
  `change_trash`, filtro `deleted_by`; `models_manager.py`: `.delete(user=)` de
  queryset crea filas Trash.
- Admin de HistoryRelation; `__init__.py` en history/ y trash/; docs
  (`docs/source/history.rst`, `trash.rst`) ampliadas; demo `CustomerViewSet` sin
  override (usa `get_log_extra`).
- Tests: `djgentelella/tests/History_Test.py` (nuevo) + `Trash_Test.py` ampliado.
  **Estado: lib+demo 371 tests, todo verde salvo 1 flake ajeno de DataTables
  (pasa solo).**

## HECHO — Fase B (organilab, rama dj060, SIN commitear)

- `src/laboratory/utils.py`: `organilab_logentry` es puente sobre `add_log`
  (firma y TEXTOS idénticos; `relobj` pk → Laboratory con DeprecationWarning;
  `find_rel_object` typo arreglado y navegación de reservedproducts corregida a
  `shelf_object.in_where_laboratory`); `get_logentries_org_management` reescrita
  sobre HistoryRelation (candidata a borrar, ver pendientes).
- Migración `laboratory/0221_delete_laborglogentry` (copy 1:1 → HistoryRelation,
  reversible, + DeleteModel). Referencias actualizadas: `admin.py`,
  `merge_organizations.py`, exclude-list de borrado de laboratorio
  (`views/laboratory.py` → "HistoryRelation"), `sga/tests/test_substance_flow.py`.
- 8 call sites con relobj-pk-de-org corregidos: flujo QR ahora pasa
  `relobj=[org, qr_obj]` (views/laboratory.py) y academic `add_steps_wrapper`
  pasa la instancia.
- `src/laboratory/api/views.py`: `LogEntryViewSet` ahora subclasea el
  `HistoryViewSet` de la lib con `scope_queryset` por join `gt_relations`
  (org + labs vía Subquery, sin pk__in en memoria), recordsTotal scoped, y la
  rama QR filtra por RELACIÓN al RegisterUserQR (no por change_message
  traducido). `LogEntryUserSerializer.get_user` arreglado; `views/logentry.py`
  con login + `user_is_allowed_on_organization`.
- `settings.py`: `GT_HISTORY_ANONYMOUS_USERNAME = DELETED_USER_SENTINEL_USERNAME`.
- Fixtures convertidos: capacitacion/organization_manage (filas laborglogentry →
  historyrelation) e initial_data/initialdata (contenttype+permisos huérfanos
  fuera).
- Tests nuevos `src/laboratory/tests/test_logentry_history.py` (8): puente,
  textos idénticos, pk-con-warning, ANTI-FUGA 2 orgs (data y recordsTotal),
  rama QR por relación, regresión del centinela.
- **Estado: suite unit completa 910/910 OK** (902 previos + 8 nuevos; la
  creación del test DB valida las migraciones 0019+0221).

## PENDIENTE (en orden)

1. ~~Humo selenium~~ HECHO: register_users + manage_organizations + capacitacion
   **74/74 OK** con el viewset nuevo.
2. ~~Lint global~~ HECHO: 0 avisos.
3. ~~Roadmap README~~ HECHO (ítem 5 de "Cambios en djgentelella").
4. ~~Commit de organilab~~ HECHO (ver git log). Los cambios de la lib siguen sin
   commitear en su checkout (los commitea Luis con su changelog).
5. ~~get_logentries_org_management~~ HECHO: eliminada (0 llamadores).
6. Traducciones: la lib ganó strings nuevos (mensajes de restore/errores) — se
   compilan en el repo de la LIB, no en organilab; organilab no ganó strings.
7. Menor preexistente: `makemigrations --check` acusa deriva en
   `report/0009_alter_taskreport_language` (default desde settings) — decidir
   aparte, no es de este proyecto.
8. **FASE C (papelera, NO iniciada)**: pilotos Protocol + Procedure con
   `DeletedWithTrash`; scope multi-tenant del Trash con el mismo patrón
   (`TrashRelation` FK Trash + GenericFK, poblado desde
   `delete(user=..., related_objects=...)`, `scope_queryset` en subclase de
   `TrashViewSet`); pantalla org-scoped basada en el demo
   (`demo/demoapp/templates/gentelella/trash/trash.html`). Diseño fino en el
   plan aprobado.

## Verificación al cerrar

- Lib: `cd demo && python manage.py test djgentelella.tests` (venv
  `~/entornos/djgentelella`).
- Organilab: suite unit completa (base 910) + selenium de logentry (org y QR:
  `manage_laboratory.test_register_users`, `manage_organizations`) — venv
  `~/entornos/organilab`, correr selenium con
  `GENERATE_SCREENSHOTS=False xvfb-run -a ...`.
- OJO entorno: la lib debe estar instalada EDITABLE en `~/entornos/organilab`
  (una reinstalación desde requirements la pisa; `pip install -e` la restaura).
