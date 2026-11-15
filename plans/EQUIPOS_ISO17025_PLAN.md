# Equipos según ISO/IEC 17025 §6.4

Este plan cubre el módulo de equipos para que un laboratorio pueda sostener el apartado 6.4 de la ISO/IEC 17025 (equipamiento) dentro de Organilab.

Lo originó la reunión con el Laboratorio de Bacteriología (UNA, Escuela de Medicina Veterinaria), que aportó la lista de campos que exige la norma y dos archivos Excel:

- **PT-05 R-10 Programa de Equipos.xlsx:**
  - La hoja 3 tiene el inventario (≈160 equipos).
  - La hoja 1 tiene el programa anual de calibración y mantenimiento.
- **Balanza Granataria LB-127.xlsx:** el registro y los gráficos de control de una balanza.

**Fases:**

| Fase | Alcance | Estado |
|---|---|---|
| F1 | Permisos; ficha ISO por unidad; estados y baja; programa de actividades; calibraciones con certificado; verificaciones; fallas; documentos; alertas | Implementada (15-nov-2026) |
| F2 | Importación del inventario y del PT-05 R-10; reportes «Hoja de vida» y «Programa anual» | Implementada (15-nov-2026) |
| F3 | Cartas de control X̄‑R e I‑MR configurables (balanzas, pHmetros) | Implementada (15-nov-2026); falta confirmar con el laboratorio las constantes de su Excel |

---

## 1. Modelo actual

- **Catálogo:** el equipo es un `Object` con `type="2"` y su ficha técnica, `EquipmentCharacteristics`.
- **Unidad física:** cada equipo concreto es un `ShelfObject` dentro de un estante, con `ShelfObjectEquipmentCharacteristics` (adquisición, proveedor, roles autorizados y contrato).
- **Registros por unidad:** `ShelfObjectMaintenance`, `ShelfObjectCalibrate`, `ShelfObjectLog` (bitácora), `ShelfObjectTraining` y `ShelfObjectGuarantee`.
  - Cada cambio queda en `ShelfObjectObservation` (línea de tiempo) y en `organilab_logentry`.
  - Pantalla: `laboratory/shelfobject/equipment_edit.html`.
  - API: `laboratory/api/shelfobject.py`.

## 2. Matriz de brechas

**Leyenda:**

- **Existe:** ya está en Organilab.
- **F1/F2/F3:** se agrega en esa fase.
- **SOEC:** `ShelfObjectEquipmentCharacteristics`, la ficha de la unidad.

