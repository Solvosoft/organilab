# Etapa 5 — iCheck / switchery → inputs nativos (gt-check / gt-switch)

**Objetivo:** portar los ~38 usos de la API de iCheck/switchery que 0.6.0 elimina.
**Riesgo: ALTO** (pantallas de organizaciones/permisos + infra selenium). **Estado: HECHA y VALIDADA (2026-08-29)** — selenium manage_organizations 28/28 OK y capacitacion 40/40 OK.

## Recetas

- `.iCheck('check')` → `.prop('checked', true).trigger('change')` si algún handler dependía del evento;
  sin `.trigger` si solo era estado visual. `'uncheck'` → `false`. `'update')` → eliminar.
- `on('ifChecked', fn)` → `on('change', function(){ if (!this.checked) return; ... })`.
- Markup `<input class="iCheck">` / contenedores `icheckbox_flat-green` → `<input class="gt-check">`.
- Switchery: `input[data-switchery=true]` ya no existe; `YesNoInput` rinde `gt-switch` solo.
- Personalización: `--gt-check-color`, `--gt-check-size` (CSS custom properties).

## Tareas

- [ ] `src/laboratory/static/laboratory/js/laboratory.js` — 14 usos
      (l.459, 530, 673, 677, 804, 806, 812, 814, 818, 875, 877, 883, 885, 889).
- [ ] `src/laboratory/static/laboratory/js/base_modal_management.js:57,63-65` — switchery + radios.
- [ ] `src/laboratory/static/laboratory/js/furniture_table.js:141`.
- [ ] `src/auth_and_perms/static/js/auth_and_perms/organization_manager.js:41,917` — `ifChecked`.
- [ ] `src/auth_and_perms/templates/auth_and_perms/organization_permission_table.html:17-19` — markup.
- [ ] `src/auth_and_perms/templates/auth_and_perms/list_organizations.html:374-376` — markup.
- [ ] Selenium: `src/laboratory/tests/selenium_tests/manage_organizations/base.py` — reescribir
      `select_org_via_icheck()` (l.153-170) como click nativo directo (ya no hay `<ins class="iCheck-helper">`
      tapando el input); usos en l.192,202 y en `test_collapse_org_name_buttons_box.py:65`,
      `test_laboratory_tab.py:15`, `test_profile_tab.py:15`.
- [ ] Revisar comentario `src/organilab_test/tests/base.py:602` (inputs tapados por widget — ya no aplica).

## Pruebas

- ANTES: correr la suite selenium de `manage_organizations` en 0.5.9 (baseline de comportamiento).
- DESPUÉS: misma suite (`make test-selenium-single-fast TEST=laboratory.tests.selenium_tests.manage_organizations`)
  + pantalla de permisos y lista de organizaciones a mano en runserver.

## Notas / hallazgos

(al cerrar la etapa)

## Cómo quedó (2026-08-29)

- laboratory.js: 14 usos portados. Los bloques de `was_donated`/`without_limit` que manipulaban el
  wrapper `.parent().hasClass('checked')` de iCheck quedaron en 3 líneas con
  `prop('checked', X).trigger('change')`. OJO: el barrido encontró MÁS de lo inventariado —
  7 listeners `on('ifChanged')` (laboratory.js 397,614,618,623,628,651,775) y 3 delegados en
  furniture_table.js (245-257) que pasaron a `on('change')`.
- base_modal_management.js: el bloque switchery (selector `data-switchery=true`, ya inexistente)
  ahora resetea `input.gt-switch:checked` con prop+change.
- organization_manager.js: `ifChecked` → `change` + guard `if (!this.checked) return;`.
- Templates: `class="iCheck"` → `class="gt-check"` (organization_permission_table, list_organizations).
- Selenium: `select_org_via_icheck()` y los scripts de mergeaction usan
  `prop('checked', true).trigger('change')`; comentarios actualizados.
- Barrido final: 0 restos de iCheck/switchery/ifChanged en src. Sintaxis JS validada con node.
