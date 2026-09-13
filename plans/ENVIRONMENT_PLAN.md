# Consumos y residuos — medición, indicadores y alertas ambientales

> **Qué es esto.** Diseño de un módulo nuevo (`src/environment/`) para registrar **cuánto consume y
> cuánto desecha** un laboratorio o un edificio —agua, electricidad, combustible, gas, papel,
> residuos sólidos, peligrosos y especiales—, convertirlo en **indicadores comparables** (por
> persona, por m²) y **avisar cuando algo se sale de lo normal**.
>
> Léelo junto a [`AGENT_BRIEFING.md`](AGENT_BRIEFING.md). Usa las funciones de
> [`PLATFORM_ADMIN_PLAN.md`](PLATFORM_ADMIN_PLAN.md) (parámetros, alertas configurables) y se
> conecta con [`MANAGEMENT_PLANS_PLAN.md`](MANAGEMENT_PLANS_PLAN.md). La base técnica es
> **djgentelella 0.6.0**: ver [`DJGENTELELLA_060_NOTES.md`](DJGENTELELLA_060_NOTES.md) antes de
> escribir el primer modelo.

---

## 0. El problema

Organilab sabe **qué sustancias hay** en un laboratorio, pero no **qué gasta ni qué bota**. Un
laboratorio consume agua, electricidad y gas, compra papel, y genera residuos peligrosos que alguien
tiene que entregar a un gestor autorizado y reportar. Nada de eso tiene hoy dónde registrarse.

Lo curioso es que Organilab ya tiene **la mitad difícil del cálculo**: el área de cada edificio y
estructura (`Buildings.area`, `Structure.area` con su unidad) y la cantidad de personas por jornada
(`Workday.num_workers`). Esos son exactamente los denominadores que hacen falta para que un consumo
crudo se convierta en un indicador comparable entre unidades desiguales. Falta el numerador.

Sin este módulo, la pregunta *"¿el laboratorio A gasta más agua que el B, corrigiendo por tamaño?"*
no se puede responder. Con él, se responde y además se vigila sola.

---

## 1. Decisiones tomadas

- **App nueva `src/environment/`.** `risk_management` ya carga dos dominios.
- **La unidad de registro es el punto de medición, no el laboratorio.** Un `MeasurementPoint`
  representa un medidor, un tanque, un punto de acopio o una estimación; se asocia opcionalmente a un
  edificio y a uno o varios laboratorios. Así se cubre tanto "el medidor eléctrico del edificio"
  como "el consumo estimado del laboratorio 3".
- **Un solo modelo de registro**, no ocho tablas paralelas por recurso. Lo que varía entre recursos
  (placa del vehículo, código de residuo, número de manifiesto) vive en un `JSONField` validado
  contra el esquema declarado para ese recurso. Ocho tablas significarían ocho veces cada reporte,
  cada gráfico y cada filtro.
- **Un residuo es un consumo de signo inverso** (`is_waste=True`) con tratamiento y gestor. Comparte
  indicadores, comparaciones y alertas — no hay un submódulo aparte de residuos.
- **Sin integraciones externas en la v1.** Se cubre con importación de archivo + captura manual.
- **Base técnica común con el resto de módulos nuevos**: viewsets sobre `BaseViewSetWithLogs`,
  pantallas con `ObjectCRUD`, borrado lógico con `DeletedWithTrash`, catálogos con
  `djgentelella.fields.catalog.GTForeignKey`, adjuntos con `FileChunkedUpload`.

**Decisión abierta que conviene cerrar antes del paso 2:** si el consumo típico del usuario será por
edificio (medidor real) o por laboratorio (prorrateo). El modelo soporta ambos, pero define cuál es
el camino corto en la interfaz.

---

## 2. Funciones y flujos de interacción

### 2.1 Configurar los puntos de medición

**Actor:** administrador de organización. Es un paso previo, se hace una vez.

