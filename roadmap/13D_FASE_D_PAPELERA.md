# Fase D — extender la papelera más allá de los pilotos (diseño, 2026-08-30)

Continuación de [`13_HISTORY_TRASH.md`](13_HISTORY_TRASH.md), cuya fase C dejó
`Protocol` y `Procedure` como únicos modelos con `DeletedWithTrash`. Este
documento es **diseño**: nada de lo que sigue está implementado.

## 0. El riesgo que condiciona todo el diseño

`ObjectQuerySet.delete()` de la biblioteca
(`djgentelella/models_manager.py`) **es soft delete**, con firma
`delete(self, user=None, related_objects=None)`. En cuanto un modelo hereda
`DeletedWithTrash`, **todo `Model.objects.filter(...).delete()` y todo
`padre.hijo_set.all().delete()` que ya existía se convierte en un borrado a
papelera sin `user` ni `related_objects`**: filas `is_deleted=True` con una
`Trash` sin `gt_relations`, fuera de la pantalla org-scoped. No falla, no avisa.
Es exactamente el bug que se corrigió en `ProtocolViewSet` al cerrar el
proyecto 13.

Sitios que caerían en la trampa según el modelo que se migre:

| Modelo | `.delete()` de queryset existente |
|---|---|
| `Shelf` | `laboratory/tasks.py:147`, `laboratory/views/furniture.py:137` |
| `ShelfObject` | `laboratory/utils.py`, `management/commands/update_vitek.py:28` |
| `Object` | `laboratory/api/views.py` (cascada de `EquipmentType`) |
| `Label` (sga) | `sga/views/substance/views.py:254` |
| `RiskZone` / `Buildings` | los tres comandos `merge_duplicate_*.py` |
| `OrganizationStructure` | `laboratory/management/commands/merge_organizations.py:176` |

**Regla de la fase D:** antes de añadir el mixin a un modelo, auditar cada
`.delete()` de queryset sobre él y decidir explícitamente `hard_delete()`
(limpieza técnica, merges, comandos) o `delete(user=…, related_objects=[…])`
(acción de usuario).

A favor: **ningún candidato de D1–D2 tiene `unique_together` ni
`UniqueConstraint`**, así que no hay colisiones por filas borradas que siguen en
la tabla. Y `laboratory/views/djgeneric.py` `DeleteView` ya deja
`self.organization` y `self.laboratory` como instancias, así que
`related_objects=[self.organization, self.laboratory]` sale gratis, igual que en
`ProtocolDeleteView`.

## 1. Los tres booleanos artesanales: NO migrar ninguno

- **`OrganizationStructure.active`** es un **interruptor de negocio reversible**,
  no una papelera: `inactive_organization()` / `active_organization()`
  (`laboratory/views/organizations.py`) lo apagan y encienden con `CHANGE`, no
  `DELETION`, y el estado inactivo **se sigue navegando** vía
  `can_use_inactive_organization` (`authentication/middleware.py`; lo usan
  `views/trash.py`, `views/logentry.py`, `api/views.py`). Además es el único
  modelo del repo que ya declara `objects` propio (`TreeQuerySet.as_manager()`),
  que pisaría el `ObjectManager` del mixin, y es el `content_type` sobre el que
  la papelera hace su join: sería circular. El borrado duro real está en
  `OrganizationDeleteView.form_valid` — si molesta, la respuesta es canalizarlo
  a `inactive_organization()`, no la papelera.
- **`PendingTask.is_archived`** es **archivado**: su único escritor es un
  `.update(is_archived=True)` masivo restringido a `status=FINISHED`
  (`pending_tasks/api/views.py`), el scoping es por perfil/rol/creador y el
  modelo **ni siquiera tiene FK a `OrganizationStructure`**, así que no habría
  `related_objects` que pasar.
- **`UserOrganization.status`** sí tiene semántica de borrado (nunca vuelve a
  `True`: el "re-alta" de `auth_and_perms/views/organizationstructure.py` es un
  `get_or_create` con `status=True` **en el lookup**, o sea una fila nueva),
  **pero migrarlo sería un fallo de seguridad**: `organization.users.remove(user)`
  ejecuta `through._default_manager…delete()` (Django 5.2,
  `related_descriptors.py:1306`), que pasaría a ser el soft delete sin contexto;
  y como las consultas M2M hacen JOIN a nivel SQL sin pasar por el manager,
  `organization.users.filter(pk=…).exists()` en
  `auth_and_perms/organization_utils.py` — el `return True` temprano de
  `user_is_allowed_on_organization` — **seguiría dando acceso a un usuario
  expulsado**. Va a la ola D0 como saneamiento, no como migración.

