# Estrategia de pruebas por vista

Qué debería probarse en cada vista, con qué herramienta, y por qué. Se apoya en
[`INVENTARIO_URLS.md`](INVENTARIO_URLS.md), que se regenera con `make url-inventory`
y clasifica las 1 681 rutas con nombre del proyecto.

Una ruta, sin embargo, no es una funcionalidad, y «cubierta» no es «cubierta para este
rol». Esas dos capas viven en
[`INVENTARIO_FUNCIONALIDADES.md`](INVENTARIO_FUNCIONALIDADES.md) —44 funcionalidades con
sus pasos y sus actores— y en [`COBERTURA_POR_ROL.md`](COBERTURA_POR_ROL.md), que **mide**
qué rol ejecutó cada paso en vez de deducirlo. Ver «La cuarta pregunta», más abajo.

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

**Es una pista, no una medición**, y conviene no olvidarlo: solo dice que alguien escribió
el nombre de la ruta en un literal. No sabe si la prueba asertó algo, si está `@skip`, ni
—lo que más importa— con qué rol se ejecutó. Para eso está el catálogo de funcionalidades
y su sonda ([`INVENTARIO_FUNCIONALIDADES.md`](INVENTARIO_FUNCIONALIDADES.md)).

| App | Páginas | Sin ninguna prueba | Prioridad |
|---|---:|---:|---|
| `laboratory` | 66 | 18 | P2 |
| `sga` | 29 | 12 | P1 |
| `riskmanagement` | 27 | 7 | P3 (IPER sin nada) |
| `report` | 18 | 15 | **piloto** |
| `academic` | 8 | 0 | — |
| `auth_and_perms` | 8 | 3 | P4 |
| `presentation` | 5 | 0 | — |
| `derb` | 4 | 1 | P5 (Formio, caro) |
| `msds` | 3 | 1 | P4 |
| `reservations_management` | 2 | 0 | — |
| `authentication` | 1 | 0 | — |
| `pending_tasks` | 1 | 0 | — |

Desde esta tanda, **las 172 páginas pasan por el smoke**, así que "sin prueba" ya solo
significa "sin prueba de interacción".

## Lo que el smoke encontró el primer día (cerrado)

Tres páginas reventaban sin que nadie lo supiera: `laboratory:furniture_create` (500 por
`{% get_qr_svg_img furniture %}` sin `furniture` en la vista de creación),
`riskmanagement:risk_report` e `incident_detail` (`NoReverseMatch` por un
`{% url 'report:report_status' … lab_pk=0 %}` que ningún patrón aceptaba) y
`sga:edit_personal` (`AttributeError` al leer `barcotesthtml` sin comprobar que exista).

**Las tres están arregladas y `KNOWN_BROKEN` está vacío**
(`src/organilab_test/tests/url_smoke.py:42`). El mecanismo se queda: las entradas se
asertan al revés, así que si una página listada ahí volviera a responder 200 la prueba
falla y obliga a sacarla. La lista vacía es el estado sano, no un descuido.

## Hallazgo cerrado: las rutas duplicadas de `report/urls.py`

`base_reports` y `base_organization_reports` se montan bajo el mismo prefijo
`<int:org_pk>/`, y durante un tiempo repitieron rutas: `create/` aparecía dos veces con
vistas distintas y `create_organization_request_by_report` era inalcanzable. **Ya no**:
las rutas de organización llevan su propio sufijo (`create/organization/`,
`download/organization/`, `table/organization/<pk>/`, `src/report/urls.py:17-39`) y el
comentario del propio fichero documenta la trampa. La plantilla que provocaba el
`NoReverseMatch` ahora pide `report:report_organization_status`
(`base_report_organizations.html:97`).

Lo único que sigue compartido es la URL `status/`, con dos nombres apuntando a la misma
vista (`urls.py:21,39`). Es deliberado y benigno: ambos nombres resuelven, ninguna ruta
queda muerta. El guardián lo confirma — la lista blanca de duplicados de
`test_url_inventory.py` tiene un solo elemento, `laboratory:create_user_qr`.

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
- **El GIF va al final, nunca durante.** Una prueba nueva se escribe y se pone verde
  **sin GIF** (`make test-selenium-single TEST=…`, que ya corre headless, en serie y con
  `GENERATE_SCREENSHOTS=False`). Solo cuando el flujo está estable se le añaden los
  `path_list` con sus `screenshot_name` y se corre una vez con `GIF=1` para producir los
  GIF que luego se revisan a mano. Iterar con las capturas activadas cuesta un orden de
  magnitud más de tiempo en un test que todavía va a cambiar — y es tiempo tirado, porque
  cada retoque invalida las capturas anteriores.
