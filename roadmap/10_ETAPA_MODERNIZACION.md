# Etapa 10 — Modernización: HTML a mano → widgets/componentes de djgentelella

**Objetivo:** eliminar HTML hecho a mano usando lo que la biblioteca proporciona. Alcance:
**completo** (decisión de Luis). Se ejecuta por sub-etapas medibles, cada pantalla con su prueba.
**Estado:** pendiente. Lista completa de candidatos: `INVENTARIO_VISTAS.md` §MODERNIZAR.

## 10a — Modales (primero: reduce superficie de 10b/10c)

**Hallazgo (2026-08-29):** las 4 plantillas de modal "propias" NO son duplicados de la lib —
son variantes con propósito:
- `modal_template.html` = el de la lib + `form.as_horizontal` + panel `add_shelf_info`
  (left/right/top/bottom). Lo usan las ~20 acciones de shelfobject (`action_modal.html`) y 6
  pantallas simples (sga/academic/observations). Mismo footer `formadd` que la lib. Cambiarles el
  include a la lib alteraría el layout del formulario (horizontal → default) sin ganancia real.
- `modal_template_submit_form.html` = POST nativo con `type="submit"` (la lib no tiene equivalente;
  su botón es `formadd` por JS). 1 consumidor.
- `modal_template_tab.html` / `modal_template_table_form.html` = estructuras propias de
  shelfobject.

Se re-alcanza: NO se eliminan; se documentan como variantes y el esfuerzo va a los modales a mano.

**Recuento real (2026-08-29):** 56 divs `class="modal fade"` escritos a mano en ~30 archivos.
La mayoría NO son "form + url" (encajable en el include de la lib) sino diálogos a medida con
cuerpo/JS propios (reportes, confirmaciones, expandir contenido). La conversión es un
mini-refactor por pantalla, no un cambio mecánico. Orden de ataque sugerido, por densidad:

- [ ] `auth_and_perms/list_organizations.html` (8 modales) — pantalla grande de gestión de orgs.
- [ ] `academic/step_modal.html` + `academic/procedure.html` (3+3) — coordinar con la conversión
      de procedure_steps (abajo).
- [ ] `sga/personal_template.html` (3), `laboratory/shelfobjectUpdate_modal.html` (3),
      `laboratory/furniture_form.html` (3 — atado a la salida de django_ajax, ver etapa 2).
- [ ] Resto (1-2 por archivo): convertir SOLO los que son form+url; dejar los diálogos a medida.

### Inventario 10a (2026-08-29) — auditoría modal por modal

**Patrón de la lib** (`djgentelella/templates/gentelella/blocks/`): `modal_template.html`
(form + botón `.formadd` type=button → `GTBaseFormModal` de `obj_api_management.js` postea
JSON por fetch), `modal_template_delete.html` (`.delbtn`), `modal_template_detail.html`
(body vacío para AJAX, solo Close). Params del include: `id, title, form, form_id, url,
principal_class, modal_class`. La lib NO trae helper de apertura; abrir/cerrar es cosa del
consumidor (`data-bs-toggle` o `$('#x').modal('show')`).

**Camino barato para form+url con recarga de página**: nuestra variante
`presentation/templates/modal_template_submit_form.html` (submit HTML nativo, cero JS) —
ya usada en `list_organizations.html:546-547` (`actionwimodal`, `actionclonemodal`).

**CONVERTIBLES claros → `modal_template_submit_form.html` (sin tocar JS, conservar ids):**

| Modal | Archivo:línea | Postea a |
|---|---|---|
| `addOrganizationmodal` | `auth_and_perms/list_organizations.html:336` | `laboratory:create_organization` |
| `actionsmodal` | `auth_and_perms/list_organizations.html:486` | `laboratory:organization_actions` |
| `add_my_procedures` | `academic/procedure.html:22` | `academic:add_my_procedures` (footer hoy mal anidado dentro del form/body; la conversión lo arregla; se abre con `open_modal()` de `my_procedures_list.js:87`) |
| `newsgalabelmodal` | `sga/templates/personal_template.html:67` (ruta SIN subdir `sga/`) | `sga:sgalabel_create` (se abre con `data-bs-toggle`, línea 30) |
| `add_inform` | `laboratory/inform.html:64` | `laboratory:add_informs` |