| Sección | Campo de la norma | Cláusula | Dónde queda |
|---|---|---|---|
| Identificación | Código interno único | 6.4 | F1 `SOEC.internal_code` (único por organización). Hoy existe `shelfobject_code`, pero es automático |
| | Nombre | 6.4 | Existe (`Object.name`) |
| | Tipo/categoría | 6.4 | Existe (`EquipmentType`, familia instrumental) |
| | Fabricante/marca, modelo, serie | 6.4.13 | F1 `SOEC.brand/model/serial_number`. Hoy modelo y serie están en el catálogo, no por unidad |
| | Activo/patrimonio (placa) | Rec. | F1 `SOEC.asset_number` |
| | Fotografía | Rec. | F1 `SOEC.photo` |
| | Software, versión, firmware | 6.4.13 | F1 `SOEC.software_name/software_version/firmware_version` |
| | Magnitud (Masa, Volumen…) | (PT-05) | F1 `SOEC.magnitude` (Catalog) |
| Ubicación | Laboratorio, sala | 6.4.13 | Existe (estante → mueble → sala → laboratorio) |
| | Ubicación física específica | 6.4.13 | F1 `SOEC.physical_location` |
| | Historial de cambios de ubicación | Trazab. | F1: se registra una observación automática al mover el equipo |
| Estado | En servicio, fuera de servicio, en mantenimiento, en calibración, dado de baja | 6.4.8/6.4.9 | F1 `SOEC.equipment_status` |
| | Estado y vigencia de calibración; última y próxima | 6.4/6.4.8 | F1: se calculan con el programa (`EquipmentActivityPlan.next_due`) y la última calibración |
| | Etiqueta visual de estado | 6.4.8 | F1: insignia en la cabecera del equipo |
| | Restricción de uso | 6.4.9 | F1 `SOEC.use_restriction` |
| Especificaciones | Rango, resolución, exactitud/tolerancia, capacidad | 6.4 | F1 `SOEC.working_range/resolution/accuracy_tolerance/capacity` y `measurement_unit` |
| | Criterios de aceptación; requisitos metrológicos | 6.4.13/6.5 | F1 `SOEC.acceptance_criteria/metrological_requirements` |
| Recepción | Fecha de adquisición, recepción y puesta en servicio; proveedor | Rec./6.4 | Existe (`purchase_equipment_date`, `delivery_equipment_date`, `first_date_use`, `provider`) |
| | Evidencia de cumplimiento antes del uso; responsable de aceptación | 6.4.4 | F1 `SOEC.acceptance_evidence/acceptance_responsible` |
| Calibración | ¿Requiere?; programa; intervalo | 6.4.6/6.4.7 | F1 `EquipmentActivityPlan` (tipo Calibración). Ya existe la marca `calibration_required` en el catálogo |
| | Fecha; quién calibró | 6.4.13/6.5 | Existe (`calibration_date`, `calibrate_name`). F1 agrega `provider` |
| | Certificado adjunto y número | 6.4/6.5 | F1 `certificate/certificate_number` |
| | Resultados, incertidumbre, correcciones, ajustes | 6.4.13/6.4.11 | F1 `results/uncertainty/correction_factor/adjustments` |
| | Criterio; conforme/no conforme; próxima | 6.4.13 | F1 `acceptance_criterion/conformity/next_calibration_date` |
| Verificaciones | ¿Requiere?; tipo; frecuencia | 6.4.10 | F1 `EquipmentActivityPlan` (tipo Verificación intermedia) |
| | Fecha, resultado, criterio, responsable, documento | 6.4.10 | F1 `ShelfObjectVerification` |
| Mantenimiento | ¿Requiere?; programa; frecuencia; próximo | 6.4.13 | F1 `EquipmentActivityPlan` (Mantenimiento preventivo, Limpieza) |
| | Último mantenimiento; responsable/proveedor | 6.4.13 | Existe (`ShelfObjectMaintenance`) |
| | Tipo preventivo/correctivo; actividades; informe | 6.4/6.4.13 | F1 `maintenance_type`, `activities` (checklist del PT-05) y `report` |
| | Afecta la calibración; detalle de daños | (PT-05) | F1 `affects_calibration/damage_details` |
| Fallas | Fecha; descripción; bloqueado | 6.4.9 | F1 `ShelfObjectFailure`. Si se marca como bloqueado, el equipo pasa a fuera de servicio |
| | Reparación; modificaciones; responsable | 6.4.13 | F1 `ShelfObjectFailure` |
| | Retorno al servicio; verificación previa; impacto en resultados anteriores | 6.4.4/6.4.9/7.10 | F1 `return_to_service_date/verification_before_use/impact_assessment` |
| Documentación | Manual, instructivo, procedimiento, certificados, informes, documentos técnicos | 6.4.3/6.4.13 | F1 `EquipmentDocument` (tipo en Catalog). El manual de uso ya existe en el catálogo |
| Responsabilidad | Responsable/custodio | Rec. | F1 `SOEC.custodian` |
| | Personal autorizado | 6.4.3 | Existe por roles (`authorized_roles_to_use_equipment`). F1 agrega `authorized_users` |
| | Restricciones de acceso | 6.4.3 | F1 `SOEC.access_restrictions` |
| Baja | Fecha, motivo, disposición final | Registros | F1 `SOEC.decommission_date/decommission_reason/final_disposition` |
| | Historial conservado | 6.4.13/8.4 | F1: la baja no borra nada; marca `marked_as_discard` y el estado |
| Bitácora de uso | | | Existe (`ShelfObjectLog`) |
| Capacitaciones | | | Existe (`ShelfObjectTraining`) |
| Control | Puntos, mediciones, promedio, rango, límites, gráficos, alertas | 6.4.10/7.7 | F3 |

