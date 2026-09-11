# Plan: CRUDAL para eliminar OrganizationStructureRelations de Laboratory

## Contexto

Se necesita una funcionalidad completa (API + vista frontend) para eliminar registros de `OrganizationStructureRelations` donde el `content_type` corresponda al modelo `Laboratory`, filtrados por el ID de organización. Al eliminar la relación, también se deben desvincular los usuarios que tengan permisos sobre ese laboratorio en esa organización.

El modelo `OrganizationStructureRelations` (en `src/laboratory/models.py:1314`) usa GenericForeignKey para vincular organizaciones con laboratorios. Los usuarios se vinculan a laboratorios mediante `ProfilePermission` (en `src/auth_and_perms/models.py:96`).

## Archivos a crear/modificar

### 1. `src/auth_and_perms/api/serializers.py` - Agregar serializer

```python
class OrganizationStructureRelationsSerializer(serializers.ModelSerializer):
    laboratory_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OrganizationStructureRelations
        fields = ["id", "organization", "object_id", "laboratory_name"]
    
    def get_laboratory_name(self, obj):
        try:
            return Laboratory.objects.get(pk=obj.object_id).name
        except Laboratory.DoesNotExist:
            return str(obj.object_id)
```

### 2. `src/auth_and_perms/api/viewsets.py` - Agregar ViewSet

```python
class OrganizationLabRelationDeleteViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": OrganizationStructureRelationsSerializer,
        "destroy": OrganizationStructureRelationsSerializer,
    }
    
    perms = {
        "list": ["laboratory.view_organizationstructurerelations"],
        "destroy": ["laboratory.delete_organizationstructurerelations"],
    }
    
    queryset = OrganizationStructureRelations.objects.all()
    pagination_class = LimitOffsetPagination
    
    def get_queryset(self):
        org_pk = self.kwargs.get("org_pk")
        lab_ct = ContentType.objects.filter(app_label="laboratory", model="laboratory").first()
        if not org_pk or not lab_ct:
            return OrganizationStructureRelations.objects.none()
        return OrganizationStructureRelations.objects.filter(
            organization_id=org_pk, content_type=lab_ct
        )
    
    def perform_destroy(self, instance):
        org = instance.organization
        lab_id = instance.object_id
        
        # 1. Eliminar ProfilePermissions de usuarios en este lab/org
        ProfilePermission.objects.filter(
            content_type__app_label="laboratory",
            content_type__model="laboratory",
            object_id=lab_id,
            organization=org
        ).delete()
        
        # 2. Log y eliminar relación
        organilab_logentry(self.request.user, instance, DELETION, ...)
        instance.delete()
```

### 3. `src/auth_and_perms/urls.py` - Agregar router y URLs

```python
# Router API
org_lab_relation_router = DefaultRouter()
org_lab_relation_router.register("api_org_lab_relation", OrganizationLabRelationDeleteViewSet, basename="api-org-lab-relation")

# Agregar a urlpatterns:
path("organization/<int:org_pk>/lab_relations/", include(org_lab_relation_router.urls)),
path("organization/<int:org_pk>/lab_relations/list/", org_lab_relations_view, name="org_lab_relations_list"),
```

### 4. `src/auth_and_perms/views/` - Crear vista frontend

Crear archivo o agregar función en archivo existente:

```python
@login_required
@permission_required("laboratory.view_organizationstructurerelations", raise_exception=True)
def org_lab_relations_view(request, org_pk):
    user_is_allowed_on_organization(request.user, org_pk)
    org = get_object_or_404(OrganizationStructure, pk=org_pk)
    return render(request, "auth_and_perms/org_lab_relations_list.html", {
        "org_pk": org_pk,
        "organization": org,
    })
```

### 5. `src/auth_and_perms/templates/auth_and_perms/org_lab_relations_list.html` - Template

```html
{% extends 'base.html' %}
{% load i18n static %}

{% block pre_head %}
    {% define_true "use_datatables" %}
{% endblock %}

{% block content %}
<h2>{% trans "Laboratory Relations" %} - {{ organization.name }}</h2>
<table class="table table-hover w-100" id="lab_relations_table"></table>

{% url 'auth_and_perms:api-org-lab-relation-detail' org_pk 0 as destroy_url %}
{% include 'gentelella/blocks/modal_template_delete.html' with form_id="delete_relation_form" id="delete_relation_modal" title="Unlink Laboratory" url=destroy_url %}
{% endblock %}

{% block js %}
<script>
const object_urls = {
    list_url: "{% url 'auth_and_perms:api-org-lab-relation-list' org_pk %}",
    destroy_url: "{% url 'auth_and_perms:api-org-lab-relation-detail' org_pk 0 %}",
}
</script>
<script src="{% static 'auth_and_perms/js/org_lab_relations.js' %}"></script>
{% endblock %}
```

### 6. `src/auth_and_perms/static/auth_and_perms/js/org_lab_relations.js` - JavaScript

```javascript
const datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", visible: false},
        {data: "laboratory_name", name: "laboratory_name", title: gettext("Laboratory")},
        {data: "actions", name: "actions", title: gettext("Actions"), filterable: false, sortable: false},
    ],
}

const config = {
    datatable_element: "#lab_relations_table",
    modal_ids: {destroy: "#delete_relation_modal"},
    datatable_inits: datatable_inits,
    delete_display: data => data['laboratory_name'],
    urls: object_urls,
}

const crud = ObjectCRUD("labrelcrud", config);
crud.init();
```

## Funciones existentes a reutilizar

- `AuthAllPermBaseObjectManagement` de `djgentelella.objectmanagement`
- `ObjectCRUD` de `djgentelella/static/gentelella/js/obj_api_management.js`
- `modal_template_delete.html` de djgentelella
- `organilab_logentry()` de `src/laboratory/utils.py`
- `user_is_allowed_on_organization()` de `src/auth_and_perms/organization_utils.py`
- Patrón de `ProviderViewSet` en `src/laboratory/api/views.py:1515`
- Patrón de `provider_list.html` en `src/laboratory/templates/laboratory/`

## Pruebas Unitarias

Archivo: `src/auth_and_perms/tests/test_org_lab_relations.py`

5 pruebas implementadas:

1. **test_list_lab_relations_returns_only_laboratory_content_type** - Verifica que el listado solo retorna relaciones donde content_type es Laboratory
2. **test_list_lab_relations_filters_by_organization** - Verifica que el listado filtra por la organización especificada en la URL
3. **test_delete_lab_relation_success** - Verifica que un usuario con permisos puede eliminar una relación
4. **test_delete_lab_relation_removes_profile_permissions** - Verifica que al eliminar una relación también se eliminan los ProfilePermissions de usuarios en ese lab/org
5. **test_delete_lab_relation_without_permission_fails** - Verifica que un usuario sin permiso de eliminación no puede eliminar

Ejecutar pruebas:
```bash
cd src && python manage.py test auth_and_perms.tests.test_org_lab_relations
```

## Verificación Manual

1. Ejecutar servidor: `cd src && python manage.py runserver`
2. Acceder a `/perms/organization/1/lab_relations/list/`
3. Verificar que muestra DataTable con laboratorios vinculados
4. Hacer clic en eliminar, confirmar en modal
5. Verificar que se eliminó la relación Y los ProfilePermission de usuarios en ese lab/org
6. Verificar log en admin de Django