1. Entra a *Ambiental → Puntos de medición → Nuevo*. Registra: código (el número de medidor o de
   servicio, tal como venga en la factura), nombre descriptivo, tipo de punto, **recurso que mide**,
   ubicación (provincia, cantón, distrito y geolocalización, con el mismo widget de mapa que ya usan
   los edificios), cantidad de medidores y estado.
2. Lo asocia a un **edificio** y/o a uno o varios **laboratorios**. Esa asociación es la que después
   permite agregar los consumos por laboratorio, por edificio y por rama organizacional.
3. Los puntos inactivos dejan de aparecer al registrar consumos, pero conservan su historial.

### 2.2 Registrar un consumo o un residuo

**Actor:** encargado de registro (puede ser el responsable del laboratorio o una persona
administrativa).

1. Entra a *Ambiental → Registrar consumo*. Un **único formulario** que se adapta:
   - Elige el **punto de medición**; el sistema deduce el recurso y la unidad por defecto.
   - Define el **período** (fecha de inicio y fin: el mes facturado, el trimestre, la entrega).
   - Escribe la **cantidad** y, si aplica, el **costo unitario**; el total se calcula solo (o al
     revés: si escribe el total, se deduce el unitario).
   - Aparecen los **campos propios del recurso**: en combustible, placa y tipo; en papel, tipo y
     cantidad de resmas; en residuo peligroso, código de residuo, tratamiento, gestor autorizado y
     número de manifiesto.
   - Adjunta el respaldo (factura, boleta, manifiesto). Si la organización lo configuró como
     obligatorio, el formulario no deja guardar sin él.
2. Si ya existe un registro para ese punto y ese período, el sistema **lo bloquea y lo muestra**, en
   vez de crear un duplicado silencioso. El usuario decide si edita el existente.
3. Guarda. El registro queda en la bitácora y —si el consumo se sale de lo normal— dispara la
   revisión de alertas (§2.5).

**Variante — carga masiva.** El encargado que recibe una planilla mensual entra a *Ambiental →
Importar*, sube el CSV o Excel, **mapea las columnas** contra los campos del sistema en una pantalla
de correspondencia, ve una **previsualización** con las filas válidas en verde y las conflictivas en
rojo (punto inexistente, período duplicado, unidad incompatible), corrige o descarta, y confirma. Si
el archivo es grande, el procesamiento se hace en segundo plano y el resultado llega como tarea
pendiente.

**Variante — desde un plan de trabajo.** Si una acción de un plan anual está marcada con un tipo de
recurso, su pantalla de seguimiento tiene un botón que abre este formulario con el punto y el período
precargados; al volver, el registro queda citado como evidencia del seguimiento
([`MANAGEMENT_PLANS_PLAN.md`](MANAGEMENT_PLANS_PLAN.md) §2.4).

### 2.3 Definir los denominadores

**Actor:** administrador. También es configuración, una vez por año.

1. Entra a *Ambiental → Bases de normalización*. La tabla ya viene **precargada** con lo que
   Organilab sabe: los m² de cada edificio y estructura, y la suma de personas por jornada de cada
   laboratorio.
2. Revisa año por año y corrige lo que haga falta (una remodelación cambió el área, la planilla
   creció). El valor que él escribe manda sobre el deducido.
3. Si un año no tiene base definida, hereda la del año anterior y la pantalla lo indica.

### 2.4 Consultar: detalle, consolidado, indicadores y comparaciones

**Actor:** administrador, coordinador o analista.

1. **Detalle** — la tabla cruda: punto, período, cantidad, unidad, costo, adjunto, quién lo
   registró. Filtros por recurso, punto, edificio, laboratorio y rango de fechas. Es la vista para
   auditar un dato puntual.
2. **Consolidado** — la misma información agregada por recurso × período × edificio o laboratorio,
   con totales de cantidad y costo. Es la vista para reportar.
3. **Indicadores** — el consumo dividido por su base: *litros de agua por persona por mes*,
   *kWh por m² por trimestre*. El usuario elige recurso, normalizador y período; la tabla muestra el
   valor del indicador, la unidad, la base usada y los datos crudos que lo componen, para que el
   número siempre sea auditable.
