# Etapa 9 — Ajustes menores de 0.6.0

**Objetivo:** cabos sueltos que no son bloqueadores pero cambian comportamiento.
**Estado:** hecha salvo dos borrados triviales (ver "Pendiente de código" abajo).

## Tareas

- [ ] **TinyMCE 8**: la config general la maneja la lib (`license_key:'gpl'`, plugins). Revisar si
      organilab tiene config custom de TinyMCE/Wysiwyg (grep `tinymce.init`, `plugins:`); revisar
      los modales con editor — los fixes `flush_editors`/`set_editor_content` deberían eliminar
      workarounds propios si los hay (buscar código que copie el contenido del editor al textarea
      a mano antes de submit).
- [ ] **`recordsTotal` corregido** en `BaseObjectManagement.list`: revisar tests que asertan
      conteos en los 32 viewsets `AuthAllPermBaseObjectManagement` (el total ahora respeta
      `get_queryset()`; es una corrección, los asserts viejos pueden estar mal).
- [ ] **moment locale**: añadir `{% load gtsettings %}{% get_moment_locale %}` en
      `src/presentation/templates/base.html` si algún widget de fecha muestra textos en inglés
      con el idioma es.
- [ ] `src/laboratory/templates/laboratory/register_user_qr/login_register_user.html:101` —
      verificar que `gentelella/statics/javascript.html` sigue existiendo en 0.6.0 (era ruta
      interna de la lib).
- [ ] `bootstrap-maxlength`: si algún template dependía del `label label-success`, ahora es
      `badge text-bg-success`.
- [ ] Grep de guardia: `paging_full_numbers`, `icheckbox`, `switchery`, `fi fi-` (flag-icons),
      `Chart.min.js`, `main.min.js` (fullcalendar) → 0 resultados en src/.
- [ ] Checkbox "borrar fichero" de uploads: los FileField/ImageField editables con
      FileChunkedUpload necesitan `blank=True` (lección del demo, migración 0028) — auditar.

## Pruebas

- `make test` del área tocada; smoke de un modal con editor TinyMCE (protocolos/procedimientos).

## Notas / hallazgos

(al cerrar la etapa)

## Avance (2026-08-29)

- TinyMCE: 0 configs custom (`tinymce.init`) en organilab → nada que portar.
- `recordsTotal`: el único test que asertaba el conteo viejo era `test_incident` (corregido en
  la etapa 4; ver 04_ETAPA_SUBIDA_060.md).
- moment locale: la lib lo incluye sola en `gentelella/statics/javascript.html`
  (`{% get_moment_locale %}`) → nada que hacer en base.html.
- `gentelella/statics/javascript.html` sigue existiendo (login_register_user.html:101 OK).
- bootstrap-maxlength: 0 usos del `label label-success` viejo.
- Auditoría `blank=True` HECHA: FileFields sin blank en apps propias:
  `ShelfObjectEquipmentCharacteristics.contract_of_maintenance`, `Protocol.file`,
  `RegisterUserQR.register_user_qr`, `msds.RegulationDocument.file` (+`ShelfObject.shelf_object_qr`
  con null=True). En todos, el archivo es semánticamente obligatorio: que el checkbox "borrar
  fichero" valide "no puede quedar vacío" es CORRECTO, no un bug. No se cambia el modelo; solo
  verificar en el smoke (etapa 12) que el mensaje al usuario sea razonable.
- PENDIENTE (menor): `laboratory/static/js/jquery-3.3.1.js` parece muerto (0 referencias) —
  confirmar y borrar.

## Avance 2 (2026-08-29, segunda pasada)

- **Grep de guardia CORRIDO y limpio**: 0 hits reales de `paging_full_numbers`, `icheckbox`,
  `switchery`, `fi fi-`, `Chart.min.js`, `main.min.js` en src/. Único hit: un comentario ya
  migrado en `src/academic/static/js/complete_my_procedure.js:230-231` (explica el rename
  DT1→DT2; el código debajo usa `.dt-search`, correcto). Si el grep se automatiza en CI,
  excluir comentarios o reescribir esas dos líneas.
- **`jquery-3.3.1.js` CONFIRMADO muerto** (271 KB, 0 referencias en templates/JS/settings).
  En el mismo directorio siguen vivos `jquery-ui.min.js` (referenciado en
  `sga/template_edit.html:48` y `laboratory/furniture_form.html:185`); revisar aparte
  `auth_and_perms/static/js/jquery-1.9.1.min.js`.
- **Hallazgo extra**: paginación DT1 muerta dentro de bloques `{% comment %}` en
  `src/reservations_management/templates/reservations_management/reservations_list.html`
  (~líneas 45-58 y 124-137). No renderiza; borrable al pasar.

## Pendiente de código (únicas acciones restantes de la etapa)

- [ ] Borrar `src/laboratory/static/js/jquery-3.3.1.js`.
- [ ] Borrar los dos bloques `{% comment %}` con paginación DT1 de
      `reservations_management/reservations_list.html`.