## 2. Olas

### D0 — saneamiento previo (sin migraciones)

1. `UserOrganization`: el `status = False` de
   `auth_and_perms/views/organizationstructure.py` es **código muerto** — 34
   líneas después, el mismo bucle hace `users.remove(user)`, que borra
   físicamente la fila; la ruta API (`auth_and_perms/api/viewsets.py`) ni
   siquiera toca `status`. Decidir: (a) borrar el `status = False` y aceptar
   `remove()` como la desvinculación real, o (b) hacer de `status` el mecanismo
   único, quitando el `remove()` y reescribiendo `organization_utils.py` para
   consultar `UserOrganization` en vez del M2M. **Recomendado (a)**: es lo que
   el código ya hace de hecho. Test: expulsar a un usuario y comprobar que
   `user_is_allowed_on_organization` da `False` por ambas rutas.
2. Quitar `delete_selected` del `ModelAdmin` de los modelos que se vayan a
   migrar (y de los pilotos ya registrados en `laboratory/admin.py` y
   `academic/admin.py`): esa acción usa el colector de Django y salta la
   papelera.
3. Test-guardia genérico en `tests/test_trash.py`:
   `Trash.objects.filter(gt_relations__isnull=True)` debe quedar vacío tras
   ejercitar los flujos. Es el detector barato de §0.

### D1 — siete modelos, réplica exacta del patrón piloto

Orden sugerido: `IPERAssessment`, `MyProcedure`, `RegisterUserQR`,
`CustomForm`, `Inform`, `IncidentReport`, `RiskZone`.

| Modelo | Punto de borrado | org / lab |
|---|---|---|
| `IPERAssessment` | `risk_management/iper_views.py` **y** `risk_management/api/viewset.py` | `instance.organization` / `instance.laboratory` |
| `MyProcedure` | `academic/views.py` | resueltos en la misma vista |
| `RegisterUserQR` | `laboratory/views/laboratory.py` | `self.organization` / `self.laboratory` |
| `CustomForm` | `derb/views/form_list.py` | `self.organization` |
| `Inform` | `laboratory/views/informs.py` | `informs.organization` / `lab` |
| `IncidentReport` | `risk_management/incidents.py` | `self.object.organization` / `laboratories.all()` |
| `RiskZone` | `risk_management/views.py` | `self.object.organization` / `laboratories.all()` |

Por cada uno: (1) añadir `DeletedWithTrash` como base; (2) migración `AddField
is_deleted` con `db_index=True, default=False`, calcada de
`laboratory/migrations/0222_protocol_is_deleted.py`; (3) cambiar el call site a
`obj.delete(user=request.user, related_objects=[organization, laboratory])`,
manteniendo el `organilab_logentry` **antes** del delete. Para los M2M de
laboratorios pasar `[organization, *obj.laboratories.all()]` — son instancias,
cumple el contrato de `relation_targets`.

Extras de D1: `RiskZone` obliga a pasar a `hard_delete()` los tres comandos
`merge_duplicate_*`; `IncidentReport` tiene `fields = "__all__"` en
`risk_management/api/serializer.py` (ver §3); `CustomForm` es `CASCADE` desde
`Inform.custom_form`, así que mandarlo a papelera **deja de arrastrar** los
informes — es una mejora, pero hay que documentarla.

### D2 — inventario (alto valor, alto acoplamiento)

`Provider`, `ObjectFeatures`, `sga.Substance`, `Object`, `ShelfObject`.

Dos pasos extra antes del mixin: sustituir los `__all__` (§3) y reescribir los
`.delete()` de queryset de §0 con decisión explícita. Y decidir la política de
reportes: recomendación es que `report/views/stock.py`, `discard_objects.py` y
`object_changes.py` pasen a `objects_with_deleted` en los informes históricos y
se queden con `objects` en los de existencias actuales.

### D3 — estructura del laboratorio (`LaboratoryRoom`, `Furniture`, `Shelf`)

