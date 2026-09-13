# Análisis: djgentelella 0.5.9 → 0.6.0 (rama `development`)

> **Fuente:** checkout local `~/Desktop/desarrollo/django-gentelella-widgets`, rama `development`,
> commit `d7bc6f9` (2026-08-28), `__version__ == '0.6.0'`. **No existe tag ni release en PyPI**;
> el último tag publicado es `v0.5.9`. `v0.5.9..development` = 110 commits, 284 archivos,
> +21158/−10273.
>
> **Sustituye el análisis de `plans/DJGENTELELLA_060_NOTES.md`**, que se hizo sobre la rama
> `cleanup` (67 commits detrás de `development`) y no cubre la revisión JS/vendors de la sección
> `Unreleased` del CHANGELOG. Ese documento sigue siendo válido para history/trash/MenuItem/
> BaseInlineObjectManagement; este cubre todo lo demás.
>
> **Advertencia sobre el CHANGELOG de la biblioteca:** hay DOS secciones vigentes en `development`:
> `0.6.0` (CHANGELOG.rst:625 — InlineAjaxCRUD, markitup, tree fields, voz, dependencias) y
> `Unreleased` (CHANGELOG.rst:5 — iCheck, DataTables 2, Chart.js 4, TinyMCE 8, FullCalendar 6,
> pdf.js 6, knob, moment, banderas, mapas, MDI). Ambas están en el código de `development`.
>
> **Ramas `async_notification`:** la del repo djgentelella ya está íntegra en `development`
> (0 commits propios pendientes) — se ignora. La rama `async_notifications` de **organilab**
> (commit real `b199f51d`, marzo 2026) se usa solo como mapa; ver §9.

---

## 1. Eliminado

### Python
| Qué | Detalle |
|---|---|
| `djgentelella.cruds.inline_crud.InlineAjaxCRUD` | Único `.py` borrado. Sustituto: `djgentelella.objectmanagement.BaseInlineObjectManagement`. |
| `CRUDView.inlines` / `add_inlines()` | Ahora `cruds/base.py:701-713` emite `DeprecationWarning` y no registra URLs (falla después en `reverse`, silencioso). |
| Tag `crud_inline_url` | Borrado de `templatetags/crud_tags.py`. El resto de tags sigue. |
| Soporte MPTT en `fields/tree.py` y `MenuItem.MPTTMeta` | Todo el árbol es django-tree-queries. |
| `blog.MarkupField` | → `TextField`; `Entry.resume.rendered` ya no existe; HTML sin sanitizar. |

**Impacto organilab: NULO** — 0 usos de InlineAjaxCRUD, crud_inline_url y tree fields (verificado por grep).

### Dependencias Python que ya no instala
`djangoajax`, `django-markitup`, `markdown`. **Impacto organilab: ALTO** — llegaban solo como
transitivas y el proyecto las tiene cableadas (ver §8, bloqueadores).

### Templates y estáticos
- `templates/cruds/ajax/*` (5), `gentelella/widgets/chart.html` (huérfano).
- `static/django_ajax/js/*` (4), `wysiwyg.js`, `djgentelella.flags.vendors.min.css` (6.35 MB).
- Bundles `djgentelella.vendors.*`, `readonly.vendors.*`, `maps.*` y `gentelella/js/base.js`
  **ya no van en git**: se generan (`make loadstatic && make basejs && make assets` en el checkout).

### Bibliotecas JS eliminadas del bundle
- **iCheck + switchery** → CSS puro `gentelella/css/checks.css` (`gt-check`, `gt-switch`).
- **jQuery-Knob** → `js/base/knob.js` (`$.fn.gt_knob`); **blueimp File-Upload** →
  `js/base/chunkedupload.js` (fetch, ~130 líneas; eventos `fileuploaddone`/`fileuploadchunkfail`
  ya no existen).
- Parsley, patternfly-bootstrap-treeview, bootstrap-progressbar, CSS de jQuery UI, 2ª copia de
  interact.js, summernote, glyphicons BS3, flag-icons CSS, `jquery.tinymce.min.js`,
  `jQuery.tagify.min.js` (Tagify en sí se queda, actualizado), 14 extensiones de DataTables.
- `moment-with-locales.min.js` (375 KB) → `moment.min.js` + locale por idioma
  (`{% load gtsettings %}{% get_moment_locale %}`).

**Impacto organilab:** solo iCheck/switchery (11 archivos) y la pérdida de `django_ajax/js/*`
referenciado en `base.html`. El resto: 0 usos directos verificados (Parsley, treeview,
progressbar, knob, blueimp, FullCalendar, pdf.js, moment directo).

---

## 2. Renombrado / movido

