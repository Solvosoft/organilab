# djgentelella 0.6.0 — qué trae y cómo usarlo en estos planes

> **⚠️ PARCIALMENTE OBSOLETO (2026-08-29).** Este análisis se hizo sobre la rama `cleanup`, que
> quedó 67 commits detrás de `development`. NO cubre la revisión JS/vendors de la sección
> `Unreleased` del CHANGELOG (iCheck eliminado, DataTables 2, Chart.js 4, TinyMCE 8,
> FullCalendar 6, pdf.js 6, mapas, banderas, dictado por voz). El análisis vigente y el plan de
> migración están en **`roadmap/00_ANALISIS_DJGENTELELLA_060.md`** y `roadmap/README.md`.
> Lo que sigue siendo válido aquí: history/trash/MenuItem/BaseInlineObjectManagement (§2-§4).

> **Qué es esto.** Análisis de la versión de djgentelella con la que se construirán los módulos
> descritos en [`PLATFORM_ADMIN_PLAN.md`](PLATFORM_ADMIN_PLAN.md),
> [`MANAGEMENT_PLANS_PLAN.md`](MANAGEMENT_PLANS_PLAN.md) y [`ENVIRONMENT_PLAN.md`](ENVIRONMENT_PLAN.md).
> Fuente: checkout local `~/Desktop/desarrollo/django-gentelella-widgets`, rama `cleanup`,
> `djgentelella.__version__ == '0.6.0'`.
>
> **Conclusión corta:** 0.6.0 ya resuelve buena parte de lo que los planes iban a construir a mano
> —bitácora, borrado lógico con papelera, plantillas de correo con variables y previsualización,
> CRUD hijo de un padre, menús en base de datos—. Los planes se reescribieron para **usar** esas
> piezas y quedarse solo con lo que es propio de Organilab: el alcance multi-tenant y las reglas de
> negocio.

---

## 1. Estado actual vs. 0.6.0

| | Hoy en Organilab | En 0.6.0 |
|---|---|---|
| Versión declarada | `djgentelella[firmador]>=0.5.9` (`requirements.txt:1`) | 0.6.0 |
| Django | 5.x | **5.2 LTS mínimo**, DRF 3.15.2 mínimo, Python 3.11+ |
| Correos | `async-notifications==0.2`, app externa `async_notifications` | **`djgentelella.async_notification`**, dentro de la biblioteca |
| Auditoría | `organilab_logentry()` propio (`src/laboratory/utils.py:249`, ≈280 usos) | `djgentelella.history` |
| Borrado lógico | `is_active` a mano, campo por campo | `DeletedWithTrash` + `Trash` |
| `GTForeignKey` | copia local en `src/laboratory/catalog/__init__.py` | `djgentelella.fields.catalog.GTForeignKey` (código equivalente) |
| Menús | plantillas parciales en `src/presentation/templates/partials/` | modelo `MenuItem` en base de datos, con permisos y árbol |

---

## 2. Mapa: función de los planes → pieza de la biblioteca

| Función planificada | Qué usar de 0.6.0 | Qué queda por escribir |
|---------------------|-------------------|------------------------|
| Bitácora consultable | `djgentelella.history.api.HistoryViewSet` + `HistoryFilterSet` + `HistorySerializer`; pantalla documentada en `docs/source/history.rst` | **El alcance por organización** (la biblioteca no lo trae) y el detalle antes→después |
| Registro automático de cambios | `history.api.BaseViewSetWithLogs` (loguea create/update/delete) y `history.utils.add_log` | Puente con `organilab_logentry` para no partir la bitácora en dos |
| Borrado lógico con recuperación | `DeletedWithTrash` + `Trash` + `TrashViewSet` (list / restore / hard delete) | Filtrar la papelera por organización |
| Plantillas de correo administrables | `djgentelella.async_notification`: modelo `EmailTemplate`, pantalla `email_template_view`, endpoint `model-fields/`, plantilla `_model_tree.html` | Estado activo/inactivo **por organización** |
| Campos dinámicos del correo | `async_notification.registry.register_context()` + `introspection.describe_model_fields()` | Registrar los procesos de Organilab |
| Previsualización del correo | `async_notification.preview`: `build_dummy_context()`, `render_preview()`, `PreviewProvider` | Proveedores de datos de ejemplo por proceso |
| Envío | `async_notification.sending.send_email_from_template(code, recipient, context, …)`, backend `SyncBackend` o `CeleryBackend` | Envolver para aplicar estado/override por org |
| Aviso dentro de la app | `djgentelella.notification.create_notification()` + `Notification` (campana en el menú) | Decidir qué alertas van a campana además de `PendingTask` |
| CRUD de hijos (ejes, componentes, acciones, actividades, seguimientos) | **`BaseInlineObjectManagement`** — CRUD sobre los hijos de un padre, con la URL cargando el `parent_pk` | `get_parent_queryset()` con el filtro por organización |
| Pantallas de tabla + modales | `ObjectCRUD` (JS) + `gentelella/blocks/modal_template*.html`; guía en `docs/source/object_management.rst` | La configuración de columnas de cada pantalla |
| Selección de la dependencia (árbol org) | `GentelellaTreeNodeChoiceField` (reconstruido sobre **django-tree-queries**, que es lo que usa `OrganizationStructure`) | Nada: encaja directo |
| Gráficos | `djgentelella.chartjs` (`LineChart`, `StackedBarChart`, `HorizontalBarChart`, `DoughnutChart`…) + `groute.register_lookups` | Los *lookups* de cada módulo |
| Subida de evidencias e importación masiva | `djgentelella.chunked_upload`, widget `FileChunkedUpload`, serializer `ChunkedFileField` | El mapeo de columnas del importador |
| Menú de los módulos nuevos | modelo `MenuItem` (categoría `sidebar`, jerárquico, con `permission`) | Migración que siembra las entradas |
| Editor enriquecido (FAQ, plantillas) | `widgets.tinymce.EditorTinymce` / `widgets.wysiwyg.TextareaWysiwyg` | — |

