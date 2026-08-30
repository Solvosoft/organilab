# Etapa 14 — labview: mapa digital del laboratorio sobre API (salida total de django_ajax)

**Estado: EN CURSO — F0 hecha (2026-08-29).** Último proyecto diferido de la migración dj060
(viene de la etapa 2 y de la etapa 10 §labview).

> Arquitectura y decisiones de diseño: [`14_ARQUITECTURA_LABVIEW.md`](14_ARQUITECTURA_LABVIEW.md).
> Prototipo visual de la pantalla: [`14_labview_prototipo.svg`](14_labview_prototipo.svg)
> (vista de consulta, modo edición, móvil y leyenda de riesgo/permisos).
> Este documento es el plan ejecutable (qué se hace, en qué orden, con qué archivos).

## Objetivo

**Mapear el laboratorio de forma digital: la representación espacial alimenta la medición de
riesgo.** La vista de laboratorio es un widget multinivel (sala → mueble → estante → objeto)
cuyo layout vive en `Furniture.dataconfig` sin representación normalizada. Hay que reemplazar
COMPLETO el AJAX heredado de `django_ajax` por APIs + componentes de la biblioteca, con una
interfaz **semejante a la actual** (el usuario debe reconocerla) pero de **navegación más
fluida** hacia todos los sectores del laboratorio, que siga pareciéndose a la ubicación real.

## Decisiones de Luis (firmes, NO re-preguntar)

1. **Vista paralela**: la interfaz nueva vive en `laboratory:labview`; `laboratory:rooms_list`
   queda intacta hasta validar. Redirect + borrado en la fase final (F7).
2. **Overlay de riesgo INCLUIDO** en esta etapa: capa activable que colorea estantes con los
   datos del hazard_map, más ocupación y agregados por sala/mueble en el endpoint de árbol.
3. **Editor de cuadrícula con persistencia POR OPERACIÓN**: cada crear/mover/borrar estante y
   añadir/quitar fila o columna persiste al instante vía API que muta `dataconfig`
   server-side. Muere el string armado en JS (`createconfigdata()`).
4. **`IPERHazard.location` → proyecto aparte** (solo queda anotado aquí).
5. **Widget generalizable en djgentelella ACEPTADO** (con demo y tests; sin conocimiento de
   organilab).
6. **Código primero, pruebas al final**: una sola fase de pruebas (F6).
7. **La vista debe adaptarse a diferentes dispositivos** (móvil / tablet / escritorio).
8. **La interfaz se muestra según lo que el usuario puede hacer**: el manejo de permisos es
   transversal (ver §Permisos).
9. **Roadmap y arquitectura se escriben PRIMERO** (F0), para que la etapa sea retomable en
   otra sesión sin re-explorar.

## Hallazgos de la exploración (verificados, con referencias)

### Qué es hoy el labview

| Pantalla | URL name | Vista | Template | django_ajax |
|---|---|---|---|---|
| Consulta (labview) | `laboratory:rooms_list` | `LaboratoryRoomsList` (`views/labroom.py:63-276`) | `laboratoryroom_list.html` | **No** — árbol server-side + DataTable/REST |
| Admin de salas | `laboratory:rooms_create` | `LabroomCreate` (`views/labroom.py:287`) | `laboratoryroom_form.html` | No |
| **Editor de cuadrícula** | `laboratory:furniture_update` | `FurnitureUpdateView` (`views/furniture.py:97-150`) | `furniture_form.html` | **Sí — aquí vive todo** |

- La pantalla de consulta **ya es mayormente API**: árbol renderizado por el servidor
  (`laboratoryroom_list.html:56-88` + `{% display_furniture %}` →
  `templatetags/furniture_tags.py:11-23` → `shelf_card.html` con radios
  `name="shelfselected"`), DataTable `#shelfobjecttable` contra
  `laboratory:api-shelfobjecttable-list` (JSON), ~10 modales de acción ya JSON
  (`shelfobject/action_modal.html` + `base_modal_management.js`), búsqueda Tagify contra
  `api-search-labview-get` (`api/shelfobject.py:2508`) que hoy solo **muestra/oculta** nodos
  del DOM (`laboratory.js:419-592`).