**Cascarones AJAX → `modal_template_detail.html` (bajo riesgo, conservar id del div
interno que rellena el JS):** `object_create`/`object_update`/`object_delete`
(`laboratory/shelfobjectUpdate_modal.html`, divs `#shelfobjectCreate/Update/Delete`),
`createshelfmodal`/`editshelfmodal` (`laboratory/furniture_form.html:104,118`, divs
`#shelfmodalbody`/`#editshelfmodalbody`), `rol_details`/`admin_users_modal`
(`list_organizations.html:508,549`, divs `#rol_details_container`/`#admin_users_container`).
Opcionales mismo patrón: `object_list.html:45`, `sustance/list.html:38`,
`equipment/list.html:55`.

**Semi-convertibles (action lo pone el JS; convertir solo si no obliga a reescribirlo):**
`orgbyusermodal` (`list_organizations.html:388`, `organization_manager.js:675`) y
`rol_details` de `auth_and_perms/rol_list.html:46` (`roles.js:16`).

**Se quedan a medida:** `addrolmodal`, `relOrganizationmodal`, `relprofilelabmodal`,
`enable_filter_modal`, `warningobjects`, `object_modal`/`observation_modal`
(`academic/step_modal.html`), `reservation_modal`, `error_reserved`, `svgtemplate`,
`deletesgalabelmodal`, reportes `reportModal` ×5 (report/ y laboratory/components),
confirmaciones de reservations (`my_reservation_delete{,_all}.html`, `product_modal.html`,
`returnModal`), `permissions_management.html`, `user_org_details`/`user_lab_details`,
`fds_modal`, `descriptionModal`, `modal_substance`, `transfer-list-modal`,
`shelfdetailmodal`, `detail_modal_container`.

**Trampas al convertir (registradas para no pisarlas):**
- El include añade `<input type="hidden" name="prefix" class="form_prefix">` → campo
  `prefix` extra en submit nativo; `GTBaseFormModal` lo exige sin guardas.
- El título del include lleva id `{{id}}_title`, NO `{{id}}Label` — JS que muta títulos
  (`organization_manager.js:272,285`) debe actualizar el selector.
- Conservar ids exactos: select2 `dropdownParent` (`organization_manager.js:548,693`),
  handlers `show.bs.modal`/`hidden.bs.modal` (:580,656) y el
  `$('.modal').modal('hide')` global (:504,566) van por id/clase.
- El include siempre añade `fade` (`enable_filter_modal` hoy no lo tiene; cambio menor).

**Arreglos menores al pasar por los mismos archivos:**
- BS4 `data-dismiss` → `data-bs-dismiss` (hoy NO cierran en BS5):
  `personal_template.html:92`, `my_reservation_delete.html:17-18`,
  `my_reservation_delete_all.html:17-18`.
- `academic/step_modal.html:53` `remove_object_modal`: HTML roto y aparentemente muerto
  (`onclick="add_observation"` sin paréntesis, footer anidado) — confirmar que nada lo
  abre y borrarlo.

### Receta pendiente: procedure_steps → BaseInlineObjectManagement

El caso de libro para `BaseInlineObjectManagement` (hijos de `ProcedureStep`:
`ProcedureRequiredObject` y `ProcedureObservations`; hoy FBVs `save_object`/`remove_object`/
`save_observation` + JS propio). NO se hizo en la primera pasada porque: (a) el flujo actual
funciona y audita con `organilab_logentry`; (b) el org-scope del padre pasa por
`step.procedure.content_object` (GenericFK) y `get_parent_queryset()` debe reconstruirlo con
cuidado; (c) hay que decidir el puente de auditoría (lib vs organilab_logentry). Hacerlo como
refactor dedicado con sus tests, siguiendo `demo/demoapp/object_management/viewset.py`.

