# Programas de gestión — planificación, asignación y seguimiento del cumplimiento

> **Qué es esto.** Diseño de un módulo nuevo (`src/management_plans/`) que le da a Organilab lo que
> hoy no tiene: un lugar donde **planificar** el trabajo de cumplimiento de un laboratorio o de una
> organización, **repartirlo** entre responsables con fechas, **darle seguimiento mensual con
> evidencias** y **medir cuánto se avanzó**, por laboratorio y por rama del árbol organizacional.
>
> Léelo junto a [`AGENT_BRIEFING.md`](AGENT_BRIEFING.md). Usa las funciones de
> [`PLATFORM_ADMIN_PLAN.md`](PLATFORM_ADMIN_PLAN.md) (justificación de cambios, parámetros, alertas)
> y se conecta con [`ENVIRONMENT_PLAN.md`](ENVIRONMENT_PLAN.md). La base técnica es
> **djgentelella 0.6.0**: ver [`DJGENTELELLA_060_NOTES.md`](DJGENTELELLA_060_NOTES.md) antes de
> escribir el primer modelo.

---

## 0. El problema

Organilab **produce hallazgos** todo el tiempo: una evaluación IPER identifica un riesgo intolerable,
un incidente exige una acción correctiva, un reactivo cae bajo el límite, un informe periódico
detecta una no conformidad. Hoy todos esos hallazgos mueren en su propia pantalla. No hay dónde
decir *"esto se corrige así, lo hace fulano, para marzo, y en junio revisamos si se hizo"*.

Lo más parecido que existe son las **tareas pendientes**, que sirven como buzón pero no tienen fecha
de vencimiento, ni porcentaje de avance, ni evidencia, ni jerarquía, ni forma de agregarse en un
indicador de cumplimiento.

Este módulo aporta ese esqueleto, y lo hace **genérico**: sirve igual para un plan de gestión de
residuos, un programa de seguridad, una preparación de acreditación o el plan anual de un
laboratorio.

---

## 1. El modelo mental

```
Programa de gestión            "Plan de Gestión de Residuos 2026–2028"   (plurianual)
  └── Eje                      "Manejo de residuos peligrosos"
        └── Componente         "Almacenamiento temporal"        (nivel opcional)
              └── Acción       "Rotular todos los contenedores"  ← vive en un PLAN ANUAL
                    └── Actividad  "Comprar etiquetas resistentes"  ← tiene responsable y fechas
                          └── Seguimiento  "Marzo: 40 % — compra aprobada" + evidencias
```

Tres reglas que definen todo el comportamiento:

1. **El programa es plurianual; el trabajo es anual.** Un programa 2026–2028 tiene tres *planes
   anuales*. La suma de sus planes determina el cumplimiento del programa.
2. **Los niveles intermedios son opcionales.** Un programa simple puede ir directo de eje a acción,
   sin componentes. El cálculo de avance lo contempla.
3. **La actividad es la unidad de trabajo real**: es lo único que tiene responsable, fechas y
   porcentaje. Todo lo de arriba es agregación.

### Vocabulario y decisiones tomadas

- **App nueva `src/management_plans/`.** `risk_management` ya carga dos dominios (riesgo + IPER).
- **Modelos dedicados, no `derb`.** Formio sirve para contenido variable; aquí la estructura es fija
  y hay que **agregar y comparar** (porcentajes, rankings), lo que exige columnas reales. Misma
  decisión que se tomó en IPER.
- **Las tareas pendientes son el buzón, no el modelo.** Cada actividad crea y mantiene una
  `PendingTask` para que el responsable la vea donde ya mira su trabajo; la actividad vive en este
  módulo porque necesita fechas, avance e historial.
- **Los estados son `Catalog`** (`key="mgmt_progress_status"`), administrables desde la UI, no
  `choices` en código, declarados con `djgentelella.fields.catalog.GTForeignKey`.
- **La jerarquía se administra con `BaseInlineObjectManagement`** (djgentelella 0.6.0): cada nivel es
  un CRUD sobre los hijos de un padre, con el `parent_pk` en la URL. Es exactamente la forma que
  tiene este módulo, y evita escribir el andamiaje de listado/modales nivel por nivel.