- El **django_ajax vivo** está en el editor: `shelf_create` (`views/shelfs.py:317-404`,
  responde `append-fragments` con `shelf_details.html:378-388`), `shelf_edit` (`:412-496`,
  `fragments["#shelf_<pk>"]`), `shelf_delete` (`:41-80`, GET fragmento con `<script>` / POST
  JSON), `get_shelfs_list` (`api/views.py:508-519`, JSON con HTML dentro), y el grid
  pre-renderizado a string en `views/furniture.py:111-129` → `dataconfig.html`, que
  `furniture_table.js:88-108` (`createconfigdata()`) re-serializa desde el DOM al guardar.
- **Capa legacy muerta** (rutas vivas sin llamador funcional): `generic.py:ShelfListView` +
  `shelf_list.html`, `components/shelf_list{,_discard}.html`, `shelfObject_list.html`,
  `furniture_list.html` + `furniture.list_furniture` (`views/furniture.py:204`),
  `shelfobject.list_shelfobject` (`:104`), `ShelfObjectCreate` (`:314`, su
  `get_success_url` apunta a una ruta comentada → `NoReverseMatch`), `shelfobject_edit`
  (`:414`), `shelfobject_delete` (`:556`), `ShelfObjectSearchUpdate` (`:492`, marcada
  `# fixme Delete`), y funciones de `shelfobjectedit.js` (`wait_*`, `function_name_*`) con
  selectores inexistentes.

### `dataconfig`

`Furniture.dataconfig` (`models.py:900`) es un `TextField` con una **matriz 3D
filas → columnas → lista de pks de Shelf**; una celda puede tener varios estantes y `[]` es
celda vacía:

```json
[[[400],[2],[3],[4]],[[1],[444],[4],[404]]]
```

- **La posición del estante SOLO existe ahí**: `Shelf.positions()/row()/col()`
  (`models.py:819-832`) delegan en `Furniture.get_position_shelf()`.
- **5 parsers**: `shelf_utils.get_dataconfig` (`shelf_utils.py:21-40`, el canónico),
  `models.py:958-992`, `views/shelfobject.py:630-638` (parse "sucio" por `replace`/`split`),
  `tasks.py:137` (regex `\d+`), `risk_management/hazard_map_utils.py:119-159` (propio).
- **3 escritores incompatibles**: el JS por concatenación (`furniture_table.js:88-108`),
  `models.remove_shelf_dataconfig`/`change_shelf_dataconfig` con `str(dataconfig)` (repr de
  Python, `models.py:926/955`), e `import_materiales._set_dataconfig` con `json.dumps` de
  strings `"1,2"` (`import_materiales.py:23-59`).
- **Bugs reales**: `models.py:915` hace `val.set("")` sobre una lista → `AttributeError` en la
  rama del formato legacy `int`; los `str()` citados producen JSON inválido con comillas
  simples (lo salva el parser tolerante, no el formato).
- `FurnitureForm.dataconfig` solo valida con un `RegexValidator` (`forms.py:460-469`): no
  comprueba rectangularidad ni existencia de los pks.
- Los `row`/`col` que viajan en las URLs del editor son **posicionales del DOM del momento**;
  si el usuario añade o borra filas antes de guardar, quedan desfasados respecto a la BD.

### APIs existentes reutilizables

- `ShelfObjectViewSet` (`api/shelfobject.py:807`): 25+ actions (create por tipo, box,
  increase/decrease, reserve, `details`, transfer_*, delete, comments, status,
  `move_shelfobject_to_shelf`, `shelf_availability_information`, container, edits por tipo,
  recipients). Permisos por dict propio `permissions_by_endpoint` (`:810-855`) +
  `_check_permission_on_laboratory` (`:858-874`).
- `ShelfObjectTableViewSet` (`:133`): la lista por estante (`?shelf=`), formato DataTable.
  Su serializer (`api/serializers.py:311-386`) devuelve `actions` como **HTML** de 124 líneas
  (`templates/laboratory/serializers/shelfobject_actions.html`). **No exige
  `view_shelfobject`.**
- `SearchLabView` (`api/shelfobject.py:2508`): devuelve los pks jerárquicos
  (labroom/furniture/shelf/shelfobject/object) de cada coincidencia. Ya es el sustrato de un
  breadcrumb / "revelar en el árbol".
- Sub-CRUDs de equipo (maintenance, log, calibrate, guarantee, training) +
  `shelfobject_equipment_tables.js` + `equipment_edit.html`: **el patrón moderno de
  referencia** (N × `ObjectCRUD` en una página con modales de la biblioteca).