Detalle auditado (2026-08-29): endpoints actuales FBV `academic:save_object`,
`academic:remove_object`, `academic:add_observation`, `academic:remove_observation`
(`academic/urls.py:41,60-63`), consumidos por `academic/static/js/procedures.js`
(`document.urls`, líneas 121-128). Vistas de página: `ProcedureStepCreateView`
(`academic/views.py:381`) y `ProcedureStepUpdateView` (`:450`), mismo template. Cobertura
buena: 12 unit tests en `academic/tests/test_procedure.py` (add/remove object,
observations, steps con form_schema) + selenium `test_procedure_template.py:30`
`test_procedure_crud` — red de seguridad para el refactor.

## 10b — Formularios con `form-control` a mano — RE-ALCANZADA (2026-08-29)

Auditados los 13 candidatos, solo UNO era un formulario Django real:
- ✅ `laboratory_list.html` → `LaboratorySearchForm(GTForm)` en `laboratory/forms.py`, contexto en
  `LaboratoryListView`, label traducido (antes "Buscar Laboratorio" hardcodeado).
- ✅ `objectview_list.html`: 64 líneas de template comentado muerto eliminadas. OJO: la rama con
  permisos rinde VACÍO desde hace tiempo — candidato en 10c a rehacer con ObjectCRUD o retirar la
  vista (`laboratory:objectview_list`).
- Los demás NO aplican: cajas de búsqueda que desaparecen al convertir su tabla en 10c
  (incidentreport/iper/riskzone/lab lists), controles manejados por JS (observations,
  detail_substance, manage_reservation, tasks-view, list_organizations modal de roles,
  informscheduler period select), o branding de login (etapa 8).

## 10c — Tablas sin DataTables — RE-ALCANZADA (2026-08-29): ~22 → 6 reales

La auditoría (¿la tabla se llena con `{% for %}` del servidor o la llena JS?) mostró que 13 de los
22 candidatos YA son ObjectCRUD/DataTable (tabla vacía + JS dedicado): lab_org_list, user_list,
objectfeatures_list, object_list, laboratory_process/list, regents, structure_list, workday_list,
building_list, danger_substance ×2, h_category/list. Y hay 3 "no aplica": shelfobject_detail e
iper_detail son páginas de detalle (tabla de atributos de UN objeto, el render de servidor es
correcto) y hazard_map{,_visual} son salidas de reporte.

Conversiones reales pendientes (auditoría fina 2026-08-29; ninguna tiene serializer/viewset
previo salvo donde se indica):

- [ ] `laboratory/shelf_list.html` — decisión de Luis (2026-08-29): NO se borra. La carga
      por AJAX de partes de la vista de laboratorio (labview) es funcionalidad deseada; la
      implementación AJAX actual (era django_ajax) debe reemplazarse COMPLETA por componentes
      de la lib, pero manteniendo una interacción de usuario similar — que no se pierda
      funcionalidad aunque la implementación cambie. Contexto técnico: hoy los fragmentos
      vivos son `shelf_details.html` (`views/shelfs.py:378,469`) y `shelf_card.html`
      (`furniture_tags.py:22`); `shelf_list.html`/`generic.py` quedan en su lugar hasta
      diseñar el equivalente. Es la continuación natural de la etapa 2 (salida total de
      django_ajax) y se trabaja como sub-proyecto propio del labview.
- [ ] `laboratory/register_user_qr/register_user_qr_list.html` — vista
      `RegisterUserQRList(ListView)` (`views/laboratory.py:500`), url
      `laboratory:list_register_user_qr`, modelo `RegisterUserQR` (GenericFK + 2 FKs org).
      Hoy DataTable client-side sobre HTML renderizado. OJO: alta/edición es página completa
      (`manage_register_qr`, `views/laboratory.py:526`, genera QR + URL absoluta) — convertir
      SOLO el listado a viewset+ObjectCRUD manteniendo las acciones como links (editar,
      PDF, historial, borrar). Cobertura: 6 tests selenium en
      `manage_laboratory/test_register_users.py` (entran por el reverse — sobreviven si se
      conservan los botones); sin unit tests.
