# Plan: Componente de Tareas Pendientes en la Vista Principal

## Contexto

Ya existe una app `pending_tasks` con modelo `PendingTask`, API ViewSet, serializers, utils y URLs registradas. Lo que falta es:
1. El componente frontend en la página principal (`/laboratory/all_labs/`)
2. Archivo `api/__init__.py` (faltante)
3. Tests
4. Pequeños ajustes al API para soportar el flujo del frontend

### Estado actual de `pending_tasks`

**Modelo `PendingTask`** (hereda `AbstractOrganizationRef`):
- `description`, `status` (0=Pending, 1=In process, 2=Finished), `profile` (FK Profile, asignado a), `rols` (M2M Rol), `link` (URL)
- Heredados: `organization`, `created_by`, `creation_date`, `last_update`

**API existente** (`/pending_tasks/api/api_pending_tasks/`):
- ViewSet sin create (solo list, retrieve, update, destroy)
- Acciones custom: `task_assign`, `task_unassign`, `updated_task_status`
- Filtrado: muestra tareas asignadas al usuario O sin asignar con roles coincidentes
- Permisos basados en `pending_tasks.view/change/delete_pending_task`

**`create_pending_task()`** en `utils.py`: función para crear tareas desde código

---

## Cambios

### 1. Crear `src/pending_tasks/api/__init__.py` (faltante)

Archivo vacío para que el directorio `api/` sea un paquete Python válido.

### 2. Modificar `src/pending_tasks/api/views.py` — Agregar acción `create`

El ViewSet actual no tiene create. Necesitamos que el usuario pueda crear tareas desde el frontend. Agregar un `@action` o cambiar el mixin base para incluir `CreateModelMixin`.

**Opción elegida:** Agregar `CreateModelMixin` a `ModelViewSet` en `model_viewset_without_create.py` y crear una nueva clase que lo incluya, O más simple: agregar un `@action` de create al ViewSet existente.

**Decisión: agregar `@action create_task`** al ViewSet para no romper la base class compartida:

```python
@action(detail=False, methods=['post'])
def create_task(self, request, *args, **kwargs):
    # Usa PendingTaskValidateSerializer para validar
    # Crea la tarea con created_by=request.user
    # Si no se da profile, asigna al usuario actual
```

Agregar también `'create_task'` a `perms` dict con permiso `pending_tasks.add_pending_task`.

### 3. Modificar template `src/laboratory/templates/laboratory/all_laboratories_list.html`

Agregar **arriba** de la sección de laboratorios un panel colapsable con:

**Header:** "Mis Tareas Pendientes" + badge con conteo + botón "Nueva Tarea"

**Body:** Lista `list-group` cargada por AJAX. Cada item muestra:
- Botón checkbox para cambiar estado (Pendiente → En proceso → Finalizada)
- Descripción de la tarea (tachada si finalizada)
- Badge de estado (Pendiente/En proceso/Finalizada)
- Enlace al URL de la tarea (icono link externo)
- "de [creador]" si fue asignada por otro
- Botón eliminar

**Modal** para crear tarea con campos: descripción*, URL de tarea

### 4. Crear `src/pending_tasks/static/pending_tasks/js/user_tasks.js`

JavaScript con jQuery AJAX para:
- `loadTasks()` — GET `/pending_tasks/api/api_pending_tasks/?status=0&status=1` (pendientes y en proceso)
- `renderTaskItem(task)` — genera HTML para cada tarea
- Crear tarea: POST a `create_task` action
- Cambiar estado: PATCH a `updated_task_status` action
- Asignarse tarea: POST a `task_assign` action
- Eliminar: DELETE
- CSRF via `getCookie('csrftoken')`

### 5. Tests en `src/pending_tasks/tests.py`

Tests usando el `TestCase` de Django + `APIClient` de DRF:
- Listar tareas propias (asignadas y sin asignar con rol coincidente)
- Crear tarea via `create_task` action
- Cambiar estado via `updated_task_status`
- Asignarse tarea via `task_assign`
- Desasignarse via `task_unassign`
- Eliminar tarea

---

## Resumen de Archivos

| Archivo | Tipo | Cambio |
|---------|------|--------|
| `src/pending_tasks/api/__init__.py` | **NUEVO** | Archivo vacío (paquete Python) |
| `src/pending_tasks/api/views.py` | Modificar | Agregar `@action create_task` + perms |
| `src/laboratory/templates/laboratory/all_laboratories_list.html` | Modificar | Panel de tareas + modal de creación |
| `src/pending_tasks/static/pending_tasks/js/user_tasks.js` | **NUEVO** | Lógica AJAX frontend |
| `src/pending_tasks/tests.py` | Modificar | Agregar tests del API |

---

## Verificación

```bash
# Tests
cd src && python manage.py test pending_tasks --no-input --exclude-tag=selenium --settings=organilab.test_settings

# Lint
pycodestyle --max-line-length=200 --exclude='*/migrations/*' src/pending_tasks/api/views.py src/pending_tasks/tests.py
```

**Verificación manual:**
1. Login → ver panel de tareas en `/laboratory/all_labs/`
2. Clic "Nueva Tarea" → modal, crear tarea → aparece en lista
3. Clic en enlace de tarea → navega al URL
4. Cambiar estado a "En proceso" y luego "Finalizada"
5. Eliminar tarea → desaparece
