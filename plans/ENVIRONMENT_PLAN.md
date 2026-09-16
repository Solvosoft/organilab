# Consumos y residuos — pendiente (no iniciado)

> **Qué es esto.** Módulo nuevo `src/environment/` para registrar **cuánto consume y desecha** un
> laboratorio o edificio (agua, electricidad, combustible, gas, papel, residuos sólidos, peligrosos y
> especiales), convertirlo en **indicadores normalizados** (por persona, por m²) y **alertar consumos
> atípicos**. Resumen; la versión larga con flujos de pantalla está en git (antes del 2026-09-16).
> Viene de [`SIGMA_GAP_ANALYSIS.md`](SIGMA_GAP_ANALYSIS.md).
>
> **Estado (2026-09-16):** nada implementado; no existe la app ni ningún modelo.

---

## 1. Decisiones

**Tomadas:** app nueva; la unidad de registro es el **punto de medición** (asociable a un edificio y/o
varios labs); **un solo modelo de registro** con `extra_data` JSON validado por recurso; un residuo es
un consumo con `is_waste=True`; sin integraciones externas en v1 (import + captura manual).

**Abierta — cerrar antes del paso 2:** ¿el camino corto de la interfaz es por **edificio** (medidor
real) o por **laboratorio** (prorrateo)? El modelo soporta ambos. Es la decisión de negocio clave.

## 2. Catálogos (`Catalog`, sembrados por migración)

`env_resource_type` (Agua, Electricidad, Combustible, Gas, Papel, Residuo sólido separado, Residuo
peligroso, Residuo especial) · `env_measure_unit` (m³, kWh, L, kg, resmas, unidades) ·
`env_point_type` (Medidor, Tanque, Punto de acopio, Estimado) · `env_normalizer` (Por persona, Por m²,
Por laboratorio, Por punto) · `env_waste_treatment` (Reciclaje, Incineración, Relleno sanitario,
Gestor autorizado, Devolución a proveedor) · `env_alert_level` (Informativa, Media, Crítica).

Atributos fijos por recurso (unidad por defecto, esquema de `extra_data`, ícono, factor de emisión) en
`src/environment/env_defaults.py`, patrón de `risk_management/iper_defaults.py`.

## 3. Modelos

| Modelo | Hereda | Campos clave |
|--------|--------|--------------|
| `MeasurementPoint` | `AbstractOrganizationRef`, `DeletedWithTrash` | `code`, `name`, `point_type`, `resource_type`, `building` FK `Buildings`, `laboratories` M2M, `meters_count`, provincia/cantón/distrito, `geolocation` con **`GTPointField`** (como `Buildings`, `risk_management/models.py:247`); único `(organization, code, resource_type)` |
| `ConsumptionRecord` | org + trash | FK `point` (PROTECT), `period_start`/`period_end` (**único con point**: anti-duplicado), `quantity` Decimal, `unit`, `unit_cost`/`total_cost` (el `save()` completa el que falte), `is_waste`, `treatment`, `provider`, `document` (chunked), `extra_data`, `source` manual/import, `note`; índices `(organization, period_start)`, `(point, period_start)` |
| `NormalizationBase` | org | `normalizer`, `building`/`laboratory`, `year`, `value`; precargada desde `Buildings.area` (`models.py:271`)/`Structure.area` y suma de `Workday.num_workers` (`models.py:374`) por lab; el valor manual manda; sin año hereda el anterior |
| `ConsumptionAlert` | org | FK `record`, FK `presentation.AlertRule`, `reference_value`, `registered_value`, `variation_pct`, `level`, `reviewed`, `reviewed_note` |

Cantidades y costos siempre `Decimal`. Conversión de unidades: reutilizar `src/laboratory/utils_base_unit.py`.

**Indicadores:** función pura `compute_indicator(org, resource_type, normalizer, period)` en
`indicators.py` con tests: base ausente → `None`; unidades mezcladas; períodos traslapados.

## 4. Pasos

| # | Entregable | Depende de |
|---|-----------|-----------|
| 1 | App + catálogos + `MeasurementPoint` + CRUD | — |
| 2 | `ConsumptionRecord` + formulario adaptable por recurso + `env_defaults.py` + bloqueo de duplicados + adjunto obligatorio configurable | 1 (+ decisión abierta) |
| 3 | `NormalizationBase` + precarga | 1 |
| 4 | Consultas/reportes: detalle, consolidado, costos | 2 |
| 5 | `indicators.py` + indicadores + comparación entre períodos (variación absoluta y %) | 3, 4 |
| 6 | Gráficos (`environment/gtcharts.py`: serie temporal, composición, ranking de edificios) + tarjetas de panel | 5 |
| 7 | Importación masiva CSV/Excel con mapeo de columnas y previsualización (en background si es grande) | 2 |
| 8 | `ConsumptionAlert` + Celery mensual `check_consumption_anomalies` + pantalla "Marcar como revisada" | 5 + PLATFORM E (`AlertRule`) |
| 9 | Reporte de residuos y manifiestos | 2 |

**Reportes** (`report/register.py`): `report_consumption_detail`, `report_consumption_summary`,
`report_environmental_indicators`, `report_consumption_comparison`, `report_consumption_cost`,
`report_waste_manifest`.

**Roles:** Administrador ambiental · Encargado de registro · Responsable de lab/edificio · Analista.

**Alertas:** `process="environment.consumption"`, disparadores variación % / umbral absoluto / sin
registro; compara último período vs. promedio móvil; crea alerta + correo (`register_context`) +
`create_pending_task()` + `create_notification()` si es crítica. La acción `review` va en `perms`.

## 5. Dependencias

- [`PLATFORM_ADMIN_PLAN.md`](PLATFORM_ADMIN_PLAN.md): E (`AlertRule`) bloquea el paso 8; C
  (`SystemParameter`) para adjunto obligatorio y ventanas.
- [`MANAGEMENT_PLANS_PLAN.md`](MANAGEMENT_PLANS_PLAN.md): acciones con `resource_type` abren este
  formulario precargado y citan el registro como evidencia.

## 6. Checklist

org-scoped + índices por fecha · vistas desde `djgeneric.py`, URLs `/environment/<int:org_pk>/…` ·
`BaseViewSetWithLogs` con `models_log` y `perform_destroy(user=…)` · `review`/`import_preview` en
`perms` · archivos con `ChunkedFileField` · `Decimal` · permisos + `update_roles` /
`load_urlname_permissions` · menú (parcial o `MenuItem`) · `gettext` + `make messages && make trans` ·
`make lint` · tests en `src/environment/tests/`.
