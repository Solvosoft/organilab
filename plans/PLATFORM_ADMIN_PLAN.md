# Administración de plataforma — bitácora, configuración y ayuda en línea

> **Qué es esto.** Diseño de seis funciones transversales de Organilab: una **bitácora de auditoría**
> realmente consultable, **justificación obligatoria** en cambios sensibles, **parámetros del sistema
> por organización**, **notificaciones administrables**, **alertas configurables** y una **ayuda en
> línea** completa (manual con video, preguntas frecuentes, "Acerca de").
>
> Léelo junto a [`AGENT_BRIEFING.md`](AGENT_BRIEFING.md). Los planes
> [`ENVIRONMENT_PLAN.md`](ENVIRONMENT_PLAN.md) y [`MANAGEMENT_PLANS_PLAN.md`](MANAGEMENT_PLANS_PLAN.md)
> dependen de las funciones C, D y E de este documento.
>
> **Principio rector: reutilizar, no reinventar.** Se construye sobre **djgentelella 0.6.0**
> (`djgentelella.history`, `djgentelella.trash`, `djgentelella.async_notification`,
> `djgentelella.notification`, `MenuItem`) y sobre lo que Organilab ya tiene
> (`organilab_logentry`, `HistoryRelation`, `Catalog`, `PendingTask`, `REPORT_FORMS`, `Tutorial`).
> Ver [`DJGENTELELLA_060_NOTES.md`](DJGENTELELLA_060_NOTES.md) para el detalle de cada pieza y las
> trampas conocidas.

---

## 0. El problema

Organilab hace bien el trabajo invisible y mal el visible:

- **Registra** cada acción del usuario (≈280 llamadas a `organilab_logentry`) pero el administrador
  **no puede consultarla**: la pantalla de bitácora solo muestra movimientos de laboratorios y
  organizaciones; lo que pasa en sustancias, riesgo, reservaciones o formularios se graba y no se ve.
- **Sabe qué campo cambió** pero no **a qué valor** ni **por qué**.
- **Envía correos** cuyas plantillas solo puede editar un desarrollador, en una migración.
- **Dispara alertas** (vencimientos, límites de inventario, precursores) con umbrales escritos en el
  código, iguales para toda organización.
- **No tiene dónde poner una preferencia por organización** sin agregar un campo o un modelo nuevo.
- **Enseña a usarse** solo con tutoriales interactivos: no hay video, ni preguntas frecuentes, ni una
  pantalla que diga qué versión se está usando.

Este plan cierra esos seis huecos sin crear un app nuevo.

---

## 0.1 Decisiones tomadas

- **Sin app nueva.** Ayuda y configuración viven en `src/presentation/`; bitácora y justificación en
  `src/laboratory/`, junto a la auditoría existente.
- **La bitácora no cambia de motor.** Sigue siendo `django.contrib.admin.LogEntry`; el proyecto 13
  (`roadmap/13_HISTORY_TRASH.md`) ya sustituyó el `LabOrgLogEntry` propio por la `HistoryRelation`
  de la biblioteca. Se amplía la **consulta**, no la captura. La consulta se arma sobre
  `djgentelella.history`, que usa exactamente ese motor.
- **La justificación es opt-in por modelo**, nunca global: solo donde el cambio arrastra registros
  dependientes.
- **Los catálogos administrables usan el modelo `Catalog`** (`src/laboratory/models.py:52`,
  `key`+`description`, global) vía `GTForeignKey`, igual que IPER. No se crean modelos de catálogo
  propios. En los módulos nuevos se importa el de la biblioteca
  (`djgentelella.fields.catalog.GTForeignKey`), no la copia local de `src/laboratory/catalog/`.
- **Los correos de los módulos nuevos usan `djgentelella.async_notification`**, no la app externa
  `async_notifications` que hoy usa Organilab. Migrar lo existente es un trabajo aparte
  ([`DJGENTELELLA_060_NOTES.md`](DJGENTELELLA_060_NOTES.md) §5).
- **El borrado lógico se hace con `DeletedWithTrash`**, no con campos `is_active` improvisados.

