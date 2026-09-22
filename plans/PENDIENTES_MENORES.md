# Pendientes menores

> **Qué es esto.** Restos de trabajos ya entregados cuyos documentos se borraron
> (`plan-org-lab-relations-crudal.md`, `DJGENTELELLA_060_NOTES.md`; siguen en git).
> Verificado contra el código el 2026-09-16.

---

## 1. Desvincular laboratorios de una organización

Entregado en `954f0c247`: `OrganizationStructureRelationsViewSet` (`src/auth_and_perms/api/viewsets.py:1250`),
vista (`views/organizationstructure.py:638`), plantilla `org_lab_relations_list.html`, JS
`static/js/auth_and_perms/org_lab_relations.js`, tests `tests/test_org_lab_relations.py`.

| Prioridad | Pendiente |
|-----------|-----------|
| **Alta (seguridad)** | `get_queryset()` filtra solo por `org_pk` de la URL y nunca llama `get_organization()` (`user_is_allowed_on_organization`): con permiso global `view_`/`delete_organizationstructurerelations` se listan/borran vínculos de otra org. Llamarlo y agregar test con usuario de otra org |
| Media | `recordsTotal` usa `self.queryset.count()` (total de plataforma); acotarlo como `LogEntryViewSet`/`OrganizationTrashViewSet` |
| Media | Botón en `list_organizations.html:96` solo dentro de `perms.laboratory.add_laboratory` y solo orgs hijas; no revisa el permiso de ver relaciones y las raíces no pueden desvincular |
| Baja | `get_laboratory_name` hace una consulta por fila; `search_fields=["object_id"]` no busca nada útil |
| Baja | Traducciones `es` faltantes: "Unlink Laboratory", "Unlinked laboratory '%(lab)s' from organization '%(org)s'" |

**Decisión abierta:** desvincular no toca `Laboratory.organization`. ¿Bloquear desvincular un lab de
la organización que es su dueña?

## 2. Restos de la migración a djgentelella 0.6.x

La migración está hecha (requirements `>=0.6.0`, `async_notification`, sin markitup/blog, bitácora
sobre `djgentelella.history`). Los restos de la migración están en `roadmap/PENDIENTES.md`; la
salida de django_ajax, en `roadmap/14_ETAPA_LABVIEW.md` (F7).

- `DeletedWithTrash` solo en los pilotos `Protocol` y `Procedure`; extenderlo está diseñado en `roadmap/13D_FASE_D_PAPELERA.md`.
- (Opcional) menús en `MenuItem`: hoy solo lo siembran `auth_and_perms/0014` y `presentation/0005`;
  el sidebar sale de parciales.
- (Opcional) eliminar la copia `src/laboratory/catalog/` (109 referencias) a favor de
  `djgentelella.fields.catalog`.
- (Opcional) declarar `GT_HISTORY_ALLOWED_MODELS`: ya **no es obligatorio** (la lib permite todo si
  falta, `history/api.py:141`), pero sirve para acotar la bitácora.