- **Nada se borra físicamente.** Programas, ejes, componentes, acciones, actividades y documentos
  heredan `DeletedWithTrash`: se marcan como borrados, se pueden restaurar desde la papelera y el
  movimiento queda en la bitácora.

---

## 2. Funciones y flujos de interacción

### 2.1 Definir un programa de gestión

**Actor:** administrador de organización.

1. Entra a *Programas de gestión → Nuevo programa*. Llena: código, siglas, nombre, tipo (catálogo),
   **año inicial y año final**, descripción, responsable general y —opcionalmente— los laboratorios
   a los que aplica. Si no elige laboratorios, el programa es de toda la organización.
2. Guarda y cae en la **vista de estructura**: un árbol editable a la izquierda, el detalle a la
   derecha.
3. Agrega ejes con el botón **+ Eje** (código, detalle, orden). Dentro de cada eje puede agregar
   componentes, o dejarlo vacío si ese eje no los necesita — la interfaz nunca obliga a crear un
   nivel intermedio.
4. Reordena por *drag and drop*; el orden se refleja en todos los reportes.
5. Al **modificar o desactivar** un eje o componente que ya tiene acciones colgando, aparece la
   advertencia con conteo de afectados y **justificación obligatoria**
   ([`PLATFORM_ADMIN_PLAN.md`](PLATFORM_ADMIN_PLAN.md) función B). Los responsables de lo afectado
   reciben una tarea de revisión.
6. En la pestaña **Documentos** adjunta archivos al programa (política, norma de referencia,
   certificados). Los documentos se descargan, se reemplazan y se **desactivan** — nunca se borran
   físicamente, para no romper la trazabilidad de lo que se usó como evidencia.

### 2.2 Armar el plan anual

**Actor:** administrador de organización.

1. Entra a *Planes anuales → Nuevo*. Elige el programa; el sistema **muestra su vigencia** y ofrece
   solo los años dentro de ella que aún no tienen plan.
2. Elige el año, pone nombre, objetivo y alcance.
3. Agrega **acciones**. Por cada una: elige el eje (y el componente si existe), escribe nombre y
   descripción, asigna **responsable** y **dependencia** —una unidad del árbol organizacional— y
   define el plazo (fecha de inicio y fecha límite).
4. Si la acción consiste en registrar un consumo (agua, electricidad, residuos…), marca el **tipo de
   recurso**. Eso habilita más adelante el acceso directo al formulario de registro
   ([`ENVIRONMENT_PLAN.md`](ENVIRONMENT_PLAN.md)).
5. Guarda. Cada acción con responsable dispara una notificación: *"Se te asignó una acción del plan
   anual 2026"*, con enlace.
6. **Vista de tablero**: el plan se puede ver como tabla o como tablero por estado (pendiente / en
   proceso / cumplida / atrasada), con filtro por eje, responsable y dependencia.

### 2.3 Registrar las actividades de una acción

**Actor:** responsable de la acción.

1. Entra a *Mi trabajo → Mis acciones*. Ve solo lo asignado a él, ordenado por fecha límite, con las
   acciones atrasadas en rojo arriba.
2. Abre una acción y agrega una o más **actividades**: nombre, descripción, responsable de ejecución
   (puede delegar en otra persona), fecha de inicio, fecha de vencimiento.
3. Al guardar, cada actividad crea automáticamente una **tarea pendiente** para su responsable de
   ejecución, con enlace a la pantalla de seguimiento.
4. Puede editar fechas y responsables mientras la actividad no esté cerrada; cada cambio queda en la
   bitácora.

### 2.4 Dar seguimiento

**Actor:** responsable de ejecución. Es el flujo más frecuente del módulo, y por eso el más corto.

1. Entra desde su tarea pendiente o por *Mi trabajo → Seguimiento*. La pantalla ya viene filtrada a
   **sus** actividades: no tiene que navegar programa → plan → eje → acción para llegar a lo suyo.
2. Elige la actividad y registra:
   - **Mes de seguimiento** (precargado con el mes actual)
   - **Detalle** de lo hecho
   - **Estado de avance** (catálogo) y **porcentaje** (0–100, con un *slider*)
   - **Evidencias**: uno o varios archivos con descripción
   - Observaciones
3. Si la acción está marcada con un tipo de recurso, aparece un botón **"Registrar el consumo"** que
   lleva al formulario correspondiente con el período ya precargado, y al volver el consumo queda
   citado como evidencia del seguimiento.