---

## A. Bitácora de auditoría consultable y exportable

### Qué hace

Una pantalla donde un administrador responde, sobre **cualquier módulo** de su organización: *quién
tocó qué, cuándo, desde qué proceso, qué valor tenía antes y qué valor tiene ahora* — y se lleva el
resultado en Excel o PDF.

### Flujo de interacción

**Actor:** administrador de organización (permiso `laboratory.view_full_audit_log`).

1. Entra por *Administración → Bitácora*. La pantalla abre con los **últimos 30 días** de su
   organización y sus organizaciones hijas, ordenados del más reciente al más antiguo.
2. La tabla muestra: `Fecha y hora | Usuario | Módulo | Tipo de registro | Registro | Acción | Detalle`.
   La columna *Acción* es un badge de color: verde "Creación", azul "Modificación", rojo "Eliminación".
3. Filtra combinando: rango de fechas, usuario (busca por nombre, apellido o username), **módulo**
   (Laboratorio, Sustancias, Riesgo, Reservaciones, Formularios, Tareas…), **tipo de registro**
   dentro del módulo, tipo de acción y texto libre.
4. Hace clic en una fila y se abre un panel lateral con el **detalle del cambio**:

   | Campo | Antes | Después |
   |-------|-------|---------|
   | Cantidad | 250 ml | 180 ml |
   | Estante | A-3 | B-1 |

   Si el cambio exigió justificación (función B), el panel muestra además el texto escrito por quien
   lo hizo y cuántos registros dependientes había en ese momento.
5. Desde cualquier registro del sistema (una sustancia, un laboratorio, una evaluación) hay un botón
   **"Ver historial"** que abre esta misma pantalla ya filtrada por ese registro. No existe una
   segunda pantalla de "histórico": es la bitácora con un filtro puesto.
6. Presiona **Exportar** y elige PDF, Excel u ODS. El archivo se genera en segundo plano y aparece
   en la bandeja de reportes del usuario cuando está listo, igual que el resto de reportes.

**Regla de aislamiento:** un usuario nunca ve entradas de organizaciones que no le corresponden.
Sin el permiso ampliado, la bitácora sigue mostrando solo lo que muestra hoy.

### Diseño en Organilab

La biblioteca ya trae la mitad de esto: `djgentelella.history` aporta el viewset, el filterset, el
serializer y la pantalla completa (tabla + filtros + selector de categoría), documentada en
`docs/source/history.rst`. Lo que **no** trae —y es justo lo que le toca a Organilab— es el alcance
multi-tenant.

| Pieza | Origen | Trabajo |
|-------|--------|---------|
| Viewset base | `djgentelella.history.api.HistoryViewSet` | **Ya hecho** por el proyecto 13: `LogEntryViewSet` (`src/laboratory/api/views.py`) subclasea el viewset de la lib y acota por `scope_queryset()` con un join a `HistoryRelation` (org de la URL + laboratorios de esa org), con `recordsTotal` también acotado. `get_logentries_org_management()` fue eliminada. Lo que falta para esta pantalla es solo extender el alcance a las **organizaciones descendientes** (el árbol ya es `TreeNode`) |
| Modelos vigilados | `GT_HISTORY_ALLOWED_MODELS` en `settings.py` | Declarar la lista, incluyendo `"djgentelella.trash"`. **Es obligatorio**: sin el setting, `HistoryViewSet.get_queryset()` falla al recibir `?contenttype=…` |
| Filtros | `history.filterset.HistoryFilterSet` | Ya filtra por fecha, usuario, acción y texto. Extender con `content_type__app_label` / `content_type__model` para el filtro por módulo |
| Selector de módulo | `HistoryFilterForm` (patrón de `docs/source/history.rst`) | Formulario `GTForm` con las apps de Organilab etiquetadas en español; el JS lo inyecta en el filtro del datatable |
| Pantalla | `ObjectCRUD` + `docs/source/history.rst` | Copiar la configuración de columnas del ejemplo y agregar la columna de detalle antes→después |
| Valor anterior → nuevo | Propio | `add_log()` de la biblioteca no guarda valores, solo nombres de campo. Se mantiene el plan: nueva `get_field_diffs(old_values, instance)` en `src/laboratory/utils.py` que devuelve `{campo: {"old": …, "new": …}}` (el antiguo `get_changed_fields()` se borró: nunca tuvo llamadores). **Las ≈280 llamadas a `organilab_logentry` no se tocan.** `organilab_logentry()` serializa `[{"changed": {"fields": [...], "diffs": {...}}}]`, compatible con el parser de Django admin |
| Serializer | `history.serializers.HistorySerializer` | Subclasificar para exponer `diffs` y `justification` |
| Exportación | `src/report/register.py` | Registrar `report_audit_log` con `html`/`pdf`/`xls`/`xlsx`/`ods`; formulario en `src/report/forms.py`, vistas en `src/report/views/audit.py` clonadas de `object_changes.py`; tarea `report.tasks.task_report` |

