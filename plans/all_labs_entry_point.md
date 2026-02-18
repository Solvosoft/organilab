# Plan: Listado de Laboratorios como Punto de Entrada + Resolución Automática de Organización

**Fecha de ejecución:** 2026-02-17
**Estado:** Completado

---

## Contexto

Actualmente el flujo es: **Login → Seleccionar Organización → Ver Laboratorios de esa Org**. El usuario quiere que sea: **Login → Ver TODOS mis Laboratorios → Cada lab resuelve su org automáticamente**.

**Reglas de resolución de org para un lab:**
1. Si el usuario tiene `ProfilePermission` directo en una org que "tiene" el lab → usar esa org (la más específica/profunda en la jerarquía)
2. Si no → usar `lab.organization` (la org donde se creó el lab)

**Los labs se crean en orgs padres y se referencian en orgs hijas** vía `OrganizationStructureRelations` (mecanismo ya existente). La metadata del lab (`laboratory.organization`) siempre apunta a la org creadora.

**Sin cambios de modelo ni migraciones.**

---

## Cambios Realizados

### 1. Funciones utilitarias en `src/laboratory/utils.py`

**`resolve_org_for_lab(user, lab)`**
- Busca todas las orgs donde el usuario tiene `ProfilePermission` con `content_type=organizationstructure`
- Filtra cuáles de esas orgs "tienen" este lab (por `lab.organization` o `OrganizationStructureRelations`)
- Si no hay match directo, busca ancestros: para cada org del lab, verifica si algún ancestro está en las orgs del usuario
- Retorna la org más profunda (`order_by("-level")`) o `lab.organization_id` como fallback

**`get_all_user_laboratories(user)`**
- Obtiene todos los `lab_pk` donde el usuario tiene `ProfilePermission` con `content_type=laboratory`
- Para cada lab, llama `resolve_org_for_lab` para determinar el `org_pk`
- Retorna lista de dicts: `[{"lab": Laboratory, "org_pk": int}, ...]`

### 2. Vista `AllLaboratoriesListView` en `src/laboratory/views/laboratory.py`

- `TemplateView` con `@login_required` (no requiere `org_pk` en URL)
- Template: `laboratory/all_laboratories_list.html`
- Usa `get_all_user_laboratories(user)` para obtener los datos
- Soporta búsqueda por nombre (`search_fil`) y paginación manual (15 por página)
- No usa `@permission_required` porque no opera en contexto de una sola org; la seguridad está dada por los registros `ProfilePermission` existentes

### 3. Template `src/laboratory/templates/laboratory/all_laboratories_list.html`

Basado en el existente `laboratory_list.html`. Diferencias:
- Itera sobre `lab_list` (lista de dicts con `item.lab` y `item.org_pk`)
- Incluye un card por lab usando `all_lab_card.html`
- Botón para ir a "Gestión de Organizaciones" (la página actual de selección de org sigue accesible)
- Paginación con soporte para mantener el filtro de búsqueda

### 4. Template `src/laboratory/templates/laboratory/all_lab_card.html`

Basado en el existente `lab_card.html`. Diferencias:
- Recibe `org_pk` por lab (no global del template padre)
- Muestra el nombre de la organización (`lab.organization.name`) para distinguir labs de distintas orgs
- Sin botones de editar/eliminar (eso se hace desde la vista por org existente)
- Usa los template tags existentes `get_materiales_lab`, `get_equipo_lab`, `get_reactivos_lab`

### 5. URL registrada en `src/laboratory/urls.py`

```python
path("all_labs/", AllLaboratoriesListView.as_view(), name="all_labs"),
```

URL final: `/laboratory/all_labs/` (sin `org_pk`)

### 6. Redirect modificado en `src/presentation/views.py`

```python
# Antes:
return redirect(reverse("auth_and_perms:select_organization_by_user"))
# Después:
return redirect(reverse("laboratory:all_labs"))
```

### 7. `LOGIN_REDIRECT_URL` modificado en `src/organilab/settings.py`

```python
# Antes:
LOGIN_REDIRECT_URL = reverse_lazy("auth_and_perms:select_organization_by_user")
# Después:
LOGIN_REDIRECT_URL = reverse_lazy("laboratory:all_labs")
```

### 8. Tests en `src/laboratory/tests/test_all_labs_view.py`

13 tests cubriendo:
- **`resolve_org_for_lab`**: user con permiso en org del lab → resuelve a esa org; user con permiso en org padre → resuelve a org padre; sin permiso → fallback a `lab.organization`; org más profunda gana; lab compartido vía `OrganizationStructureRelations` → resuelve correctamente
- **`get_all_user_laboratories`**: retorna solo labs con `ProfilePermission`; no retorna labs sin permiso; cada resultado incluye `org_pk`
- **`AllLaboratoriesListView`**: usuario no autenticado → redirect a login; usuario autenticado → ve sus labs; búsqueda funciona
- **Redirect**: `/` redirige a `/laboratory/all_labs/` para usuarios autenticados; no autenticados ven index

---

## Resumen de Archivos

| Archivo | Tipo | Cambio |
|---------|------|--------|
| `src/laboratory/utils.py` | Modificar | Agregado `resolve_org_for_lab()` y `get_all_user_laboratories()` |
| `src/laboratory/views/laboratory.py` | Modificar | Agregada clase `AllLaboratoriesListView` |
| `src/laboratory/templates/laboratory/all_laboratories_list.html` | **NUEVO** | Template de listado de labs |
| `src/laboratory/templates/laboratory/all_lab_card.html` | **NUEVO** | Template de card por lab |
| `src/laboratory/urls.py` | Modificar | Registrada URL `all_labs/` |
| `src/presentation/views.py` | Modificar | Redirect a `laboratory:all_labs` |
| `src/organilab/settings.py` | Modificar | `LOGIN_REDIRECT_URL` |
| `src/laboratory/tests/test_all_labs_view.py` | **NUEVO** | 13 tests |

---

## Verificación

```bash
# Tests del nuevo módulo (13 tests, todos pasaron)
python manage.py test laboratory.tests.test_all_labs_view --no-input --exclude-tag=selenium --settings=organilab.test_settings

# Lint (todos los archivos nuevos/modificados pasan pycodestyle)
pycodestyle --max-line-length=200 --exclude='*/migrations/*' src/laboratory/utils.py src/laboratory/urls.py src/presentation/views.py src/laboratory/tests/test_all_labs_view.py
```

**Verificación manual:**
1. Login → verificar que redirige a `/laboratory/all_labs/`
2. Ver listado de labs con nombre de organización visible
3. Clic en un lab → verificar que el `org_pk` en la URL es la org más específica
4. Buscar por nombre → filtro funciona
5. La página de selección de organización sigue accesible desde el botón "Gestión de Organizaciones"
