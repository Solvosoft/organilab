# Etapa 14 — labview: mapa digital del laboratorio sobre API (salida total de django_ajax)

**Estado (verificado 2026-09-16): F0–F5 hechas; F6 escrita y commiteada (falta la regresión
completa); F7 sin empezar.** Resumen; la versión larga con los hallazgos de la exploración
(línea por línea del código previo) está en git.

> Arquitectura y porqués: [`14_ARQUITECTURA_LABVIEW.md`](14_ARQUITECTURA_LABVIEW.md).
> Prototipo visual: [`14_labview_prototipo.svg`](14_labview_prototipo.svg).

## Objetivo

Mapear el laboratorio (sala → mueble → estante → objeto) sobre APIs y componentes de la
biblioteca —la representación espacial alimenta la medición de riesgo— y eliminar **por
completo** `django_ajax`, con una interfaz reconocible pero de navegación más fluida.

## Decisiones de Luis (firmes, NO re-preguntar)

1. **Vista paralela**: `laboratory:labview` convive con `laboratory:rooms_list` hasta validar;
   redirect + borrado en F7.
2. **Overlay de riesgo** incluido (colores del hazard_map, ocupación y agregados).
3. **Editor con persistencia por operación** vía API que muta `dataconfig` en el servidor.
4. **`IPERHazard.location` → proyecto aparte.**
5. **Widgets genéricos en djgentelella** (sin conocimiento de organilab).
6. **Código primero, pruebas al final** (F6).
7. **Responsive** (móvil / tablet / escritorio).
8. **La UI se pinta según lo que el payload autoriza**; cada endpoint vuelve a exigir su permiso.
9. **La cuadrícula NO es rectangular**: la forma la define el usuario; filas irregulares
   preservadas, el árbol manda `grid: {"cells": [...]}` sin `rows`/`cols`; las operaciones de
   columna son globales.

## Lo construido (F0–F6)

| Fase | Entregable real |
|---|---|
| F1 | `src/laboratory/dataconfig.py` (`parse`/`parse_strict`, `dump` compacto, `normalize`, `resolve_shelves`, `get_position`, `iter_shelf_pks`, `dimensions`, `max_width`, `remove_shelf_from_matrix`, `DataconfigService` con 7 operaciones y `DataconfigConflict`); migración `0223_normalize_dataconfig.py`; `hazard_map_utils.py` usa el módulo. No quedan parsers propios |
| F2 | Biblioteca: `static/gentelella/js/base/positionsgrid.js`, `base/breadcrumbnav.js`, `css/positionsgrid.css`, `css/breadcrumbnav.css`, `templates/gentelella/blocks/breadcrumb.html`, demo `/positionsgrid_view`, docs `appwidgets/*.rst`. Publicado desde v0.6.0 |
| F3 | `src/laboratory/api/labview/` (`actions.py`, `permissions.py`, `serializers.py`, `tree_builder.py`, `viewsets.py`), montado en `labview/api/<org_pk>/<lab_pk>/` (`urls.py:692`): `LabRoomManagement`, `FurnitureManagement` (grid: `POST grid/row/`, `POST grid/row/remove`, ídem `col`; 409 en conflicto), `ShelfManagement` (create con `{row, col}`, `move`, `availability` JSON), árbol `tree/?risk=1`, tabla con `actions` como dict `{accion: bool}` que exige `view_shelfobject` |
| F4 | `views/labview.py` + `views/labview_helpers.py`, `templates/laboratory/labview/labview.html`, JS en `static/laboratory/js/labview/` (`labview.js`, `_state`, `_render`, `_search`, `_actions`), compartido `shelfobject_action_helpers.js`; URL `rooms/labview/`; entrada en `presentation/templates/gentelella/app/laboratory_menu.html` |
| F5 | `labview_editor.js` (crear/mover/borrar estante, ± fila/columna, metadatos del mueble) |
| F6 | `tests/test_dataconfig.py` (56); `tests/labview/`: `test_api_smoke`, `test_tree_queries`, `test_view`, `test_permission_matrix`, `test_tenant_isolation`, `test_actions_equivalence`, `test_function_inventory`, `test_migrations_state`; `risk_management/tests/test_hazard_map_equivalence.py`; biblioteca `PositionsGrid_Test.py` (17) y `BreadcrumbNav_Test.py` (9); Selenium `selenium_tests/labview_new/test_smoke_navigation.py` (8) |

**Desvíos que siguen vigentes:**
- En un estante de descarte, borrar exige `can_manage_disposal` (la plantilla vieja leía una
  variable fuera de contexto). Cambia comportamiento observable.
- `dump` escribe JSON compacto; `parse` deduplica (un estante queda en su primera posición).
- Los permisos efectivos vienen del `Rol` vía `ProfileMiddleware`: una prueba de denegación que
  solo vacíe `user_permissions` miente.
- El helper de permisos quedó en `api/labview/permissions.py`; `ShelfObjectViewSet` sigue con su
  `_check_permission_on_laboratory` propio (la extracción planeada no se hizo).

## Pendiente

### F6 — cierre
1. **Regresión completa**: suite unit, Selenium viejo (`selenium_tests/laboratory_view/`) y nuevo,
   lint en los dos repos, `makemigrations --check`. Hay merges posteriores (check-v3, arreglos de
   `13b96ed22`/`a39e34514`/`c26d8302f`), así que correrla de nuevo.
2. (Opcional) Selenium de edición: crear/mover/borrar estante y columnas (el smoke solo cubre
   añadir fila y rechazo de quitar fila).