**Captura de eventos en los módulos nuevos.** Los viewsets de los planes de programas y de consumos
extienden `djgentelella.history.api.BaseViewSetWithLogs`, que registra create / update / delete sin
escribir una línea. Dos advertencias: hay que declarar el atributo `models_log` en la subclase (la
clase base lo lee y no lo define, y borrar sin él lanza `AttributeError`), y conviene sobreescribir
`perform_destroy` para pasar `user=` a `delete()`, si no la papelera no guarda quién borró.

**Papelera.** Con `GT_HISTORY_ALLOWED_MODELS` incluyendo `djgentelella.trash`, la bitácora muestra
también los borrados lógicos, las restauraciones (acción 5) y los borrados definitivos (acción 4).
La pantalla de papelera es `TrashViewSet` + la configuración de `docs/source/trash.rst`; hay que
filtrarla por organización igual que la bitácora.

**Tests** (`src/laboratory/tests/test_logentry.py`): cobertura multi-app, aislamiento entre
organizaciones, `diffs` presentes en el serializer, exportación genera archivo.

---

## B. Justificación de cambios sensibles

### Qué hace

Cuando alguien modifica o desactiva un registro del que **cuelgan otros**, el sistema le advierte
cuántos quedarán afectados, le exige escribir por qué, avisa a los responsables de lo afectado y deja
todo eso en la bitácora.

### Flujo de interacción

**Actor:** quien edita un catálogo, un parámetro, un eje de programa o una acción con dependientes.

1. Abre el formulario de edición normalmente. Nada cambia si el registro no tiene dependientes.
2. Al presionar **Guardar**, si hay dependientes, aparece un modal:

   > ⚠️ **Este cambio afecta 14 registros**
   > 8 acciones y 6 actividades dependen de "Eje 2 — Manejo de residuos".
   > [Ver detalle]
   >
   > **Justificación del cambio** *(obligatorio)*
   > `___________________________________`
   >
   > [Cancelar] [Guardar con justificación]

3. "Ver detalle" despliega la lista de registros afectados con enlace a cada uno; el usuario puede
   cancelar sin perder lo que escribió en el formulario.
4. Al confirmar: se guarda el cambio, se registra en la bitácora con la justificación y el conteo de
   afectados, y **se crea una tarea pendiente** a cada responsable de los registros dependientes
   ("El eje del que dependen tus actividades fue modificado — revisar").
5. Ese responsable ve la tarea en su bandeja de pendientes con enlace directo al registro modificado
   y a la entrada de bitácora que la explica.

### Diseño en Organilab

```python
# src/laboratory/models.py
class ChangeJustification(models.Model):
    log_entry = models.OneToOneField("admin.LogEntry", on_delete=models.CASCADE)
    justification = models.TextField(verbose_name=_("Justification"))
    affected_records = models.PositiveIntegerField(default=0)
```

- Mixin `JustifiedUpdateMixin` en `src/laboratory/views/djgeneric.py`. La vista concreta implementa
  `get_dependents(obj) -> QuerySet`; el mixin se encarga del resto: si hay dependientes, agrega el
  campo `justification` como obligatorio, crea el `ChangeJustification` tras
  `organilab_logentry(...)` y lanza las tareas con `create_pending_task()`
  (`src/pending_tasks/utils.py:12`).
