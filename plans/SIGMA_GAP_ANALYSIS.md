# SIGMA vs. Organilab — análisis comparativo y priorización

> **Qué es esto.** Comparación entre los *Requerimientos Mínimos del Sistema Integrado de Gestión
> Ambiental (SIGMA)* del MOPT (Dirección de Informática, junio 2026, 67 pp.) y lo que Organilab ya
> tiene implementado, con una recomendación de **qué vale la pena incorporar** y qué **no**.
>
> Léelo junto a [`AGENT_BRIEFING.md`](AGENT_BRIEFING.md) (arquitectura) y los tres planes derivados:
> [`PLATFORM_ADMIN_PLAN.md`](PLATFORM_ADMIN_PLAN.md),
> [`ENVIRONMENT_PLAN.md`](ENVIRONMENT_PLAN.md),
> [`MANAGEMENT_PLANS_PLAN.md`](MANAGEMENT_PLANS_PLAN.md).

---

## 0. Resumen ejecutivo

SIGMA es un sistema de **gestión ambiental institucional** para un ministerio: registra consumos
(agua, luz, combustible, papel, residuos), gestiona *instrumentos de gestión ambiental* con planes de
trabajo anuales, y reporta cumplimiento por dependencia. Organilab es un sistema de **gestión de
laboratorios** multi-tenant. No son el mismo producto, pero **tres bloques de SIGMA son directamente
aprovechables** porque atacan huecos reales de Organilab:

| # | Qué tomar de SIGMA | Por qué encaja en Organilab | Plan |
|---|--------------------|------------------------------|------|
| 1 | **Capa de plataforma**: bitácora de auditoría consultable/exportable, histórico de cambios con justificación, catálogo de notificaciones y alertas configurables, parámetros generales, ayuda en línea (FAQ + videos + "Acerca de") | Organilab **captura** auditoría (≈280 llamadas a `organilab_logentry`) pero casi no la **expone**; las plantillas de correo se crean a mano en migraciones; no hay parámetros por organización ni FAQ | [plataforma](PLATFORM_ADMIN_PLAN.md) |
| 2 | **Consumos y residuos institucionales** + indicadores normalizados (por m², por persona) + alertas por consumo atípico | Un laboratorio consume agua/electricidad/gas y genera residuos peligrosos; Organilab ya tiene los **denominadores** (`Buildings.area`, `Structure.area`, `Workday.num_workers`) y el motor de reportes | [consumos](ENVIRONMENT_PLAN.md) |
| 3 | **Instrumentos de gestión → planes de trabajo anuales → acciones → actividades → seguimiento con % de avance y evidencias** | Organilab genera hallazgos (IPER, incidentes, límites de inventario, informes `derb`) pero **no tiene dónde darles seguimiento planificado** ni medir cumplimiento por unidad organizacional | [programas](MANAGEMENT_PLANS_PLAN.md) |

**Recomendación de orden:** plataforma → programas → consumos. El plan de plataforma es transversal y
barato; el de programas crea el esqueleto de cumplimiento del que el de consumos se cuelga (una
acción de un plan puede exigir "registrar el consumo de agua del trimestre"). El de consumos es el
más caro y el que más depende de decisiones de negocio (¿qué mide realmente cada laboratorio?).

---

## 1. Tabla de comparación requisito por requisito

Estado: ✅ existe · 🟡 parcial · ❌ falta · ⛔ no aplica a Organilab

### Módulo 1 — Ingreso al sistema

| Req. SIGMA | Estado | Evidencia en Organilab |
|-----------|--------|------------------------|
| 1.1 Pantalla principal con menú según perfil | ✅ | djgentelella + `src/presentation/templates/base.html`, menús parciales en `src/presentation/templates/partials/` filtrados por permisos |
| 1.2 Acceso vía Portal de Aplicaciones institucional del MOPT | ⛔ | Específico del MOPT. Organilab ya soporta **OIDC** (`src/authentication/oidc_backend.py`) y firma digital CR (`src/auth_and_perms/authBackend.py`), que es el equivalente genérico |
| 1.2 Autenticación por token, control de sesión activa | 🟡 | DRF `TokenAuthentication` (`settings.py`) y `django-otp`; **no** hay expiración de sesión configurable por sistema |
| 1.2 Usuarios pre-aprobados con rol asignado | ✅ | `ProfilePermission` + `Rol` + `UserOrganization` |

### Módulo 2 — Administrativo

