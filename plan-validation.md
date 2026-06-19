# Plan: Validación / Aprobación de Laboratorios y Organizaciones

**Fecha:** 2026-06-17  
**Estado:** Definido — listo para implementación

---

## Decisiones confirmadas

| # | Decisión |
|---|----------|
| 1 | Aplica a **todas** las organizaciones sin importar nivel |
| 2 | Acceso a la vista de aprobación: permisos existentes `add_organizationstructure` + `change_organizationstructure` / `add_laboratory` + `change_laboratory` — sin permisos nuevos |
| 3 | Al crear: email a usuarios con ese rol + nueva vista de aprobación |
| 4 | Rechazo = **eliminación** del objeto con modal de confirmación previo |
| 5 | Auditoría con `organilab_logentry` para creación, aprobación y rechazo |
| 6 | Vista de aprobación sigue patrón API ViewSet (DRF) + djgentelella DataTable |

---

## Opción elegida: campo `approval_status` en cada modelo

**Mínimo impacto. Sin modelos nuevos. Sin permisos nuevos.**

Dos estados únicos (`PENDING`, `APPROVED`). No hay `REJECTED` — rechazo elimina el objeto.

---

## Cambios necesarios

### 1. Modelos (`src/laboratory/models.py`)

Agregar a **`OrganizationStructure`** y **`Laboratory`**:

```python
PENDING = 0
APPROVED = 1
APPROVAL_STATUS = (
    (PENDING, _("Pending approval")),
    (APPROVED, _("Approved")),
)
approval_status = models.SmallIntegerField(
    _("Approval status"), choices=APPROVAL_STATUS, default=PENDING
)
approved_by = models.ForeignKey(
    User, null=True, blank=True, on_delete=models.SET_NULL,
    related_name="approved_%(class)ss"
)
approved_at = models.DateTimeField(null=True, blank=True)
```

**Migración:** data migration marca todos los registros existentes como `APPROVED`.  
Nuevos registros nacen como `PENDING`.

---

### 2. Filtrado central — UN solo lugar

En `OrganizationStructureManager.filter_user()` (`models.py:1110`):

```python
# Antes
return OrganizationStructure.objects.filter(pk__in=pks)

# Después
return OrganizationStructure.objects.filter(pk__in=pks, approval_status=OrganizationStructure.APPROVED)
```

Y en `filter_user_orgs()` (`models.py:1177`) idem.  
Esto cubre automáticamente todos los listados que usan el manager.

Para `Laboratory`: agregar filtro en el queryset base del listado de labs.

---

### 3. Creación — set PENDING + log

**Org** (`organizations.py:257`): `approval_status=OrganizationStructure.PENDING` en el `create()`.  
**Lab** (`laboratory.py:163`): `self.object.approval_status = Laboratory.PENDING` antes del `save()`.

Tras guardar → log de creación + disparar email (ver puntos 5 y 6).

---

### 4. Vista de aprobación — patrón API ViewSet + djgentelella DataTable

Una sola vista lista ambos pendientes (orgs + labs) vía DataTable. Las acciones (aprobar/rechazar) se exponen como endpoints DRF siguiendo el patrón `AuthAllPermBaseObjectManagement` ya usado en `laboratory/api/views.py`.

**Estructura:**

```
# Vista Django (template + DataTable)
GET  organization/manage/approvals/
     → template con dos DataTables: una para orgs pendientes, otra para labs pendientes
     → Permiso: add_organizationstructure

# API DRF (acciones AJAX desde DataTable)
GET  api/approvals/orgs/           → lista orgs PENDING (DataTableSerializer)
POST api/approvals/orgs/<pk>/approve/  → aprueba org
POST api/approvals/orgs/<pk>/reject/   → elimina org

GET  api/approvals/labs/           → lista labs PENDING (DataTableSerializer)
POST api/approvals/labs/<pk>/approve/  → aprueba lab
POST api/approvals/labs/<pk>/reject/   → elimina lab
```

**Serializer pattern** (igual que `LaboratoryProcessDataTableSerializer`):

```python
class OrgApprovalSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    actions = serializers.SerializerMethodField()

    def get_actions(self, obj):
        user = self.context["request"].user
        return {
            "approve": user.has_perm("laboratory.change_organizationstructure"),
            "reject":  user.has_perm("laboratory.delete_organizationstructure"),
        }

    class Meta:
        model = OrganizationStructure
        fields = ["pk", "name", "level", "creation_date", "created_by", "actions"]


class OrgApprovalDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=OrgApprovalSerializer())
    draw = serializers.IntegerField()
    recordsFiltered = serializers.IntegerField()
    recordsTotal = serializers.IntegerField()
```

**ViewSet pattern** (igual que `LaboratoryProcessViewset`):

```python
class OrgApprovalViewset(AuthAllPermBaseObjectManagement):
    serializer_class = {"list": OrgApprovalDataTableSerializer}
    perms = {
        "list":    ["laboratory.view_organizationstructure"],
        "approve": ["laboratory.change_organizationstructure"],
        "reject":  ["laboratory.delete_organizationstructure"],
    }
    queryset = OrganizationStructure.objects.filter(approval_status=OrganizationStructure.PENDING)
    pagination_class = LimitOffsetPagination

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        org = self.get_object()
        org.approval_status = OrganizationStructure.APPROVED
        org.approved_by = request.user
        org.approved_at = now()
        org.save()
        organilab_logentry(request.user, org, CHANGE, "approve organization",
                           changed_data=["approval_status", "approved_by", "approved_at"])
        return Response({"ok": True})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        org = self.get_object()
        organilab_logentry(request.user, org, DELETION, "reject organization")
        org.delete()
        return Response({"ok": True})
```

