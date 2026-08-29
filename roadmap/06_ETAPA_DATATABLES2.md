# Etapa 6 — DataTables 1.12 → 2.3.7

**Objetivo:** portar `dom`→`layout`, clases `dataTables_*`→`dt-*` y el hook de `base.html`.
**Riesgo: ALTO** — el hook `init.dt` de `base.html` sostiene `data-organilab-ready`, del que depende
TODA la suite selenium. **Estado: HECHA y VALIDADA (2026-08-29)** — selenium manage_organizations 28/28 OK y capacitacion 40/40 OK.

## Recetas

- `dom: '<...>'` → `layout: {topStart:…, top:…, topEnd:…, top2Start:…, bottomStart:…, bottomEnd:…}`.
- `document.table_default_dom` → `document.table_default_layout` (objeto).
- `dt.context[0].nTable` → `dt.table().node()`.
- Clases: `dataTables_wrapper→dt-container`, `_filter→dt-search`, `_paginate→dt-paging`,
  `_length→dt-length`, `_info→dt-info`, `_processing→dt-processing`, `_empty→dt-empty`.
  `paging_full_numbers`/`table.display`: reglas borradas — decidir sustituto local si hacía falta.
- Server-side NO cambia (formatDataTableParams / draw / recordsTotal iguales).

## Tareas

- [ ] **Primero y aislado**: `src/presentation/templates/base.html:65` — `$(settings.nTable)` →
      `dt.table().node()` en el hook `init.dt` del modo testing. Validar con UN test selenium
      cualquiera antes de seguir.
- [ ] laboratory (10): `laboratory.js:277,310,924` · `reports.js:200` · `shelfobject_management.js:13` ·
      `shelfobject_equipment_tables.js:12,30,44,60,79,95` (define `table_default_dom` local) ·
      `equipmenttype/list.html:43,56` · `instrumentalfamily/list.html:42,54` · `inform.html:89,94` ·
      `logentry_list.html:34` · `register_user_qr/logentry_list.html:29`.
- [ ] sga (7): `prudence_advice.js:137`, `review_flow_substance.js:43`, `displaylables.js:74`,
      `warning_words.js:162`, `list_substance.js:76`, `danger_indication.js:47`, `recipient_size.js:175`.
- [ ] report (2): `organization_report.js:188`, `templates/report/general_reports.html:62`.
- [ ] academic (2): `my_procedures_list.js:35`, `procedure_list.js:20`; + `complete_my_procedure.js:174`
      (`document.table_default_dom`) y l.226-230 (clases CSS).
- [ ] auth_and_perms: `select_organization.js:3,27` (`document.table_default_dom`).
- [ ] `src/presentation/static/css/organilab.css:203` (`.dataTables_wrapper`).
- [ ] Confirmar eliminación del vendorizado `jquery.dataTables.min.js` (etapa 1).
- [ ] Grep final: `dom\s*:`, `dataTables_`, `table_default_dom`, `nTable` → 0 resultados.

## Pruebas

- Selenium puntual sobre 2-3 pantallas con tabla (laboratory + sga) tras cada bloque.
- Revisión visual de una tabla por app (posición de buscador/paginador con el nuevo layout).

## Notas / hallazgos

(al cerrar la etapa)

## Cómo quedó (2026-08-29)

- base.html:65 — el hook usa `$(e.target)` (init.dt se dispara sobre la tabla; funciona igual en
  DT 1.x y 2.x). Semántica intacta.
- 17 `dom:` de los 2 patrones comunes convertidos por script a `layout` (14 con botones, 3 sin).
- Locales convertidos a mano: select_organization.js (const local, ya no clobberea el global del
  documento), complete_my_procedure.js (layout pasado al createDataTable + clases `dt-search`;
  el swap paging_full/simple_numbers de DT1 se eliminó por inexistente), shelfobject_equipment_tables.js
  + equipmenttype/list.html + instrumentalfamily/list.html (variable local `table_default_layout`),
  inform.html (layout inline), register_user_qr/logentry_list.html (layout en el config).
- organilab.css:203 `.dataTables_wrapper` → `.dt-container`.
- Barrido final: 0 restos de `dom:`, `table_default_dom`, `dataTables_*`. Nota: DT2 aún acepta
  `dom` como legado, pero se migró todo para no depender de ello.