4. **Comparación entre períodos** — elige dos o más períodos (meses, trimestres, años) y ve, lado a
   lado, el valor de cada uno, la **variación absoluta**, la **variación porcentual** y la flecha de
   tendencia. Se puede segmentar por edificio, laboratorio, punto o unidad organizacional.
5. **Costos** — cantidad, costo unitario y costo total por recurso y período, agregable por rama del
   árbol organizacional. Responde "cuánto nos cuesta el agua de esta sede al año".
6. **Residuos** — listado por tipo, tratamiento y gestor autorizado, con los manifiestos adjuntos:
   la vista que se necesita cuando llega una inspección.

Todas se exportan a PDF, Excel u ODS y traen su gráfico.

### 2.5 Alertas por consumo atípico

**Actor:** el sistema avisa; el responsable revisa.

1. El administrador define la regla una vez, desde la pantalla de alertas
   ([`PLATFORM_ADMIN_PLAN.md`](PLATFORM_ADMIN_PLAN.md) función E): *"avísame si el consumo de un
   punto supera en 20 % el promedio de los últimos 12 meses"*, o *"si un punto lleva 2 meses sin
   registro"*.
2. Una tarea programada mensual evalúa cada punto de medición contra su propio historial.
3. Cuando algo se dispara, el responsable del edificio o laboratorio recibe correo **y** tarea
   pendiente: *"El punto Medidor Edificio C consumió 340 m³ en marzo, 38 % sobre su promedio"*, con
   enlace al registro.
4. El responsable entra a *Ambiental → Alertas*, revisa el caso y lo **marca como revisado** con una
   nota: fuga detectada, error de digitación, aumento justificado por una obra. La alerta no
   desaparece: queda con su explicación.
5. La pestaña de historial muestra las alertas de los últimos meses ordenadas por variación, para
   priorizar y para calibrar los umbrales cuando una regla se vuelve ruido.

---

## 3. Diseño en Organilab

### 3.1 Catálogos (`Catalog`, `key`+`description`, global)

Sembrados en migración, igual que los catálogos IPER:

| `key` | Valores |
|-------|---------|
| `env_resource_type` | Agua, Electricidad, Combustible, Gas, Papel, Residuo sólido separado, Residuo peligroso, Residuo especial |
| `env_measure_unit` | m³, kWh, L, kg, resmas, unidades |
| `env_point_type` | Medidor, Tanque, Punto de acopio, Estimado |
| `env_normalizer` | Por persona, Por m², Por laboratorio, Por punto de medición |
| `env_waste_treatment` | Reciclaje, Incineración, Relleno sanitario, Gestor autorizado, Devolución a proveedor |
| `env_alert_level` | Informativa, Media, Crítica |

Los **atributos fijos** por recurso (unidad por defecto, esquema de campos extra, ícono, factor de
emisión) van como constantes en `src/environment/env_defaults.py`, indexadas por el `description`
sembrado — mismo patrón que `src/risk_management/iper_defaults.py`.

### 3.2 Modelos (`src/environment/models.py`)

