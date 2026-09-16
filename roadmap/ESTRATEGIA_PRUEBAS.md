# Estrategia de pruebas por vista

Qué debería probarse en cada vista, con qué herramienta y por qué. Las cifras vivas **no se copian
aquí**: salen de los informes generados —[`INVENTARIO_URLS.md`](INVENTARIO_URLS.md) (rutas y su
clasificación), [`INVENTARIO_FUNCIONALIDADES.md`](INVENTARIO_FUNCIONALIDADES.md) (funcionalidades,
pasos y actores) y [`COBERTURA_POR_ROL.md`](COBERTURA_POR_ROL.md) (qué rol ejecutó cada paso,
medido)—. Resumido el 2026-09-16; los hallazgos cerrados y su historia están en git.

## El reparto

| Va a Selenium | Va a prueba de cliente o unitaria |
|---|---|
| Formularios con widgets que solo existen en el navegador: select2, datepicker, drag & drop de Formio | Que la página renderice (eso es el smoke) |
| Modales, SweetAlert y flujos que solo se completan con JS | Validación de formularios, `clean_*`, `form.is_valid()` |
| DataTables: búsqueda, paginación, acciones por fila | El endpoint que alimenta el DataTable: JSON, orden, filtros |
| Estado en el cliente: el mapa del labview, el editor SGA, el overlay de riesgo | Permisos y multi-tenencia (403/404 con org o lab ajeno) |
| **Un** recorrido representativo por página compartida entre muchas rutas | Cada variante de esa página compartida |

> **Si dos rutas comparten plantilla, comparten escenario Selenium. Lo que las diferencia va a
> pruebas unitarias.**

## Las tres capas (+ la cuarta pregunta)

1. **Smoke de rutas** — `make test-urls` (`src/organilab_test/tests/test_url_smoke.py`): todas las
   rutas `pagina` responden 200. Verifica que renderiza, no permisos. `KNOWN_BROKEN`
   (`url_smoke.py:42`) se aserta al revés y su estado sano es **vacío**.
2. **Unitarias / de cliente** — validación, permisos, datasets, serializers, exportadores. Todo lo
   que se multiplica por variante. Modelo: `src/report/tests/test_register.py` recorre
   `REPORT_FORMS` con `subTest`, así un reporte nuevo queda cubierto solo por registrarse.
3. **Selenium** — solo interacción real, en flujos que encadenan acciones. Modelo: el piloto de
   `report` (`src/report/tests/selenium_tests/`): 3 escenarios cubren 18 rutas.
4. **¿Con qué rol?** — `presentation/probe.py` (middleware, `ORGANILAB_FEATURE_PROBE=1`) anota cada
   petición con los `Rol` del usuario en el ámbito de la URL, con el mismo `Q` que usa
   `ProfileMiddleware`. `RoleCoverageBaselineTest` impide que la cobertura retroceda contra
   `cobertura_por_rol.json`. Reglas:
   - **Una petición de superusuario no cuenta como cobertura de ningún rol.**
   - **Un `Rol` que solo existe en fixtures no cuenta** (alias reales en `presentation/role_catalog.py`).

## Convenciones Selenium

- **Un `test_` por flujo, no por acción** (referencias: `academic/tests/selenium_tests/test_procedure_template.py:30`,
  `laboratory/tests/selenium_tests/manage_laboratory/test_laboratoryroom.py:152`).
- Selectores en `src/organilab_test/tests/selenium_xpaths.py`; **nada de XPath posicional**.
- **Nunca asertar `//body`**: la página de error 403 también lo tiene. Cada escenario espera un
  marcador **propio de su pantalla** (sección «marcadores de página»). Un fallo de permisos debe
  romper la prueba, no canalizarse.
- `@modifies_db` solo surte efecto en clases que heredan `OptimizedSeleniumBase`; marcar solo el test
  que ensucia.
- **El GIF va al final**: primero verde sin GIF (`make test-selenium-single TEST=…`), luego una corrida
  con `GIF=1`.
- El último paso de un test que muta espera de verdad (`wait_ready` / `wait_dt`), no `sleep` (con
  capturas apagadas el `sleep_factor` es 0.1).

## Backlog

| # | Pendiente | Fuente |
|---|-----------|--------|
| 1 | Fusionar los ~44 `test_view_*` de un solo paso en el flujo CRUD de su vista, **conservando los `folder_name` de GIF**. Antes, cruzarlos contra `organilab_docs/source/**/*.rst` y `source/_extra/capacitacion/**/*.html`: los referenciados crecen a 3–4 pasos con el mismo nombre; los no referenciados se fusionan y borran | `grep "def test_view_" -r src --include=*.py` en suites Selenium |
| 2 | **15 de 18 roles canónicos sin ejercitar**; la sección «Lo que falta probar» lista cada par (paso, rol) con su escenario | `COBERTURA_POR_ROL.md` |
| 3 | Funcionalidades marcadas **sin prueba** (15 a 2026-09-16) | `INVENTARIO_FUNCIONALIDADES.md` / `make feature-gaps` |
| 4 | Páginas sin prueba de interacción (60 a 2026-09-16) | `INVENTARIO_URLS.md` |
| 5 | `URLNAME_PERMISSIONS` desalineado: se reportaron 69 claves fantasma y 190 nombres reales faltantes (sin reverificar); darle un guardián como el del inventario | `auth_and_perms/management/commands/urlname_permissions.py` |

## Cómo mantener esto vivo

```bash
make url-inventory          # regenera el inventario de rutas y el CSV
make url-inventory-check    # falla si el commiteado quedó viejo
make test-urls              # smoke de todas las páginas
make feature-catalog        # regenera el catálogo de funcionalidades
make feature-catalog-check  # falla si el catálogo commiteado quedó viejo
make feature-gaps           # funcionalidades sin prueba y rutas sin funcionalidad
make feature-roles          # qué roles del eje aparecen en el catálogo
make feature-coverage       # mide con la sonda qué ROL ejercita cada paso (~20 min; -fast ~4 min)
```