## 3. Alertas (F1)

**Qué cubren:** avisos de calibración, verificación intermedia, mantenimiento preventivo y limpieza por vencer o vencidos. Cada equipo tiene un **programa de actividades** (`EquipmentActivityPlan`): tipo, intervalo, días de aviso y responsable. La próxima fecha se calcula desde el último registro del tipo.

**Infraestructura que se reutiliza** (`presentation.alerts`):

- `AlertRule`: reglas por organización, configurables desde Plataforma → Alertas.
- `fire_alert`: envía el correo por `async_notification` (respetando `NotificationSetting` por organización), crea la tarea pendiente (`pending_tasks`) y, si es crítica, el aviso en la campana (`Notification`).

**Destinatarios:** el responsable del plan, el custodio, el responsable del laboratorio y los roles de la regla.

**Evidencia:** al registrar la actividad (por ejemplo, la calibración con su certificado) la próxima fecha avanza y la alerta queda resuelta.

**Núcleo genérico en djgentelella:** se pidió `djgentelella.alerts`, que incluye:

- registro de procesos y disparadores, con un disparador por vencimiento;
- modelos abstractos `AlertRule` y `AlertEvent`, con `dedupe_key` y resolución;
- canales enchufables: email, campana y canales propios como el de tareas pendientes.

Organilab conservará lo suyo: el ámbito por organización, los roles y los overrides de correo.

## 4. Permisos y errores corregidos (F1)

- **Permisos que no se aplicaban:** los registros de equipo y el catálogo de equipos ignoraban sus `perms` (`HALLAZGOS_COBERTURA.md`). Ahora encadenan `AllPermissionByAction` con `PermissionByLaboratoryInOrganization`, como en el labview.
- **Listados filtrados por laboratorio:** el listado de registros solo devuelve equipos del laboratorio de la ruta.
- **«Error de organización» en mantenimiento:**
  - *Síntoma:* en un laboratorio **compartido** con otra organización (`OrganizationStructureRelations`), los registros fallaban con «The shelfobject do not belong to the organization».
  - *Causa:* se exigía que la organización de la URL fuera la dueña del laboratorio, y los proveedores se filtraban por esa misma organización dueña.
  - *Corrección:* `organization_can_change_laboratory` en la validación y `Provider.objects.for_laboratory(org, lab)` en formularios, validadores y select.
  - *Pruebas:* `laboratory/tests/test_equipment_org_scope.py`.

## 5. Importación (F2)

**Flujo**, siguiendo `laboratory/views/loadArchive.py`:

1. Subida (`ChunkedFileField`) junto con la elección del laboratorio y el estante destino.
2. Lectura con openpyxl, **ubicando los encabezados por nombre**: las dos hojas tienen distinta estructura y filas de título.
3. Almacenamiento temporal.
4. Revisión por fila (formset).
5. Creación.

djgentelella no incorporará un importador genérico por ahora.

**Inventario (hoja 3)** — columnas: Equipo, Marca, Modelo, Serie, N° Activo, Código del laboratorio, Responsable, Verificación, Ubicación y Placa.

- El `Object` se busca o se crea por nombre, y la unidad se crea en el estante elegido.
- «Ubicación» se guarda en `physical_location`.
- «NI» y «NA» se tratan como vacíos.
- Un «Retirada…» en Responsable significa dado de baja.
- Las iniciales del responsable se resuelven a perfiles con una tabla de equivalencias en la revisión.

**Programa PT-05 R-10 (hoja 1):** el encabezado ocupa tres filas (8 a 12), con bloques combinados.

- Magnitud, estado, especificaciones (unidad, resolución, intervalo), responsable y usuarios autorizados.
- Calibración (fecha, próxima, resultado) → `ShelfObjectCalibrate` y un plan anual.
- Mantenimiento 1..4 (Programado/Ejecutado, tipo y el checklist: inspección visual, limpieza, cambio de batería, pintura, engrasado; incluye reporte; afecta la calibración; detalle de daños) → plan y `ShelfObjectMaintenance` con `activities`.