- Lookups select2 encadenados: `gtapis/lab_room/`, `gtapis/furniture/?relfield=`,
  `gtapis/shelf/?relfield=` (`report/gtselects.py:36,101,270`).
- **NO existen**: viewsets ni serializers de `LaboratoryRoom`, `Furniture` ni `Shelf`, ni
  endpoint de árbol.

### Riesgo (el objetivo del mapa)

- `risk_management/hazard_map_utils.py`: `collect_room_shelf_hcodes` (`:33`),
  `compute_shelf_danger` (`:82`, incompatibilidad H-code **entre estantes de la misma sala**,
  colores R/A/V/-), `_build_furniture_grid` (`:228`, re-parsea `dataconfig` con **N+1**:
  `Shelf.objects.get(pk=...)` dentro de doble bucle), `compute_lab_tonnage` (`:162`, **solo
  por laboratorio**), `build_lab_hazard_map` (`:189`), `_collect_alerts` (`:288`, ya emite
  pks espaciales). Motor: `compatibility_utils.get_compatibility`.
- Salidas: `report/views/riskzones.py:467-516` (hazard_map html/pdf/visual).
  `report/templates/report/hazard_map_visual.html:45-49` enlaza a
  `laboratory:rooms_list?labroom=&furniture=&shelf=` — **contrato de deep-link** que también
  usan los QR impresos (`views/labroom.py:305-311`, `shelf_card.html:32`).
- Ya existe validación de capacidad del estante al crear/mover
  (`shelfobject/utils.py:888-950`) y filtros de destino por capacidad (`:804-874`).

### Biblioteca (djgentelella 0.6.0)

Disponible: `ObjectCRUD` (`static/gentelella/js/obj_api_management.js:375-757`, con
`object_actions` cuya visibilidad por fila la decide el dict `actions` del serializer, y
`link:true` para navegar), `GTBaseFormModal` (`:25-241`), `BaseDetailModal` (`:243-373`),
`BaseObjectManagement`/`BaseInlineObjectManagement`/`AuthAllPermBaseObjectManagement`
(`objectmanagement.py`), `CardList`/`ListAreaViewset`, Squirrelly.
**No hay**: breadcrumb (el bloque de `base.html:60` está vacío), tabs, árbol navegable de
datos, ni grid de posiciones → de ahí el widget nuevo de F2.

## Permisos (eje transversal)

Hoy la decisión se toma en tres capas y **las tres deben sobrevivir**:

1. **Vista**: `permission_required` + `user_is_allowed_on_organization` +
   `organization_can_change_laboratory`.
2. **Pantalla**: `{% if perms.laboratory.* %}` en el template y booleanos inyectados al JS
   (`laboratoryroom_list.html:120,146-148`: `can_add_shelfobject`, recipients create/remove,
   transfer).
3. **Fila**: `serializers/shelfobject_actions.html` combina ~10 permisos **con el estado del
   objeto** (`type == REACTIVE/EQUIPMENT`, `is_box`, contenedor) para decidir cada botón.

Al pasar a JSON la decisión sigue siendo **del servidor** y viaja en el payload:

- **Capacidades en el árbol**: la respuesta de `tree/` trae un bloque `permissions` a nivel de
  laboratorio (`add_labroom`, `change_labroom`, `delete_labroom`, `add_furniture`,
  `change_furniture`, `delete_furniture`, `add_shelf`, `change_shelf`, `delete_shelf`,
  `add_shelfobject`, `view_shelfobject`, `view_report`…) y, cuando dependa del nodo, flags
  por nodo (`can_edit`, `can_delete`, `can_edit_grid`). **La UI no deduce permisos**: pinta lo
  que el payload autoriza.
- **Acciones por fila**: el campo `actions` del serializer de la tabla es un dict
  `{accion: bool}` que replica EXACTAMENTE las reglas de `shelfobject_actions.html` (permiso
  Y estado del objeto). Es una traducción 1:1 documentada, no un rediseño.
- **Doble control**: el payload sirve para *mostrar*; cada endpoint **vuelve a exigir** su
  permiso (dict `perms` por acción + `AllPermissionByAction`: acción no mapeada → 403). Un
  cliente manipulado no gana nada.