- El último paso de un test que muta debe esperar de verdad (`wait_ready` / `wait_dt`), no
  confiar en `sleep`: con `GENERATE_SCREENSHOTS=False` el `sleep_factor` es 0.1 y un
  `sleep: 2` dura 0.2 s. De ahí venía el deadlock del teardown.

## Cómo mantener esto vivo

```bash
make url-inventory          # regenera el inventario de rutas y el CSV
make url-inventory-check    # falla si el commiteado quedó viejo
make test-urls              # smoke de las 172 páginas, ~28 s
make feature-catalog        # regenera el catálogo de funcionalidades
make feature-catalog-check  # falla si el catálogo commiteado quedó viejo
make feature-gaps           # funcionalidades sin prueba y rutas sin funcionalidad
make feature-roles          # qué roles del eje aparecen en el catálogo
make feature-coverage       # mide con la sonda qué ROL ejercita cada paso
```

`src/presentation/tests/test_url_inventory.py` guarda cuatro invariantes: ninguna ruta sin
clasificar, **los dos ficheros generados** al día, no perder páginas por una heurística
rota, y ningún nombre duplicado nuevo. Cuando alguien añada una ruta que la cascada de `classify()` no reconozca,
la prueba falla y obliga a decidir — que es justo lo que a `URLNAME_PERMISSIONS` nunca le
pasó, y por eso hoy tiene 69 claves fantasma y le faltan 190 nombres reales.

## La cuarta pregunta: ¿con qué rol se ejecutó?

Las tres capas de arriba contestan *qué* se prueba. Falta *quién*: Organilab es
multiinquilino y con permisos por rol, así que «la página abre» no dice nada si abre
para un superusuario.

Y la respuesta, medida y no estimada, es incómoda:

| Estado del paso | Pasos |
|---|---:|
| ejercitado por un rol canónico | **8** |
| solo superusuario | **131** |
| nunca ejercitado | 21 |
| fuera del alcance de la sonda (Celery) | 9 |

**15 de los 18 roles canónicos no los ejercita ninguna prueba.** De casi 4 900
peticiones observadas en la suite completa, la gran mayoría las hace `admin`, que es
superusuario.

La primera medición fue peor todavía —3 pasos y 16 roles— y mejoró al quitarle el
`is_superuser` a `lab_manager` en `fixtures/selenium/capacitacion.json` y darle al rol
los cinco permisos de reservación que le faltaban. Ese cambio de un flag es lo que
convirtió el taller 5 en una prueba de permisos de verdad.

Eso no significa que las pruebas no sirvan —prueban la interacción, y eso es real—,
significa que **no prueban la autorización**, que es la mitad del sistema.

### Cómo se mide

`presentation/probe.py` es un middleware que se enciende con
`ORGANILAB_FEATURE_PROBE=1` y anota cada petición con los `Rol` que el usuario tenía en
el ámbito de esa URL, resueltos con **el mismo `Q` que usa `ProfileMiddleware` para
autorizar** (`auth_and_perms.organization_utils.profile_permission_scope_query`, extraído
justo para que no haya dos versiones). Va al final de la cadena, después de
`ProfileMiddleware`, para ver el resultado real: un 403 es parte de la medición.

No hubo que tocar ni una prueba. `django.test.Client` recorre la cadena entera y
`StaticLiveServerTestCase` levanta el servidor en el mismo proceso con el mismo
`MIDDLEWARE`, así que las 235 pruebas Selenium alimentan la sonda solas.

La alternativa era que cada prueba declarase lo que ejercita (`covers = [...]`). Se
descartó: 1 271 anotaciones a mano, y una lista paralela que se pudre. Aquí no se
escribe una lista, se observa lo que ocurre.

### Las dos reglas que dan el número

> **Una petición ejecutada por un superusuario no cuenta como cobertura de ningún rol.**

`ProfileMiddleware` se salta a los superusuarios (`authentication/middleware.py:49-50`) y
`has_perm` cortocircuita antes de mirar backends. Con superusuario, cualquier aserción de
permiso pasa sin probar nada.

