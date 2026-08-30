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

## HECHO — Fase A (lib, checkout `~/Desktop/desarrollo/django-gentelella-widgets`; commiteada: `ba63783`)

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

## HECHO — Fase B (organilab, rama dj060; commiteada: `2bbd4568`)

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
4. ~~Commit de organilab~~ HECHO (ver git log). ~~Commit de la lib~~ HECHO en su
   checkout (`ba63783`, `7645a4e`, `94a568d`).
5. ~~get_logentries_org_management~~ HECHO: eliminada (0 llamadores).
6. Traducciones: la lib ganó strings nuevos (mensajes de restore/errores) — se
   compilan en el repo de la LIB, no en organilab; organilab no ganó strings.
7. Menor preexistente: `makemigrations --check` acusa deriva en
   `report/0009_alter_taskreport_language` (default desde settings) — decidir
   aparte, no es de este proyecto.
8. ~~FASE C (papelera)~~ **HECHA (2026-08-29)** — ver la sección siguiente.

## HECHO — Fase C (papelera, 2026-08-29)

Lib (commiteada en su checkout: `94a568d`, con el refactor previo `7645a4e`
que unificó la resolución `app.model`→ContentType en
`djgentelella.utils.contenttypes_from_labels`, usado por history y trash):

- `djgentelella/models.py`: modelo **`TrashRelation`** (FK Trash
  `related_name='gt_relations'` + GenericFK + índice ct/object_id, migración
  `0020_trashrelation`) y helper `relation_targets` (valida instancias; pk
  pelado → ValueError, igual que add_log). `DeletedWithTrash.delete(...,
  related_objects=None)` registra el contexto del borrado; regla "el primer
  borrado gana" (un re-delete no pisa las relaciones existentes; el restore
  vía fila Trash las cascadea y el siguiente borrado registra contexto nuevo).
- `models_manager.py`: el `delete(user=, related_objects=)` de queryset
  también crea las relaciones (solo para filas Trash aún sin contexto).
- `trash/api.py` `TrashViewSet`: `get_queryset` pasa por `filter_by_related`
  (params `related_contenttype`/`related_id`, espejo de HistoryViewSet) y por
  el hook `scope_queryset()`; como restore/destroy resuelven por
  `get_object()`, el scope acota también esas acciones; recordsTotal scoped.
- Admin de TrashRelation; demo `Customer.delete` reenvía `**kwargs` (antes
  tragaba `related_objects`); docs `trash.rst` con la sección de contexto y
  scoping multi-tenant. Tests: `Trash_Test.py` +8 (relaciones instancia/
  queryset, pk rechazado, primer-borrado-gana, cascade, filtro related,
  scope + recordsTotal). **Lib 35/35 en Trash+History (suite completa OK).**

Organilab (rama dj060):

- Pilotos: `Protocol` y `Procedure` heredan `DeletedWithTrash` (migraciones
  `laboratory/0222` y `academic/0018`); managers por defecto ocultan borrados
  (listas, API, selects y admin dejan de verlos; los FK existentes —
  MyProcedure→custom_procedure, GFK de Trash — siguen resolviendo porque
  Django usa el base manager sin filtrar). Ningún form/serializer usa
  `__all__` sobre los pilotos, `is_deleted` no se filtra a la UI.
- `ProtocolDeleteView.form_valid` → `delete(user=..., related_objects=[org,
  lab])`; `academic delete_procedure` → `delete(user=...,
  related_objects=[org])` y su logentry ahora lleva `relobj=organization`
  (antes ese DELETE no salía en la bitácora org-scoped).
- `laboratory/api/views.py`: **`OrganizationTrashViewSet(TrashViewSet)`** —
  `scope_queryset` por join TrashRelation→organización de la URL +
  `user_is_allowed_on_organization`; `get_log_related_objects` propaga el
  contexto del borrado al log de restore/hard-delete (aparecen en la
  bitácora). Router `laboratory:api-trash-*` bajo `trash/api/<org_pk>/`.
- Pantalla: `laboratory/views/trash.py` + `templates/laboratory/trash_list.html`
  + `static/js/trash_list.js` (ObjectCRUD según el demo: restore con Swal y
  manejo de 404/403/410, hard-delete con modal_template_delete); enlace con
  ícono de papelera en `list_organizations.html` junto al de bitácora, gateado
  por `perms.djgentelella.view_trash`.
- Permisos: `update_roles.py` gana `update_papelera()` — view/change/delete
  trash para "Administrador de Laboratorio" y "Administrativo superior"
  (correr `python manage.py update_roles` al desplegar).
- Tests `laboratory/tests/test_trash.py` (7): vista de protocolo → papelera
  con contexto, procedure FBV → papelera, ANTI-FUGA 2 orgs (data y
  recordsTotal), restore con log relacionado a la org, restore cross-tenant
  bloqueado, hard-delete purga (objeto+fila+relaciones), sin view_trash → 403.

Notas de corte:

- Los borrados de Protocol/Procedure ANTERIORES a esta fase fueron hard
  deletes: la papelera solo aplica hacia adelante.
- El CASCADE de Django (p.ej. borrar un Laboratory arrastra sus Protocol) es
  hard delete por colección, no pasa por `delete()` del modelo: esos no van a
  papelera (huérfanos ya cubiertos por el 410/hard_delete de la lib).
- Los flags booleanos artesanales de otros modelos NO se migraron (decisión
  de Luis para esta fase).

## Verificación al cerrar

- Lib: `cd demo && python manage.py test djgentelella.tests` (venv
  `~/entornos/djgentelella`).
- Organilab: suite unit completa (base 910) + selenium de logentry (org y QR:
  `manage_laboratory.test_register_users`, `manage_organizations`) — venv
  `~/entornos/organilab`, correr selenium con
  `GENERATE_SCREENSHOTS=False xvfb-run -a ...`.
- OJO entorno: la lib debe estar instalada EDITABLE en `~/entornos/organilab`
  (una reinstalación desde requirements la pisa; `pip install -e` la restaura).
