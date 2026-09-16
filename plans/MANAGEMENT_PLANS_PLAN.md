# Programas de gestión — pendiente (no iniciado)

> **Qué es esto.** Módulo nuevo `src/management_plans/` para **planificar** trabajo de cumplimiento,
> **repartirlo** con responsables y fechas, **darle seguimiento mensual con evidencias** y **medir el
> avance** por laboratorio y por rama del árbol organizacional. Resumen; la versión larga con los
> flujos de pantalla está en git (antes del 2026-09-16). Viene de
> [`SIGMA_GAP_ANALYSIS.md`](SIGMA_GAP_ANALYSIS.md).
>
> **Estado (2026-09-16):** nada implementado; no existe la app ni ningún modelo.

---

## 1. Modelo mental

```
Programa (plurianual) → Eje → Componente (opcional) → Acción (en un PLAN ANUAL) → Actividad → Seguimiento + evidencias
```

- El programa es plurianual; el trabajo es anual (un plan por año).
- Los niveles intermedios son opcionales; el cálculo de avance lo contempla.
- La **actividad** es la única unidad con responsable, fechas y porcentaje; lo demás agrega.

**Decisiones tomadas:** app nueva; modelos dedicados (no `derb`); `PendingTask` es el buzón, no el
modelo; estados como `Catalog` (`mgmt_progress_status`, `mgmt_plan_status`, `mgmt_program_type`);
jerarquía con `BaseInlineObjectManagement`; nada se borra físicamente (`DeletedWithTrash`).

## 2. Modelos (`src/management_plans/models.py`)

| Modelo | Hereda | Campos clave |
|--------|--------|--------------|
| `ManagementProgram` | `AbstractOrganizationRef`, `DeletedWithTrash` | `code` (único por org), `acronym`, `name`, `program_type`, `start_year`/`end_year` (`clean`: fin ≥ inicio), `responsible`, `laboratories` M2M (vacío = toda la org) |
| `ProgramAxis` | `DeletedWithTrash` | FK `program`, `code`, `detail`, `order` |
| `ProgramComponent` | `DeletedWithTrash` | FK `axis`, `code`, `detail`, `order` |
| `AnnualPlan` | org + trash | FK `program`, `year` (único por programa), `name`, `objective`, `scope`, `status` |
| `PlanAction` | org + trash | FK `annual_plan`, `axis`/`component` opcionales, `responsible`, `dependency` FK `OrganizationStructure` (`GentelellaTreeNodeChoiceField`), `laboratory`, `start_date`/`due_date`, `status`, `resource_type` (`env_resource_type`), `source_object` GFK con índice |
| `PlanActivity` | org + trash | FK `action`, `responsible`, fechas, `progress_status`, `progress_pct` 0–100, `carried_from` self-FK, `pending_task` FK |
| `ActivityFollowUp` | org | FK `activity`, `record_date`, `follow_month`, `detail`, estado, `progress_pct`, `observations` |
| `FollowUpEvidence` | — | FK `follow_up`, `file` (chunked), `description` |
| `ProgramAttachment` | org + trash | FK `program`, `name`, `document_type`, `file`, `description` |

**Reglas:** guardar un seguimiento actualiza `progress_pct`/estado de la actividad; actividad al 100 %
cierra su `PendingTask` y avisa al responsable de la acción.

**API:** programa y plan anual con `BaseViewSetWithLogs`; hijos con `BaseInlineObjectManagement`
registrados con `parent_pk` en la URL y **`get_parent_queryset()` filtrado por organización
(obligatorio, si no hay fuga entre orgs)**. Acciones propias (`restore`, `dependents`, `transfer`) en
`perms`. Ejemplos del patrón inline: `academic/api/views.py:443`, `laboratory/api/labview/viewsets.py:40`.

## 3. Avance (`progress.py`, función pura con tests)

```
acción = promedio de actividades · componente = promedio de acciones
eje = promedio de componentes (o de acciones directas) · plan = promedio de ejes
programa = promedio de planes · dependencia = actividades de esa unidad y descendientes
```

Con el ORM (`Avg`/`Count`), sin dividir por cero; estado global por umbrales `SystemParameter`
(`mgmt_completed_threshold`, `mgmt_in_process_threshold`); **desviada** = `progress_pct` < % de tiempo
transcurrido (con tolerancia).

## 4. Pasos

| # | Entregable | Depende de |
|---|-----------|-----------|
| 1 | App + catálogos sembrados + programa/ejes/componentes + vista de estructura | — |
| 2 | `AnnualPlan` + `PlanAction` + pantalla de plan anual y tablero por estado (notifica al asignar) | 1 |
| 3 | `PlanActivity` + "Mis acciones" + `PendingTask` por actividad | 2 |
| 4 | Seguimiento + evidencias + línea de tiempo | 3 |
| 5 | `progress.py` + avance por programa y plan (atrasos y desviaciones) | 4 |
| 6 | Avance por persona y por dependencia + ranking | 5 |
| 7 | Documentos del programa + traslado de responsable + cierre de año con arrastre (conservar / reiniciar / nada) | 4 |
| 8 | `source_object` + botón "Crear acción de seguimiento" desde IPER, `IncidentReport`, `ReactiveLimit`/`ObjectMaximumLimit` y consumos | 3 (+ ENVIRONMENT para consumos) |
| 9 | Recordatorios diarios (por vencer, vencida sin seguimiento, plan sin seguimiento en el mes) | 3 + PLATFORM E |

**Reportes** (`report/register.py`): `report_programs`, `report_program_detail`,
`report_program_progress`, `report_annual_plan_progress`, `report_activities_by_user`,
`report_activities_by_dependency`, `report_dependency_ranking`. **Gráficos** en
`management_plans/gtcharts.py`: avance por eje, evolución mensual, semáforo por estado, ranking.

**Roles:** Administrador de programas · Responsable de acción · Responsable de ejecución · Analista
(solo lectura).

## 5. Bloqueos (de [`PLATFORM_ADMIN_PLAN.md`](PLATFORM_ADMIN_PLAN.md))

- C `SystemParameter`: umbrales de cumplimiento y días de aviso.
- B `JustifiedUpdateMixin`: editar ejes/componentes/acciones con dependientes.
- E `AlertRule`: recordatorios (paso 9).
- A diffs de bitácora: "Ver historial".

Reutilizables ya disponibles: `create_pending_task` (`pending_tasks/utils.py`), `BaseViewSetWithLogs`
y `BaseInlineObjectManagement` (djgentelella), `DeletedWithTrash`.

## 6. Decisiones abiertas

- Menú: parcial `management_plans_menu.html` o `MenuItem`; cómo armar "Mi trabajo".
- ¿El cierre de año reutiliza `InformScheduler`/`InformsPeriod` (`laboratory/models.py:1695-1823`)? Revisar antes del paso 7.
- `weight` opcional en el avance (segunda etapa).
- Estados a sembrar en los catálogos.
- Prefijo URL `/management_plans/<org_pk>/`.

## 7. Checklist

`AbstractOrganizationRef` + FKs reales (nunca texto libre) · vistas desde `djgeneric.py` ·
`models_log` declarado y `perform_destroy(user=…)` · acciones en `perms` · modelos en
`GT_HISTORY_ALLOWED_MODELS` si se declara · evidencias con `ChunkedFileField` · correos con
`register_context()` en `apps.py` · agregaciones en ORM · `gettext` + `make messages && make trans` ·
`make lint` · tests en `src/management_plans/tests/`.