- Endpoint `GET …/dependents/` que devuelve `{"count": n, "detail": [...]}`, consumido por el modal.
  Si el CRUD es el de la biblioteca, va como `@action(detail=True, methods=['get'])` en el viewset y
  **tiene que declararse en el diccionario `perms`**: `AllPermissionByAction` responde 403 a toda
  acción que no esté mapeada.
- En las pantallas construidas con `ObjectCRUD`, el modal es una acción de instancia
  (`object_actions`) que abre el formulario con el campo de justificación, siguiendo el patrón de
  `restore` documentado en `docs/source/trash.rst`.
- **Se aplica a:** parámetros del sistema (C), configuración de alertas (E), y programas / ejes /
  componentes / acciones del plan de gestión. **No** se aplica a inventario ni a operaciones de alta
  frecuencia: ahí el costo de fricción supera el beneficio.

---

## C. Parámetros del sistema por organización

### Qué hace

Un lugar único donde un administrador ajusta el comportamiento de Organilab para su organización
—cada cuántos meses toca renovar una evaluación, cuántos días antes avisar de un vencimiento, si el
adjunto es obligatorio— sin tocar `settings.py` ni pedirle un campo nuevo a un desarrollador.

### Flujo de interacción

**Actor:** administrador de organización (`presentation.change_systemparameter`).

1. Entra a *Administración → Parámetros del sistema*. Ve una tabla agrupada por módulo:
   `Parámetro | Descripción | Tipo | Valor | Origen`.
2. La columna **Origen** es la clave de la experiencia: dice `Propio`, `Heredado de <organización
   padre>` o `Valor por defecto del sistema`. Así el administrador entiende de dónde sale el número
   antes de cambiarlo.
3. Edita en línea. El campo se renderiza según el tipo declarado: un `switch` para booleanos, un
   `datepicker` para fechas, un numérico con validación para enteros. Un valor inválido se rechaza en
   el momento con el mensaje del tipo esperado.
4. Al guardar, si el parámetro tiene dependientes (p. ej. cambiar la periodicidad reprograma
   evaluaciones), entra el flujo de justificación (B).
5. Botón **Restaurar valor heredado** que borra el valor propio y devuelve la fila a su origen.
6. Todo cambio queda en la bitácora (A) con valor anterior y nuevo.

### Diseño en Organilab

```python
# src/presentation/models.py
class SystemParameter(AbstractOrganizationRef):
    DATA_TYPES = (("int", …), ("float", …), ("bool", …), ("str", …), ("date", …), ("json", …))
    key = models.SlugField(max_length=100)          # "iper_period_months"
    description = models.CharField(max_length=500)
    data_type = models.CharField(max_length=10, choices=DATA_TYPES)
    raw_value = models.TextField(blank=True)
    is_editable = models.BooleanField(default=True)

    class Meta:
        unique_together = [("organization", "key")]
```

- `clean()` valida `raw_value` contra `data_type`; `value` es una `@property` que castea.
- `get_parameter(org, key, default=None)` en `src/presentation/utils.py`: busca en la organización,
  luego en sus ancestros (`OrganizationStructure` es `TreeNode`), luego en `settings`. **Con caché
  por request** — la tabla de caché ya la crea `init_checks`. Esto evita sembrar N filas por org.
- Los módulos **declaran** sus parámetros (clave, descripción, tipo, defecto) en
  `src/presentation/parameters.py` con un registro por app, análogo a `REPORT_FORMS`; la pantalla
  lista el registro, no solo las filas existentes en base de datos.
- CRUD con `djgeneric.ListView`/`UpdateView` bajo `/perms/<org_pk>/parameters/`.
- `IPERConfig` (`src/risk_management/models.py:437`) se deja como está; se documenta que los
  parámetros nuevos van aquí. Migrarlo es trabajo aparte.

---

## D. Notificaciones administrables

### Qué hace

Permite a un administrador funcional **leer, editar, activar y desactivar** los correos que el
sistema envía, viendo qué variables puede usar en cada uno, sin tocar código.