4. Al guardar, el porcentaje sube por toda la jerarquía: la acción, el componente, el eje, el plan y
   el programa recalculan su avance.
5. Cuando una actividad llega al 100 %, su tarea pendiente se cierra sola y el responsable de la
   acción recibe el aviso.
6. La actividad conserva su **línea de tiempo**: todos los seguimientos en orden, con quién los
   registró y qué evidencia adjuntó. Nada se sobrescribe.

### 2.5 Reasignar trabajo

**Actor:** administrador.

1. Entra a *Planes anuales → Traslado de responsable*. Elige la persona que sale y la que entra.
2. El sistema lista todas sus acciones y actividades **abiertas**, con casillas de selección.
3. Selecciona qué se traslada y confirma. Se reasignan los registros, se cierran las tareas
   pendientes de quien sale y se crean las de quien entra, y todo queda en bitácora con la
   justificación escrita en el mismo paso.

Este flujo existe porque la rotación de personal es la causa más común de que un plan quede
huérfano y el avance se congele sin que nadie lo note.

### 2.6 Cerrar el año

**Actor:** administrador, al crear el plan del año siguiente.

1. Al elegir el año N+1 de un programa que ya tuvo plan en el año N, el sistema pregunta:

   > **Hay 12 actividades sin concluir en el plan 2026.**
   > ¿Qué desea hacer?
   > ( ) Arrastrarlas al plan 2027 conservando su avance
   > ( ) Arrastrarlas reiniciando el avance en 0 %
   > ( ) No arrastrar nada

2. Si arrastra, cada actividad nueva queda **encadenada a la anterior**, de modo que en el histórico
   se ve que viene de 2026 y cuánto llevaba.
3. El plan del año anterior pasa a estado *cerrado*: sigue consultable, ya no editable.

### 2.7 Consultar el cumplimiento

**Actor:** administrador, coordinador o analista (rol de solo lectura).

1. **Por programa**: avance global, avance por eje y por componente, actividades evaluadas /
   cumplidas / pendientes, fecha de última actualización. Gráfico de barras por eje.
2. **Por plan anual**: avance desagregado hasta actividad, con una sección destacada de **atrasos y
   desviaciones** (actividades vencidas sin cerrar, o con avance menor al esperado según el tiempo
   transcurrido).
3. **Por persona**: carga de trabajo y cumplimiento de cada responsable, con sus actividades, fechas
   y porcentajes. Sirve para detectar sobrecarga, no solo incumplimiento.
4. **Por dependencia**: avance consolidado por unidad del árbol organizacional, sumando hacia arriba
   (una dirección incluye lo de sus departamentos), y **ranking** de unidades por cumplimiento.
5. **Histórico de cambios**: no es una pantalla nueva — el botón "Ver historial" abre la bitácora
   filtrada por ese programa o plan, con valores anteriores y justificaciones
   ([`PLATFORM_ADMIN_PLAN.md`](PLATFORM_ADMIN_PLAN.md) funciones A y B).
6. Todas estas consultas se **exportan** a PDF, Excel u ODS y traen su gráfico.

### 2.8 Recordatorios automáticos

Una tarea programada revisa diariamente las actividades y avisa según las reglas configuradas
([`PLATFORM_ADMIN_PLAN.md`](PLATFORM_ADMIN_PLAN.md) función E):

- Actividad **por vencer** (N días antes, N configurable por organización).
- Actividad **vencida** sin seguimiento.
- Plan anual **sin ningún seguimiento** en el último mes.

Cada aviso llega como correo y como tarea pendiente, con enlace directo a la pantalla de seguimiento.

---

## 3. Diseño en Organilab

### 3.1 Modelos (`src/management_plans/models.py`)

