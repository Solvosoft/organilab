# IPER — Seguimiento de Riesgo en Laboratorios (documento de diseño)

> **Qué es esto.** Documento descriptivo de la funcionalidad de **Identificación de Peligros y
> Evaluación de Riesgos (IPER)** que se integra en Organilab dentro del app `risk_management`.
> Toma como referencia la app pública **IPER-CL** (https://iperclab.netlify.app/), basada en la
> metodología **INTE T55**, y la extiende para aprovechar los datos que Organilab ya tiene.
>
> Léelo junto a [`IPER_IMPLEMENTATION_PLAN.md`](IPER_IMPLEMENTATION_PLAN.md) (la guía técnica) y
> [`AGENT_BRIEFING.md`](AGENT_BRIEFING.md) (arquitectura general de Organilab).

---

## 1. Problema y objetivo

Los laboratorios deben identificar peligros y evaluar sus riesgos de forma **periódica** y dejar
constancia de los controles aplicados. Hoy Organilab no tiene un flujo guiado para esto.

Queremos:

1. Que el **responsable de cada laboratorio** llene un formulario IPER (peligro → riesgo → control),
   con **ayuda contextual** basada en el inventario y los peligros químicos (SGA/GHS) que el sistema
   ya conoce de ese laboratorio.
2. Que el riesgo se **mida en el tiempo**: cada cierto periodo (12 meses por defecto, configurable)
   o bajo demanda se llena una nueva versión —precargada con la anterior— para ver si el riesgo
   **baja o sube**.
3. Que exista un **perfil de Analista de Riesgo** que vea todos los reportes de su organización,
   con un **dashboard** de avance y tendencias, y que detecte qué responsables **no** han llenado
   el formulario.
4. Que se pueda **solicitar el llenado** de forma masiva a todos los laboratorios de una **zona de
   riesgo**, y que existan **recordatorios automáticos** vía el gestor de tareas pendientes.

**Resultado esperado:** seguimiento longitudinal del riesgo por laboratorio, con cumplimiento
medible y ayuda al llenado.

---

## 2. Las tres vistas de la aplicación

### 2.1 Formulario IPER (rol: responsable de laboratorio)

El responsable abre una **Evaluación IPER** de su laboratorio y registra uno o más **peligros**.
Cada peligro captura:

| Campo | Tipo | Notas |
|-------|------|-------|
| **Clasificación del peligro** | 6 categorías (§3) | Tarjetas con emoji + descripción (como IPER-CL) |
| **Descripción del peligro** | texto | Se sugieren ejemplos (constantes INTE T55) por categoría; en químico/biológico, sugerencias derivadas del inventario del lab (§4) |
| **Ubicación del peligro** | texto | Ej.: "Cuarto de análisis de muestras" |
| **Probabilidad (P)** | B / M / A | Baja / Media / Alta |
| **Consecuencia (C)** | LD / D / ED | Lig. Dañino / Dañino / Ext. Dañino |
| **Nivel de riesgo** | *calculado* | Matriz P×C → Trivial…Intolerable (no editable) |
| **Controles implementados** | texto | Medidas actuales |

Cabecera de la evaluación: **fecha**, **laboratorio**, **escuela/organización** (derivada del árbol
`OrganizationStructure`, mostrando la **cadena completa org→lab** como breadcrumb, no texto libre),
**responsable**, **estado** y **versión**.

### 2.2 Historial

Tabla de peligros evaluados con:

- **Contadores por nivel de riesgo**: Trivial / Tolerable / Moderado / Importante / Intolerable.
- **Filtros**: categoría de peligro, nivel de riesgo, rango de fechas (Desde / Hasta).
- **Exportación**: Excel y PDF.

Columnas (observadas en IPER-CL):
`Fecha | Laboratorio | Escuela | Clasificación | Peligro | Ubicación | P | C | Riesgo | Controles`.

### 2.3 Dashboard del Analista de Riesgo (rol: analista)

- **Lectura global**: todas las evaluaciones IPER de su organización.
- **Cumplimiento**: laboratorios con IPER vigente vs. vencido vs. nunca llenado; lista de
  responsables morosos.
- **Tendencia temporal** (diferenciador clave vs. el clon): cómo cambia la distribución de niveles
  de riesgo de un laboratorio entre sus versiones — ¿el riesgo baja o sube?
- **Métricas agregadas**: peligros por categoría, peligros Importante/Intolerable abiertos,
  prioridad promedio, etc.
- **Observaciones**: el analista puede dejar comentarios sobre una evaluación (sin flujo de
  aprobación formal); el responsable los ve como solo-lectura.

### 2.4 Solicitud y periodicidad

- **Periódica** (12 meses por defecto, configurable): una tarea programada crea un recordatorio
  (tarea pendiente + notificación) al responsable de cada laboratorio cuyo IPER esté por vencer.
- **Bajo demanda**: el responsable actualiza cuando cambian las condiciones (nuevo equipo o
  sustancia). Al actualizar, el sistema **clona** la última evaluación como nueva versión editable,
  con opción de **iniciar en limpio** (sin precargar los peligros anteriores).
- **Por zona de riesgo**: el analista dispara "Solicitar IPER a todos los laboratorios de la zona"
  desde una `RiskZone`; se notifica a cada responsable de los laboratorios de esa zona.

---

## 3. Metodología INTE T55 (catálogos exactos)

> Estos catálogos están extraídos del bundle real de IPER-CL (`riskData-*.js`) y son los valores
> **por defecto**. Las listas (categorías, probabilidad, consecuencia, niveles) reutilizan el modelo
> `Catalog` de organilab (global), y la **matriz P×C→nivel** es un modelo pequeño (`IPERRiskMatrix`).
> Solo la **organización raíz** (`parent=Null`) puede agregar/editar valores IPER. Los atributos de
> presentación fijos (prioridad, color, acción, emoji, ejemplos) viven como constantes. Todo se
> siembra con estos valores INTE T55 vía una migración.

### 3.1 Categorías de peligro (con ejemplos de ayuda)

| Id | Categoría | Descripción | Ejemplos (ayuda al llenar la descripción) |
|----|-----------|-------------|--------------------------------------------|
| `seguridad` ⚠️ | Seguridad | Condiciones físicas que pueden causar accidentes | Pisos mojados/resbaladizos; maquinaria sin guardas; instalaciones eléctricas deficientes; trabajo en alturas; almacenamiento inadecuado de materiales pesados; herramientas en mal estado; señalización deficiente; inflamables mal almacenados; riesgo de explosión por gases/presión; falta de orden y limpieza |
| `fisico` 🔊 | Físico | Energía en el ambiente que puede dañar la salud | Ruido excesivo (centrífugas, agitadores); vibraciones; iluminación insuficiente; calor excesivo (hornos, autoclaves); frío extremo; radiación UV; radiación ionizante; presiones anormales; ventilación inadecuada |
| `quimico` 🧪 | Químico | Sustancias tóxicas, corrosivas o peligrosas | Vapores de solventes (acetona, metanol, hexano); gases tóxicos de reacciones; ácidos corrosivos (HCl, H₂SO₄, HNO₃); bases corrosivas (NaOH, KOH); polvo de reactivos; aerosoles químicos; cancerígenos/mutagénicos; formaldehído/glutaraldehído; derrames; mezcla de incompatibles |
| `biologico` 🦠 | Biológico | Agentes vivos que causan enfermedades/infecciones | Bacterias patógenas; virus en sangre/fluidos; hongos y esporas; parásitos; pinchazos con agujas contaminadas; contacto con fluidos; aerosoles infecciosos al centrifugar; residuos biológicos mal gestionados; cultivos patógenos |
| `ergonomico` 🏋️ | Ergonómico | Lesiones musculoesqueléticas | Postura forzada (microscopio); pipeteo manual continuo; carga manual pesada; trabajo prolongado de pie; mobiliario no ajustable; espacio insuficiente; tensión visual; inclinación frecuente |
| `psicosocial` 🧠 | Psicosocial | Bienestar mental y emocional | Exceso de carga/plazos; alta responsabilidad/presión; funciones poco claras; trabajo monótono; falta de comunicación/apoyo; jornadas prolongadas/nocturnas; acoso/conflictos; falta de reconocimiento |

### 3.2 Probabilidad (P)

| Valor | Etiqueta | Significado |
|-------|----------|-------------|
| `B` | Baja | El daño ocurrirá raramente (pocas veces al año / condiciones excepcionales) |
| `M` | Media | El daño ocurrirá algunas veces (mensualmente / ciertas tareas) |
| `A` | Alta | El daño ocurrirá siempre o casi siempre (diariamente / mayoría de ocasiones) |

### 3.3 Consecuencia (C)

| Valor | Etiqueta | Significado | Ejemplos |
|-------|----------|-------------|----------|
| `LD` | Ligeramente Dañino | Lesiones superficiales / irritación leve | Cortes menores, irritación piel/ojos, primeros auxilios |
| `D` | Dañino | Incapacidad temporal | Quemaduras, fracturas, sordera, enfermedades reversibles |
| `ED` | Extremadamente Dañino | Lesiones graves, irreversibles o muerte | Amputaciones, intoxicaciones graves, cáncer, muerte |

### 3.4 Matriz de estimación (P × C → Nivel de riesgo)

|         | LD (Lig. Dañino) | D (Dañino) | ED (Ext. Dañino) |
|---------|------------------|------------|-------------------|
| **B (Baja)**  | **Trivial**   | **Tolerable** | **Moderado**     |
| **M (Media)** | **Tolerable** | **Moderado**  | **Importante**   |
| **A (Alta)**  | **Moderado**  | **Importante**| **Intolerable**  |

### 3.5 Niveles de riesgo y acción recomendada

| Prioridad | Nivel | Acción recomendada |
|-----------|-------|--------------------|
| 1 | **Trivial** | No se requiere acción específica. Mantener las condiciones actuales. |
| 2 | **Tolerable** | No se necesitan controles adicionales. Verificar periódicamente los existentes. |
| 3 | **Moderado** | Esfuerzos para reducir el riesgo en un plazo determinado. |
| 4 | **Importante** | No comenzar el trabajo hasta reducir el riesgo. Acción urgente. |
| 5 | **Intolerable** | No comenzar ni continuar. Prohibir la actividad hasta eliminar el riesgo. |

---

## 4. Ayuda contextual (diferenciador con datos de Organilab)

Al llenar el formulario, un **panel de ayuda** muestra lo que Organilab ya sabe del laboratorio:

- **Inventario del lab** (reactivos / materiales / equipo) presente en sus estantes.
- **Peligros químicos**: códigos H (SGA/GHS), pictogramas, si es precursor, CAS — derivados de las
  sustancias del inventario.
- **Sugerencias automáticas de peligros**: por ejemplo, si hay sustancias corrosivas/tóxicas se
  sugiere un peligro `quimico`; si hay centrífugas o autoclaves, se sugiere `fisico`/`seguridad`.

Esto reduce el esfuerzo del responsable, mejora la calidad de la identificación, y conecta el IPER
con el inventario real del laboratorio (trazabilidad peligro ↔ sustancia/equipo).

---

## 5. Glosario

- **IPER**: Identificación de Peligros y Evaluación de Riesgos.
- **INTE T55**: norma de referencia (Costa Rica) para la evaluación de riesgos laborales.
- **Evaluación / versión**: un IPER completo de un laboratorio en un momento dado; al actualizar se
  crea una versión nueva precargada con la anterior, lo que permite el seguimiento en el tiempo.
- **Analista de Riesgo**: rol con lectura global, dashboard, observaciones y capacidad de solicitar
  el llenado.
- **Responsable de laboratorio**: usuario que llena y mantiene el IPER de su laboratorio.
- **Catálogo (org raíz)**: las listas de categorías, probabilidad, consecuencia y niveles se guardan
  como entradas del modelo `Catalog` (global) y la matriz como `IPERRiskMatrix`; solo la organización
  raíz (`parent=Null`) puede agregar/editar estos valores.
