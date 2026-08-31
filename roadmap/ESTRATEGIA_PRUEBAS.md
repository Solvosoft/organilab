# Estrategia de pruebas por vista

Qué debería probarse en cada vista, con qué herramienta, y por qué. Se apoya en
[`INVENTARIO_URLS.md`](INVENTARIO_URLS.md), que se regenera con `make url-inventory`
y clasifica las 1 683 rutas con nombre del proyecto.

## El reparto

Hasta ahora, comprobar que una página abría costaba un test Selenium: arranque de Chrome,
carga de fixtures, unos tres segundos. De las 216 pruebas Selenium, **50 son de un solo
paso** y casi todas son `test_view_*` que solo capturan un listado. Eso es usar el
instrumento más caro para la pregunta más barata.

El criterio, aplicable sin discutir caso por caso:

| Va a Selenium | Va a prueba de cliente o unitaria |
|---|---|
| Formularios con widgets que solo existen en el navegador: select2, datepicker, drag & drop de Formio | Que la página renderice (eso es el smoke) |
| Modales, SweetAlert y flujos que solo se completan con JS | Validación de formularios, `clean_*`, `form.is_valid()` |
| DataTables: búsqueda, paginación, acciones por fila | El endpoint que alimenta el DataTable: JSON, orden, filtros |
| Estado en el cliente: el mapa del labview, el editor SGA, el overlay de riesgo | Permisos y multi-tenencia (403/404 con org o lab ajeno) |
| **Un** recorrido representativo por página compartida entre muchas rutas | Cada variante de esa página compartida |

De ahí sale la regla que más trabajo ahorra:

> **Si dos rutas comparten plantilla, comparten escenario Selenium. Lo que las diferencia
> va a pruebas unitarias.**

## Las tres capas

1. **Smoke de rutas** — `make test-urls`
   (`src/organilab_test/tests/test_url_smoke.py`). Recorre las 172 rutas de categoría
   `pagina` con `django.test.Client` y comprueba que responden 200. Seis clases, una por
   familia de fixture, **28 segundos**. Verifica que la vista *renderiza*; no verifica
   permisos, y el docstring lo dice para que nadie lo confunda.
2. **Pruebas unitarias / de cliente** — validación, permisos, datasets, serializers,
   exportadores. Es donde va todo lo que se multiplica por variante.
3. **Selenium** — solo interacción real, y en flujos que encadenan varias acciones.

## Estado por app

Las columnas salen del cruce automático del inventario: una ruta cuenta como cubierta si
alguna prueba la nombra en un `reverse()`.

| App | Páginas | Sin ninguna prueba | Prioridad |
|---|---:|---:|---|
| `laboratory` | 66 | 19 | P2 |
| `sga` | 29 | 13 | P1 |
| `riskmanagement` | 27 | 7 | P3 (IPER sin nada) |
| `report` | 18 | 15 | **piloto** |
| `academic` | 8 | 0 | — |
| `auth_and_perms` | 8 | 3 | P4 |
| `presentation` | 5 | 3 | P4 |
| `derb` | 4 | 1 | P5 (Formio, caro) |
| `msds` | 3 | 1 | P4 |
| `reservations_management` | 2 | 0 | — |
| `authentication` | 1 | 1 | P4 |
| `pending_tasks` | 1 | 0 | — |

Desde esta tanda, **las 172 páginas pasan por el smoke**, así que "sin prueba" ya solo
significa "sin prueba de interacción".

## Lo que el smoke encontró el primer día

Tres páginas que reventaban sin que nadie lo supiera. Están en `KNOWN_BROKEN`
(`src/organilab_test/tests/url_smoke.py`), asertadas al revés: cuando una empiece a
responder 200, la prueba falla y obliga a sacarla de la lista.

