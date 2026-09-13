# Inventario de impacto por app/vista — migración a djgentelella 0.6.0

> Categorías: **ROMPE** (deja de funcionar con 0.6.0), **REVISAR** (puede cambiar comportamiento,
> hay que validar), **MODERNIZAR** (HTML a mano que pasa a widgets de la biblioteca).
> Cifras globales: 190 líneas `djgentelella` en ~75 .py · 169 `GTForm` · 32 viewsets
> `AuthAllPermBaseObjectManagement` · 78 `register_lookups` · 145 templates extienden `base.html`.
> Estado por etapa: ver `roadmap/0N_ETAPA_*.md`.

## Sin impacto (verificado con grep, 0 usos)

`InlineAjaxCRUD` · `CRUDView.inlines` · tag `crud_inline_url` · tree fields de la lib ·
`document.chartcallbacks` · Parsley · treeview · bootstrap-progressbar · knob · blueimp fileupload
(eventos `fileuploaddone`) · FullCalendar directo · pdf.js directo · moment directo · markdown
(imports propios) · `{% load tree_tags %}`.

---

## ROMPE — arranque del proceso (settings/urls)

| Archivo | Qué | Etapa |
|---|---|---|
| `src/organilab/settings.py:77` | `"django_ajax"` en INSTALLED_APPS | 2 |
| `src/organilab/settings.py:91` | `"markitup"` | 3 |
| `src/organilab/settings.py:93` | `"djgentelella.blog"` (decisión: quitar) | 1 |
| `src/organilab/settings.py:88,300,306,348-350` | `async_notifications`, `ASYNC_*_WIDGET`, `MARKITUP_*`, beat `send_daily` | 3 |
| `src/organilab/urls.py:89,91` | `markitup.urls`, `async_notifications.urls` | 3 |
| `requirements.txt:1,2,19` | djgentelella pin, `async-notifications==0.2`, `Markdown==3.10` | 3-4 |

## ROMPE — django_ajax (etapa 2)

| Archivo | Uso |
|---|---|
| `src/presentation/templates/base.html:36-37` | `<script>` `django_ajax/js/*` → 404 en TODAS las páginas (145 templates) |
| `src/laboratory/views/shelfs.py:19-20` | `@ajax`, `AJAXMixin` |
| `src/laboratory/views/shelfobject.py:23-24` | ídem |
| `src/laboratory/views/furniture.py:14` | `@ajax` |

## ROMPE — iCheck / switchery (etapa 5) — 11 archivos, ~38 usos

| Archivo | Usos | Pantalla afectada |
|---|---|---|
| `src/laboratory/static/laboratory/js/laboratory.js` | 14 `.iCheck()` (l.459,530,673,677,804-889) | selección de objetos/estantes |
| `src/laboratory/static/laboratory/js/base_modal_management.js:57,63-65` | switchery + radios | modales CRUD de laboratorio |
| `src/laboratory/static/laboratory/js/furniture_table.js:141` | 1 | mobiliario |
| `src/auth_and_perms/static/js/auth_and_perms/organization_manager.js:41,917` | `ifChecked` ×2 | gestión de organizaciones |
| `src/auth_and_perms/templates/auth_and_perms/organization_permission_table.html:17-19` | markup ×3 | tabla de permisos |
| `src/auth_and_perms/templates/auth_and_perms/list_organizations.html:374-376` | markup ×3 | lista organizaciones |
| `src/laboratory/tests/selenium_tests/manage_organizations/base.py:153-170,192,202` | helper `select_org_via_icheck()` | infra selenium |
| `.../manage_organizations/test_collapse_org_name_buttons_box.py:65`, `test_laboratory_tab.py:15`, `test_profile_tab.py:15` | 3 | tests |
| `src/organilab_test/tests/base.py:602` | comentario | — |

## ROMPE — DataTables 2 (etapa 6) — ~28 archivos

`dom:` → `layout:`
- laboratory (10): `laboratory.js:277,310,924` · `reports.js:200` · `shelfobject_management.js:13` ·
  `shelfobject_equipment_tables.js:12,30,44,60,79,95` · `equipmenttype/list.html:43,56` ·
  `instrumentalfamily/list.html:42,54` · `inform.html:89,94` · `logentry_list.html:34` ·
  `register_user_qr/logentry_list.html:29`