---

## 3. Cómo se usa cada pieza (lo esencial)

### 3.1 Auditoría

```python
# settings.py — sin esto, HistoryViewSet no filtra por modelo
GT_HISTORY_ALLOWED_MODELS = [
    "djgentelella.trash",          # siempre, cuando se usa papelera
    "management_plans.planactivity",
    "environment.consumptionrecord",
]
```

`add_log(user, object, action_flag, model_name=None, changed_data=None, object_repr='', change_message='', content_type=None)` escribe un `LogEntry` de admin. Agrega dos acciones a las tres de Django:
`HARD_DELETION = 4` y `RESTORE = 5`.

`BaseViewSetWithLogs` (extiende `AuthAllPermBaseObjectManagement`) registra solo:
`perform_create` → ADDITION, `perform_update` → CHANGE con los campos que cambiaron,
`perform_destroy` → DELETION.

### 3.2 Papelera

```python
from djgentelella.models import DeletedWithTrash

class ProgramAttachment(AbstractOrganizationRef, DeletedWithTrash):
    ...
```

Da tres managers: `objects` (solo vivos), `objects_with_deleted`, `objects_deleted_only`.
`delete()` marca `is_deleted` y crea la fila de `Trash`; `delete(hard=True)` borra de verdad.
En los formularios hay que **excluir `is_deleted`**.

### 3.3 Correos

```python
# apps.py -> ready()
from djgentelella.async_notification.registry import register_context

register_context(
    code='activity_due_soon',
    subject='La actividad {{ activity.name }} vence el {{ activity.due_date }}',
    models={'activity': 'management_plans.PlanActivity', 'user': 'auth.User'},
    exclude={'user': ['password', 'last_login', 'is_superuser']},
    extra_variables={'site_url': 'URL del sitio'},
    depth=2,
)
```

Con eso, la pantalla de plantillas muestra el árbol de variables disponibles y la previsualización
con datos ficticios, sin escribir UI.

### 3.4 CRUD de hijos

```python
class PlanActionManagement(BaseInlineObjectManagement):
    queryset = PlanAction.objects.all()
    parent_model = AnnualPlan
    parent_field = 'annual_plan'

    def get_parent_queryset(self):          # OBLIGATORIO en Organilab
        return AnnualPlan.objects.filter(organization__in=self.request.user_orgs)

router.register(r'annual_plan/(?P<parent_pk>[^/.]+)/action',
                PlanActionManagement, 'api-annualplan-action')
```

---

## 4. Cinco cosas que hay que tener claras al integrarlo

1. **`HistoryViewSet` no sabe de organizaciones.** Filtra por `GT_HISTORY_ALLOWED_MODELS` y por un
   parámetro `contenttype`, nada más: cualquier usuario con `admin.view_logentry` vería la bitácora
   de **todas** las organizaciones. Esto no es un defecto de la biblioteca: es la parte que le toca
   al proyecto, y **ya está resuelta** por el proyecto 13 (`roadmap/13_HISTORY_TRASH.md`): la lib
   ganó el hook `scope_queryset()` y organilab lo implementa en `LogEntryViewSet`
   (`src/laboratory/api/views.py`) cruzando con `HistoryRelation`, que sustituyó al `LabOrgLogEntry`
   propio.