1. **`laboratory:furniture_create` — 500.** `furniture_form.html:48` llama
   `{% get_qr_svg_img furniture %}`, pero en la vista de creación no existe `furniture`:
   el tag recibe la cadena vacía y revienta en `get_qr_by_instance`
   (`presentation/utils.py:51`) con `'str' object has no attribute '_meta'`. La página de
   crear mueble no abre.
2. **`riskmanagement:risk_report` y `riskmanagement:incident_detail` — NoReverseMatch.**
   `report/base_report_organizations.html:97` pide
   `{% url 'report:report_status' org_pk=org_pk lab_pk=0 %}`, y el patrón que gana ese
   nombre solo acepta `org_pk` (`report/urls.py:28`). Es la secuela directa de los nombres
   duplicados de `report/urls.py` (ver abajo).
3. **`sga:edit_personal` — AttributeError.** `sga/views/editor.py:256` lee
   `display_label.barcotesthtml` sin comprobar que exista; cualquier `DisplayLabel` sin
   código de barras tumba la página.

## Hallazgo: rutas duplicadas en `report/urls.py`

`base_reports` (l.14-29) y `base_organization_reports` (l.30-47) se incluyen **bajo el
mismo prefijo** `<int:org_pk>/` (l.136-137):

- `create_organization_report_request` está en l.16-20 y l.31-35.
- `generate_organization_report`, en l.22-26 y l.36-40.
- `create/` aparece dos veces con vistas distintas (l.15 y l.16): al resolver siempre gana
  la primera, así que `create_organization_request_by_report` es inalcanzable por esa URL.
- `report_status` (l.28) y `report_organization_status` (l.46) apuntan a la misma URL
  `status/`.

No hay ningún `report_status` con `lab_pk`, y por eso el hallazgo 2 del smoke. Conviene
arreglarlo antes de escribir pruebas nuevas de reportes: mientras el nombre resuelva a la
ruta equivocada, cualquier prueba que use `reverse()` estará midiendo otra cosa.

## Piloto: la app `report`

15 de sus 18 páginas no tenían ninguna prueba. Pero contarlas como 18 pruebas Selenium
sería exactamente el error que este documento intenta evitar.

**Once de las trece vistas de listado comparten la misma plantilla**,
`report/base_report_form_view.html` (`src/report/views/reports_org.py`: `ObjectList`:47,
`LimitedShelfObjectList`:99, `ReactivePrecursorObjectList`:128, `LogObjectView`:162,
`DiscardShelfReportView`:314, `ReactiveReport`:346, `RiskZoneReport`:377,
`ReactiveStockReport`:409, `FurnitureReportView`:440, `CompatibilityReport`:489,
`HazardMapReport`:520, `DonationReportView`:595). Es la misma pantalla con distinto
dataset: un formulario, un botón `#send` y un panel de estado que hace polling.

### Escenarios Selenium: 3, no 18

| # | Escenario | Cubre |
|---|---|---|
| 1 | Sobre `base_report_form_view.html`: llenar el formulario, pulsar `#send`, esperar el panel de estado, abrir la tabla en `report_table`, descargar | las 11 vistas que comparten la plantilla |
| 2 | `precursor_report` (`PrecursorsView`:192, plantilla propia `precursor_report.html`) con su tabla de valores | 2 rutas |
| 3 | `regency_report` (`report/views/base.py:529`, `regency_report.html`), formulario distinto | 1 ruta |

Lo que justifica Selenium aquí es el ciclo asíncrono: el `#send` dispara una tarea, el
panel hace polling contra `report_status` y la descarga aparece al final. Eso no se puede
comprobar con `client.get()`.

### Pruebas unitarias: el registro, parametrizado

`src/report/register.py` declara `REPORT_FORMS`: **16 tipos de reporte** —
`reactive_precursor`, `report_laboratory_room`, `report_objects`, `report_limit_objects`,
`report_objectschanges`, `report_furniture`, `report_organization_reactive_list`,
`report_waste_objects`, `reactive_report`, `risk_zone_report`, `stock_reactive_report`,
`regency_report`, `compatibility_report`, `hazard_map_report`, `chemicalinventory`,
`donations_report`— **× 5 formatos** (`html`, `pdf`, `xls`, `xlsx`, `ods`), cada uno
apuntando a un callable por ruta de importación.