**Precondición: resolver la cascada.** La cadena
`LaboratoryRoom → Furniture → Shelf → ShelfObject` es todo `CASCADE`, así que
borrar una sala borraría duro los muebles y estantes aunque estuvieran en
papelera. Dos opciones: (i) cascada consciente en el `delete()` del contenedor,
con restauración que también cascade; (ii) **bloquear el borrado de contenedores
no vacíos**, como ya hace `laboratory/api/labview/viewsets.py` (409 si el
estante tiene objetos). **Recomendada la (ii)**: más barata y coherente con lo
que el labview ya implementó.

### Fuera de la papelera (decidido, no migrar)

Bitácora y logs (`ShelfObjectLog`, `EstablishmentLogs`, `ImpostorLog`);
catálogos globales sin organización (`Catalog`, `EquipmentType`, `WarningWord`,
`DangerIndication`, `PrudenceAdvice`, `ZoneType`) — sin org no hay pantalla
donde mostrarlos, un `delete()` a papelera sería justo el caso irrecuperable;
tablas puente (`ProfilePermission`, `OrganizationStructureRelations`,
`SubstanceLaboratory`, `MaterialCapacity`, `PendingTaskManager`); hijos que ya
se arrastran con el padre (`ProcedureStep`, `ProcedureRequiredObject`,
`ProcedureObservations`, `IPERHazard`, comentarios de `Inform`); objetos
regenerables (`sga.Label`, `FeedbackEntry`, `PeriodicTask`, `ChunkedUpload`).

### Pendientes de decisión de negocio (no entran en D1–D3)

`Laboratory` (su vista de borrado tiene dos semánticas según sea la org dueña o
no), `OrganizationStructure` (§1), `ReservedProducts`/`Reservations` (¿basura o
histórico?), `sga.BuilderInformation` y `DisplayLabel` (¿papelera del creador o
de la organización?), `LabOrOrgRequest` (solicitud propia),
`ShelfObjectMaintenance`/`Calibrate`/`Guarantee`/`Training` (¿historial de
equipo o dato editable?), `RecipientSize`.

## 3. `fields = "__all__"` que expondrían `is_deleted`

Un `ModelForm` con `__all__` genera un checkbox visible **y** un POST sin ese
campo lo resetea a `False` al guardar: editar un objeto lo restauraría desde la
papelera sin pasar por la pantalla. Hay que añadir `exclude = ("is_deleted",)` o
lista explícita **en el mismo cambio que añade el campo**:

`ShelfObject` (`views/shelfobject.py`, `shelfobject/serializers.py` ×2,
`api/serializers.py`) · `Object` (`api/serializers.py` ×3) · `Provider`
(`api/serializers.py`, `sga/forms.py`) · `ObjectFeatures` (`laboratory/forms.py`,
`api/serializers.py`) · `Furniture` (`views/furniture.py`) · `IncidentReport`
(`risk_management/api/serializer.py`) · `Substance` (`sga/forms.py`).

## 4. Tests por modelo migrado (patrón `src/laboratory/tests/test_trash.py`)

1. `test_delete_view_sends_X_to_trash_with_context`: `X.objects` no lo ve,
   `X.objects_deleted_only` sí, `trash.deleted_by == user` y
   `{r.content_object for r in trash.gt_relations.all()} == {org, lab}`.
2. **Anti-fuga**: extender `test_each_org_sees_only_its_trash` y
   `test_a_stranger_cannot_restore_another_orgs_entry` al nuevo tipo — `data` y
   `recordsTotal`.
3. `test_restore_brings_X_back_and_logs_for_the_org`.
4. **Nuevo — `test_no_orphan_trash`**: ejercitar los flujos colaterales del
   modelo (para `Shelf`, `tasks.py`; para `ShelfObject`, `utils.py`; para
   `Object`, `api/views.py`) y afirmar
   `Trash.objects.filter(gt_relations__isnull=True).count() == 0`. Es el seguro
   contra §0.
5. **Nuevo — `test_form_does_not_expose_is_deleted`**: `"is_deleted" not in
   form.fields` / `serializer.fields`.

## 5. Verificación por ola

```bash
make lint
cd src && python manage.py makemigrations --check --dry-run
make single-test TEST=laboratory.tests.test_trash
make test
```

Humo tras cada ola: `Trash.objects.filter(gt_relations__isnull=True)` vacío. La
pantalla `laboratory:trash_list` es genérica por `content_type` (el
`TrashViewSet` de la lib no conoce modelos), así que los tipos nuevos deberían
aparecer sin tocar `static/js/trash_list.js` — confirmarlo en la primera ola.