| Antes | Ahora |
|---|---|
| `cruds.inline_crud.InlineAjaxCRUD` | `objectmanagement.BaseInlineObjectManagement` |
| `GentelellaTreeNodeChoiceField` (widget, roto) | form **field** (`fields/tree.py:80`); widget default `trees.TreeSelect` |
| `class="flat"` / `icheckbox_flat-green` / `iradio_flat-green` | `class="gt-check"` |
| `YesNoInput` (switchery) | `class="gt-switch"`; `data-checkboxclass`/`data-radioclass` inertes → `--gt-check-color`, `--gt-check-size` |
| `dataTables_wrapper/filter/paginate/length/info/processing/empty` | `dt-container/search/paging/length/info/processing/empty` (reglas `paging_full_numbers`, `DTTT_button`, `table.display` **borradas**, no renombradas) |
| `document.table_default_dom` (string `dom`) | `document.table_default_layout` (objeto `layout`: `topStart`, `top`, `topEnd`, `top2Start`, `bottomStart`, `bottomEnd`) |
| `dt.context[0].nTable` | `dt.table().node()` |
| `vendors/chartjs/Chart.min.js` | `vendors/chartjs/chart.umd.min.js` |
| `vendors/fullcalendar/main.min.js` (+css) | `vendors/fullcalendar/index.global.min.js` (CSS inyectado por JS) |
| `vendors/htmlx/` | `vendors/htmx/` |
| i18n DataTables `plug-ins/1.x/i18n/` | `plug-ins/2.3.7/i18n/` (cambian las claves) |
| `<i class="fi fi-cr">` (flag-icons) | `{% load gtflags %}{% flag 'cr' %}` (sprite svg propio) |
| blog `MarkItUpWidget` | `widgets.tinymce.EditorTinymce` |

### Serializers de Chart.js (`djgentelella/chartjs.py`)
`TooltipsSerializer`→`TooltipSerializer`, `scaleLabelSerializer`→`ScaleTitleSerializer`
(`labelString`→`text`), `gridLinesSerializer`→`GridSerializer`, `OptionScaleSerializer`
(listas `xAxes`/`yAxes`)→`scales = DictField(child=ScaleSerializer())`,
`RectangleSerialize`/`ElementsSerialize`→`ElementsSerializer`, `AnimationSerialize`→
`AnimationSerializer`; nuevo `PluginsSerializer` (`title`/`legend`/`tooltip`).
**Los getters conservan nombre** (`get_title`, `get_legend`, `get_tooltips`) y se archivan bajo
`options.plugins`. Hay traducción transitoria automática (una release) para: `xAxes`/`yAxes`
(`scales_to_v4`), `elements.rectangle`, `dataset.steppedLine`, `get_type()=='horizontalBar'`
(→ `bar` + `indexAxis:'y'`). Lo único sin capa de compatibilidad: callbacks en
`document.chartcallbacks` escritos para Chart.js 2 (organilab: **0 usos**).

---

## 3. Nuevo

### Módulos
- **`djgentelella.async_notification`** — app completa: `EmailTemplate`, newsletters, compliance
  (unsubscribe one-click, supresión), preview con datos ficticios, `registry.register_context()`,
  `sending.send_email_from_template()`, backends `SyncBackend`/`CeleryBackend`, comando
  `process_notifications`, batching reanudable, 8 migraciones, 23 templates.
- `voice/` (dictado: `VoiceDictation`, `VoiceEditorTinymce`, backend local onnx o remoto),
  `widgets/maps.py` + `fields/maps.py` (`MapPointInput`, `GTPointField` — lat,lng sin GeoDjango),
  `widgets/pdf.py` (`PDFViewerWidget`, `PDFChunkedUploadView` con validación de magic bytes),
  `flags.py` + `templatetags/gtflags.py`, `blog/migrations/0002` (**irreversible**, borra columnas
  markitup).
- `BaseInlineObjectManagement`: `parent_model`, `parent_field`, `parent_url_kwarg='parent_pk'`;
  hooks `get_parent_queryset()` (**obligatorio sobreescribirlo en organilab**: sin él cualquier
  usuario autorizado alcanza cualquier `parent_pk`), `perform_create/update` fijan el FK desde la
  URL. Patrón completo en el demo (§7).
- `ChunkedUploadBaseView.login_required` (default `True`).

### JS/CSS
- `checks.css`, `fileupload.css`, `knob.css`, `flags.css`, `maps.css`, `pdfviewer_widget.css`,
  `sidebar.css` (nuevo comportamiento del menú).
- `gt_chunked_upload()`, `gt_file_md5()`, `flush_editors(form)`, `set_editor_content()`,
  `gentelella_tinymce_config()/init()`, `gt_friconix_refresh()`, `createGTMap()`,
  `$.fn.pdfviewerwidget`, `$.fn.gt_knob`.