- **Degradación coherente**: sin `change_furniture` no aparece el modo edición ni sus
  handlers; sin `add_shelf` la celda vacía no ofrece "crear"; sin `view_shelfobject` la tabla
  no se pide. Nunca se ofrece una acción que el servidor va a rechazar.
- **Endurecimiento que se aprovecha aquí**: `ShelfObjectTableViewSet` no exige
  `view_shelfobject`; `ShelfObjectAPI`/`ShelfObjectGraphicAPI` (`api/views.py:474,489`) no
  declaran `permission_classes`. Los viewsets nuevos nacen con permisos por acción.

## Fases

### F0 — Roadmap y arquitectura (HECHA)

Este documento + [`14_ARQUITECTURA_LABVIEW.md`](14_ARQUITECTURA_LABVIEW.md) + entrada en la
tabla de `README.md`. Si la sesión se cierra aquí, otra sesión implementa F1-F7 desde estos
documentos sin re-explorar.

### F1 — Módulo canónico de `dataconfig`

**Nuevo `src/laboratory/dataconfig.py`**:

- `parse(text) -> list[list[list[int]]]` tolerante a todos los formatos históricos (JSON,
  CSV `"1,2"`, `int`, y el `str()` de Python vía `ast.literal_eval`).
- `dump(matrix) -> str` — siempre `json.dumps` de matriz de `int`.
- `resolve_shelves(matrix)` — un solo query `pk__in`, preserva el orden (absorbe
  `shelf_utils.get_dataconfig`).
- `get_position(matrix, shelf_pk)`, `iter_shelf_pks(matrix)`, `dimensions(matrix)`.
- `DataconfigService(furniture)` — cada método con `transaction.atomic` +
  `Furniture.objects.select_for_update()`: `place_shelf(shelf_pk, row, col)`,
  `move_shelf(shelf_pk, row, col)`, `remove_shelf(shelf_pk)`, `add_row(index=None)`,
  `remove_row(index)`, `add_col(index=None)`, `remove_col(index)`. `remove_row`/`remove_col`
  lanzan `DataconfigConflict` si la fila/columna tiene estantes (→ 409 en la API).

**Recableado** (los nombres públicos no cambian): `models.py`
(`remove_shelf_dataconfig` con el fix de `:915`, `change_shelf_dataconfig` con el fix de
`str()` en `:926/:955`, `get_position_shelf`, `get_row_count`, `get_col_count`),
`shelf_utils.py` (delega), `import_materiales.py` (ints en vez de strings), `tasks.py:137`,
`views/shelfobject.py:630-638`.

**Migración de datos** `laboratory/00XX_normalize_dataconfig.py`: parse + dump de todos los
`Furniture.dataconfig` (idempotente, no bloqueante porque el parser es tolerante).

### F2 — Widgets genéricos en djgentelella

Checkout `~/Desktop/desarrollo/django-gentelella-widgets`, rama `development`.

- `djgentelella/static/gentelella/js/positions_grid.js` + `css/positions_grid.css`:

  ```js
  new PositionsGrid(el, {
    data: {rows, cols, cells: [[[id, ...], ...], ...]},  // ids opacos
    items: {id: {...}},
    renderItem: (item) => html,       // el host decide el aspecto
    editable: false,
    handlers: {addRow, removeRow(idx), addCol, removeCol(idx),
               createItem(row, col), moveItem(id, row, col), removeItem(id)}
  })
  ```

  Cada handler devuelve `Promise<{data, items}>` y el widget **re-renderiza con lo que
  responde el servidor**: nunca serializa estado propio. Eventos `pg:item-click` /
  `pg:cell-click`; métodos `setData()`, `setEditable()`, `highlight(id)`.
- `djgentelella/static/gentelella/js/breadcrumb_nav.js`: `set(levels)`, `push({id,label})`,
  `truncateTo(i)`, callback `onNavigate(level, index)`; pensado para el bloque
  `{% block breadcrumbs %}` de `base.html:60`.
- **Responsive de fábrica**: CSS mobile-first, cuadrícula en CSS grid con scroll horizontal
  contenido en pantallas angostas, targets táctiles ≥44px, y el modo mover por toque
  (click-origen / click-destino, sin depender de drag). El breadcrumb colapsa niveles
  intermedios en "…".
- Demo en `demo/demoapp` (grid de "bodega" con endpoints JSON para los handlers, patrón de la
  demo de cardlist) + entrada de menú + docs breves. Tests en F6.

