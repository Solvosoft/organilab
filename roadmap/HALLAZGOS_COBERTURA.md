# Hallazgos de la campaña de cobertura (rama `performance`, octubre 2026)

Al llevar la cobertura del código web de 75.5% a 96.7% aparecieron defectos. Los que
tenían un arreglo evidente se corrigieron junto con su prueba. Este documento lista **lo
que sigue abierto** (primero seguridad), y debajo un resumen de lo corregido y del código
muerto detectado.

Medición de rendimiento: [`RENDIMIENTO.md`](RENDIMIENTO.md). Cobertura: [`COBERTURA.md`](COBERTURA.md).

## 1. Seguridad sin corregir (requieren decidir el permiso correcto)

### Críticos

| Dónde | Problema |
|---|---|
| `auth_and_perms` `RolAPI` / `UpdateRolOrganizationProfilePermission` | **Escalada de privilegios.** Basta con iniciar sesión para crear un rol con cualquier permiso y asignárselo a uno mismo a nivel de perfil (global). Además, PUT edita cualquier rol. |
| `auth_and_perms` `show_qr_img` | Sirve el secreto TOTP sin pedir sesión. |
| `auth_and_perms` `change_impostorlog` | Permite suplantar a un superusuario. |
| `api/utils` `AllPermissionOrganization` / `PermissionBase` | Por el orden de herencia, el chequeo de organización **nunca se ejecuta**. |
| `laboratory` API: 13 viewsets | Las clases de `permission_classes` ignoran los `perms`, así que cualquier miembro crea y borra. Afecta a Maintenance, Log, Calibrate, Guarantee, Training, Equipment, EquipmentType, InstrumentalFamily, Reactive, LaboratoryProcess, ShelfObjectHcode, ShelObjectReactive y ObjectViewSet. |

### Acceso entre organizaciones (cross-org)

- `auth_and_perms`:
  - `UpdateGroupsByProfile` no exige permiso y opera sobre grupos Django globales.
  - `ManageOrgLabsAPI` vincula laboratorios de otra organización.
  - `copy_rols` no comprueba la organización.
  - `LaboratoryOrganizationRoles` y `UserRoles` leen roles de cualquier organización.
  - `LabUserS2OrgManagement` ignora `organization_can_change_laboratory`.
  - `digitalsignature/notify` reescribe solicitudes BCCR.
- `laboratory`:
  - `ApiReservedProductsCRUD` deja ver y editar reservas ajenas.
  - `InformViewSet.retrieve` no comprueba la organización.
  - `ShelfObjectGraphicAPI` no comprueba la organización.
  - `ReactiveLimitSerializer.object` y el validador de equipo aceptan objetos de otra organización.
  - `furniture.add_catalog`: cualquier usuario crea filas globales de `Catalog`, unidades incluidas.
- `sga`:
  - `remove_company` y `edit_company` no se acotan a la organización.
  - `delete_substance`, `detail_substance`, `step_four`, `security_leaf_pdf` y `generate_label` tampoco.
- `risk_management`:
  - `ZoneDashboard` no pide sesión.
  - `RiskZoneReport` no comprueba la organización.
  - Hay que validar con Selenium los mapas de `perms` de los viewsets.
- `msds`: la trazabilidad SDS cruza organizaciones.
- `reservations`: las acciones y `rm/api` no comprueban la organización.
- `academic`: `ProcedureStepCreateView` no comprueba la organización.

## 2. Defectos funcionales sin corregir

- **reservations**:
  - El JS envía `boxes_codes` y el backend espera `boxes_to_return`, así que la devolución de cajas siempre falla.
  - Se mezcla el estado `"1"` con `1`.
  - `generate_reservation` informa éxito aunque falle.
- **laboratory API**:
  - `tag` devuelve None y da 500.
  - En `move_shelfobject_to`, la rama de cajas da 500, igual que `TransferInShelfObjectSerializer` con cajas.
  - Los listados de muebles y estantes de labview dan 500.
  - `EditEquimentShelfobjectCharacteristicSerializer` siempre rechaza.
  - `ValidateShelfObjectTrainingSerializer` confunde user con profile.
  - El cambio de cajas de `UpdateBoxShelfObjectSerializer` no está implementado.
- **laboratory núcleo**:
  - La columna de códigos H del reporte repite códigos.
- **risk_management**:
  - Las vistas de incidentes no se acotan al edificio.
  - `incidentreport_detail` revienta si no hay `risk_zone`.