Son 80 combinaciones, y se prueban recorriendo el registro con `subTest`: que cada ruta
importe, que cada `form` valide, que cada constructor arme su dataset. Es lo que ya empezó
`src/report/tests.py` (194 líneas sobre `get_dataset`, `furniture_doc`,
`report_discard_object_doc`), pero recorriendo el registro en vez de a mano — así un
reporte nuevo queda cubierto por el solo hecho de registrarse.

**El contraste es el argumento entero:** 18 rutas se cubren con 3 escenarios de navegador
y ~80 aserciones unitarias, no con 18 pruebas Selenium.

## La convención: un test, varias acciones

El encadenado ya es el estilo dominante —71 % de las pruebas hacen dos o más acciones y el
41 % hacen cinco o más—. Lo que falta es cerrar dos huecos.

**1. Un `test_` por flujo, no por acción.** Patrón de referencia en el repo:
`src/academic/tests/selenium_tests/test_procedure_template.py:30`, un único `test_` que
encadena crear → actualizar → detalle → pasos → borrar; y
`src/laboratory/tests/selenium_tests/manage_laboratory/test_laboratoryroom.py:152`
(`view → add → update → delete`, cinco GIFs en un test).

**2. Fusionar los 50 de un paso conservando los GIFs.** Se absorben en el flujo CRUD de su
vista llamando `create_gif_process` varias veces dentro del mismo `test_`, **con los
nombres de carpeta originales**: la documentación sigue encontrando sus GIFs y desaparecen
50 arranques de navegador. Antes de tocar nada hay que cruzar los `folder_name` contra
`docs/source/**/*.rst`: los referenciados se promueven (crecen a tres o cuatro pasos
manteniendo el nombre), los que nadie referencia se fusionan y se borran.

Reglas que acompañan, todas con causa conocida en esta rama:

- Reutilizar `src/organilab_test/tests/selenium_xpaths.py` (`select2_result`,
  `modal_submit_btn`, `datatable_row_action`, `sidebar_menu_item`) en vez de escribir
  XPath a mano.
- **Nada de XPath posicional** tipo `//*[@id='movesocontainerform']/div[7]/div/span`: es la
  fuente de los flakes ya diagnosticados y se rompe con cualquier retoque de plantilla.
  Selector por `id`, `data-*` o clase.
- `@modifies_db` solo surte efecto en clases que heredan `OptimizedSeleniumBase`; en las
  que heredan `SeleniumBase` directo es un no-op. Marcar solo el test que ensucia, y
  agrupar en él las acciones destructivas: cada marca cuesta un `flush` más un `loaddata`.
- El último paso de un test que muta debe esperar de verdad (`wait_ready` / `wait_dt`), no
  confiar en `sleep`: con `GENERATE_SCREENSHOTS=False` el `sleep_factor` es 0.1 y un
  `sleep: 2` dura 0.2 s. De ahí venía el deadlock del teardown.

## Cómo mantener esto vivo

```bash
make url-inventory        # regenera el inventario y el CSV
make url-inventory-check  # falla si el commiteado quedó viejo
make test-urls            # smoke de las 172 páginas, ~28 s
```

`src/presentation/tests/test_url_inventory.py` guarda cuatro invariantes: ninguna ruta sin
clasificar, el fichero al día, no perder páginas por una heurística rota, y ningún nombre
duplicado nuevo. Cuando alguien añada una ruta que la cascada de `classify()` no reconozca,
la prueba falla y obliga a decidir — que es justo lo que a `URLNAME_PERMISSIONS` nunca le
pasó, y por eso hoy tiene 69 claves fantasma y le faltan 190 nombres reales.
