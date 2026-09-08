# Plan: Duplicar IPERAssessment con Modal

## Contexto

El usuario necesita una funcionalidad para crear una copia independiente de un IPERAssessment, clonando también sus IPERHazard e IPERObservation relacionados. A diferencia de `iper_clone_for_update` (que versiona y marca el original como OBSOLETE), este duplicado:
- Es completamente independiente (version=1, sin `previous`)
- No modifica el original
- **Solo disponible para IPERAssessment con status "completed"**
- Permite al usuario elegir laboratorio y fecha desde un modal
- Crea un IPERConfig si el laboratorio destino no tiene uno

## Archivos a modificar

| Archivo | Cambios |
|---------|---------|
| `src/risk_management/iper_views.py` | Nueva vista `iper_duplicate` (AJAX POST), contexto en `IPERAssessmentList` |
| `src/risk_management/forms.py` | Nuevo formulario `IPERDuplicateForm` |
| `src/risk_management/urls.py` | Nueva URL `iper/<int:pk>/duplicate/` |
| `src/risk_management/templates/risk_management/iper_detail.html` | Modal + botón "Duplicar" (solo status completed) |
| `src/risk_management/templates/risk_management/iper_list.html` | Modal de duplicación para el listado |
| `src/risk_management/static/js/iper_list.js` | Implementación de `ocrud.duplicate` para abrir modal |
| `src/risk_management/api/serializer.py` | Agregar `duplicate` en `get_actions` de `IPERAssessmentSerializer` |

## Implementación

### 1. Formulario (`forms.py`)

Agregar `IPERDuplicateForm`:

```python
class IPERDuplicateForm(GTForm, forms.Form):
    laboratory = forms.ModelChoiceField(
        queryset=Laboratory.objects.none(),
        label=_("Target laboratory"),
        widget=AutocompleteSelect("laboratory_by_org"),
    )
    assessment_date = forms.DateField(
        label=_("Assessment date"),
        widget=DateInput,
    )

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields["laboratory"].queryset = Laboratory.objects.filter(
                organization=organization
            )
```

### 2. Vista AJAX (`iper_views.py`)

Agregar después de `iper_clone_for_update` (~línea 558):

```python
@login_required
@permission_required("risk_management.add_iperassessment", raise_exception=True)
def iper_duplicate(request, org_pk, pk):
    """Duplica un IPERAssessment de forma independiente (AJAX)."""
    user_is_allowed_on_organization(request.user, org_pk)
    org = get_object_or_404(OrganizationStructure, pk=org_pk)
    original = get_object_or_404(IPERAssessment, pk=pk, organization__pk=org_pk)

    # Solo se pueden duplicar assessments completados
    if original.status != IPERAssessment.COMPLETED:
        return JsonResponse(
            {"error": str(_("Only completed IPER assessments can be duplicated."))},
            status=400,
        )

    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    form = IPERDuplicateForm(request.POST, organization=org)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    laboratory = form.cleaned_data["laboratory"]
    assessment_date = form.cleaned_data["assessment_date"]

    # 1. Crear nuevo IPERAssessment
    new = IPERAssessment(
        organization=org,
        laboratory=laboratory,
        assessment_date=assessment_date,
        responsible=request.user,
        created_by=request.user,
        status=IPERAssessment.DRAFT,
        version=1,
        previous=None,
        source=IPERAssessment.ON_DEMAND,
        is_anonymous=original.is_anonymous,
    )

    # 2. IPERConfig: buscar existente o crear
    cfg = get_iper_config(org, laboratory)
    if not cfg:
        cfg = IPERConfig.objects.create(
            organization=org.root if hasattr(org, 'root') else org,
            laboratory=laboratory,
            period_months=12,
            reminder_days_before=30,
            is_active=True,
            created_by=request.user,
        )
    new.due_date = add_months(assessment_date, cfg.period_months)
    new.save()

    # 3. Clonar IPERHazard con M2M
    for hazard in original.hazards.all():
        shelfobjects = list(hazard.related_shelfobjects.all())
        hazard.pk = None
        hazard._state.adding = True
        hazard.assessment = new
        hazard.save()
        if shelfobjects:
            hazard.related_shelfobjects.set(shelfobjects)

    # 4. Clonar IPERObservation
    for obs in original.observations.all():
        obs.pk = None
        obs._state.adding = True
        obs.assessment = new
        obs.author = request.user
        obs.save()

    # 5. Log
    organilab_logentry(
        request.user, new, ADDITION, "iperassessment",
        changed_data=["laboratory"],
        change_message=_("Duplicated from IPER #%(id)s") % {"id": pk},
        relobj=[laboratory],
    )

    # 6. Retornar URL de redirect
    return JsonResponse({
        "success": True,
        "redirect_url": reverse(
            "riskmanagement:iper_detail",
            kwargs={"org_pk": org_pk, "pk": new.pk}
        ),
        "message": str(_("IPER assessment duplicated successfully.")),
    })
```