Mismo patrón para `LabApprovalViewset`.

---

### 5. Log de auditoría con `organilab_logentry`

Usar el helper existente (`laboratory/utils.py:254`) con flags de `django.contrib.admin.models`:

| Evento | `action_flag` | `change_message` |
|--------|--------------|-----------------|
| Creación (PENDING) | `ADDITION` | `"organization/laboratory pending approval"` |
| Aprobación | `CHANGE` | `"approval_status approved"` |
| Rechazo (eliminación) | `DELETION` | `"rejected and deleted"` |

```python
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from laboratory.utils import organilab_logentry

# Al crear
organilab_logentry(request.user, obj, ADDITION, changed_data=["approval_status"])

# Al aprobar
organilab_logentry(request.user, obj, CHANGE,
                   changed_data=["approval_status", "approved_by", "approved_at"])

# Al rechazar (antes de delete)
organilab_logentry(request.user, obj, DELETION, "reject and delete")
```

---

### 6. Email al crear

Helper `notify_pending_approval(instance, request)` llamado desde `form_valid` de creación:

```python
from async_notifications.utils import send_email_from_template

def notify_pending_approval(instance, request):
    admins = User.objects.filter(
        groups__permissions__codename__in=["add_organizationstructure", "add_laboratory"]
    ).values_list("email", flat=True).distinct()

    approval_url = request.build_absolute_uri(reverse("laboratory:approvals"))
    for email in admins:
        send_email_from_template(
            "Pending approval",
            email,
            context={"obj": instance, "url": approval_url},
            enqueued=True,
            user=None,
            upfile=None,
        )
```

---

### 7. Modal de confirmación para rechazo

Usar patrón `BaseFormModal` existente (`base_modal_management.js`):

```html
<!-- Botón rechazo en DataTable actions -->
<button onclick="show_me_modal(this, event)"
        data-modalid="reject-modal"
        data-object-pk="{{ obj.pk }}"
        data-object-type="org|lab">
  Rechazar
</button>

<!-- Modal -->
<div id="reject-modal">
  <p>¿Confirmar eliminación de "<span id="reject-obj-name"></span>"? Esta acción no se puede deshacer.</p>
  <form method="post" action="">{% csrf_token %}
    <button type="submit">Eliminar</button>
    <button type="button" data-bs-dismiss="modal">Cancelar</button>
  </form>
</div>
```

---

## Archivos a crear/modificar

| Archivo | Tipo | Cambio |
|---------|------|--------|
| `src/laboratory/models.py` | Modificar | Campos `approval_status`, `approved_by`, `approved_at` en `OrganizationStructure` y `Laboratory`. Filtro en manager. |
| `src/laboratory/migrations/XXXX_approval_status.py` | Crear | Migración esquema + data migration existentes → APPROVED |
| `src/laboratory/views/organizations.py` | Modificar | Set `PENDING` + log en creación y `clone_organization()` |
| `src/laboratory/views/laboratory.py` | Modificar | Set `PENDING` + log en `CreateLaboratoryFormView.form_valid()` |
| `src/laboratory/api/serializers.py` | Modificar | Agregar `OrgApprovalSerializer`, `OrgApprovalDataTableSerializer`, `LabApprovalSerializer`, `LabApprovalDataTableSerializer` |
| `src/laboratory/api/views.py` | Modificar | Agregar `OrgApprovalViewset`, `LabApprovalViewset` |
| `src/laboratory/urls.py` | Modificar | URL vista template + registro de viewsets en router |
| `src/laboratory/utils.py` | Modificar | Agregar `notify_pending_approval()` |
| `src/laboratory/templates/laboratory/approvals.html` | Crear | Dos DataTables + modal de rechazo |
| `src/laboratory/templates/email/pending_approval.html` | Crear | Template email |

**Archivos NO tocados:** `gtselects.py` (cubierto por manager), `auth_and_perms/`, `sga`, `msds`, `academic`.

---

## Archivos a revisar (querysets directos fuera del manager)

| Archivo | Línea | Fix necesario |
|---------|-------|--------------|
| `auth_and_perms/gtselects.py` | ~670 | Agregar `approval_status=APPROVED` al filter de orgs |
| `auth_and_perms/api/viewsets.py` | ~877 | Agregar filtro en queryset de org |
| `laboratory/models.py` | 1361 | `organization__approval_status=APPROVED` |

---

## Estimación de esfuerzo

| Tarea | Esfuerzo |
|-------|----------|
| Modelos + migración | 1h |
| Filtro manager + 3 querysets directos | 1h |
| Creación org/lab: set PENDING + log | 0.5h |
| Serializers (org + lab) | 1h |
| ViewSets API (org + lab) + URLs | 1.5h |
| `notify_pending_approval` helper + template email | 1h |
| Template vista + DataTable + modal | 1.5h |
| Tests | 2h |
| **Total** | **~9.5h** |

---

## Pros y contras

### Pros
- Sin modelos nuevos, sin permisos nuevos.
- Un solo punto de filtrado (manager) cubre la mayoría de listados.
- Patrón ViewSet + DataTableSerializer ya establecido — consistente con el resto del código.
- `organilab_logentry` registra toda la trazabilidad en el `LogEntry` ya existente.
- Modal de rechazo con patrón `BaseFormModal` ya establecido.
- `send_email_from_template` con `enqueued=True` — no bloquea el request.

### Contras
- Data migration necesaria para registros existentes → `APPROVED`.
- 3 querysets directos fuera del manager requieren revisión manual.
- `clone_organization()` debe heredar `PENDING` explícitamente.
- Historial de rechazos queda solo en `LogEntry` (no hay objeto persistido); suficiente para auditoría.