- **regencia**:
  - html y pdf leen `data["years"]`, que nunca llega.
  - Un `except` amplio clasifica cualquier error como «riesgo menor».
  - `get_inventory` usa `.last().quantity` sin protección.
- **auth_and_perms**:
  - La regex de `identification_validator` incluye comillas y rechaza todo (el arreglo necesita migración).
  - `inerit_profile` da 500.
- **academic**: `check_user_access_kwargs_org_lab` rechaza la búsqueda de «mis procedimientos» aun con la relación org-lab y un ProfilePermission de laboratorio. Se retiró la prueba.
- **djgentelella** (dependencia): `widgets/files.py` `parse_value` lanza TypeError con `json.loads(None)` si el campo falta en los datos.

## 3. Corregido durante la campaña (resumen)

- **Seguridad**:
  - Toma de cuenta vía `create_user_qr`.
  - Callback JSONP con XSS reflejado.
  - OIDC sin email devolvía la primera cuenta con email vacío.
  - `ShelfObjectAPI` era `AllowAny`.
  - Vistas legacy de shelfobject y reportes de cualquier laboratorio.
  - gtselects filtraban por la organización del querystring.
  - Los viewsets de risk_management tenían `permission_classes=()`.
  - `update_rol` y `enable_child_organizations` no comprobaban nada.
  - `get_org_administrators` exponía nombres y correos.
  - Contenedores y traslados hacia otra organización.
  - Más de 15 accesos entre organizaciones en sga, risk, msds y reservations.
- **Funcionales**:
  - Reglas IPER que nunca se aplicaban (no se deshacía la traducción).
  - El año del reporte de precursores se invertía en enero.
  - Sobreasignación de stock en reservas.
  - Reservar 1.3 cajas apartaba 4.
  - Combinación de códigos H314-H316.
  - Gráficos de riesgo vacíos a nivel de organización.
  - Org/lab no numérico en la URL ahora da 404 en vez de 500.
  - Unos treinta 500/KeyError/NameError más, documentados en los commits.
- **Segunda pasada (cobertura combinada al 100%)**:
  - Reservas: el serializer rechazaba las fechas si el formulario se había cargado con el inglés activo (se añadió `%Y-%m-%d %H:%M:%S` a `DATETIME_INPUT_FORMATS`).
  - `ReturnProductView` aceptaba `nan`/`inf` como cantidad devuelta.
  - `fva_rest_authentication` devolvía `Http404()` en vez de lanzarlo (500).
  - `pending_tasks` devolvía el diccionario de serializers como clase (500 con `Accept: text/html`).
  - `LabroomUpdate` tenía dos `get_context_data` y el modal «Crear mueble» salía vacío.
  - `ShelfObjectTableViewSet` ordenaba solo por `-last_update`: filas en orden indefinido y paginación inestable.
  - `PrecursorReportValuesViewSet` con pk=0 daba 500 (ahora 404).
  - El HTML de regencia no guardaba su tabla; el orden de los códigos H del reporte de objetos ya es determinista.
  - Se quitaron rutas rotas sin uso: `api/reactive/name`, `add_rol_by_laboratory` y la rama POST de `create_personal_template`.

## 4. Código muerto

Borrado en la campaña (sin referencias en código, plantillas, JS ni catálogo):
- `api/access_management.py` y sus rutas; `api/views.py`.
- `laboratory/sustance/`, `laboratory/reactive.py`, `laboratory/limit_shelfobject.py` y la copia duplicada de `move_shelfobject_to`.
- En `laboratory/views/shelfobject.py`: `get_shelfobject_template`, `get_shelf_list` y `objects_transfer`; formularios `ShelfObjectListForm`, `TransferObjectForm`, `AddObjectForm`, `AddTransferObjectForm` y los duplicados de `EquipmentForm` y `ShelfObjectStatusForm`.
- `authBackend.py`, `register_user_to_platform`, `create_profile_otp`, `create_profile_by_digital_signature`, `OrganizationAPI` y sus formularios y plantillas.
- `sga/views/h_danger_category.py` (y su entrada en `urlname_permissions`), `templatetags/label_tags.py`, `PersonalFormAcademic`, `SubstanceForm`.
- `academic/convertions.py`, `utils_risk.examples()`, los restos de MPTT en `laboratory/utils.py` y la plantilla `report/regency_report_table.html`.

Pendiente: `check_lab_group_has_perm` ya no lo usa ninguna plantilla (solo sus pruebas).