### 3. URL (`urls.py`)

Agregar después de línea 144 (después de `iper_clone`):

```python
path(
    "iper/<int:pk>/duplicate/",
    iper_views.iper_duplicate,
    name="iper_duplicate",
),
```

### 4. Modal en `iper_detail.html`

Agregar botón después de línea 53 (solo visible para status completed):

```html
{% if perms.risk_management.add_iperassessment and object.status == 'completed' %}
    <button type="button" class="btn btn-sm btn-outline-info"
            data-bs-toggle="modal" data-bs-target="#duplicateModal"
            title="{% trans 'Create independent copy' %}">
        <i class="fa fa-clone"></i> {% trans 'Duplicate' %}
    </button>
{% endif %}
```

Agregar modal al final del template (antes de `{% endblock %}`):

```html
<!-- Modal Duplicate -->
<div class="modal fade" id="duplicateModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">{% trans 'Duplicate IPER Assessment' %}</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form id="duplicateForm" method="post"
                  action="{% url 'riskmanagement:iper_duplicate' org_pk object.pk %}">
                {% csrf_token %}
                <div class="modal-body">
                    <p class="text-muted">
                        {% trans 'Creates an independent copy (version 1) with all hazards and observations.' %}
                    </p>
                    <div class="mb-3">
                        <label class="form-label">{% trans 'Target laboratory' %}</label>
                        <select name="laboratory" class="form-select" required>
                            {% for lab in laboratories %}
                                <option value="{{ lab.pk }}"
                                    {% if lab.pk == object.laboratory.pk %}selected{% endif %}>
                                    {{ lab.name }}
                                </option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">{% trans 'Assessment date' %}</label>
                        <input type="date" name="assessment_date" class="form-control"
                               value="{{ today }}" required>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        {% trans 'Cancel' %}
                    </button>
                    <button type="submit" class="btn btn-info">
                        <i class="fa fa-clone"></i> {% trans 'Duplicate' %}
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
document.getElementById('duplicateForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const form = this;
    fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect_url;
        } else {
            alert(data.errors ? JSON.stringify(data.errors) : 'Error');
        }
    });
});
</script>
```

### 5. Contexto en vista `IPERAssessmentDetail`

En `iper_views.py`, modificar `IPERAssessmentDetail.get_context_data()` para agregar:

```python
context["laboratories"] = Laboratory.objects.filter(organization=self.org)
context["today"] = now().date().isoformat()
```

### 6. Serializer (`api/serializer.py`)

En `IPERAssessmentSerializer.get_actions()`, agregar acción `duplicate`:

```python
def get_actions(self, obj):
    user = self.context["request"].user
    return {
        "open": user.has_perm("risk_management.view_iperassessment"),
        "destroy": user.has_perm("risk_management.delete_iperassessment"),
        "duplicate": (
            user.has_perm("risk_management.add_iperassessment")
            and obj.status == IPERAssessment.COMPLETED
        ),
    }
```

## Imports necesarios

En `iper_views.py`:
```python
from risk_management.models import IPERConfig
```

## Verificación

1. Ejecutar tests: `make single-test TEST=risk_management.tests.test_iper`
2. Probar manualmente:
   - Acceder a detalle de IPERAssessment en estado "draft" -> NO debe aparecer botón "Duplicate"
   - Acceder a detalle de IPERAssessment en estado "completed" -> SI debe aparecer botón "Duplicate"
   - Clic en "Duplicate" abre modal
   - Seleccionar laboratorio y fecha
   - Submit -> redirect al nuevo assessment
   - Verificar que hazards y observations se clonaron
   - Verificar que IPERConfig se creó si no existía
   - Verificar que el original permanece sin cambios
3. Verificar API: en listado de assessments, el campo `actions.duplicate` debe ser `true` solo para status "completed"