- `DEFAULT_JS_IMPORTS`: se elimina `use_flags`; nuevos `use_maps`, `use_mdi`.
- Bundles nuevos: `djgentelella.maps.{vendors,plugins}.min.{js,css}`.

### Settings nuevos relevantes (del demo)
`ASYNC_NOTIFICATION_BASE_TEMPLATES/_BRAND/_BASE_URL/_MAILING_ADDRESS/_UNSUBSCRIBE_MAILTO`,
`ASYNC_NEWS_BASE_MODELS`, `GENTELELLA_ASR_*`, `SECURE_REFERRER_POLICY =
'strict-origin-when-cross-origin'` (**obligatorio si se usan mapas**: OSM devuelve 403 sin Referer).
`GT_HISTORY_ALLOWED_MODELS` ya existía en 0.5.9.

---

## 4. Comportamiento cambiado (eventos JS) — lo que hay que portar en JS propio

1. **iCheck → nativo**: `ifChecked`→`change` + `if (!this.checked) return;`, `ifUnchecked`→
   `change` + guard inverso, `ifToggled`→`change`. Imperativos: `.iCheck('check')`→
   `.prop('checked', true)`, `'uncheck'`→`false`, `'update')`→nada. Los selectores de la lib se
   estrecharon a `input[type=checkbox]`.
2. **`clear_action_form()`** ya no dispara `click` sintético sobre switches — el `reset` nativo
   repinta. Código que dependía de ese click deja de recibirlo.
3. **TinyMCE en modales, arreglado en ambas direcciones**: `obtainFormAsJSON()` llama
   `flush_editors()` (el textarea ya no llega vacío al servidor) y la lectura usa
   `set_editor_content()` vía `tinymce.get(id)` (funciona con cualquier subclase de editor).
4. **`ObjectCRUD`**: `config.actions`/`config.urls` con defaults (antes `ObjectCRUD(id, {urls})`
   sin `actions` abortaba `init()`); un serializer sin clave `actions` ya no tumba la tabla.
5. **`GTBaseFormModal`**: valores no-objeto en selects estáticos hacen `.val(x)` (antes se corrompía).
6. **DataTables 2**: `layout` en vez de `dom`; server-side sin cambios (`formatDataTableParams`
   sigue igual); render `DataTable.render.datetime()`.
7. **Menú lateral/navbar** (custom.js +277 líneas): entradas con submenú son *disclosure* —
   `preventDefault()`, **ya no navegan aunque tengan url_name**; bajo 991.98px el sidebar es un
   drawer (`body.sidebar-open` + backdrop, Escape cierra); flyout `position:fixed`; dropdowns del
   navbar se abren con click (táctil); `flex-row-reverse` reactivo a resize.
8. **`gt_find_initialize()`** llama `gt_friconix_refresh()` (iconos en formsets/modales/redraws ya
   no quedan vacíos).
9. Listener global `focusin` con `stopImmediatePropagation` para diálogos TinyMCE dentro de modales
   Bootstrap.
10. `CheckboxInput`, `NullBooleanSelect`, `RadioVerticalSelect/Horizontal` ya no tienen función
    inicializadora en `document.gtwidgets` (siguen siendo widgets; `data-widget` sigue siendo
    obligatorio en el markup).
11. **Subida de ficheros**: promesa `gt_chunked_upload({file,url,done_url,csrf,onprogress})`;
    `parent.set_progress(percent)`; race del md5 arreglada.
12. **TinyMCE 8**: `license_key:'gpl'` obligatorio (sin él arranca read-only), `models/dom`
    obligatorio, plugins 46→29, `fontselect/fontsizeselect/formatselect`→`fontfamily/fontsize/blocks`,
    `paste_preprocess` recibe el editor, `setDisabled`→`setEnabled` (sentido invertido).
13. **pdf.js 6**: `getDocument({url})` (un string produce canvas en blanco sin error); worker por URL.
14. **`BaseObjectManagement.list`**: `recordsTotal` desde `get_queryset()` (antes queryset de
    clase) — los 32 viewsets de organilab que estrechan queryset **cambiarán el total mostrado**
    (corrección; puede romper asserts de conteo).
15. `bootstrap-maxlength`: `warningClass` → `'badge text-bg-success'`.
16. Helper palette: z-index 1035, `d-none`, placeholders ya no se ven.

---

## 5. Dependencias

| | 0.5.9 | 0.6.0 |
|---|---|---|
| django | >=4.2 | **>=5.2** (organilab 5.2.11 ✅) |
| djangorestframework | >=3.13 | **>=3.15.2** (organilab 3.16.1 ✅) |
| djangoajax | >=3.3 | ❌ eliminado |
| django-markitup | >=4.0.0 | ❌ eliminado |
| markdown | sí | ❌ eliminado |
| python | >=3.11 | igual |

