# Etapa 8 — Overrides de templates de la biblioteca (23 archivos)

**Objetivo:** re-sincronizar las copias locales en `src/presentation/templates/gentelella/` con la
versión 0.6.0 (riesgo silencioso: la copia gana al template de la lib sin error visible).
**Estado:** pendiente.

## Método

Por cada override: `diff` contra el archivo homónimo del checkout 0.6.0 → decidir:
(a) borrar el override (si solo difería en cosas que la lib ya hace), (b) reducirlo a
`{% extends %}` + bloques de branding, (c) actualizarlo a mano conservando lo propio.

## Tareas por prioridad

- [ ] **`gentelella/blocks/permissions_management.html`** — crítico: `permissionmanagement.js` de
      la lib quitó iCheck (commit "fix: los checkboxes de permisos quedaron invisibles"); la copia
      vieja + JS nuevo = checkboxes invisibles. Validar la pantalla de permisos de inmediato.
- [ ] **`gentelella/app/sidebar.html`** y **`top_navigation.html`** — nuevo comportamiento del menú
      (drawer <992px, disclosure que ya NO navega, flyout fijo, dropdowns con click,
      `sidebar.css` nuevo). Revisar también las plantillas propias que se les cuelgan:
      `administration_menu.html`, `laboratory_menu.html`, `top_navigation_user_authenticated.html`.
- [ ] `gentelella/app/footer.html`.
- [ ] `gentelella/registration/` (20 archivos): activate, activation_complete, email_base,
      email_footer, email_header, footer, login, logout, new_user, password_change_done,
      password_change_form, password_reset_complete, password_reset_confirm, password_reset_done,
      password_reset_email, password_reset_form, registration_closed, registration_complete,
      registration_form. La mayoría debería quedar como extends + branding. `login.html` además
      tiene inputs a mano (coordinar con etapa 10b).

## Pruebas

- Selenium de capacitación (navegación por menú) y de manage_organizations (permisos).
- Manual: login/logout/reset de contraseña, menú en ancho <992px y >=992px.

## Notas / hallazgos

(al cerrar la etapa)

## Cómo quedó (2026-08-29)

**Validación:** selenium capacitacion 40/40 OK (navegación completa por el menú nuevo) y
manage_organizations 28/28 OK (pantalla de permisos con el permissions_management conservado).

- **11 overrides borrados** por ser byte-idénticos a la lib: activate, activation_complete,
  email_base, email_footer, email_header, footer (registration), new_user, password_reset_email,
  registration_closed, registration_complete, registration_form.
- **permissions_management.html**: se conserva — su única divergencia es que quita el selector de
  usuario del modal (decisión de organilab); el JS nuevo de la lib lo tolera
  (`if (selectuser.length > 0)`). Ya incluye el markup del fix de checkboxes.
- **sidebar.html**: se conserva el menú por partials de organilab; adaptado al esqueleto nuevo:
  clase `gt-sidebar`, `hidden-print` (BS3) → `d-print-none`, y se eliminó el bloque comentado del
  blog.
- **top_navigation.html**: adaptado — `navbar navbar-expand-lg` en el nav, `id="items-top-navbar"`
  en la ul derecha (custom.js 0.6.0 le cuelga los dropdowns por click, flyout y flex-row-reverse
  reactivo) y `#menu_toggle` con role/tabindex/aria como el de la lib.
- **footer.html** (app): se conserva (branding Solvosoft).
- Los password_* y login/logout extienden bases PROPIAS de organilab (`base.html`,
  `base_without_sidebar.html`) con branding — no son copias a la deriva; sin cambios.
- Barrido: 0 referencias a assets retirados (glyphicon, markitup, icheckbox, progressbar,
  flag-icon, Chart.min, summernote, moment-with-locales) en templates propios.