- [x] `risk_management/iper_list.html` — **HECHA (2026-08-29)**:
      `IPERAssessmentViewSet(AuthAllPermBaseObjectManagement)` en `api/viewset.py`
      (solo `list`+`destroy`; crear/editar siguen siendo páginas por su lógica de
      versionado; acción no mapeada → 403 vía `AllPermissionByAction`, verificado con
      test), serializer `IPERAssessmentSerializer` que enmascara el laboratorio anónimo
      EN EL SERVIDOR (laboratory=null), `IPERSearchFilter` que excluye el nombre de labs
      anónimos de la búsqueda (mismo criterio que la vista vieja),
      `perform_destroy` con `organilab_logentry` (paridad con `IPERAssessmentDelete`).
      Página → `TemplateView` + tabla vacía `#table-iper` + `iper_list.js` (ObjectCRUD,
      búsqueda global del DataTable, sin filtros por columna). La acción "Open" navega a
      `iper_detail` con la nueva acción `link:true` de la lib (ver Cambios en djgentelella).
      Tests: 5 nuevos de API en `test_iper.py` (enmascarado, búsqueda-anonimato, destroy,
      create→403) — risk_management 32/32 OK. Traducciones extraídas y compiladas
      (djangojs.po tenía fuzzy erróneos de makemessages: corregidos a mano).
      OJO: `IPERAssessmentDelete` (`riskmanagement:iper_delete`) quedó huérfana — solo la
      usaba el modal viejo del listado; candidata a retirar tras la validación (etapa 12).
      Los viewsets hermanos usan `permission_classes = ()` (¡sin chequeo de permisos!):
      el de IPER usa el default `AllPermissionByAction`; revisar los hermanos aparte.
- [ ] `risk_management/iper_history.html` — `IPERHistory(ReportListView)`
      (`iper_views.py:618`), modelo `IPERHazard`, SIN acciones por fila (reporte). ⚠️ La
      exportación XLSX/ODS/PDF depende de `?{{pgparams}}&format=` de la vista actual:
      decidir si el export queda en la vista (solo la tabla pasa a ObjectCRUD, compartiendo
      filterset) o si NO se convierte (es salida de reporte, como hazard_map). Cobertura:
      `test_iper.py:182,188`.
- [ ] `academic/procedure_steps.html` — NO es un listado: página de formulario con 2 tablas
      inline (`procedurerequiredobject_set`, `procedureobservations_set`). Es el caso
      `BaseInlineObjectManagement` de la receta de abajo, no ObjectCRUD plano.
- [x] `msds/regulation/regulations_document.html` — **SE QUEDA como está** (verificado
      2026-08-29): vista PÚBLICA/anónima (`msds/views.py:187`, sin login ni org_pk, url raíz
      `regulation_docs`) y EN USO (sidebar.html:42 y tutorial.html:105).
      `AuthAllPermBaseObjectManagement` exige sesión+permisos → convertirla rompería el
      acceso anónimo y `msds/tests.py:39`. Son 3 columnas con solo link de descarga; no
      justifica un viewset con permisos laxos.
- [x] `laboratory:objectview_list` — **RETIRADA (hecho 2026-08-29)**: verificado que la rama
      con permisos rendía vacío y ningún menú/JS enlazaba la página; era duplicado de las
      pantallas vivas por tipo (material `object_view` + ObjectCRUD, reactivo
      `sustance_list`, equipo `equipment_list`). Hecho: borrado
      `objectview_list.html`; eliminada `ObjectListView` interna y la ruta `list` de
      `ObjectView.get_urls()`; los 3 `success_url` de crear/editar/borrar ahora redirigen
      POR TIPO vía helper `get_object_list_url()` (`views/objects.py`); tests ajustados
      (`test_object.py`, `test_object_material.py`) → 43/43 OK. Se conservan:
      `objectview_create/update/delete` (páginas con tests de validación de capacidad),
      la clave `objectview_list` en `urlname_permissions.py:623` y los
      `define_urlname_action 'objectview_list'` de las 5 pantallas vivas (es clave de grupo
      de permisos, no una URL — `define_urlname_action` no hace reverse).