**Reportes** (`report/register.py`): «Hoja de vida del equipo» en PDF y «Programa anual de equipos» en xlsx con el formato del PT-05.

### Decisiones (15-nov-2026)

- **F2, mantenimiento ejecutado sin fecha:** el PT-05 indica qué se ejecutó, pero no cuándo.
  - Se crea el programa anual de mantenimiento preventivo, con su checklist en las notas.
  - En la revisión, cada fila tiene «Mantenimiento ejecutado el»: si se llena, se crea el mantenimiento con las actividades marcadas; si no, queda solo el programa.
- **F2, reimportación:** es idempotente. El equipo se reconoce por su código interno dentro del laboratorio, y una celda vacía no borra datos.
- **F2, responsables:** se resuelven por nombre completo o por iniciales (XVR). Si el nombre es ambiguo, se elige en la revisión.
- **F3, límites:** se calculan con un **período de referencia** que elige el laboratorio y quedan fijos. Se pueden recalcular cuando el laboratorio decida, guardando el historial de límites.
- **F3, tipos de carta:** **X̄‑R** para subgrupos (n ≥ 2, el bloque x1..x5 del LB-127) e **I‑MR** para una lectura diaria (n = 1, la «variación» de la tabla diaria del LB-127). El tipo lo define el método de control de cada punto.

## 6. Cartas de control (F3)

**Lógica del Excel LB-127:**

- La balanza tiene 4 puntos de control (5 g, 25 g, 100 g y 1000 g) y cada medición son 5 lecturas (x1..x5).
- De cada subgrupo se calcula el promedio y el rango (máx. − mín.).
- El promedio se corrige con el error de indicación de las pesas patrón (certificado COC 051-2024).
- Se usan las constantes A2 = 0.577, D3 = 0, D4 = 2.225 y d2 = 2.326.
- Límites de medias: LC = promedio corregido; LCS y LCI = LC ± A2·R̄.
- Límites de rangos: LC = R̄; LCS = D4·R̄; LCI = D3·R̄.
- Hay dos gráficos por punto: medias y rangos.

**Problemas del Excel que hay que confirmar con el laboratorio:**

- Para n = 5, la tabla estándar da D4 ≈ 2.114, no 2.225.
- Las referencias relativas «se corren» entre filas: la LC apunta a AB37, AB38, AB39… según la fila.
- Las columnas «Corrección» y «Variación» de la tabla diaria restan una celda fija, que en algunos puntos no corresponde.

**Diseño (todo configurable, nada fijo en el código):**

- **`ControlMethod`** (por tipo de equipo o procedimiento):
  - tipo X̄‑R y número de repeticiones `n`;
  - constantes A2/D3/D4, precargadas según `n` y editables;
  - modo de límites: calculados con k subgrupos de referencia, o fijos;
  - criterio de aceptación.
- **`ControlPoint`** (por equipo y punto): valor nominal, unidad, patrón o material de referencia con su certificado, y corrección o factor.
- **`ControlSubgroup`:**
  - captura fecha, responsable, observaciones, desviación y las `n` lecturas;
  - calcula en el servidor el promedio, el rango, el promedio corregido y si está fuera de límites.
- **Gráficos:** dos `LineChart` de djgentelella. Desde djgentelella 0.7.0 los datasets aceptan `borderDash`, `pointRadius` y `pointBackgroundColor` por punto, y `null`, así que los límites pueden ir con línea discontinua y los puntos fuera de control resaltados.
- **Alertas:** un proceso `laboratory.equipment_control` que dispara cuando un resultado sale de los límites o del criterio de aceptación.

## 7. Dependencias de djgentelella

Organilab sube a **djgentelella >= 0.7.0** (publicada en PyPI). Organilab no usa `djgentelella.flows`, y `django.contrib.sites` ya estaba instalada.

