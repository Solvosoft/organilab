# Etapa 12 — Validación final

**Objetivo:** confirmar que no se fue funcionalidad. **Estado:** pendiente.

## Tareas

- [ ] `make test` completo (sin selenium) — comparar contra `BASELINE.md` (891/891 OK).
- [ ] Suite selenium completa UNA vez (`make test-selenium-dev`; presupuestar 1-2 h).
- [ ] `make lint`.
- [ ] `make messages && make trans` si se tocaron strings traducibles.
- [ ] `python manage.py migrate` en BD limpia (instalación desde cero) y en copia de la BD real.
- [ ] Smoke manual con `runserver`:
      - login / logout / reset de contraseña,
      - sidebar y navbar en <992px (drawer) y >=992px (rail/flyout),
      - una tabla DataTables por app (layout, buscador, paginación, i18n es),
      - pantalla de permisos (checkboxes visibles y funcionales),
      - un modal con TinyMCE (crear y editar: contenido no se pierde),
      - dashboards de charts (objectlimit + risk),
      - crear una notificación de correo, drenar la cola (`process_notifications`) y verla en Mailhog,
      - subir un archivo por chunked upload.
- [ ] Actualizar `plans/AGENT_BRIEFING.md` (frontend/notificaciones) y dejar nota de obsolescencia
      en `plans/DJGENTELELLA_060_NOTES.md` apuntando a `roadmap/00_ANALISIS_DJGENTELELLA_060.md`.
- [ ] Registrar en `roadmap/README.md` la lista final de cambios hechos a djgentelella (para su
      changelog/release).

## Notas / hallazgos

(al cerrar)