Extras: `firmador` pasa de pines `==` a `>=` (resuelve conflictos, no los crea); nuevos `celery`
(`celery[redis]>=5.3`, backend de cola de async_notification), `asr`, `asr-remote`.

Frontend: DataTables 1.12.1→2.3.7, Chart.js 2.9.3→4.5.1, TinyMCE 5.6.1→8.8.2, FullCalendar
5.11.3→6.1.20, pdf.js 4.6.82→6.2.108, jQuery 3.6.1→3.7.1, bootstrap 5.2.0→5.3.8, sweetalert2
10→11, inputmask 3→5, autosize 3→6, select2/moment/tagify/htmx actualizados.

**Instalación desde checkout**: `pip install -e` NO trae vendors ni bundles. En el checkout:
`make loadstatic && make basejs && make assets` (en ese orden; `assets` sin `basejs` previo no
escribe nada y no avisa). Bundles unidos ahora con `;\n` (bug de concatenación resuelto).

---

## 6. Estado del venv de organilab (punto de partida)

El `.venv` tiene instalado un **snapshot viejo de 0.6.0 (rama `cleanup`)**: aún contiene
`cruds/inline_crud.py`, vendors iCheck/flag-icon-css/bootstrap-progressbar, y **no** contiene
`async_notification`. `django-markitup 4.1.0`, `djangoajax 3.3` y `async_notifications 0.2`
siguen instalados. Es decir: organilab hoy corre un híbrido pre-Unreleased. El baseline de pruebas
se toma sobre ese entorno (ver `roadmap/BASELINE.md`).

---

## 7. Patrones del demo (referencia de uso)

- **CRUD inline** (`demo/demoapp/templates/object_management_inline.html` +
  `object_management/viewset.py`): includes de `gentelella/blocks/modal_template{,_detail,_delete}.html`,
  URLs con `parent.pk` y placeholder `0` para el pk de instancia, `ObjectCRUD(id, config).init()`,
  viewset con `get_parent_queryset()` sobreescrito y `@action detail_template`; el serializer
  incluye `get_actions` si la columna existe.
- **Mapas**: `BaseMapView` + `gentelella/widgets/djmap.html`; `MapPointInput` en forms; modelo con
  `GTPointField`. Requiere `SECURE_REFERRER_POLICY`.
- **Checkbox de borrado de fichero en uploads**: el campo del modelo necesita `blank=True` o el
  submit siempre falla con "This field cannot be blank" (migración demo 0028).
- **Selects con imagen/bandera**: `AutocompleteSelectImage('lookupname')` + lookup que devuelve
  `flag_url(code)`.
- Páginas de referencia de iconos: `/icons/fontawesome|friconix|mdi|flags` en el demo.
- `TIME_ZONE`: `DateTimeInput` envía string naive; el demo usa `America/Costa_Rica` (organilab ya).
- El demo trae suite selenium propia (`demo/demoapp/tests/selenium/`, ~3500 líneas) — útil como
  referencia de selectores `gt-check`/`dt-*`.

## 8. Bloqueadores de arranque en organilab (resumen; detalle en INVENTARIO_VISTAS.md)

1. `django_ajax`: `settings.py:77`, `base.html:36-37`, `laboratory/views/{shelfs,shelfobject,furniture}.py`.
2. `markitup`: `settings.py:91,300,348-350`, `urls.py:89`.
3. `async_notifications` 0.2 → `djgentelella.async_notification`: 16 .py + 10 migraciones de datos
   + CELERYBEAT + urls (la etapa más grande).
4. `djgentelella.blog`: se elimina de INSTALLED_APPS (decisión tomada) + permisos en `update_roles.py`.

## 9. Rama `async_notifications` de organilab — solo mapa

Commit real `b199f51d` (2026-03-20). Sirve para ver qué archivos tocar y qué códigos de plantilla
usar, pero se **rehace**: línea corrupta en `limit_shelfobject.py`
(`get_backend().sesend_email_from_template...nd(...)`), `print()` de debug, migraciones con
dependencia a `('async_notification','0006_newslettertemplate_model_base_m2m')` que ya no existe
(hoy: `0006_emailconsent_emailsuppression_and_more`, van por la 0008), contextos
`update_template_context` comentados con TODO en vez de migrados a `register_context`, cambio
accidental de `DBNAME` a `organilab_pro`, y no cubre `lab_or_org_request_notifications.py` ni
`sga/utils.py` ni `sga/tests/test_substance_flow.py` (nuevos en dj060).

Semántica de encolado (decisión tomada: **mantener cola + drenado**): `enqueued=False` dispara
envío por señal `post_save`; `enqueued=True` deja la fila para que la drene `process_notifications`.
Hay que programar el drenado en CELERYBEAT (reemplazo de `send_daily_emails`).