| Pedido | Estado |
|---|---|
| Datasets de Chart.js con claves libres y `null` (`PassThroughSerializer`) | Disponible en la 0.7.0 |
| `djgentelella.serializers.DataTableSerializer` genérico | Disponible en la 0.7.0. Sustituye las copias de `ambiental/api/serializers.py` y `presentation/platform/alerts_api.py` |
| Importador xlsx/csv genérico | Rechazado por ahora; se hace en organilab |
| `CalendarInput` de solo lectura | Funciona con `events=callable` |
| Núcleo de alertas `djgentelella.alerts` | Disponible en la 0.7.0. Organilab lo adopta (ver abajo) |

### Adopción de `djgentelella.alerts`

- **`presentation.alerts` queda como fachada de organilab.** Mantiene los mismos nombres públicos y delega en djgentelella el registro, los disparadores en código, `fire_alert` con `dedupe_key`, `resolve_alert` y `run_alert_rules`.
- **Modelos.** `AlertRule` hereda de `AbstractOrganizationRef` y `AbstractAlertRule`; `AlertEvent`, de `AbstractAlertEvent`.
  - El disparador pasa de FK a Catalog a un código (`absolute`, `percent`, `missing`, `due`), con migración de datos.
  - El umbral `months` pasa a `periods`.
- **Canales:**
  - `email` envía con `send_process_email`, que respeta la `NotificationSetting` de cada organización.
  - `notification` avisa en la campana solo para el nivel crítico.
  - `pending_task` es propio de organilab: crea la tarea al disparar y la marca FINISHED al resolver.
- **Destinatarios** (`AlertRule.get_recipients`): responsables (si la regla lo pide) más los usuarios con los roles de la regla en su organización.
- **Equipos.** El proceso `laboratory.equipment_due` usa el disparador `due` (`days_before`, `overdue_repeat_days`) con `fire_due_alert`. Registrar la actividad resuelve la alerta y la deja con su evidencia.

## 8. Implementación de F2 y F3 (15-nov-2026)

### F2: importación y reportes

- **Módulos:** `laboratory/equipment/importer.py` (lectura, sin base de datos), `import_service.py` (creación y actualización), `import_forms.py`, `import_views.py` y `reports.py`.
- **Pantallas:**
  - Equipos → «Importar equipos»: subir el archivo, elegir el estante destino y revisar fila por fila.
  - La revisión advierte cuando el código de una fila ya pertenece a un equipo con otro nombre.
  - La plantilla de inventario se puede descargar.
- **Programa anual:** se exporta con los encabezados del PT-05 R-10, y el archivo exportado se vuelve a importar sin cambios. La exportación usa 5 consultas sin importar cuántos equipos haya (hay una prueba que lo verifica).
- **Hoja de vida:** PDF desde la ficha del equipo.
- **Prueba con los Excel reales del laboratorio:**
  - Inventario: 160 equipos creados, 14 de ellos como bajas.
  - PT-05: 21 equipos actualizados sin duplicar, 10 calibraciones y 31 programas.
- **Hallazgo en los datos:** LB-123 es una «Balanza Granataria» en el PT-05 y una «Micropipeta 0,5-10ul» en el inventario. Hay que pedirle al laboratorio que lo corrija.

### F3: cartas de control

- **Módulos:** `laboratory/equipment/spc.py` (cálculo puro), `control.py` (servicio y alertas), `charts.py` (gráficos de djgentelella) y `control_views.py`.
- **Modelos:**
  - `ControlMethod`: tipo de carta, n y constantes A2, D3 y D4. Si se dejan vacías, se precargan con la tabla estándar; todas son editables.
  - `ControlPoint`: nominal, unidad, patrón, corrección y tolerancia.
  - `ControlLimits`: un registro por cada cálculo de límites, con su período de referencia, las constantes y la corrección usadas, y si está vigente.
  - `ControlMeasurement`: las n lecturas; media, rango y media corregida; si quedó fuera de control o de aceptación; la desviación y la acción tomada.