- sga (7): `prudence_advice.js:137` · `review_flow_substance.js:43` · `displaylables.js:74` ·
  `warning_words.js:162` · `list_substance.js:76` · `danger_indication.js:47` · `recipient_size.js:175`
- report (2): `organization_report.js:188` · `templates/report/general_reports.html:62`
- academic (2): `my_procedures_list.js:35` · `procedure_list.js:20`
- `document.table_default_dom` → `table_default_layout`: `auth_and_perms/.../select_organization.js:3,27` ·
  `academic/.../complete_my_procedure.js:174`

Clases CSS `dataTables_*` → `dt-*`:
- `academic/static/js/complete_my_procedure.js:226-230` (además `paging_full_numbers`: regla borrada)
- `presentation/static/css/organilab.css:203`

API interna:
- **`src/presentation/templates/base.html:65`** — `$(settings.nTable)` en hook `init.dt` →
  `dt.table().node()`. **Sostiene `data-organilab-ready` → toda la suite selenium.**
- `src/laboratory/static/js/jquery.dataTables.min.js` — copia vendorizada DataTables 1.x, eliminar.

## REVISAR — Chart.js 4 (etapa 7)

| Archivo | Qué |
|---|---|
| `src/risk_management/gtcharts.py` | 12 lookups; `get_scales()` l.1063-1066 formato v2 (funciona por shim, portar); 9 `get_options()` a auditar (l.151,274,399,523,645,770,894,1048) |
| `src/laboratory/gtcharts.py` | 2 lookups |
| Templates con `chartjs.html` (5) | `laboratory/objectlimit/dashboard.html`, `risk_management/{iper_dashboard,risk_graphics,riskzone_detail,riskzone_list}.html` |

## ROMPE/REVISAR — async_notifications → djgentelella.async_notification (etapa 3)

Emisores y contextos:
| Archivo | Uso |
|---|---|
| `src/laboratory/apps.py:11-12` | `update_template_context`, `DummyContextObject` → `register_context` |
| `src/authentication/apps.py:8` + `views.py:3` | `update_template_context` ×3 ("new user", "New feedback", "Request demo") |
| `src/laboratory/signals.py:89` | `send_email_from_template` (shelf-object-in-limit) |
| `src/laboratory/tasks.py:10` | expiring-reactives |
| `src/laboratory/limit_shelfobject.py:55` | llamada comentada |
| `src/laboratory/lab_or_org_request_notifications.py:13` | lab_or_org_request |
| `src/presentation/views.py:275` | new-feedback |
| `src/sga/utils.py:6,25` | sga |
| `src/sga/tests/test_substance_flow.py:3` | importa `EmailNotification` viejo |

Migraciones históricas con `apps.get_model('async_notifications', ...)` (neutralizar para BD limpia):
`laboratory/migrations/0040,0041,0042,0043,0044,0171,0203,0204,0205` · `authentication/migrations/0007`.

## REVISAR — migraciones que referencian la biblioteca (etapa 4)

| Migración | Referencia |
|---|---|
| `src/sga/migrations/0066_add_key_show_sga.py:7,15` | `GentelellaSettings` + dep `djgentelella.0017_alter_chunkedupload_status` |
| `src/auth_and_perms/migrations/0014_impostorwidget.py` | `MenuItem` + dep `djgentelella.0010_menuitem_position` |
| `src/presentation/migrations/0005_load_notification_menu.py:8,12` | ruta `djgentelella.notification.widgets.NotificationMenu` |

## REVISAR — overrides de templates de la lib (etapa 8) — 23 archivos en `src/presentation/templates/gentelella/`

- `blocks/permissions_management.html` — **crítico** (el JS de la lib cambió: checkboxes invisibles sin el fix).
- `app/sidebar.html`, `app/top_navigation.html`, `app/footer.html` — nuevo drawer/disclosure del menú.
- `registration/` (20): activate, activation_complete, email_base, email_footer, email_header,
  footer, login (tiene inputs a mano), logout, new_user, password_change_done, password_change_form,
  password_reset_complete, password_reset_confirm, password_reset_done, password_reset_email,
  password_reset_form, registration_closed, registration_complete, registration_form.
- Propias de organilab (no son overrides, revisar igual): `app/administration_menu.html`,
  `app/laboratory_menu.html`, `app/top_navigation_user_authenticated.html`.

## REVISAR — permisos y comandos