| Req. SIGMA | Estado | Evidencia |
|-----------|--------|-----------|
| 2.1.1 Manual de usuario / guía interactiva | 🟡 | `Tutorial`/`TutorialStep`/`TutorialProgress` (`src/presentation/models.py:79`) da guías interactivas paso a paso, **pero no videos** ni organización por título/sección editable |
| 2.1.2 Preguntas frecuentes gestionables | ❌ | No existe |
| 2.1.3 "Acerca de…" (versión, fecha, patrocinador, colaboradores) | ❌ | La versión vive en `src/organilab/__init__.py`; no hay pantalla |
| 2.2.1 Catálogo de notificaciones (ID, proceso, asunto, cuerpo, estado) + campos dinámicos | 🟡 | `async_notifications.EmailTemplate` existe y se usa, pero las plantillas se **crean en migraciones** (ver `laboratory/migrations/0203_*`); no hay UI, ni "estado", ni lista de variables disponibles |
| 2.2.2 Parámetros generales (ID, descripción, tipo de dato, valor) | ❌ | Todo está en `settings.py` o hardcodeado. Único precedente: `IPERConfig` (`src/risk_management/models.py:437`), configuración *ad hoc* por organización |
| 2.2.3 Alertas configurables (proceso, disparador, asunto, cuerpo, estado) | 🟡 | Hay alertas **hardcodeadas**: límites de inventario (`src/laboratory/limit_shelfobject.py`), vencimientos, precursores — vía `CELERYBEAT_SCHEDULE`. No son configurables por el usuario |
| 2.3.1 Catálogo de NIS (punto de consumo, ubicación, medidores, edificio) | ❌ | No existe. `Buildings`/`Structure` (`src/risk_management/models.py:219`) son la base natural sobre la que colgarlo |
| 2.3.2 Catálogo de instrumentos de gestión | ❌ | No existe |
| 2.3.3 Catálogo de estado de avance | 🟡 | El modelo `Catalog` (`src/laboratory/models.py:52`, `key`+`description` global) sirve para esto sin crear nada nuevo |

### Módulo 3 — Instrumentos de gestión

| Req. SIGMA | Estado | Evidencia |
|-----------|--------|-----------|
| 3.1 Jerarquía Ejes → Parámetros → Acciones → Actividades, niveles opcionales | ❌ | Lo más cercano es `Procedure`/`ProcedureStep` (`src/academic/models.py`), que es lineal y sin responsables ni avance |
| 3.2.1 Planes de trabajo **anuales** por instrumento | 🟡 | `InformScheduler`/`InformsPeriod`/`Inform` (`src/laboratory/models.py:1695-1823`) ya modela **campañas periódicas de llenado de formularios** con ventana de aplicación. Es el precedente más útil, pero no maneja jerarquía ni % de avance |
| 3.2.2 Actividades por responsable con fechas y % de avance | 🟡 | `PendingTask` (`src/pending_tasks/models.py`) asigna tareas a perfiles/roles con estado (pendiente/en proceso/finalizada), **sin** fechas de vencimiento ni porcentaje |
| 3.2.3 Seguimiento mensual con evidencias adjuntas | ❌ | No existe un flujo de seguimiento periódico con adjuntos |
| 3.1/3.2 Modificación con advertencia + **justificación obligatoria** | ❌ | `organilab_logentry` registra qué campos cambiaron, no el porqué ni el valor anterior |
| 3.2.1 Arrastre de actividades no concluidas al año siguiente | ❌ | No existe |
| 3.3 Adjuntos por instrumento con borrado lógico | 🟡 | Hay `FileField` en varios modelos (`Protocol`, `Buildings`); no hay gestor genérico de adjuntos |

### Módulo 4 — Consumos institucionales

| Req. SIGMA | Estado | Evidencia |
|-----------|--------|-----------|
| 4.1–4.4 Registro de agua, electricidad, combustible, papel | ❌ | No existe ningún modelo de consumo de servicios |
| 4.5–4.7 Residuos sólidos separados / peligrosos / especiales | 🟡 | Existe **descarte de reactivos** (`report_waste_objects` en `src/report/register.py`, `src/report/views/discard_objects.py`) — residuo *de laboratorio*, no residuo institucional pesado y reportado por período |
| Integración SPP / CITEC | ⛔ | Sistemas del MOPT. El patrón aprovechable es "importar de fuente externa con *fallback* manual" |

### Módulo 5 — Consultas y reportes