> **Un `Rol` que solo existe en las fixtures tampoco cuenta.**

Los 22 «Gestión de X» de `base_selenium.json` son uno por modelo y no existen en
producción. La tabla de alias de `presentation/role_catalog.py` sí traduce los que son de
verdad: `capacitacion.json` escribe `Docente` donde el catálogo dice `Profesor`, y
`Tecnico` sin tilde.

### Cómo se usa

```bash
make feature-coverage        # suite completa + Selenium headless + ingesta (~20 min)
make feature-coverage-fast   # solo sin navegador, medición parcial (~4 min)
```

Deja `roadmap/COBERTURA_POR_ROL.md` para leer y `roadmap/cobertura_por_rol.json` como
línea base commiteada. No corre en cada commit —costaría la suite Selenium entera—: el
guardián de cada commit compara contra el JSON, y `RoleCoverageBaselineTest` impide que
los dos números empeoren y que la medición hable de pasos que ya no existen.

La sección **«Lo que falta probar»** del informe es el backlog ya escrito: **739 pares
(paso, rol)** que el catálogo declara y la sonda nunca vio, cada uno con su escenario.

### La prueba de fuego, y lo que destapó

`lab_manager` (pk 2) era superusuario y es quien corre casi todos los flujos de
aprobación del taller 5. Quitarle esa bandera tenía que hacer **fallar** pruebas que
pasaban. Cayeron **3 de las 8** del taller.

Lo interesante fue por qué no cayeron las otras cinco. Su `path_list` entero era esto:

```python
{"path": "//body", "wait_ready": True, "screenshot_name": "..."}
```

Y **una página de error 403 también tiene `<body>`**. Esas pruebas pasaban sobre una
pantalla que el usuario no puede ver. Eran **19 de las 40** del corpus de capacitación:
la mitad de la suite no distinguía la pantalla real de la de error, así que decía
«cubierta» justo donde faltaba un permiso.

> **Una aserción que no distingue la pantalla real de la de error no comprueba nada.**
> En un sistema con permisos por rol, organización y laboratorio, es peor que no tener
> la prueba: da una señal verde falsa exactamente en el caso que hay que detectar.

La solución **no** fue un guardia genérico que detectase la página de error. Un guardia
es una capa intermedia con puertas traseras, y un fallo de permisos no debe ignorarse ni
canalizarse: debe romper la prueba donde ocurre. Cada escenario espera ahora un elemento
**propio de su pantalla**, y todos esos selectores viven en
`organilab_test/tests/selenium_xpaths.py` (sección «marcadores de página»), que es el
módulo que ya existía para no repartir selectores por decenas de ficheros. Las dos
plantillas que no tenían ningún `id` estable —`report_index.html` y
`manage_reservation.html`— lo recibieron.

Comprobación de que el arreglo sirve: quitándole al rol los permisos de reservación,
antes fallaban **3 de 8** pruebas del taller 5; ahora fallan **7 de 8**. La octava corre
como docente y no debe verse afectada.

## Dos correcciones a la heurística de cobertura

La cifra de "sin ninguna prueba" pasó de 41 a 57 páginas sin que se borrara un solo test.
Lo que cambió fue dejar de mentir en las dos direcciones:

1. **Se casaba también por el nombre pelado.** `annotate_coverage()` comparaba contra
   `{full_name, name}`, así que un `reverse("index")` de cualquier app marcaba como
   cubierta cualquier ruta llamada `index` de cualquier namespace. Ahora, si la ruta tiene
   namespace, se exige el nombre completo.
2. **Solo se leía `test*.py`.** Los `base.py` de las suites Selenium
   —`capacitacion/base.py`, `transversal/base.py`— son justamente donde viven los
   ayudantes `navigate_to_*` con su `reverse()` literal, y quedaban fuera del barrido. Eso
   producía falsos negativos en las rutas que solo se visitan por ayudante. Ahora se lee
   todo `.py` dentro de un paquete `tests/`.

Y una tercera, en el comando: **`annotate_coverage()` se llama siempre**. Estaba
condicionada a `--coverage | --format md | --check`, y el target del CSV no pasaba
ninguno: `roadmap/inventario_urls.csv` se generó durante toda su vida con las columnas
`selenium` y `pruebas` a cero en las 1 681 filas. El guardián no lo veía porque `--check`
solo comparaba el markdown; ahora comprueba los dos ficheros.
