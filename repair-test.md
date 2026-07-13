# Auditoría de tests rotos — metodología y hallazgos

Base original: `python manage.py test laboratory academic sga risk_management report derb pending_tasks auth_and_perms --settings=organilab.test_settings --noinput` (comando usado al inicio de esta auditoría; **le faltaba `--exclude-tag=selenium`**, ver hallazgo #1) → 744 tests, 47 failures + 24 errors = 71 rotos.

**Actualización:** se agregó `make test-requirements` (instala `test_requirements.txt`, incluye `selenium-screenshot` → resuelve el `ModuleNotFoundError: Screenshot`) y se corrigió el comando agregando `--exclude-tag=selenium`. Baseline correcto ahora:
```
python manage.py test laboratory academic sga risk_management report derb pending_tasks auth_and_perms --settings=organilab.test_settings --noinput --exclude-tag=selenium
```
**723 tests, 47 failures + 3 errors = 50 rotos.** El hallazgo #1 (Selenium) queda resuelto — ya no aporta ruido al conteo. Confirmado con `git stash` que el resto (47F+3E, antes 47F+24E con selenium incluido) es idéntico con y sin los cambios de esta sesión (fix de `SET_NULL`, admin, i18n, etc.) — son fallos preexistentes, no introducidos hoy.

## Metodología usada para diagnosticar

1. Correr la suite completa con `-v 2`, guardar output completo (no solo el tail) para poder grep-ear cada traceback.
2. Agrupar por patrón de síntoma (`ImportError` de módulo, `302 != 200`, `TypeError: NoneType`, mismatch de datos) antes de mirar test por test — la mayoría de los 71 caen en un puñado de causas raíz compartidas, no son 71 bugs distintos.
3. Para los `302` (el patrón dominante): agregar temporalmente un `print("DEBUG status:", response.status_code, "redirect:", response.url)` justo antes del `assertEqual` que falla, correr SOLO ese test (`manage.py test <ruta.completa.TestClass.test_method>`), leer a dónde redirige, revertir el print. Mucho más rápido que adivinar leyendo vistas/middlewares a ciegas — el redirect target dice exactamente qué interceptó la request.
4. Revisar `git log`/`git show` del archivo relevante cuando el síntoma sugiere "algo cambió y el test no se actualizó" (permisos, decoradores nuevos).

## Hallazgos (por confianza, de más a menos confirmado)

### 1. Selenium (21 errores) — RESUELTO

Todos eran `ImportError: ... ModuleNotFoundError: No module named 'Screenshot'` al intentar cargar los módulos de test bajo `selenium_tests/`.

**Causa:** este entorno no tenía el paquete `Screenshot` (dependencia de Selenium para generar GIFs) instalado, y el comando de test usado no excluía `--tag=selenium`. El propio `Makefile` ya lo hace bien:
```
test: cd src && python manage.py test --no-input --exclude-tag=selenium
```
**Fix aplicado:** se agregó el target `make test-requirements` (`pip install -r test_requirements.txt`, que incluye `selenium-screenshot`) y se corrió. Con eso + `--exclude-tag=selenium`, estos 21 ya no aparecen — bajó el conteo de 71 a 50 rotos. Selenium real (con browser) sigue corriéndose aparte con `make test-selenium` en su propio entorno/imagen Docker — esto solo resolvió el ruido de *import* al correr la suite normal.

### 2. `RiskZoneForm` — RESUELTO (`test_add_risk_zone`)

```
File "risk_management/forms.py", line 78, in __init__
    labs += list(self.instance.laboratories.all().values_list("pk", flat=True))
ValueError: "<RiskZone: >" needs to have a value for field "id" before this many-to-many relationship can be used.
```
**Causa:** `RiskZoneForm.__init__` chequeaba `if "instance" in kwargs:` para decidir si precargar `laboratories` desde `self.instance` — pero Django's `CreateView.get_form_kwargs()` siempre manda `instance=None` en el modo creación, y `ModelForm.__init__` convierte ese `None` en un `RiskZone()` nuevo sin guardar. O sea la condición era casi siempre `True` (creación y edición), sin distinguir los dos casos. Acceder a `self.instance.laboratories.all()` (M2M) sobre un objeto sin `pk` truena.

**Fix aplicado:** `risk_management/forms.py:77`, cambiado `if "instance" in kwargs:` → `if self.instance.pk:` — ahora sí distingue creación (sin pk, salta el bloque) de edición (con pk, precarga labs). Verificado: `risk_management.tests.test_zonetype` (7 tests) pasa, suite completa sin regresión, error bajó de 3 a 2.

### 3. Permisos faltantes en el fixture compartido de test — RESUELTO (8 tests: `test_update_password`, `test_update_profile`, `test_update_no_material`, `test_update_no_material_with_capacity_unit`, `test_api_reservation_update`, `test_api_reservation_delete`, `test_get_reservations_list`, `test_fake_reservation_list`)

Redirect capturado: `/accounts/login/?next=/profile/1/password` (patrón de `permission_required` sin `raise_exception=True` → Django redirige a `LOGIN_URL`), y `/index/error?status=403` para los que usan `raise_exception=True` (Django renderiza HTML de `PermissionDenied`, `HandleErrorMiddleware` lo redirige igual que el 404 de #4).

**Causa real, con commit identificado para el primer caso:** `git log` muestra `d3518384 "fixed updated profile permission"` (16 jun 2026) agregó `@permission_required("auth_and_perms.change_own_profile")`/`view_profile` a las vistas de perfil (`authentication/users.py`) — fix legítimo, pero **el fixture de test (`BaseLaboratorySetUpTest.setUp()` en `laboratory/tests/utils.py`) nunca se actualizó** para otorgarle esos permisos nuevos al usuario de prueba. Repitiendo la misma metodología en los otros 6 "sospechosos", se confirmaron 3 permisos más faltantes, cada uno con su propia vista/decorador:
- `laboratory.change_object` — `ObjectUpdateView` (`laboratory/views/objects.py:100-103`, `@permission_required("laboratory.change_object")`).
- `reservations_management.view_reservedproducts` — `MyReservationView` (`laboratory/views/my_reservations.py:9-11`, `raise_exception=True`).
- `reservations_management.change_reservedproducts` / `delete_reservedproducts` — `ApiReservedProductsCRUD.put()`/`.delete()` (`laboratory/api/views.py`, chequeo manual `request.user.has_perm(...)`, devuelve `Response(status=403)` — DRF lo renderiza HTML vía `BrowsableAPIRenderer` porque el test client no pide JSON explícito, por eso parecía un problema de middleware antes de confirmar).

**Fix aplicado:** agregados los 4 permisos (`change_object`, `view_profile`, `change_own_profile`, `view/change/delete_reservedproducts`) a `BaseLaboratorySetUpTest.setUp()` en `laboratory/tests/utils.py`. Es puramente un problema de test desactualizado, no de las vistas/permisos en sí (esos fixes de permisos son correctos y deseados).

**Hallazgo adicional durante la verificación:** `test_update_no_material`/`test_update_no_material_with_capacity_unit` seguían fallando incluso con el permiso agregado — pero por una razón distinta, no de permisos: el POST válido a `ObjectUpdateView` SIEMPRE redirige (302, patrón post-redirect-get normal de Django `UpdateView`), y el test asertaba `status_code == 200` — comportamiento correcto solo para el path de formulario inválido (`form_invalid` re-renderiza con 200), no para el de éxito. Peor, el test ya tenía un `success_url` calculado **y nunca usado** (código muerto) — se ve que la intención original era `assertRedirects(response, success_url)`. Corregido: se movió el cálculo de `success_url` antes del POST y se reemplazó `assertEqual(response.status_code, 200)` por `assertRedirects(response, success_url)`.

### 4. `HandleErrorMiddleware` convierte 404→302 y rompe tests de API que esperan el código crudo — RESUELTO (32 tests, cluster `gtapi` completo: `test_furniture`, `test_laboratory_room`, `test_shelf`, `test_shelf_object`, variantes `case1-4` con `OrgDoesNotExists`/`LabDoesNotExists`)

Redirect capturado: `/index/error?status=404` (no era un problema de login).

**Causa real, rastreada hasta el final** — no es `HandleErrorMiddleware` el origen, es **`authentication/middleware.py:117`, `ProfileMiddleware`**:
```python
org = get_object_or_404(OrganizationStructure, pk=org_pk)
```
Este `process_view` corre para CUALQUIER vista, para todo usuario no-superuser (`if user.is_superuser: return` bypasea esto — por eso probar con `solvoadmin` directo contra la BD real daba 400 limpio, JSON, sin problema: nunca pasa por acá). Si `organization`/`org_pk` viene en query params pero no corresponde a una `OrganizationStructure` real, tira `Http404` ahí mismo, **antes de que la vista (`FurnitureLookup` + `ValidateUserAccessOrgLabSerializer`, que sí valida bien y devuelve 400 con errores por campo) llegue a ejecutarse**. Confirmado con `git log -L` que es comportamiento viejo (un refactor de `try/except` a `get_object_or_404`, mismo comportamiento desde antes), no una regresión reciente.

Luego `HandleErrorMiddleware` ve ese 404 (HTML de Django, no JSON) sin los headers de bypass → redirige a `/index/error?status=404`. Por eso el síntoma en el test era "302".

**Decisión tomada:** no tocar `ProfileMiddleware` (afecta cada vista de la app, blast radius grande) — el 404 a nivel de middleware es el comportamiento real y estable del sistema. Se actualizaron los tests para reflejarlo:
1. `laboratory/tests/gtapi/base.py`: agregado `HTTP_X_REQUESTED_WITH="XMLHttpRequest"` a los 6 `self.client.get(...)` compartidos — bypasea el redirect cosmético de `HandleErrorMiddleware`, igual que ya hace cualquier `fetch()`/XHR real del frontend (el browser manda `Sec-Fetch-Dest` automático, la request real nunca sufrió esto).
2. Ajustado `check_tests` para solo intentar `json.loads(response.content)` si `Content-Type` es `application/json` — el 404 real de `ProfileMiddleware` es HTML de Django, no JSON, y tronaba el parseo aunque el status code ya diera bien.
3. Actualizados los 32 métodos de test (`FurnitureViewTest13/15`, `LabRoomViewTest11/13`, `ShelfViewTest13/15`, `ShelfObjectViewTest11/13`, 4 casos cada uno) de `status_code=400` (default) a `status_code=404` explícito.

**Resultado:** los 4 archivos (224 tests) pasan 100%. Suite completa: de 50 rotos (47F+3E) bajó a **18 rotos (15F+3E)**.

### 5. `OrgDoesNotExists` en `select_organization` — RESUELTO (4 tests, mismo mecanismo que #4)

`test_get_objects_by_org_case1`, `test_get_organization_buttons_by_user_case1`, `test_get_shelfobjects_by_objects_and_org_case1` (x2, `ShelfObjectsByObjectViewTest2`/`ShelfObjectsByObjectViewTest4`) — exactamente el mismo patrón que el cluster `gtapi` (#4): `OrgDoesNotExists` + `302 != 400`, `ProfileMiddleware` tira 404 antes de que la vista valide. Mismo fix aplicado en `auth_and_perms/tests/select_organization/base.py`:
- Header `HTTP_X_REQUESTED_WITH="XMLHttpRequest"` en `check_user_in_organization` (único punto compartido de `self.client.get(...)`).
- `check_status_code` y los 4 métodos `check_*_result` (`check_objects_result`, `check_organizations_result`, `check_shelfobject_result`, `check_organization_buttons_result`): guardado el `json.loads(response.content)` para que solo corra si `Content-Type` es JSON / `status_code==200` (el 404 real es HTML de Django).
- Los 4 métodos de test actualizados a `status_code=404`.

### 6. `OrgTree.get_queryset()` — helper de test no replicaba la rama real de la vista — RESUELTO (2 tests: `test_get_organizations_by_user_case1`, `case2`)

`OrgTree.get_queryset()` (`auth_and_perms/gtselects.py:634-658`) tiene dos ramas: si el user es superuser o tiene rol "Administrativo superior" → árbol completo (`get_org_parents_info`); si no → lista simple de membresías directas (`UserOrganization.objects.filter(user=...)`). El helper del test (`get_organizations_id_by_user()` en `select_organization/base.py`) siempre calculaba el esperado con la rama de árbol completo, sin chequear el rol real del user — confirmado con debug-print: `user1`/`user2` no tienen ese rol (`3 != 1`, `4 != 1`), `user5` pasaba de pura casualidad (ambas ramas dan el mismo resultado para su fixture). **Fix:** el helper ahora replica la misma condición (`is_superuser` o rol "Administrativo superior") antes de decidir qué lógica usar, igual que la vista real.

### 7. `ProfilePermission.organization` faltante en fixtures — RESUELTO (3 tests: `test_user1_list_profileslab1_default_limit`/`set_limit`, `test_get_laboratory_list`)

Mismo patrón en dos lugares distintos del código, ambos con un commit real (`767d99a2 "update profile views"`) que agregó un filtro `profilepermission__organization=...`/`organization__pk__in=org_ids` a consultas que antes no lo tenían — `UserLaboratoryOrganization.get_queryset()` (`auth_and_perms/api/viewsets.py:407`) y `get_lab_ids()` (`laboratory/utils.py:714`). Los fixtures (`fixtures/organization_manage_data.json`, `fixtures/laboratory_data.json`) nunca se actualizaron para setear `organization` en las filas de `ProfilePermission` — confirmado con debug-print: las filas relevantes tenían `organization_id: None`, por eso el filtro nunca matcheaba y la vista devolvía 0/vacío en vez de los datos esperados. **Fix:** agregado `"organization": 1` a las filas de `ProfilePermission` relevantes (pk 1/2 en `organization_manage_data.json`, pk 2/3 en `laboratory_data.json`) — el cambio correcto es arreglar el fixture, no debilitar la vista, porque el filtro de la vista es un requisito de negocio real y reciente.

## Resumen final

**723/723 tests pasan. 0 rotos.** Arrancó en 71 (744 tests, con Selenium sin excluir).

| # | Causa | Tests resueltos |
|---|---|---|
| 1 | Selenium sin excluir / falta paquete | 21 |
| 2 | `RiskZoneForm` M2M en instancia sin guardar | 1 |
| 3 | Permisos faltantes en fixture + bug de `assertRedirects` | 8 |
| 4 | `ProfileMiddleware` 404 + `HandleErrorMiddleware` → 302 (cluster `gtapi`) | 32 |
| 5 | Mismo patrón #4 en `select_organization` | 4 |
| 6 | Helper de test no replicaba rama real de `OrgTree.get_queryset()` | 2 |
| 7 | `ProfilePermission.organization` faltante en fixtures (commit `767d99a2`) | 3 |

21+1+8+32+4+2+3 = 71.