| Req. SIGMA | Estado | Evidencia |
|-----------|--------|-----------|
| 5.1 Panel informativo consolidado con KPIs y *drill-down* | 🟡 | Hay gráficos por módulo (`src/laboratory/gtcharts.py` con `djgentelella.chartjs`), dashboards de zona de riesgo e IPER; **no** hay panel institucional único |
| 5.2–5.4 Consultas de instrumentos/planes/avance por dependencia | ❌ | Depende del plan de programas |
| 5.4.2 Avance por unidad organizacional (integración SIOR) | 🟡 | Organilab **ya tiene el árbol organizacional propio** (`OrganizationStructure`, `TreeNode`) — no necesita integrar SIOR, solo agregar por rama |
| 5.4.3 Ranking de dependencias por cumplimiento | ❌ | Depende del plan de programas |
| 5.5.8 Costo económico asociado a consumos | ❌ | Depende del plan de consumos |
| 5.5.9 Indicadores normalizados (por funcionario, m², vehículo, NIS) | ❌ | Los **denominadores ya existen**: `Buildings.area`, `Structure.area` + unidad, `Workday.num_workers` |
| 5.5.10 Comparación entre períodos con variación absoluta y % | ❌ | Depende del plan de consumos |
| 5.5.11 Alertas por consumo atípico contra umbrales | ❌ | Existe el patrón en inventario (`ReactiveLimit`, `ObjectMaximumLimit`), no para consumos |
| 5.6 Bitácora de auditoría consultable, filtrable y exportable | 🟡 | **Captura sí, consulta limitada.** `organilab_logentry` (`src/laboratory/utils.py`) instrumenta ≈280 puntos y, desde el proyecto 13, es un puente sobre `add_log` de djgentelella: la relación con lab/org la guarda `HistoryRelation` (antes el `LabOrgLogEntry` propio, ya eliminado). `LogEntryViewSet` (`src/laboratory/api/views.py`) ya acota por organización con `scope_queryset()`, pero la pantalla `logentry_list` sigue **sin exportar** y **sin mostrar valor anterior/nuevo** |
| Exportación PDF/Word/Excel de todo reporte | ✅ | `REPORT_FORMS` en `src/report/register.py` ya declara `html`/`pdf`/`xls`/`xlsx`/`ods` por reporte, con generación asíncrona (`report.tasks.task_report`) |

---

## 2. Qué **no** incorporar (y por qué)

| Requisito SIGMA | Motivo |
|-----------------|--------|
| Integración con el Portal de Aplicaciones del MOPT | Acoplamiento institucional; Organilab ya resuelve el caso general con OIDC |
| Integración SPP / CITEC / SIOR | Sistemas internos del MOPT sin equivalente fuera de él. Se conserva **el patrón**: importador opcional + captura manual como *fallback* (plan de consumos §6) |
| Catálogo de NIS tal cual (Número de Identificación del Servicio del AyA/ICE) | Es un caso particular. Se generaliza a **"punto de medición"** con código externo libre (plan de consumos §2) |
| Plantillas de captura de residuos de un ente externo | El PDF advierte (§4) que pueden cambiar. Se modelan los campos estables y se deja el resto extensible |
| Manual por videos como único mecanismo de ayuda | Organilab ya tiene guías interactivas, que son mejores. Se **agrega** video como recurso opcional del mismo `Tutorial`, no como módulo aparte (plan de plataforma §5) |

---

## 3. Lo que SIGMA hace bien y conviene copiar como *principio*, no como módulo

1. **Toda modificación con dependientes exige justificación y avisa al usuario** (§3.1, §3.2.1). Es
   un patrón de auditoría fuerte y barato de adoptar de forma selectiva.
2. **Histórico consultable con valor anterior → valor nuevo → usuario → justificación** (§5.2.5,
   §5.3.5), no solo un registro de "cambió el campo X".
3. **Todo reporte se exporta y se grafica** (§5). Organilab ya lo hace; el plan es no romper esa
   regla en los módulos nuevos: todo lo que se agregue se registra en `REPORT_FORMS`.
4. **Los indicadores se normalizan** (por m², por persona) para poder comparar unidades desiguales.
5. **Los catálogos son datos, no código**: estados, tipos y disparadores se administran desde la UI.

---

## 4. Riesgos y decisiones abiertas

- **Alcance del plan de consumos.** Registrar consumos institucionales empuja a Organilab hacia gestión
  ambiental de edificios. Decisión pendiente: ¿el consumo se registra por **laboratorio**, por
  **edificio** (`Buildings`) o por **punto de medición** independiente? El plan de consumos propone punto de
  medición asociable a ambos, pero es la decisión de negocio más importante.
- **Un app nuevo vs. extender `risk_management`.** Los planes de consumos y de programas proponen apps nuevas
  (`environment`, `management_plans`). Extender `risk_management` evita migraciones y menús nuevos,
  pero mezcla dominios. Recomendación: apps nuevas, dado el tamaño de `risk_management` hoy.
- **Carga de trabajo del usuario final.** SIGMA asume digitadores dedicados. En Organilab el
  responsable de laboratorio ya llena IPER, informes `derb` y tareas pendientes. Cualquier módulo
  nuevo debe entrar por `PendingTask` y no por "una pantalla más en el menú".