### F7 — tras la validación de Luis (gate)
1. `rooms_list` → redirect 302 a `labview` **conservando el query string**; actualizar menú y
   `top_navigation.html:12`; retarget de `selenium_tests/laboratory_view/`; quitar el test
   "vista vieja alcanzable".
2. **Capa muerta**: `generic.py:ShelfListView`, rutas `furniture_list`, `list_shelfobject`,
   `shelfobject_create/edit/delete`, `ShelfObjectSearchUpdate` (`urls.py:192-231`); plantillas
   `shelf_list.html`, `shelfObject_list.html`, `furniture_list.html`,
   `components/shelf_list{,_discard}.html`; funciones muertas de `shelfobjectedit.js`.
3. **Legado vivo**: `ShelfCreate`/`ShelfEdit`/`delete_shelf` (`views/shelfs.py`, `urls.py:164-171`),
   `get_shelfs_list` (`urls.py:708`), `furniture_form.html`, `dataconfig.html`, `shelf_form.html`,
   `shelf_details.html`, `furniture_table.js`, modal `shelfobjectUpdate_modal.html` (diferido de la
   etapa 10); `FurnitureUpdateView` se elimina o simplifica; consolidar `ShelfObjectTableViewSet`
   con el dict de actions y borrar `serializers/shelfobject_actions.html` y el HTML de
   `shelf_availability_information` (mover sus tests de `test_shelf.py:129` a la action JSON).
4. **Quitar django_ajax**: `djangoajax` de `requirements.txt:8`, `"django_ajax"` de
   `settings.py:78`, `src/presentation/static/django_ajax/`, `<script>` de `base.html:36-37`, `@ajax`
   (`views/shelfs.py:40`, `views/shelfobject.py:104`, `views/furniture.py:205`), `AJAXMixin`, todo
   `data-ajax*`/`processResponse*` (~12–16 archivos), y el caso especial en
   `presentation/url_inventory.py:222,405`. Regenerar `make url-inventory`. Re-correr F6.

**Contrato del plugin** (para reconocer lo que se quita): servidor `{status, statusText, content}`,
301/302 → redirect a `content`; cliente `content.fragments` → `replaceWith`,
`content['inner-fragments']` → `.html()` (evalúa `<script>`), `append-/prepend-fragments`; anchors
`[data-ajax]` y forms `[data-ajax-submit]` con `data-success="fn"`; helpers globales `ajax()`,
`ajaxGet`, `ajaxPost`, `ajaxMethod`.

### Decisiones abiertas
- `FurnitureUpdateView`: ¿eliminar o versión simplificada?
- Crear/editar/borrar **salas y muebles** desde el labview: la API lo soporta, sin UI. ¿Antes de F7?
- ¿Terminar la extracción del helper de permisos para `ShelfObjectViewSet` o descartarla?

### Fuera de esta etapa
Incompatibilidad intra-estante (`compute_shelf_danger` salta el mismo estante) ·
`IPERHazard.location` como referencia real · `dataconfig` → `JSONField` · mover estante entre
muebles · `utils_risk.get_inventory` usa límites declarados en vez de cantidades reales.

## Contratos que NO pueden romperse
- Deep-link `?labroom=&furniture=&shelf=&shelfobject=` (QR impresos y `hazard_map_visual.html`).
- `api-search-labview-get` (`SearchLabView`) y su respuesta.
- Las acciones de shelfobject existentes (`action_modal.html` + `base_modal_management.js` +
  endpoints de `ShelfObjectViewSet`).

## Funciones que NO se pueden perder (inventario por nivel)

Fuente de `tests/labview/test_function_inventory.py`. Cambia de dónde sale el dato, no lo que el
usuario puede hacer.

| Nivel | Función | En el labview nuevo |
|---|---|---|
| Sala | QR propio con enlace directo | `qr`/`deep_link` por nodo en el árbol |
| Sala | Colapsar/expandir, crear, editar, borrar | panel colapsable + `LabRoomManagement` |
| Mueble | QR propio | campo por nodo en el árbol |
| Mueble | Reporte PDF (`report:reports_furniture_detail`, `do_report`) | mismo enlace, capacidad `do_report` en el payload |
| Mueble | Cuadrícula, nombre, tipo, color; crear/editar/borrar | `grid` en el árbol + `FurnitureManagement` |
| Estante | QR propio | campo por nodo en el árbol |
| Estante | Enlace directo | mismo query string, desde el estado de la UI |
| Estante | Color, tipo, descarte, unidad, capacidad, % ocupación, límites | campos del árbol + action `availability` |
| Objeto | Detalle con su QR y descarga | `BaseDetailModal` sobre `api-shelfobject-details` |
| Objeto | Etiquetas y recipientes (SGA, solo reactivo, `sga.view_recipientsize`) | acción `labels` |
| Objeto | Reservar | acción `reserve` |
| Objeto | Aumentar / disminuir (no equipos) | `increase` / `decrease` |
| Objeto | Transferir a otro laboratorio | `transfer_out` |
| Objeto | Mover de estante y gestionar contenedor | `move` / `container` |
| Objeto | Editar según tipo | `edit` |
| Objeto | Bitácora y observaciones | acción `log` (`link:true`) |
| Objeto | Mantenimiento, calibración, garantía, capacitación (solo equipo) | acción `maintenance` (`link:true`) |
| Objeto | Descargar su reporte | acción `report` (`link:true`) |
| Objeto | Borrar / desechar (`can_manage_disposal` en estante de descarte) | `destroy` |