```python
class ManagementProgram(AbstractOrganizationRef, DeletedWithTrash):
    code = models.CharField(max_length=50)
    acronym = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=255)
    program_type = catalog.GTForeignKey(Catalog, key_value="mgmt_program_type", …)
    start_year / end_year = models.PositiveSmallIntegerField()
    description = models.TextField(blank=True)
    responsible = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    laboratories = models.ManyToManyField(Laboratory, blank=True)   # vacío = toda la org

    class Meta:
        unique_together = [("organization", "code")]


class ProgramAxis(DeletedWithTrash):             # Eje
    program = models.ForeignKey(ManagementProgram, related_name="axes", …)
    code / detail / order


class ProgramComponent(DeletedWithTrash):        # Componente (nivel opcional)
    axis = models.ForeignKey(ProgramAxis, related_name="components", …)
    code / detail / order


class AnnualPlan(AbstractOrganizationRef, DeletedWithTrash):
    program = models.ForeignKey(ManagementProgram, related_name="annual_plans", …)
    year = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=255)
    objective / scope = models.TextField(blank=True)
    status = catalog.GTForeignKey(Catalog, key_value="mgmt_plan_status", …)

    class Meta:
        unique_together = [("program", "year")]


class PlanAction(AbstractOrganizationRef, DeletedWithTrash):
    annual_plan = models.ForeignKey(AnnualPlan, related_name="actions", …)
    axis = models.ForeignKey(ProgramAxis, null=True, blank=True, …)
    component = models.ForeignKey(ProgramComponent, null=True, blank=True, …)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    responsible = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    dependency = models.ForeignKey(OrganizationStructure, null=True, …)
    laboratory = models.ForeignKey(Laboratory, null=True, blank=True, …)
    start_date / due_date = models.DateField()
    status = catalog.GTForeignKey(Catalog, key_value="mgmt_progress_status", …)
    resource_type = catalog.GTForeignKey(Catalog, key_value="env_resource_type",
                                         null=True, blank=True, …)
    observations = models.TextField(blank=True)
    # origen del hallazgo que motivó la acción (§3.3)
    source_content_type = models.ForeignKey(ContentType, null=True, blank=True, …)
    source_object_id = models.PositiveIntegerField(null=True, blank=True)
    source_object = GenericForeignKey("source_content_type", "source_object_id")


class PlanActivity(AbstractOrganizationRef, DeletedWithTrash):
    action = models.ForeignKey(PlanAction, related_name="activities", …)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    responsible = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    start_date / due_date = models.DateField()
    progress_status = catalog.GTForeignKey(Catalog, key_value="mgmt_progress_status", …)
    progress_pct = models.PositiveSmallIntegerField(default=0)      # 0..100 con validators
    carried_from = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    pending_task = models.ForeignKey("pending_tasks.PendingTask", null=True, blank=True, …)


class ActivityFollowUp(AbstractOrganizationRef):
    activity = models.ForeignKey(PlanActivity, related_name="follow_ups", …)
    record_date = models.DateField(default=timezone.localdate)
    follow_month = models.PositiveSmallIntegerField()               # 1..12
    detail = models.TextField()
    progress_status = catalog.GTForeignKey(Catalog, key_value="mgmt_progress_status", …)
    progress_pct = models.PositiveSmallIntegerField()
    observations = models.TextField(blank=True)


class FollowUpEvidence(models.Model):
    follow_up = models.ForeignKey(ActivityFollowUp, related_name="evidences", …)
    file = models.FileField(upload_to=upload_files)
    description = models.CharField(max_length=255, blank=True)


class ProgramAttachment(AbstractOrganizationRef, DeletedWithTrash):
    program = models.ForeignKey(ManagementProgram, related_name="attachments", …)
    name / document_type (Catalog) / file (FileField) / description
    # el borrado lógico y la restauración los aporta DeletedWithTrash
```

**Reglas de negocio en el modelo**

- `clean()` de `ManagementProgram`: `end_year >= start_year`.
- Guardar un `ActivityFollowUp` actualiza `progress_pct` y `progress_status` de su actividad: el
  seguimiento es la fuente de verdad, la actividad cachea el último valor por rendimiento.
- Actividad al 100 % → su `PendingTask` pasa a `FINISHED`.
- `dependency` apunta al árbol organizacional que Organilab **ya tiene**: no hace falta un catálogo
  paralelo de unidades. En el formulario se selecciona con `GentelellaTreeNodeChoiceField`, que
  indenta cada opción según su profundidad — está reconstruido sobre `django-tree-queries`, que es
  justo lo que usa `OrganizationStructure`. Se declara **como campo**, no como `widget=`.
- `objects` de estos modelos ya excluye lo borrado (lo aporta `DeletedWithTrash`); usar
  `objects_with_deleted` solo en reportes históricos.