- `src/auth_and_perms/management/commands/update_roles.py` — permisos blog en 5 roles
  (l.152-154,406-408,739-743,815,836-838,1037-1041) → quitar (etapa 1);
  `djgentelella.can_manage_permissions` en 5 roles (l.450,521,744,882,1105) → conservar.
- `src/auth_and_perms/admin.py:11` `LogEntryAdmin` + nota de orden de autodiscover en `apps.py:14`.
- `src/laboratory/templates/laboratory/register_user_qr/login_register_user.html:101` — incluye
  `gentelella/statics/javascript.html` (verificar que exista en 0.6.0).
- `BaseObjectManagement.list` corregido → revisar asserts de `recordsTotal` en tests de los 32 viewsets.

## MODERNIZAR (etapa 10)

### 10b — Formularios con `form-control` a mano (13)
`auth_and_perms/list_organizations.html` · `laboratory/informs/informscheduler_detail.html` ·
`laboratory/laboratory_list.html` · `laboratory/laboratoryroom_list.html` ·
`laboratory/objectview_list.html` · `pending_tasks/tasks/tasks-view.html` ·
`presentation/gentelella/registration/login.html` · `reservations_management/manage_reservation.html` ·
`risk_management/incidentreport_list.html` · `risk_management/iper_list.html` ·
`risk_management/riskzone_list.html` · `sga/substance/detail_substance.html` ·
`sga/substance/observations.html`

### 10c — Tablas sin DataTables (~22, excluidos PDF/correo)
auth_and_perms: `lab_org_list.html`, `user_list.html` · laboratory: `objectfeatures_list.html`,
`object_list.html`, `shelf_list.html`, `shelfobject_detail.html`, `laboratory_process/list.html`,
`register_user_qr/register_user_qr_list.html` · risk_management: `iper_detail.html`,
`iper_history.html`, `iper_list.html`, `regents.html`, `structure_list.html`, `workday_list.html`,
`building_list.html` · sga: `danger_substance/danger_substance.html`,
`danger_substance_category.html`, `h_category/list.html` · academic: `procedure_steps.html` ·
msds: `regulation/regulations_document.html` · report: `hazard_map.html`, `hazard_map_visual.html`

### 10a — Modales
56 templates con `class="modal"`; 24 ya usan `gentelella/blocks/modal_template*.html`; **32 a mano**
(~20 en laboratory). Además 4 plantillas de modal propias duplicadas de la lib:
`src/presentation/templates/modal_template.html`, `modal_template_submit_form.html`,
`modal_template_tab.html`, `modal_template_table_form.html`.

### 10d — Oportunidades nuevas (opcional, al final)
`MapPointInput`/`GTPointField` en vez de `django-location-field==2.7.3`
(`risk_management/forms.py:240,328`, settings `LOCATION_FIELD`) · `{% flag %}` si se necesitan
banderas · `VoiceDictation`/`VoiceEditorTinymce` donde aporte.

## Uso normal por app (no rompe; contexto para etapas)

| App | .py con djgentelella | GTForm | Viewsets AAPBOM | Lookups | Notas |
|---|---|---|---|---|---|
| laboratory | 23 | 84 | 19 | 28+2 charts | 13 templates con modal_template de la lib |
| sga | 12 | 33 | 3 | 6 | `TaggingInput` (sigue existiendo); migración 0066 |
| auth_and_perms | 9 | 17 | 1 | 15 | admin LogEntryAdmin; migración 0014 |
| risk_management | 6 | 13 | 6 | 4+12 charts | forms.py el más grande; alias renombrar (etapa 1) |
| report | 6 | 6 | 2 | 7 | usa modelo `Notification` de la lib (`utils.py:6,137`) |
| academic | 3 | 8 | — | 2 | |
| pending_tasks | 4 | — | — | — | `AllPermissionByAction` |
| presentation | 2 | — | — | — | migración 0005 MenuItem; 23 overrides |
| reservations_management | 2 | — | — | — | `Notification` en `tasks.py:10,80` |
| msds | 2 | — | 1 | — | |
| derb | 1 | — | — | 2 | Formio independiente de djgentelella |
| authentication | 1 | — | — | — | |
| api/organilab/deploy | 3 | — | — | — | firmador/ASGI (`asgi.py:11`, `gunicorn_config_asgi.py:9`, settings:475) |
