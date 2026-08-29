# Etapa 11 — Selenium: mejoras menores

**Objetivo:** ahorrar tiempo de corrida. **Hallazgo previo importante:** NO existe ejecución
multi-tamaño — `screenshot_size = "1280x720"` (`src/organilab_test/tests/base.py:334-339`) es solo
el nombre del directorio de capturas; nada itera tamaños. Los grandes ahorros ya existen:
`GENERATE_SCREENSHOTS=False`, `SELENIUM_SLEEP_FACTOR`, `OptimizedSeleniumBase` + `@modifies_db`.
**Estado:** pendiente.

## Tareas

- [ ] Homogeneizar `--parallel` de los targets del Makefile y corregir el texto del help.
      Estado real (auditado 2026-08-29): `test-selenium`, `test-selenium-fast` y
      `test-selenium-dev` usan `--parallel` (auto); `test-selenium-parallel`,
      `test-selenium-xvfb` y `docs_full` fijan `--parallel 12`;
      `test-selenium-single-fast` corre en serie. El help de `test-selenium` no dice que
      paraleliza y el de los de 12 workers no explica por qué 12.
- [x] `screenshot_delay = 3` (`base.py:36`) NO aplica con `GENERATE_SCREENSHOTS=False`:
      su único uso está en `create_screenshot()` (`src/organilab_test/tests/base.py:495-503`)
      y el early-return por el setting va antes del sleep. `create_gif_process`,
      `create_directory_path` y `create_gif` también hacen early-return. Nada que hacer.
- [x] `tblib>=3.0` ya está en `requirements.txt:39-41` con comentario explicativo (no hay
      requirements de desarrollo separado; ese es el único fichero de deps).
- [ ] Documentar (o mitigar) que `--keepdb` deja la BD selenium sin permisos y `loaddata`
      revienta en setUpClass (candidato: nota en el help de `test-selenium-dev`, que es el
      target que usa `--keepdb`).
- [ ] Actualizar selectores rotos por la migración que hayan quedado — ver hallazgos: la
      deuda real es `/ins` era-iCheck en los 3 tests rescatados, no clases DT1.
      **Premisa corregida:** `body.sidebar-open` NO existe ni en organilab ni en la lib;
      el menú alterna `body.nav-md`/`body.nav-sm` vía `#menu_toggle`
      (`custom.js` de djgentelella). Ningún test cubre el colapso del menú hoy.
- [ ] Los 3 tests renombrados en etapa 1: siguen `@skip` y NO migrados (ver hallazgos).
      Migrarlos a selectores 0.6.0 (`gt-check`, `dt-*`) y quitar el skip, o dejar el skip
      como exclusión documentada.
- [ ] Cosmético: renombrar `select_org_via_icheck`
      (`src/laboratory/tests/selenium_tests/manage_organizations/base.py:153-165`) — ya
      marca el radio con inputs nativos por script; solo el nombre quedó de la era iCheck.

## Pruebas

- `make test-selenium-dev` sobre las suites tocadas.

## Notas / hallazgos (2026-08-29)

- **Selectores DT1 en tests: cero hits** de `dataTables_filter`/`dataTables_paginate`/
  `paginate_button`/`dataTables_length`/`dataTables_wrapper`/`dataTables_info` en
  `selenium_tests/` y `organilab_test/`. Los restos fuera de tests son bloques comentados
  en `reservations_list.html` (se borran en etapa 9) y un comentario en
  `complete_my_procedure.js:230`.
- **Los 3 tests rescatados** (`laboratory_view/test_actions_buttons_shelfobject_table_
  {actions_column,wrapper_top}.py`, `test_shelfobject_detail_actions.py`): el rename de la
  etapa 1 solo añadió `@skip` + prefijo `test_`; conservan XPaths con `/ins` (helper que
  inyectaba iCheck, ya no existe) y XPaths posicionales del toolbar del wrapper DT1
  (`#shelfobjecttable_wrapper/div/div[2]/...`), que DT2 reordena. Líneas con `/ins`:
  actions_column 198-259 (10), wrapper_top 115-304 (5); detail_actions no usa `/ins` pero
  sí XPaths posicionales frágiles. La clase base `ButtonsActionsTableColumnBase` vive en
  `test_actions_buttons_shelfobject_table_actions_column.py:11` sin `@skip` propio —
  correcto porque no tiene métodos `test_*`, verificar al rehabilitar.
- **Sidebar**: helper `sidebar_menu_item()` en
  `src/organilab_test/tests/selenium_xpaths.py:229-244` usa `@class='nav side-menu'` con
  igualdad exacta e índices posicionales (frágil pero funcional con el markup actual de
  `presentation/templates/gentelella/app/sidebar.html:27`). Ningún test referencia
  `#menu_toggle`.
- `screenshot_size = "1280x720"` es solo el nombre del directorio de capturas (coincide con
  `set_window_size(1280, 720)` y el `-screen` de xvfb); no hay ejecución multi-tamaño.