### F3 — Capa API labview

**Nuevo paquete `src/laboratory/api/labview/`** (`serializers.py`, `viewsets.py`,
`tree_builder.py`), router bajo el prefijo de laboratorio en `src/laboratory/urls.py`:
`path("api/labview/", include(labview_router.urls))` dentro del bloque `<org_pk>/<lab_pk>`.

- `src/laboratory/api/permissions.py`: extraer `_check_permission_on_laboratory`
  (`api/shelfobject.py:858`) a un mixin `LabOrgObjectManagement`
  (`BaseInlineObjectManagement` + dict `perms` por acción); `ShelfObjectViewSet` pasa a usar
  el helper extraído sin cambiar de comportamiento.
- CRUDs (perms django estándar de laboratoryroom/furniture/shelf):
  - `LabRoomManagement` — padre `Laboratory` (por `lab_pk` de la URL).
  - `FurnitureManagement` — padre `LaboratoryRoom`; `retrieve` incluye `grid`. Actions de
    grid (perm `change_furniture`, devuelven `{grid, shelves}` actualizado, 409 en conflicto):
    `POST .../<pk>/grid/row/` `{index?}`, `DELETE .../<pk>/grid/row/<idx>/`, ídem `col`.
  - `ShelfManagement` — padre `Furniture`. `create` exige `{row, col}` y delega en
    `DataconfigService.place_shelf` (la posición nace atómica con el estante); `destroy` usa
    `remove_shelf` (409 si tiene shelfobjects, reutilizando la guarda de
    `shelfs.delete_shelf`); action `PUT .../<pk>/move/` `{row, col}`. **Siempre por
    `shelf_pk`, nunca por índices del DOM.**
- **Árbol**: `GET .../api/labview/tree/?risk=1` (perm `view_laboratoryroom`).
  `tree_builder.py` en 3-4 queries (salas; muebles con `select_related`; estantes por
  `pk__in` de todos los `dataconfig` parseados; agregados de ShelfObject por
  `values(...).annotate(...)`). Contrato:

  ```json
  {
    "laboratory": {"id": 1, "name": "..."},
    "permissions": {"add_labroom": true, "change_furniture": false, "...": false},
    "rooms": [{
      "id": 3, "name": "Sala A",
      "counts": {"furniture": 4, "shelves": 12, "shelfobjects": 87},
      "risk": {"color": "red", "alerts": 2, "tonnage": {"amount": 120.5, "unit": "kg"}},
      "furniture": [{
        "id": 9, "name": "Mueble 1", "type": "F", "color": "#73879C",
        "counts": {"shelves": 4, "shelfobjects": 30},
        "risk": {"color": "yellow", "tonnage": {"amount": 30.0, "unit": "kg"}},
        "grid": {"rows": 2, "cols": 3, "cells": [[[21], [22, 23], []], [[24], [], []]]},
        "shelves": {"21": {"id": 21, "name": "A", "type": "D", "position": [0, 0],
                           "quantity": 10, "measurement_unit": "L",
                           "infinity_quantity": false, "occupancy_percent": 42.0,
                           "discard": false, "counts": {"shelfobjects": 8},
                           "risk": {"color": "green", "hcodes": ["H225"]}}}
      }]
    }]
  }
  ```

  `risk` es `null` sin el flag; el toggle de overlay refetchea con `?risk=1` y cachea.
- **Tabla**: `LabviewShelfObjectTableViewSet(ShelfObjectTableViewSet)` con serializer que
  hereda de `ShelfObjectLaboratoryViewSerializer` pero cuyo `actions` es el dict
  `{accion: bool}` (patrón `risk_management/api/serializer.py:108`), y que **exige
  `view_shelfobject`**. El viejo queda intacto para `rooms_list` hasta F7.
- **Disponibilidad en JSON**: action `GET .../api_labview_shelf/<pk>/availability/`
  (name, type, quantity, unit, porcentaje, discard, límites) — sustituto del HTML que hoy
  devuelve `shelf_availability_information` (`shelfobject/serializers.py:1320-1441`), que
  sobrevive sin tocar hasta F7.