### Flujo de interacción

**Actor:** administrador funcional.

1. Entra a *Administración → Notificaciones*. Ve la lista de **procesos** que envían correo:
   `Proceso | Asunto | Estado | Última modificación`. Ejemplos: "Solicitud de laboratorio creada",
   "Reactivo bajo el límite", "Recordatorio de evaluación de riesgo".
2. Abre uno. La pantalla se divide en dos:
   - **Izquierda**: asunto y cuerpo editables con el editor enriquecido que ya usa el módulo de
     informes.
   - **Derecha**: panel de **campos dinámicos** con las variables disponibles *para ese proceso*
     (`{{ laboratorio }}`, `{{ usuario }}`, `{{ fecha_vencimiento }}`…), cada una con su
     descripción. Un clic la copia al portapapeles o la inserta en el cursor.
3. Presiona **Previsualizar**: el sistema renderiza asunto y cuerpo con datos de ejemplo y los
   muestra tal como llegarán al correo. Si usó una variable inexistente, el guardado se rechaza
   señalando cuál.
4. Puede **desactivar** el proceso con un switch: el sistema deja de enviar ese correo para su
   organización, sin afectar a las demás.
5. Al guardar, el cambio queda en la bitácora.

### Diseño en Organilab

**Casi todo esto ya existe en `djgentelella.async_notification`** y no hay que escribirlo: el modelo
`EmailTemplate` (con `context_code` y `base_template`), la pantalla de administración
(`email_template_view`), el árbol de variables (`_model_tree.html` alimentado por el endpoint
`model-fields/`), la previsualización (`_preview_modal.html` + `preview.build_dummy_context()`), el
editor TinyMCE, la subida de imágenes y el envío con backend síncrono o Celery.

Lo que hay que hacer:

1. **Registrar cada proceso** en el `ready()` de su app:

```python
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

   Con eso la pantalla muestra sola las variables disponibles y la previsualización con datos
   ficticios. **No se escribe UI de notificaciones.**

2. **Agregar lo único que la biblioteca no tiene: el estado y el override por organización.**
   `EmailTemplate` es global; Organilab es multi-tenant:

```python
# src/presentation/models.py
class NotificationSetting(AbstractOrganizationRef):
    code = models.CharField(max_length=100)          # EmailTemplate.code
    is_active = models.BooleanField(default=True)
    override_subject = models.TextField(blank=True)
    override_message = models.TextField(blank=True)