Patrón: viewset `AuthAllPermBaseObjectManagement` (o reusar el existente) + serializer con
columnas + template con tabla vacía + `ObjectCRUD` (ver `regents.html` como referencia interna).

**Anatomía del patrón de referencia `regents` (auditada, para replicar):**
- Template `risk_management/regents.html`: `{% define_urlname_action 'regent_crud' %}` en
  `pre_head`; `<input hidden id="org" value="{{org_pk}}">` (lo leen los select2 con
  `data-s2filter-org_pk="#org"`); tabla VACÍA `#table-regent`; 3 includes de modal de la lib
  (create/update con `modal_template.html`, delete con `modal_template_delete.html`); en
  `block js`: globals `has_perm`, `object_urls` (list/create/destroy/update, pk placeholder
  `0`), `selects2_url`, y `<script regents.js>`.
- Vista de página: FBV `regent_view` (`risk_management/views.py:361`) con
  `permission_required` + `user_is_allowed_on_organization`; contexto = forms con prefijos
  `create`/`update` + `org_pk`.
- ViewSet `RegentViewSet` (`api/viewset.py:35`): `serializer_class` y `perms` como dicts por
  acción, `permission_classes=()` (lo resuelve `AllPermissionByAction` de la base),
  `LimitOffsetPagination`, `filterset_class`, `get_queryset()` por org_pk,
  `get_serializer_context()` inyecta org_pk, `perform_create()` setea
  `created_by`+`organization`. Router: `urls.py:16-17` + include bajo prefijo con org_pk
  (`urls.py:129`).
- Serializers (`api/serializer.py`): fila con `actions` SerializerMethodField por permisos +
  envoltorio `...DataTableSerializer` (`data/draw/recordsFiltered/recordsTotal`) + serializers
  de add/update.
- JS (`static/js/regents.js`): `datatable_inits.columns`, `modalids` (create solo si
  `has_perm`), `objconfig` → `ObjectCRUD(uniqueid, objconfig).init()`
  (`obj_api_management.js:375`).
- Segunda referencia más cercana a laboratory (misma receta): `object_list.html` +
  `object_view` (`views/objects.py:345`) + `ObjectViewSet` (`api/views.py:1653`) +
  `object_management.js`.

## 10d — Oportunidades nuevas (evaluar al final, opcional)

- `MapPointInput`/`GTPointField` en vez de `django-location-field==2.7.3`
  (`risk_management/forms.py:240,328` + settings `LOCATION_FIELD`; requiere
  `SECURE_REFERRER_POLICY='strict-origin-when-cross-origin'` y `use_maps`).
- `djgentelella.history`/`Trash` para bitácora/borrado lógico (ver plans/DJGENTELELLA_060_NOTES.md
  §4: trampas conocidas — `models_log`, org-scope) — probablemente proyecto aparte.

## Método por pantalla

1. Captura del comportamiento actual (test existente o manual).
2. Cambio.
3. Prueba (unit del endpoint + selenium puntual si existe).
4. Marcar en la tabla de INVENTARIO_VISTAS.md.

## Cambios en djgentelella (esta etapa)

- `obj_api_management.js` `do_action()`: soporte de **acciones de navegación** en
  `object_actions` — `link: true` hace `window.location.assign(url)` en vez de fetch.
  Cubre el caso genérico "abrir la página de detalle de la fila" (lo usan iper_list en
  organilab y el demo). Prueba en demo: `object_management.html` reemplazó su columna
  "Notes" con `<a>` a mano por una object_action `link:true` hacia la página inline.

## Notas / hallazgos

(al cerrar la etapa)