- **Refactor de riesgo** (`risk_management/hazard_map_utils.py`): el parser pasa a
  `laboratory.dataconfig.parse` con un prefetch único (mata el N+1 de `:228`); nueva entrada
  `compute_lab_risk(laboratory) -> {shelf_colors, shelf_hcodes, alerts, aggregates}` que
  envuelve `collect_room_shelf_hcodes` + `compute_shelf_danger` + `_collect_alerts` y que
  consumen **tanto `build_lab_hazard_map` como el árbol**; `compute_lab_tonnage` se
  generaliza a `compute_tonnage_aggregates` (totales por laboratorio, sala y mueble). La
  semántica de color no cambia.

### F4 — UI nueva `laboratory:labview` (vista paralela)

- URL en `lab_rooms_urls` (`urls.py:169`): `path("labview/", ...)`, name `labview`.
- `src/laboratory/views/labview.py`: TemplateView delgada (perm `view_laboratoryroom`) que
  resuelve el deep-link `?labroom=&furniture=&shelf=&shelfobject=` server-side (misma
  semántica que `labroom.py:107-124`: completa la cadena hacia arriba, 404 si es inválido) y
  pasa `initial_state` como JSON. Las sugerencias Tagify se extraen de
  `LaboratoryRoomsList.get_suggestions_tag` (`labroom.py:126-199`) a un helper compartido
  `src/laboratory/views/labview_helpers.py` usado por **ambas** vistas.
- Template `templates/laboratory/labview/labview.html` + `_sq_templates.html` (plantillas
  Squirrelly). **Reutiliza** por `{% include %}` los modales de
  `shelfobject/action_modal.html` y `base_modal_management.js` (ya JSON): las acciones de
  shelfobject NO se reescriben. Breadcrumb con `BreadcrumbNav`.
- JS nuevo en `src/laboratory/static/laboratory/js/labview/`:
  - `labview_state.js` — estado (sala/mueble/estante/objeto) y `history.pushState`
    manteniendo EXACTOS los query params (compatibilidad con QR y `hazard_map_visual`).
  - `labview_render.js` — un fetch al árbol; paneles de sala colapsables (aspecto semejante a
    `laboratoryroom_list.html`); cada mueble con su cuadrícula real vía `PositionsGrid` en
    modo lectura (`renderItem` = tarjeta de estante semejante a `shelf_card.html`: nombre,
    % de ocupación, unidad, discard; color de riesgo cuando el overlay está activo); toggle
    de overlay.
  - `labview_search.js` — Tagify + `api-search-labview-get` (sin cambios en el endpoint):
    con los pks jerárquicos **navega** (expande la sala, hace scroll al mueble,
    `highlight(shelf)`, filtra la tabla) en vez de ocultar DOM.
  - `labview_actions.js` — `ObjectCRUD` de la tabla contra
    `api-labview-shelfobjecttable` (object_actions por dict, patrón `equipment_edit.html`) +
    modal de disponibilidad del estante.
- **Permisos en la UI**: `labview_render.js` guarda el bloque `permissions` en el estado y
  cada botón/panel/handler se pinta solo si su capacidad está ahí.
- **Responsive**: grid/flex de Bootstrap 5 — escritorio: mapa y tabla lado a lado;
  tablet/móvil: apilados, con la tabla bajo el estante seleccionado y scroll-to; DataTable en
  modo responsive; breadcrumb colapsable; convive con el drawer <992px del tema.

### F5 — Modo edición (editor de cuadrícula nuevo)

En la misma página, botón "editar mueble" **visible solo si el payload lo autoriza**
(`change_furniture`); dentro del modo, cada handler se ofrece según su capacidad
(`add_shelf` para crear en celda, `change_shelf` para mover, `delete_shelf` para quitar).
`PositionsGrid` pasa a `editable: true` y sus handlers llaman a las APIs de F3: crear estante
abre un `GTBaseFormModal` con el form de Shelf y postea con `row`/`col`; mover llama `move/`;
borrar hace DELETE con confirmación; ±fila/columna usa las grid actions; cada respuesta
re-renderiza. JS: `labview_editor.js`. Los metadatos del mueble (nombre, tipo, color) se
editan por modal contra `FurnitureManagement`. El editor viejo `furniture_update` queda
funcional sin tocar hasta F7.

### F6 — PRUEBAS (fase única)

- `src/laboratory/tests/test_dataconfig.py`: formatos históricos, dump normalizado, servicio
  (place/move/remove, filas y columnas, conflictos), regresión de los dos bugs.