2. **`BaseViewSetWithLogs.perform_destroy` exige un atributo no documentado.** Hace
   `if instance._meta.verbose_name.title() in self.models_log:` y `models_log` no está definido en la
   clase (`djgentelella/history/api.py:63`); sin declararlo en la subclase, borrar lanza
   `AttributeError`. Declararlo siempre, o sobreescribir `perform_destroy` como muestra
   `docs/source/trash.rst`.

3. **`HistoryViewSet.get_queryset()` revienta si `GT_HISTORY_ALLOWED_MODELS` no está definido** y
   alguien pasa `?contenttype=…`: evalúa `ctypes_param in allowed` con `allowed = None`. Definir
   siempre el setting.

4. **La papelera solo guarda quién borró si se le pasa el usuario.** `perform_destroy` de DRF llama a
   `instance.delete()` sin argumentos y `deleted_by` queda en `NULL`. Hay que sobreescribirlo con
   `instance.delete(user=self.request.user)`.

5. **Toda acción personalizada necesita su entrada en `perms`.** `AllPermissionByAction` devuelve 403
   cuando la acción no está en el diccionario (`perms.get(action) is None`). Los `@action` que
   agreguen los planes —`restore`, `dependents`, `follow_up`— deben declararse ahí o responden 403
   sin explicación.

---

## 5. Decisiones que abre la actualización (fuera del alcance de los planes)

- **Correos: migrar o convivir.** `async-notifications==0.2` (app `async_notifications`) y
  `djgentelella.async_notification` son apps distintas, con tablas distintas. Las plantillas actuales
  de Organilab se crean en migraciones (`laboratory/migrations/0203_*`, `0204`, `0205`, `0043`,
  `0041`, `0044`) y `CELERYBEAT_SCHEDULE` apunta a `async_notifications.tasks.send_daily`
  (`settings.py:306`). Los planes asumen que **los módulos nuevos usan la de djgentelella**; migrar
  lo existente es un trabajo aparte que hay que decidir y presupuestar.
- **`GTForeignKey` duplicado.** `src/laboratory/catalog/__init__.py` es una copia de
  `djgentelella.fields.catalog`. Los módulos nuevos deben importar el de la biblioteca; unificar los
  existentes es opcional y no urgente.
- **Menús.** Los planes originales agregaban plantillas parciales. Con `MenuItem` en base de datos el
  menú se siembra por migración y respeta permisos solo. Conviene decidir si los módulos nuevos
  estrenan el mecanismo o siguen el patrón actual de Organilab por consistencia visual.
- **La salida de `django-markitup` sí toca a Organilab, y es lo más delicado de la actualización.**
  0.6.0 saca `django-markitup` del blog y deja de instalarlo, pero Organilab lo tiene cableado en
  cuatro puntos: `INSTALLED_APPS` incluye `"markitup"` y `"djgentelella.blog"`
  (`src/organilab/settings.py:91,93`), `src/organilab/urls.py:89` incluye `markitup.urls`, y dos
  settings apuntan al widget: `ASYNC_NOTIFICATION_TEXT_AREA_WIDGET` y `ASYNC_NEWSLETTER_WIDGET`
  (`settings.py:300,348`, más `MARKITUP_SET` en `:350`). Antes de actualizar hay que: cambiar esos
  dos widgets por `EditorTinymce`, decidir si el blog se conserva —su migración `blog.0002` mueve el
  HTML de las columnas `_resume_rendered`/`_content_rendered` y luego las borra, **no es reversible**
  y su `DROP COLUMN` exige SQLite 3.35+ (en PostgreSQL no aplica)— y **respaldar las tablas del blog**.
  Si el blog no se usa, lo limpio es sacarlo de `INSTALLED_APPS` antes de subir de versión.
  Ojo también con la advertencia del changelog: los cuerpos del blog pasan a servirse como HTML sin
  sanitizar, así que `blog.add_entry`/`change_entry` solo deben tenerlo autores de confianza.
- **Otros cambios que rompen y que Organilab no usa hoy** (verificado con `grep` sobre `src/`): se
  eliminó `InlineAjaxCRUD` junto con `inlines` de `CRUDView` y el tag `crud_inline_url`; los campos
  de árbol dejaron de ser widgets y ahora son *form fields*; se soltaron `djangoajax` y `markdown`.