```

3. **Punto de entrada único**: `presentation.utils.send_process_email(org, code, context, recipients)`
   consulta estado y overrides y delega en
   `djgentelella.async_notification.sending.send_email_from_template(code, recipient, context, …)`.

4. **Aviso dentro de la aplicación**: para lo que además debe verse en la campana del menú,
   `djgentelella.notification.create_notification()` crea la `Notification` del usuario. Se usa junto
   con `create_pending_task()`, no en lugar de él: la campana es para enterarse, la tarea pendiente
   es para trabajar.

> **Decisión previa.** Organilab hoy corre sobre la app externa `async-notifications==0.2`, que es
> otra app con otras tablas. Los módulos nuevos deben nacer sobre la de djgentelella; migrar las
> plantillas existentes (creadas en `laboratory/migrations/0203_*`, `0204`, `0205`, `0041`, `0043`,
> `0044`) y el `CELERYBEAT_SCHEDULE` que apunta a `async_notifications.tasks.send_daily` es un
> trabajo aparte — ver [`DJGENTELELLA_060_NOTES.md`](DJGENTELELLA_060_NOTES.md) §5.

---

## E. Alertas configurables

### Qué hace

Convierte las alertas hoy escritas en el código (vencimientos, límites de inventario) en **reglas
que el administrador define**: qué se vigila, con qué umbral, a quién se avisa y por qué medio.

### Flujo de interacción

**Actor:** administrador de organización.

1. Entra a *Administración → Alertas*. Ve las reglas activas:
   `Proceso | Disparador | Umbral | Notifica a | Estado`.
2. Crea una regla en un asistente de tres pasos:
   - **Paso 1 — Qué vigilar**: elige el proceso de una lista (los que cada módulo registró):
     "Vencimiento de sustancias", "Consumo atípico", "Actividad por vencer".
   - **Paso 2 — Cuándo disparar**: elige el disparador (variación porcentual / umbral absoluto / sin
     registro en el período) y llena solo los campos que ese disparador necesita —
     `días antes = 30`, `variación = 20 %`.
   - **Paso 3 — A quién avisar**: selecciona roles y/o el responsable del registro afectado, marca si
     además se crea una tarea pendiente, y elige la plantilla de correo (de las de la función D).
3. Guarda. La regla queda activa; el switch de estado la apaga sin borrarla.
4. Cuando la tarea programada dispara la regla, el destinatario recibe el correo **y** ve la tarea en
   su bandeja de pendientes con enlace al registro que la originó.
5. En la misma pantalla, la pestaña **Historial** lista los disparos recientes de cada regla — sirve
   para calibrar el umbral cuando una alerta se vuelve ruido.

### Diseño en Organilab

```python
# src/presentation/models.py
class AlertRule(AbstractOrganizationRef):
    process = models.CharField(max_length=100)        # del registro de procesos (D)
    trigger = catalog.GTForeignKey(Catalog, key_value="alert_trigger", …)
    threshold = models.JSONField(default=dict)        # {"days_before": 30} / {"pct": 20}
    notification_code = models.CharField(max_length=100)
    notify_roles = models.ManyToManyField("auth_and_perms.Rol", blank=True)
    notify_responsible = models.BooleanField(default=True)
    create_task = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