- `src/laboratory/tests/labview/`: árbol con y sin riesgo (shape y número de queries), CRUDs
  por nivel, grid ops con 409, availability, deep-link de la vista (patrones
  `BaseSetUpAjaxRequest` / `BaseLaboratorySetUpTest`).
- **Matriz de permisos** (test central, dos organizaciones): por cada capacidad, un usuario
  CON y otro SIN el permiso → (a) el bloque `permissions` del árbol y el dict `actions` de
  fila reflejan exactamente lo que la UI mostraría, y (b) el endpoint responde 403 aunque el
  cliente lo invoque igual. Incluye la equivalencia 1:1 del dict `actions` contra las reglas
  de `shelfobject_actions.html` (permiso × tipo REACTIVE/EQUIPMENT × `is_box` × estante de
  descarte) — **las 13 acciones del inventario, no solo el CRUD**.
- **Inventario de funciones**: un test por cada fila de la tabla del inventario, de modo que
  perder el QR de un nivel, el reporte del mueble, las etiquetas, la bitácora o el
  mantenimiento rompa la suite.
- `src/risk_management/tests/`: equivalencia del hazard_map antes/después del refactor.
- Biblioteca: `djgentelella/tests/PositionsGrid_Test.py` (+ breadcrumb) sobre la demo.
- Selenium: smoke nuevo `selenium_tests/labview_new/test_smoke_navigation.py` (recorrido
  sala → mueble → estante → tabla, overlay, deep-link, modo edición básico, y una pasada con
  viewport angosto).
- **Regresión**: suite unit completa + selenium existentes en verde, incluidas
  `selenium_tests/laboratory_view/` sobre `rooms_list` (intacta hasta aquí). Lint en ambos
  repos y `makemigrations --check`.

### F7 — Tras la validación de Luis (última fase de código)

1. `rooms_list` → redirect 302 a `labview` **conservando el query string** (QR y
   `hazard_map_visual` siguen funcionando); retarget de las suites selenium
   `laboratory_view/` a la vista nueva.
2. Borrado de la capa muerta (lista en §Hallazgos).
3. Migración del legado vivo: borrar `ShelfCreate`/`ShelfEdit`/`delete_shelf`
   (`views/shelfs.py`), `get_shelfs_list` (`api/views.py:508`), `furniture_form.html`,
   `dataconfig.html`, `shelf_form.html`, `shelf_details.html`, `furniture_table.js`;
   `FurnitureUpdateView` se elimina o se simplifica (el editor ES labview); consolidar
   `ShelfObjectTableViewSet` con el dict de actions único y borrar
   `shelfobject_actions.html` y el HTML de `shelf_availability_information`.
4. Compromiso de la etapa 2: quitar `djangoajax` de `requirements.txt` y de
   `INSTALLED_APPS`, borrar `src/presentation/static/django_ajax/`, quitar los `<script>` de
   `base.html:36-37` y todo `data-ajax*` / `processResponse*`. Re-correr F6 completa.

## Orden y dependencias

```
F0 → F1 → F3 → (F4, F5) → F6 → F7 (tras OK de Luis)
     F2 ──────→ (F4, F5)
```

Sin migraciones de esquema; una migración de datos (F1) y `make messages` + `make trans` al
cierre de F5.

## Funciones que NO se pueden perder (inventario por nivel)

Traducción 1:1 de lo que hoy ofrecen `laboratoryroom_list.html`, `shelf_card.html` y
`serializers/shelfobject_actions.html`. **Cambia de dónde sale el dato, no lo que el usuario
puede hacer.** Está dibujado en [`14_labview_prototipo.svg`](14_labview_prototipo.svg) §5.