```python
class MeasurementPoint(AbstractOrganizationRef, DeletedWithTrash):
    code = models.CharField(max_length=100)          # número de medidor o de servicio
    name = models.CharField(max_length=255)
    point_type = catalog.GTForeignKey(Catalog, key_value="env_point_type", …)
    resource_type = catalog.GTForeignKey(Catalog, key_value="env_resource_type", …)
    building = models.ForeignKey("risk_management.Buildings", null=True, blank=True, …)
    laboratories = models.ManyToManyField(Laboratory, blank=True)
    meters_count = models.PositiveSmallIntegerField(default=1)
    province / canton / district = models.CharField(max_length=100, blank=True)
    geolocation = PlainLocationField(...)             # mismo widget que Buildings
    # activo/inactivo lo resuelve DeletedWithTrash: el punto retirado sale de las
    # listas pero conserva su historial y se puede restaurar desde la papelera

    class Meta:
        unique_together = [("organization", "code", "resource_type")]


class ConsumptionRecord(AbstractOrganizationRef, DeletedWithTrash):
    point = models.ForeignKey(MeasurementPoint, on_delete=models.PROTECT)
    period_start / period_end = models.DateField()
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    unit = catalog.GTForeignKey(Catalog, key_value="env_measure_unit", …)
    unit_cost / total_cost = models.DecimalField(max_digits=14, decimal_places=2,
                                                 null=True, blank=True)
    is_waste = models.BooleanField(default=False)
    treatment = catalog.GTForeignKey(Catalog, key_value="env_waste_treatment",
                                     null=True, blank=True, …)
    provider = models.ForeignKey("laboratory.Provider", null=True, blank=True, …)
    document = models.FileField(upload_to=upload_files, null=True, blank=True)   # FileChunkedUpload
    extra_data = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=20, choices=(("manual", …), ("import", …)))
    note = models.TextField(blank=True)

    class Meta:
        unique_together = [("point", "period_start", "period_end")]   # anti-duplicado (§2.2)
        indexes = [models.Index(fields=["organization", "period_start"]),
                   models.Index(fields=["point", "period_start"])]


class NormalizationBase(AbstractOrganizationRef):
    normalizer = catalog.GTForeignKey(Catalog, key_value="env_normalizer", …)
    building = models.ForeignKey("risk_management.Buildings", null=True, blank=True, …)
    laboratory = models.ForeignKey(Laboratory, null=True, blank=True, …)
    year = models.PositiveSmallIntegerField()
    value = models.DecimalField(max_digits=12, decimal_places=2)


class ConsumptionAlert(AbstractOrganizationRef):
    record = models.ForeignKey(ConsumptionRecord, on_delete=models.CASCADE)
    rule = models.ForeignKey("presentation.AlertRule", on_delete=models.SET_NULL, null=True)
    reference_value / registered_value = models.DecimalField(max_digits=14, decimal_places=4)
    variation_pct = models.DecimalField(max_digits=7, decimal_places=2)
    level = catalog.GTForeignKey(Catalog, key_value="env_alert_level", …)
    reviewed = models.BooleanField(default=False)
    reviewed_note = models.TextField(blank=True)
```

**Reglas de negocio**

- `save()` de `ConsumptionRecord` completa `total_cost` o `unit_cost`, el que falte.
- `extra_data` se valida contra el esquema declarado en `env_defaults.py` para ese recurso.
- `NormalizationBase` se **precarga** desde `Buildings.area` / `Structure.area` (m²) y de la suma de
  `Workday.num_workers` (`src/risk_management/models.py:365`) por laboratorio; el valor manual manda.
- Cantidades y costos siempre `Decimal`, **nunca** `float`.

### 3.3 Cálculo de indicadores

Función pura `compute_indicator(org, resource_type, normalizer, period) -> Decimal` en
`src/environment/indicators.py`, con tests propios. La consumen los reportes y los gráficos; **nunca**
se recalcula en una plantilla. Casos que los tests deben cubrir: base ausente (devuelve `None`, no
divide por cero), unidades mezcladas en el mismo período, y períodos parcialmente traslapados.

Antes de escribir cualquier conversión de unidades, revisar `src/laboratory/utils_base_unit.py`: ya
existe la infraestructura.

### 3.4 Reportes y gráficos

Registrar en `src/report/register.py` con `html`/`pdf`/`xls`/`xlsx`/`ods` y `report.tasks.task_report`:

| Reporte | Corresponde a |
|---------|---------------|
| `report_consumption_detail` | Detalle (§2.4.1) |
| `report_consumption_summary` | Consolidado (§2.4.2) |
| `report_environmental_indicators` | Indicadores normalizados (§2.4.3) |
| `report_consumption_comparison` | Comparación entre períodos (§2.4.4) |
| `report_consumption_cost` | Costos (§2.4.5) |
| `report_waste_manifest` | Residuos por tratamiento y gestor (§2.4.6) |