- **Límites:** se calculan con el período de referencia que se elija. Cada registro se grafica con los límites que se le aplicaron, así que un recálculo se ve como un escalón.
- **Alertas:** proceso `laboratory.equipment_control`, disparador «fuera de control». La alerta se dispara al registrar y se resuelve al cargar la acción tomada.
- **Pantallas:** pestaña «Cartas de control» en la ficha del equipo, carta por punto y métodos de control por organización.
- **Prueba con los datos reales del LB-127** (P1 5 g, P2 25 g y P3 100 g; 20 a 22 registros por punto):
  - P1: LC 4.99571 g, R̄ 0.00818 g y LCS de rangos 0.0173 g.
  - Varios registros reales tienen rango 0.02 g, por encima de ese LCS. Hay que comentarlo con el laboratorio junto con el D4 de su Excel (2.225 frente a 2.114 de la tabla).

## 9. Correcciones tras la revisión del branch (15-nov-2026)

La revisión del commit de las tres fases contra el correo del laboratorio y sus Excel dejó estos cambios. Las pruebas están en `laboratory/tests/test_equipment_review.py`.

### Problemas corregidos

- **Reglas de alerta por defecto:** el primer programa de actividades o punto de control de una organización crea su regla (`ensure_default_rule` en `equipment/alerts.py`). La tarea diaria la crea para los programas que ya existían. Una regla desactivada no se recrea.
- **Corrección por registro:** `ControlMeasurement.correction` guarda la corrección del punto al registrar. Cambiar el certificado del patrón aplica solo a los registros nuevos.
- **Alertas de las cartas:**
  - recalcular o fijar límites ya no avisa por registros históricos;
  - un registro que queda dentro (por nuevos límites o por corregir una lectura) cierra su alerta;
  - borrar un registro también la cierra.
- **Rango móvil (I‑MR):** mover o borrar un registro recalcula a sus vecinos.
- **Línea de tiempo:** verificaciones, fallas, calibraciones, mantenimientos y registros de control tienen descripción propia (antes «… object (3)»).

### Mejoras

- **Límites fijos:** el laboratorio puede fijar los seis límites a mano con «aplicar desde» (`ControlLimits.manual`); quedan en el historial junto a los calculados.
- **Método con registros:** no se le puede cambiar el tipo de carta ni `n`; tampoco se edita el método de una organización ancestra.
- **Cartas con muchos registros:** sin período muestran los últimos 100; con período, los de esas fechas.
- **Programa sin fecha:** estado «Sin fecha» (antes «Al día») y la API exige la fecha de inicio si el equipo no tiene registros de esa actividad.
- **Calibración no conforme:** la etiqueta ya no dice «vigente».
- **Estado del equipo:**
  - cada cambio queda en la línea de tiempo;
  - la baja marca la unidad como descartada y pone la fecha;
  - borrar la falla que bloqueaba el equipo lo devuelve al servicio;
  - no se registra uso en la bitácora de un equipo fuera de servicio o dado de baja (6.4.9).
- **Importación:** «Sujeto a confirmación» queda sin conformidad (antes «No conforme») y la revisión avisa si el código ya existe en otro laboratorio de la organización.
- **Nombre del equipo:** alertas, programa exportado y listado usan el nombre, sin el código de catálogo (salía «None Balanza granataria»).

### Pantallas nuevas

- **Equipos del laboratorio** (`equipment_units`): código interno, estado, calibración y próxima actividad; búsqueda por código, nombre, serie, placa o ubicación y filtro por estado.
- **Control del día:** en la pestaña «Cartas de control», una fecha y las lecturas de todos los puntos activos en un solo envío.

### Sigue pendiente

- `authorized_users` es informativo: no restringe quién registra uso.
- El código interno no tiene restricción en la base de datos; lo validan el formulario y la importación.
- Con el laboratorio: D4 = 2,225 frente a 2,114; LB-123 con dos equipos; LB-107 con «Volumen» en la columna Serie; LB-124 «Sujeto a confirmación»; y si usan la lectura diaria (I‑MR), los subgrupos de 5 (X̄‑R) o ambas.