| Nivel | Función | Hoy | En el labview nuevo |
|---|---|---|---|
| Sala | **QR propio** con enlace directo | `{% get_qr_svg_img LaboratoryRoom … url=labindex %}` (`laboratoryroom_list.html:59`) | campo `qr`/`deep_link` por nodo en el árbol |
| Sala | Colapsar/expandir, crear, editar, borrar | árbol server-side + CBVs | panel colapsable + `LabRoomManagement` |
| Mueble | **QR propio** | `laboratoryroom_list.html:67` | campo por nodo en el árbol |
| Mueble | **Reporte PDF** | `report:reports_furniture_detail` con `perms.laboratory.do_report` (`:69-73`) | mismo enlace, capacidad `do_report` en el payload |
| Mueble | Cuadrícula, nombre, tipo, color; crear/editar/borrar | `display_furniture` + `FurnitureUpdateView` | `grid` en el árbol + `FurnitureManagement` |
| Estante | **QR propio** | `{% get_qr_svg_img item … %}` (`shelf_card.html:56`) | campo por nodo en el árbol |
| Estante | **Enlace directo** (abrir en otra pestaña) | `<a … ?labroom=&furniture=&shelf=>` con icono de etiquetas (`shelf_card.html:58`) | mismo query string, desde el estado de la UI |
| Estante | Color, tipo, descarte, unidad, capacidad, % ocupación, límites | `shelf_card.html` + `shelf_availability_information` (HTML) | campos del árbol + action `availability` en JSON |
| Objeto | **Detalle con su QR y descarga** | `shelfObjectDetail()` → `api-shelfobject-details` (devuelve QR b64) | igual; modal con `BaseDetailModal` |
| Objeto | **Etiquetas y recipientes (SGA)** | `api-shelfobject-recipient-list` + `generate_shelfobject_label`, `perms.sga.view_recipientsize`, solo REACTIVO | acción `labels` del dict |
| Objeto | Reservar | `reservations_management.add_reservedproducts` | acción `reserve` |
| Objeto | Aumentar / disminuir | `change_shelfobject`, no equipos | `increase` / `decrease` |
| Objeto | Transferir a otro laboratorio | `add_tranferobject` | `transfer_out` |
| Objeto | Mover de estante y gestionar contenedor | `movesomodal` / `movesocontainermodal` / `managecontainermodal` | `move` / `container` |
| Objeto | Editar según tipo (reactivo, material, equipo, caja) | 4 modales distintos | `edit` (el serializer ya sabe el tipo) |
| Objeto | **Bitácora y observaciones** | `laboratory:get_shelfobject_log`, exige `view_shelfobject` + `view_shelfobjectobservation` | acción `log` (enlace, `link:true`) |
| Objeto | **Mantenimiento, calibración, garantía, capacitación** | `laboratory:equipment_shelfobject_detail`, solo EQUIPO con view+change | acción `maintenance` (enlace) |
| Objeto | **Descargar su reporte** | `laboratory:reports_shelf_objects` con `do_report` | acción `report` (enlace) |
| Objeto | Borrar / desechar | `delete_shelfobject`, o `can_manage_disposal` si el estante es de descarte | `destroy` |

Consecuencias para las APIs de F3:

- El **árbol** incluye, por sala/mueble/estante, su `deep_link` (el mismo query string de
  siempre) y lo necesario para pintar su QR; y expone `do_report` entre las capacidades para
  que el mueble muestre su enlace de reporte.
- El **dict `actions`** de cada fila cubre las 13 acciones de la tabla anterior, no solo el
  CRUD: `labels`, `log`, `maintenance` y `report` incluidas. Las que son navegación a otra
  página se declaran con `link: true` en `object_actions` (soportado por la biblioteca desde
  la etapa 10).
- La regla de descarte (`shelf.discard` → borrar exige `can_manage_disposal` en vez de
  `delete_shelfobject`) se traduce tal cual: depende del estante, no solo del objeto.

## Contratos que NO pueden romperse

- Deep-link `?labroom=&furniture=&shelf=&shelfobject=` (QR impresos y
  `hazard_map_visual.html:45-49`).
- `api-search-labview-get` (`SearchLabView`) y su shape de respuesta.
- Las acciones de shelfobject existentes (`shelfobject/action_modal.html` +
  `base_modal_management.js` + los endpoints de `ShelfObjectViewSet`).

## Pendientes futuros (fuera de esta etapa)

- **Incompatibilidad intra-estante**: `compute_shelf_danger` salta `other_pk == shelf_pk` por
  diseño; dos sustancias incompatibles en el MISMO estante no generan alerta.
- **`IPERHazard.location`** (`risk_management/models.py:566`) es `CharField` de texto libre →
  convertirlo en referencia real a sala/mueble/estante y poblarlo desde el labview
  (proyecto aparte, decisión de Luis).
- **`dataconfig` → `JSONField`**: trivial una vez que solo escriba el módulo canónico.
- **Mover un estante entre muebles**: hoy tampoco existe.
- `utils_risk.get_inventory` usa `ObjectMaximumLimit` (límites declarados) en vez de las
  cantidades reales por ubicación.