Gráficos en `src/environment/gtcharts.py` con `djgentelella.chartjs` + `register_lookups`, igual que
`src/laboratory/gtcharts.py`: serie temporal por recurso (`LineChart`), composición por tipo
(`StackedBarChart`), ranking de edificios por indicador (`HorizontalBarChart`).

### 3.5 Alertas

`ConsumptionAlert` se apoya en `AlertRule` de
[`PLATFORM_ADMIN_PLAN.md`](PLATFORM_ADMIN_PLAN.md) función E, con
`process = "environment.consumption"` y disparadores *variación porcentual* / *umbral absoluto* /
*sin registro en el período*. Tarea Celery mensual
`environment.tasks.check_consumption_anomalies`: por cada punto activo compara el último período
contra el promedio móvil de la ventana configurada; si excede, crea la alerta, envía el correo del
proceso (registrado con `register_context()`), llama a `create_pending_task()` y —cuando el nivel es
crítico— a `create_notification()` para que aparezca en la campana del menú.

La pantalla de alertas es un `ObjectCRUD` cuya acción de instancia **"Marcar como revisada"** sigue
el mismo patrón que `restore` en `docs/source/trash.rst`: `@action(detail=True, methods=['POST'])`,
declarado en `perms`, con recarga del datatable al terminar.

### 3.6 Roles y permisos

| Rol | Puede |
|-----|-------|
| Administrador ambiental | Configurar puntos, bases de normalización y reglas de alerta |
| Encargado de registro | Registrar e importar consumos y residuos de sus puntos |
| Responsable de laboratorio/edificio | Ver sus consumos y atender sus alertas |
| Analista / consulta | Solo lectura de consultas, indicadores y reportes de su organización |

---

## 4. Orden de ejecución

| Paso | Entregable | Depende de | Tamaño |
|------|-----------|-----------|--------|
| 1 | App + catálogos sembrados + `MeasurementPoint` + CRUD (§2.1) | — | M |
| 2 | `ConsumptionRecord` + formulario adaptable + `env_defaults.py` (§2.2) | 1 | L |
| 3 | `NormalizationBase` + precarga desde edificios y jornadas (§2.3) | 1 | S |
| 4 | Consultas y reportes de detalle, consolidado y costos (§2.4.1–2, §2.4.5) | 2 | M |
| 5 | `indicators.py` + indicadores y comparaciones (§2.4.3–4) | 3, 4 | M |
| 6 | Gráficos y tarjetas para el panel general | 5 | S |
| 7 | Importación masiva con mapeo y previsualización, sobre `chunked_upload` (§2.2 variante) | 2 | M |
| 8 | `ConsumptionAlert` + tarea programada + pantalla de alertas (§2.5) | 5, plan de plataforma función E | M |
| 9 | Reporte de residuos y manifiestos (§2.4.6) | 2 | S |

---

## 5. Checklist

- [ ] `AbstractOrganizationRef` en todos los modelos org-scoped; índices por `(organization, fecha)`.
- [ ] Vistas HTML heredan de `src/laboratory/views/djgeneric.py`; URLs `/environment/<int:org_pk>/…`.
- [ ] Viewsets sobre `BaseViewSetWithLogs` con `models_log` declarado; `perform_destroy` pasa
      `user=self.request.user` para que la papelera guarde quién borró.
- [ ] Acciones personalizadas (`review`, `import_preview`) declaradas en `perms`.
- [ ] Modelos del módulo agregados a `GT_HISTORY_ALLOWED_MODELS`.
- [ ] Facturas, manifiestos y archivos de importación con `FileChunkedUpload` / `ChunkedFileField`:
      son los archivos más pesados del sistema.
- [ ] `Decimal` en cantidades y costos; conversión de unidades vía `utils_base_unit.py`.
- [ ] Permisos declarados y sincronizados con `update_roles` / `load_urlname_permissions`.
- [ ] Menú: `src/presentation/templates/partials/environment_menu.html` o entradas `MenuItem`.
- [ ] `gettext` + `make messages && make trans`; `make lint`; tests en `src/environment/tests/`.
