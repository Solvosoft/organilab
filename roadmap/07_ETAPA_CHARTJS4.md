# Etapa 7 — Chart.js 2.9.3 → 4.5.1

**Objetivo:** portar los lookups de gráficos al formato v4 (el shim de la lib es temporal, "una
release"). **Estado: HECHA (2026-08-29)** — falta smoke visual de los 5 dashboards (etapa 12).

## Contexto

Los getters (`get_title`, `get_legend`, `get_tooltips`) conservan nombre y la lib los archiva bajo
`options.plugins`. Shims temporales: `xAxes`/`yAxes`, `elements.rectangle`, `steppedLine`,
`horizontalBar`. `document.chartcallbacks`: 0 usos en organilab.

## Tareas

- [ ] `src/risk_management/gtcharts.py` (12 lookups):
      - `get_scales()` l.1063-1066: `{"xAxes":[...],"yAxes":[...]}` → `{"x":{...},"y":{...}}`
        (`scaleLabel.labelString` → `title.text`).
      - Auditar los 9 `get_options()` (l.151, 274, 399, 523, 645, 770, 894, 1048):
        `title`/`legend`/`tooltips` sueltos → verificados contra el serializer nuevo.
      - Si algún lookup usa `horizontalBar`/`steppedLine`/`elements.rectangle`, portarlo.
- [ ] `src/laboratory/gtcharts.py` (2 lookups) — misma auditoría.
- [ ] Smoke visual de los 5 templates con `gentelella/widgets/chartjs.html`:
      `laboratory/objectlimit/dashboard.html`, `risk_management/iper_dashboard.html`,
      `risk_graphics.html`, `riskzone_detail.html`, `riskzone_list.html`.

## Pruebas

- Unit de los lookups si existen; si no, respuesta JSON del endpoint groute comparada antes/después.
- Revisión visual de los 5 dashboards en runserver.

## Notas / hallazgos

(al cerrar la etapa)

## Cómo quedó (2026-08-29)

- risk_management/gtcharts.py: `get_scales()` portado a `{"x": {...}, "y": {...}}` con min/max a
  nivel de escala; los 9 `get_options()` cambiaron `options["plugins"] = {...}` por
  `options.setdefault("plugins", {}).update({...})` — el reemplazo clobbereaba el
  title/legend/tooltip que el `super()` nuevo archiva en plugins.
- laboratory/gtcharts.py: solo define `get_title` — sin cambios.
- **Cambio genérico en djgentelella** (checkout, con tests): Chart.js 4 ignora `ticks.min/max` y la
  lib ni los elevaba (`scale_to_v4`) ni aceptaba `min`/`max`/`suggestedMin`/`suggestedMax` en
  `ScaleSerializer` — cualquier proyecto perdía el rango del eje. Arreglado en
  `djgentelella/chartjs.py` + 2 tests en `djgentelella/tests/ChartJS_Test.py` (19/19 OK).