### 3.1.1 Capa de API y pantallas

| Nivel | Viewset | Notas |
|-------|---------|-------|
| Programa, plan anual | `BaseViewSetWithLogs` (extiende `AuthAllPermBaseObjectManagement`) | Declarar `models_log`; `perform_destroy` propio que pase `user=self.request.user` |
| Eje ← programa, componente ← eje, acción ← plan, actividad ← acción, seguimiento ← actividad | **`BaseInlineObjectManagement`** | Un viewset por relación, registrado con el padre en la URL: `router.register(r'annual_plan/(?P<parent_pk>[^/.]+)/action', …)` |
| Alcance multi-tenant | `get_parent_queryset()` | **Obligatorio.** Sin él, cualquier usuario con permiso del modelo puede nombrar el `parent_pk` de otra organización y leer o escribir sus datos — está advertido en el docstring de la clase |
| Permisos | diccionario `perms` por acción | Incluir también las acciones personalizadas (`restore`, `dependents`, `transfer`), o responden 403 |

Las pantallas se arman con `ObjectCRUD` + `gentelella/blocks/modal_template*.html`
(`docs/source/object_management.rst`): tabla con filtros, modales de crear/editar/ver/borrar y
acciones de instancia. El árbol editable de la vista de estructura (§2.1) es una tabla por nivel con
el CRUD hijo colgando del nodo seleccionado.

### 3.2 Cálculo de avance

Función pura en `src/management_plans/progress.py`, con tests propios, **nunca duplicada en
plantillas**:

```
avance(acción)      = promedio de progress_pct de sus actividades activas   (0 si no tiene)
avance(componente)  = promedio de sus acciones
avance(eje)         = promedio de sus componentes, o de sus acciones directas si no hay componentes
avance(plan anual)  = promedio de sus ejes
avance(programa)    = promedio de sus planes anuales
avance(dependencia) = promedio de las actividades cuya acción apunta a esa unidad o a sus descendientes
```

- Ponderación simple en la v1; dejar `weight` opcional para una segunda etapa.
- Todo se calcula con `Sum`/`Count`/`Avg` en el ORM. Nada de recorrer querysets en Python.
- El **estado global** (cumplido / en proceso / no cumplido) sale de umbrales en `SystemParameter`:
  `mgmt_completed_threshold`, `mgmt_in_process_threshold`.
- **Actividad desviada** = `progress_pct` < porcentaje de tiempo transcurrido entre `start_date` y
  `due_date`, con una tolerancia configurable.

### 3.3 Conexión con lo que Organilab ya produce

Esta es la razón de fondo para construir el módulo. El `source_object` genérico de `PlanAction`
(mismo patrón que `PendingTaskManager`, `Inform` y `QRModel`, con
`models.Index(fields=["source_content_type", "source_object_id"])`) permite un botón **"Crear acción
de seguimiento"** en:

| Origen | Flujo |
|--------|-------|
| Evaluación IPER con riesgo alto (`src/risk_management/models.py:467+`) | El control propuesto se convierte en acción del plan anual, precargando descripción, laboratorio y responsable |
| `IncidentReport` | Acción correctiva tras un incidente |
| Límites de inventario (`ReactiveLimit`, `ObjectMaximumLimit`) | Acción de reposición o de ajuste de límite |
| Registro de consumo ([`ENVIRONMENT_PLAN.md`](ENVIRONMENT_PLAN.md)) | Acción "registrar el consumo del período", con el tipo de recurso marcado |

Desde el hallazgo se ve el estado de su acción; desde la acción se vuelve al hallazgo.

**Antes de escribir el cierre de año**, revisar `InformScheduler` / `InformsPeriod` / `Inform`
(`src/laboratory/models.py:1695-1823`): ya resuelven campañas periódicas con ventana de aplicación y
puede que parte se reutilice en vez de reimplementarse.

### 3.4 Reportes y gráficos

Registrar en `src/report/register.py` con `html`/`pdf`/`xls`/`xlsx`/`ods` y `report.tasks.task_report`:

| Reporte | Contenido |
|---------|-----------|
| `report_programs` | Programas con tipo, período, vigencia, estado |
| `report_program_detail` | Estructura completa: ejes, componentes, acciones, actividades |
| `report_program_progress` | Avance por programa / eje / componente con conteos y última actualización |
| `report_annual_plan_progress` | Avance desagregado + atrasos y desviaciones |
| `report_activities_by_user` | Actividades por responsable, con carga de trabajo |
| `report_activities_by_dependency` | Actividades agrupadas por rama del árbol organizacional |
| `report_dependency_ranking` | Ranking de unidades por porcentaje de cumplimiento |

Gráficos en `src/management_plans/gtcharts.py` con `djgentelella.chartjs` + `register_lookups`
(mismo patrón que `src/laboratory/gtcharts.py`): avance por eje (`HorizontalBarChart`), evolución
mensual del cumplimiento (`LineChart`), semáforo de actividades por estado (`DoughnutChart`),
ranking de dependencias (`HorizontalBarChart`).

### 3.5 Roles y permisos

| Rol | Puede |
|-----|-------|
| Administrador de programas | Crear/editar programas, ejes, componentes, planes anuales y acciones; trasladar responsables; cerrar años |
| Responsable de acción | Crear y editar las actividades de sus acciones; ver el avance de su acción |
| Responsable de ejecución | Registrar seguimientos y evidencias de sus actividades |
| Analista / consulta | Solo lectura de todas las consultas y reportes de su organización |

Permisos declarados en `Meta.permissions` y sincronizados con `update_roles` /
`load_urlname_permissions`.

---

## 4. Orden de ejecución

| Paso | Entregable | Depende de | Tamaño |
|------|-----------|-----------|--------|
| 1 | App + catálogos sembrados + programa/ejes/componentes + vista de estructura (§2.1) | — | M |
| 2 | `AnnualPlan` + `PlanAction` + pantalla de plan anual y tablero (§2.2) | 1 | L |
| 3 | `PlanActivity` + "Mis acciones" + integración con tareas pendientes (§2.3) | 2 | M |
| 4 | `ActivityFollowUp` + evidencias + pantalla de seguimiento (§2.4) | 3 | M |
| 5 | `progress.py` + consultas de avance por programa y plan (§2.7.1–2) | 4 | M |
| 6 | Consultas por persona, por dependencia y ranking (§2.7.3–4) | 5 | M |
| 7 | Documentos del programa + traslado de responsable + cierre de año (§2.1, §2.5, §2.6) | 4 | M |
| 8 | `source_object` + botones desde IPER, incidentes y límites (§3.3) | 3 | S |
| 9 | Recordatorios automáticos (§2.8) | 3, plan de plataforma función E | S |

---

## 5. Checklist

- [ ] `AbstractOrganizationRef` en modelos org-scoped; `Laboratory` / `OrganizationStructure` como FK,
      nunca texto libre.
- [ ] Vistas HTML heredan de `src/laboratory/views/djgeneric.py`; URLs `/management_plans/<int:org_pk>/…`.
- [ ] Viewsets: `BaseViewSetWithLogs` con `models_log` declarado; los de hijos,
      `BaseInlineObjectManagement` **con `get_parent_queryset()` filtrado por organización**.
- [ ] Cada acción personalizada (`restore`, `dependents`, `transfer`) declarada en `perms`.
- [ ] `DeletedWithTrash` en todo lo que se "desactiva"; formularios excluyen `is_deleted`;
      `perform_destroy` pasa `user=self.request.user`.
- [ ] Modelos del módulo agregados a `GT_HISTORY_ALLOWED_MODELS` para que aparezcan en la bitácora.
- [ ] `JustifiedUpdateMixin` en programa, ejes, componentes y acciones con dependientes.
- [ ] Evidencias y documentos con `FileChunkedUpload` / `ChunkedFileField`, no con un `FileInput`
      plano: son archivos que pueden ser grandes.
- [ ] Correos del módulo registrados con `register_context()` en `apps.py::ready()`.
- [ ] `progress.py` con tests propios: jerarquía incompleta (sin componentes, sin actividades) da 0 y
      no divide por cero.
- [ ] Agregaciones con el ORM; nada de recorrer querysets en Python.
- [ ] Menú: `src/presentation/templates/partials/management_plans_menu.html` o entradas `MenuItem`
      sembradas por migración, según lo que se decida para todo el proyecto.
- [ ] `gettext` + `make messages && make trans`; `make lint`; tests en `src/management_plans/tests/`.