```

- `process` referencia el **mismo código** que se registró con `register_context()` en la función D,
  de modo que la plantilla de correo y su lista de variables ya existen cuando se crea la regla.
- Las tareas Celery existentes (`CELERYBEAT_SCHEDULE` en `settings.py`: vencimientos, límites,
  precursores) pasan a **leer su `AlertRule`** en lugar de constantes: sin regla activa, no disparan.
- **Empezar migrando una sola**: vencimiento de `ShelfObject` (`src/laboratory/limit_shelfobject.py`),
  como prueba del patrón. Las demás se migran después, una por una, con su test.
- Al disparar: `send_process_email()` + `create_pending_task()` + —si la alerta amerita verse en el
  acto— `create_notification()` para la campana.
- La pantalla es un `ObjectCRUD` sobre un viewset `BaseViewSetWithLogs`, con el asistente de tres
  pasos como formulario en modal.
- El consumidor grande de esta función es el plan de consumos ([`ENVIRONMENT_PLAN.md`](ENVIRONMENT_PLAN.md) §E).

---

## F. Ayuda en línea

### Qué hace

Tres piezas que hoy faltan alrededor de los tutoriales interactivos existentes: **manual con video**,
**preguntas frecuentes** y una pantalla **"Acerca de"**.

### Flujo de interacción

**Manual de usuario** — actor: cualquier usuario.

1. Entra a *Ayuda → Manual de usuario*. Ve los temas agrupados por capítulo (los `chapter` que ya
   define `Tutorial`), filtrados por su rol: solo aparece lo que puede usar.
2. Cada tema muestra título, descripción, el **video explicativo** si lo tiene, y un botón
   **"Hacerlo paso a paso"** que inicia la guía interactiva existente sobre la pantalla real.
3. Un administrador técnico entra al mismo listado con permiso de edición y carga o reemplaza el
   video de cada tema, sin salir de la pantalla.

**Preguntas frecuentes** — actor: cualquier usuario.

1. Entra a *Ayuda → Preguntas frecuentes*. Ve un acordeón agrupado por categoría, con un buscador
   que filtra por texto de pregunta y respuesta mientras escribe.
2. El administrador funcional edita, reordena, activa o desactiva preguntas, y puede limitarlas a
   ciertos roles (vacío = todos).

**Acerca de** — actor: cualquier usuario.

1. Entra desde el menú de usuario. Ve nombre del sistema, descripción, **versión** (leída de
   `src/organilab/__init__.py`), fecha de última actualización, patrocinador y lista de colaboradores.
2. El administrador técnico edita los textos; la versión nunca se edita a mano.

### Diseño en Organilab

| Función | Cambio |
|---------|--------|
| Manual con video | **Extender `Tutorial`** (`src/presentation/models.py:79`), no crear módulo aparte: agregar `video_url` (URL o `FileField`) y `section`; `video_url` también en `TutorialStep` para pasos que lo ameriten. La agrupación por capítulo ya existe (`chapter`) |
| Preguntas frecuentes | Modelo `FAQ(AbstractRegistry, DeletedWithTrash)`: `question`, `answer` (HTML con `EditorTinymce`), `category` (`Catalog`, `key="faq_category"`), `order`, `target_roles` (M2M `Rol`). CRUD con `ObjectCRUD` + página pública `/faq/` con búsqueda `icontains`. El borrado es lógico vía papelera, no un campo `is_active` propio |
| Acerca de | Vista `about` en `src/presentation/views.py` + plantilla. Textos editables como `SystemParameter` (función C); versión leída del módulo |

Existe además la iniciativa de auto-tutoriales ya en curso; este plan **no la sustituye**, le agrega
el soporte de video y la FAQ.

---

## G. Orden de ejecución

| Paso | Entregable | Depende de | Tamaño |
|------|-----------|-----------|--------|
| 0 | Actualizar a djgentelella 0.6.0: `GT_HISTORY_ALLOWED_MODELS`, salida de `markitup`, revisión del blog ([`DJGENTELELLA_060_NOTES.md`](DJGENTELELLA_060_NOTES.md) §5) | — | M |
| 1 | Bitácora: subclase de `HistoryViewSet` con alcance por organización + filtros por módulo + `diffs` (A) | 0 | M |
| 2 | Bitácora: exportación registrada en `REPORT_FORMS` + pantalla de papelera (A) | 1 | S |
| 3 | `SystemParameter` + registro declarativo + `get_parameter()` + pantalla (C) | — | M |
| 4 | `ChangeJustification` + `JustifiedUpdateMixin` + modal de advertencia (B) | 1 | M |
| 5 | Ayuda: FAQ + "Acerca de" + video en `Tutorial` (F) | — | S |
| 6 | Registro de procesos + `NotificationSetting` + pantalla de notificaciones (D) | 3 | M |
| 7 | `AlertRule` + asistente + migración de la alerta de vencimientos (E) | 6 | M |

Los pasos 1–2, 3 y 5 son independientes y se pueden paralelizar.

---

## H. Checklist transversal

- [ ] Modelos org-scoped heredan `AbstractOrganizationRef` (`src/presentation/models.py:8`).
- [ ] Vistas HTML heredan de `src/laboratory/views/djgeneric.py` (chequeo de org/lab gratis); las de
      API extienden `BaseViewSetWithLogs` con `models_log` declarado.
- [ ] Cada `@action` personalizado tiene su entrada en el diccionario `perms` — si no, responde 403.
- [ ] Permisos nuevos en `Meta.permissions`, sincronizados con `load_urlname_permissions` y
      `update_roles`.
- [ ] Toda escritura queda registrada: `organilab_logentry(...)` en las vistas propias,
      `BaseViewSetWithLogs` en los viewsets nuevos. Si no, no aparece en la bitácora.
- [ ] Modelos con borrado lógico heredan `DeletedWithTrash`, sus formularios excluyen `is_deleted` y
      su `perform_destroy` pasa `user=self.request.user`.
- [ ] Modelo nuevo que deba auditarse: agregarlo a `GT_HISTORY_ALLOWED_MODELS`.
- [ ] Strings con `gettext`; luego `make messages && make trans`.
- [ ] Tests en `src/<app>/tests/`; `make single-test TEST=…` y `make lint` (línea máx. 200).
- [ ] Pantallas nuevas enlazadas en `src/presentation/templates/partials/` o
      `gentelella/app/administration_menu.html` (o sembradas como `MenuItem`, si se adopta el
      mecanismo de la biblioteca).
