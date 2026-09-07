# Inventario de rutas

Generado por `make url-inventory`. No editar a mano: se regenera.

Clasifica cada ruta con nombre por lo que **es**, para poder decidir con
qué se prueba. Las de categoría `pagina` son las que un navegador visita;
el resto se cubre con pruebas de cliente o unitarias.

## Resumen

| Categoría | Rutas |
|---|---:|
| `pagina` | 172 |
| `parcial` | 5 |
| `api` | 696 |
| `autocomplete` | 6 |
| `ajax` | 10 |
| `json` | 44 |
| `descarga` | 18 |
| `accion` | 29 |
| `infra` | 701 |
| **total** | **1681** |

Páginas: 172, de las cuales **41 sin ninguna prueba**.

## Rutas por app

Se omiten las categorías `api` e `infra` (1397 rutas de routers DRF y de
la administración de Django): están en `inventario_urls.csv`.

### academic — 8 páginas, 0 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `add_steps_wrapper` | `/academic/<int:org_pk>/procedure/add_steps_wrapper/<int:pk>/` | accion | `academic.views.add_steps_wrapper` | — | org_pk, pk | — | sí |
| `remove_my_procedure` | `/academic/<int:org_pk>/myprocedure/<int:lab_pk>/remove_procedure/<int:pk>/` | accion | `academic.views.remove_my_procedure` | — | org_pk, lab_pk, pk | — | sí |
| `delete_procedure` | `/academic/<int:org_pk>/procedure/delete_procedure/` | json | `academic.views.delete_procedure` | — | org_pk | — | sí |
| `delete_step` | `/academic/<int:org_pk>/procedure/step/delete/` | json | `academic.views.delete_step` | — | org_pk | — | sí |
| `generate_reservation` | `/academic/<int:org_pk>/myprocedure/<int:lab_pk>/generate_reservation/` | json | `academic.views.generate_reservation` | — | org_pk, lab_pk | — | sí |
| `get_procedure` | `/academic/<int:org_pk>/procedure/get_procedure/<int:pk>/` | json | `academic.views.get_procedure` | — | org_pk, pk | — | sí |
| `add_my_procedures` | `/academic/<int:org_pk>/myprocedure/<int:lab_pk>/add_procedures/<str:content_type>/<str:model>/` | pagina | `academic.views.create_my_procedures` | `academic/procedure.html` | org_pk, lab_pk, content_type, model | — | sí |
| `complete_my_procedure` | `/academic/<int:org_pk>/myprocedure/<int:lab_pk>/complete_procedure/<int:pk>/` | pagina | `academic.views.complete_my_procedure` | `academic/complete_my_procedure.html` | org_pk, lab_pk, pk | — | sí |
| `get_my_procedures` | `/academic/<int:org_pk>/myprocedure/<int:lab_pk>/get_list/` | pagina | `academic.views.get_my_procedures` | `academic/procedure.html` | org_pk, lab_pk | sí | sí |
| `procedure_create` | `/academic/<int:org_pk>/procedure/procedure_create/` | pagina | `academic.views.ProcedureCreateView` | `academic/procedure_create.html` | org_pk | — | sí |
| `procedure_detail` | `/academic/<int:org_pk>/procedure/procedure_detail/<int:pk>/` | pagina | `academic.views.procedureStepDetail` | `academic/detail.html` | org_pk, pk | — | sí |
| `procedure_step` | `/academic/<int:org_pk>/procedure/procedure/<int:pk>/step/` | pagina | `academic.views.ProcedureStepCreateView` | `academic/procedure_steps.html` | org_pk, pk | — | sí |
| `procedure_update` | `/academic/<int:org_pk>/procedure/procedure_update/<int:pk>/` | pagina | `academic.views.ProcedureUpdateView` | `academic/procedure_create.html` | org_pk, pk | — | sí |
| `update_step` | `/academic/<int:org_pk>/procedure/step/<int:pk>/update/` | pagina | `academic.views.ProcedureStepUpdateView` | `academic/procedure_steps.html` | org_pk, pk | — | sí |
| `procedure_list` | `/academic/<int:org_pk>/procedure/procedure_list/` | parcial | `academic.views.ProcedureListView` | — | org_pk | sí | sí |

### auth_and_perms — 8 páginas, 0 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `add_contenttype_to_org` | `/perms/organization/manage/relorgcont/add/` | accion | `auth_and_perms.views.organizationstructure.add_contenttype_to_org` | — | — | — | sí |
| `change_to_impostor` | `/perms/switch_user/<int:org_pk>/<int:pk>` | accion | `auth_and_perms.views.impostor.add_user_impostor` | — | org_pk, pk | — | — |
| `copy_rols` | `/perms/organization/manage/rols/copy/<int:pk>/` | accion | `auth_and_perms.views.organizationstructure.copy_rols` | — | pk | — | sí |
| `enable_child_organizations` | `/perms/enable_child_organizations/` | accion | `auth_and_perms.views.organizationstructure.enable_child_organizations` | — | — | — | — |
| `remove_impostor` | `/perms/end_switch_user` | accion | `auth_and_perms.views.impostor.remove_impostor` | — | — | — | — |
| `update_rol` | `/perms/update_rol/<int:org_pk>/<int:pk>/` | accion | `auth_and_perms.views.organizationstructure.update_rol` | — | org_pk, pk | — | — |
| `add_rol_by_laboratory` | `/perms/organization/manage/rols/add/` | descarga | `auth_and_perms.views.organizationstructure.add_rol_by_laboratory` | — | — | — | — |
| `addusersorganization` | `/perms/organization/manage/addusersorganization/<int:pk>/` | descarga | `auth_and_perms.views.organizationstructure.add_users_organization` | — | pk | — | sí |
| `get_org_administrators` | `/perms/get_org_administrators/<int:pk>/` | descarga | `auth_and_perms.views.organizationstructure.get_org_administrators` | — | pk | — | — |
| `show_qr_img` | `/perms/totp/img/<int:pk>/` | descarga | `auth_and_perms.views.user_org_creation.show_QR_img` | — | pk | — | — |
| `check_signature_window_status_register` | `/perms/registration/digitalsignature/checkstatus` | json | `auth_and_perms.views.fva_rest_authentication.check_signature_window_status_register` | — | — | — | — |
| `get_rol` | `/perms/get_rol/<int:pk>/` | json | `auth_and_perms.views.organizationstructure.get_rol` | — | pk | — | — |
| `get_roles_by_organization` | `/perms/get_roles_by_organization/<int:pk>/` | json | `auth_and_perms.views.organizationstructure.get_roles_by_organization` | — | pk | — | — |
| `login_with_bccr` | `/perms/login_bccr` | json | `auth_and_perms.views.fva_rest_authentication.login_with_bccr` | — | — | — | — |
| `add_user` | `/perms/organization/manage/users/add/<int:pk>/` | pagina | `auth_and_perms.views.organizationstructure.AddUser` | `auth/user_form.html` | pk | — | sí |
| `del_rol_by_org` | `/perms/organization/manage/rols/del/<int:org_pk>/<int:pk>` | pagina | `auth_and_perms.views.organizationstructure.DeleteRolByOrganization` | `auth_and_perms/rol_confirm_delete.html` | org_pk, pk | — | sí |
| `get_users` | `/perms/get_users/` | pagina | `auth_and_perms.views.user_org_creation.get_users` | `auth_and_perms/user_list.html` | — | sí | — |
| `lab_org_list` | `/perms/lab_org_list/` | pagina | `auth_and_perms.views.organizationstructure.get_labs_orgs` | `auth_and_perms/lab_org_list.html` | — | sí | — |
| `list_rol_by_org` | `/perms/organization/manage/rols/list/<int:org_pk>/` | pagina | `auth_and_perms.views.organizationstructure.ListRolByOrganization` | `auth_and_perms/rol_list.html` | org_pk | — | sí |
| `map_of_laboratories` | `/perms/<int:org_pk>/organization/map/laboratories/` | pagina | `auth_and_perms.views.select_organization.map_of_laboratories_view` | `auth_and_perms/map_of_laboratories.html` | org_pk | sí | — |
| `organizationManager` | `/perms/organization/manage/` | pagina | `auth_and_perms.views.organizationstructure.organization_manage_view` | `auth_and_perms/list_organizations.html` | — | — | sí |
| `select_organization_by_user` | `/perms/organizations/` | pagina | `auth_and_perms.views.select_organization.select_organization_by_user` | `auth_and_perms/select_organization.html` | — | sí | sí |

### authentication — 1 páginas, 0 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `permission_denied` | `/permission_denied` | pagina | `authentication.views.PermissionDeniedView` | `laboratory/permission_denied.html` | — | sí | — |

### derb — 4 páginas, 0 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `delete_form` | `/derb/<int:org_pk>/FormList/delete/<int:pk>/` | accion | `derb.views.form_list.DeleteForm` | — | org_pk, pk | — | sí |
| `create_form` | `/derb/<int:org_pk>/FormList/create/` | json | `derb.views.form_list.CreateForm` | — | org_pk | — | sí |
| `update_form` | `/derb/<int:org_pk>/editView/update/` | json | `derb.views.EditView.UpdateForm` | — | org_pk | — | — |
| `edit_view` | `/derb/<int:org_pk>/editView/` | pagina | `derb.views.EditView.EditView` | `formBuilder/edit_view.html` | org_pk | sí | sí |
| `edit_view` | `/derb/<int:org_pk>/editView/<int:form_id>/` | pagina | `derb.views.EditView.EditView` | `formBuilder/edit_view.html` | org_pk, form_id | sí | sí |
| `form_list` | `/derb/<int:org_pk>/FormList/` | pagina | `derb.views.form_list.FormList` | `formBuilder/form_list.html` | org_pk | sí | sí |
| `preview_form` | `/derb/<int:org_pk>/FormList/preview/<int:form_id>/` | pagina | `derb.views.preview_form.previewForm` | `formBuilder/preview_form.html` | org_pk, form_id | sí | — |

### django — 0 páginas, 0 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `home` | `/` | accion | `django.views.generic.base.RedirectView` | — | — | — | — |

### djgentelella — 0 páginas, 0 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `api-notificationtable-detail` | `/tableapi/^notificationtableview/(?P<pk>[^/.]+)/$` | autocomplete | `djgentelella.notification.base.NotificationViewSet` | — | pk | — | — |
| `api-notificationtable-detail` | `/tableapi/^notificationtableview/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | autocomplete | `djgentelella.notification.base.NotificationViewSet` | — | pk, format | — | — |
| `api-notificationtable-list` | `/tableapi/^notificationtableview/$` | autocomplete | `djgentelella.notification.base.NotificationViewSet` | — | — | — | — |
| `api-notificationtable-list` | `/tableapi/^notificationtableview\.(?P<format>[a-z0-9]+)/?$` | autocomplete | `djgentelella.notification.base.NotificationViewSet` | — | format | — | — |

### laboratory — 66 páginas, 19 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `rebuild_laboratory_qr` | `/lab/<int:org_pk>/<int:lab_pk>/rooms/rebuild_laboratory_qr` | accion | `laboratory.views.labroom.rebuild_laboratory_qr` | — | org_pk, lab_pk | — | — |
| `redirect_user_to_labindex` | `/register_user_qr/<int:org_pk>/<int:lab_pk>/redirect_user_to_labindex/<int:pk>/` | accion | `laboratory.views.laboratory.redirect_user_to_labindex` | — | org_pk, lab_pk, pk | — | — |
| `remove_inform` | `/lab/<int:org_pk>/<int:lab_pk>/informs/remove_inform/<int:pk>/` | accion | `laboratory.views.informs.remove_inform` | — | org_pk, lab_pk, pk | — | sí |
| `furniture_list` | `/lab/<int:org_pk>/<int:lab_pk>/furniture/` | ajax | `laboratory.views.furniture.list_furniture` | — | org_pk, lab_pk | — | sí |
| `list_shelfobject` | `/lab/<int:org_pk>/<int:lab_pk>/shelfobject/list/` | ajax | `laboratory.views.shelfobject.list_shelfobject` | — | org_pk, lab_pk | — | — |
| `shelf_create` | `/lab/<int:org_pk>/<int:lab_pk>/shelf/create/` | ajax | `laboratory.views.shelfs.ShelfCreate` | — | org_pk, lab_pk | — | sí |
| `shelf_delete` | `/lab/<int:org_pk>/<int:lab_pk>/shelf/delete/<int:pk>/<int:row>/<int:col>/` | ajax | `laboratory.views.shelfs.delete_shelf` | — | org_pk, lab_pk, pk, row, col | — | sí |
| `shelf_edit` | `/lab/<int:org_pk>/<int:lab_pk>/shelf/edit/<int:pk>/<int:row>/<int:col>/` | ajax | `laboratory.views.shelfs.ShelfEdit` | — | org_pk, lab_pk, pk, row, col | — | sí |
| `shelfobject_create` | `/lab/<int:org_pk>/<int:lab_pk>/shelfobject/create/` | ajax | `laboratory.views.shelfobject.ShelfObjectCreate` | — | org_pk, lab_pk | — | — |
| `shelfobject_delete` | `/lab/<int:org_pk>/<int:lab_pk>/shelfobject/delete/<int:pk>/` | ajax | `laboratory.views.shelfobject.ShelfObjectDelete` | — | org_pk, lab_pk, pk | — | — |
| `shelfobject_detail` | `/lab/<int:org_pk>/<int:lab_pk>/shelfobject/detail/<int:pk>/` | ajax | `laboratory.views.shelfobject.ShelfObjectDetail` | — | org_pk, lab_pk, pk | — | — |
| `shelfobject_edit` | `/lab/<int:org_pk>/<int:lab_pk>/shelfobject/edit/<int:pk>/` | ajax | `laboratory.views.shelfobject.ShelfObjectEdit` | — | org_pk, lab_pk, pk | — | — |
| `shelfobject_searchupdate` | `/lab/<int:org_pk>/<int:lab_pk>/shelfobject/q/update/<int:pk>/` | ajax | `laboratory.views.shelfobject.ShelfObjectSearchUpdate` | — | org_pk, lab_pk, pk | — | — |
| `download_h_code_reports` | `/<int:org_pk>/reports/download/hcode` | descarga | `laboratory.views.reports.report_h_code` | `pdf/hcode_pdf.html` | org_pk | — | sí |
| `download_register_user_qr` | `/register_user_qr/<int:org_pk>/<int:lab_pk>/download/<int:pk>/` | descarga | `laboratory.views.laboratory.get_pdf_register_user_qr` | `pdf/qr_pdf.html` | org_pk, lab_pk, pk | — | — |
| `download_shelfobject_qr` | `/lab/<int:org_pk>/<int:lab_pk>/shelfobject/download_shelfobject_qr/<int:pk>/` | descarga | `laboratory.views.shelfobject.download_shelfobject_qr` | — | org_pk, lab_pk, pk | — | — |
| `generate_shelfobject_label` | `/<int:org_pk>/<int:lab_pk>/<int:pk>/generate_shelfobject_label/<int:recipient>/` | descarga | `laboratory.views.shelfobject.generate_shelfobject_label` | — | org_pk, lab_pk, pk, recipient | — | — |
| `organization_actions` | `/organization/manage/actions` | descarga | `laboratory.views.organizations.OrganizationActionsFormview` | — | — | — | — |
| `reports_shelf_objects` | `/lab/<int:org_pk>/<int:lab_pk>/reports/shelf_objects/<int:pk>` | descarga | `laboratory.views.reports.report_shelf_objects` | `pdf/shelf_object_pdf.html` | org_pk, lab_pk, pk | — | — |
| `sds_coverage_svg` | `/<int:org_pk>/reports/sds-coverage.svg` | descarga | `laboratory.views.reports.sds_coverage_svg` | — | org_pk | — | — |
| `shelfobject_label` | `/lab/<int:org_pk>/<int:lab_pk>/shelfobject/label/<int:pk>/` | descarga | `laboratory.views.shelfobject.generate_shelfobject_label` | — | org_pk, lab_pk, pk | — | — |
| `add_furniture_type_catalog` | `/catalogs/furniture/furniture_type` | json | `laboratory.views.furniture.add_catalog` | — | — | — | sí |
| `add_shelf_type_catalog` | `/catalogs/shelf/container_type` | json | `laboratory.views.furniture.add_catalog` | — | — | — | sí |
| `add_shelfobject_status` | `/catalogs/shelf/shelfobject_status` | json | `laboratory.views.furniture.add_catalog` | — | — | — | — |
| `add_structure_type_catalog` | `/catalogs/add/structure/type/` | json | `laboratory.views.furniture.add_catalog` | — | — | — | — |
| `add_workplace_type_catalog` | `/catalogs/workplace/type/<str:key>` | json | `laboratory.views.furniture.add_catalog` | — | key | — | — |
| `get_lab_id` | `/returnLabId` | json | `laboratory.functions.return_laboratory_of_shelf_id` | — | — | — | — |
| `get_shelfobject_limit` | `/lab/<int:org_pk>/<int:lab_pk>/shelfobject/get_shelfobject_limit/<int:pk>/` | json | `laboratory.views.shelfobject.edit_limit_object` | — | org_pk, lab_pk, pk | — | — |
| `password_change` | `/profile/<int:pk>/password` | json | `authentication.users.password_change` | — | pk | — | sí |
| `add_informs` | `/lab/<int:org_pk>/<int:lab_pk>/informs/add_informs/<str:content_type>/<str:model>/` | pagina | `laboratory.views.informs.create_informs` | `laboratory/inform.html` | org_pk, lab_pk, content_type, model | — | sí |
| `add_period_scheduler` | `/inform_manager/<int:org_pk>/add/` | pagina | `laboratory.views.inform_period.InformSchedulerAdd` | `informs/informscheduler_create.html` | org_pk | — | sí |
| `block_notification` | `/lab/<int:lab_pk>/blocknotifications/<int:obj_pk>/` | pagina | `laboratory.views.objects.block_notifications` | `laboratory/block_object_notification.html` | lab_pk, obj_pk | — | — |
| `chemicalinventory` | `/<int:org_pk>/chemicalinventory/` | pagina | `laboratory.views.reports.ChemicalInventoryReport` | `report/base_report_form_view.html` | org_pk | — | — |
| `complete_inform` | `/lab/<int:org_pk>/<int:lab_pk>/informs/complete_inform/<int:pk>/` | pagina | `laboratory.views.informs.complete_inform` | `laboratory/complete_inform.html` | org_pk, lab_pk, pk | sí | sí |
| `create_lab` | `/<int:org_pk>/create_lab/` | pagina | `laboratory.views.laboratory.CreateLaboratoryFormView` | `laboratory/laboratory_create.html` | org_pk | — | sí |
| `create_organization` | `/organization/create` | pagina | `laboratory.views.organizations.OrganizationCreateView` | `laboratory/organizationstructure_form.html` | — | — | sí |
| `create_user_qr` | `/register_user_qr/<int:org_pk>/<int:lab_pk>/create_user_qr/<int:pk>` | pagina | `laboratory.views.laboratory.create_user_qr` | `laboratory/register_user_qr/login_register_user.html` | org_pk, lab_pk, pk | — | — |
| `create_user_qr` | `/register_user_qr/<int:org_pk>/<int:lab_pk>/create_user_qr/<int:pk>/<int:user>` | pagina | `laboratory.views.laboratory.create_user_qr` | `laboratory/register_user_qr/login_register_user.html` | org_pk, lab_pk, pk, user | — | — |
| `delete_organization` | `/organization/<int:pk>/delete` | pagina | `laboratory.views.organizations.OrganizationDeleteView` | `laboratory/organizationstructure_confirm_delete.html` | pk | — | sí |
| `delete_register_user_qr` | `/register_user_qr/<int:org_pk>/<int:lab_pk>/delete/<int:pk>/` | pagina | `laboratory.views.laboratory.RegisterUserQRDeleteView` | `laboratory/register_user_qr/confirm_delete.html` | org_pk, lab_pk, pk | — | — |
| `detail_period_scheduler` | `/inform_manager/<int:org_pk>/detail/<int:pk>/` | pagina | `laboratory.views.inform_period.InformSchedulerDetail` | `informs/informscheduler_detail.html` | org_pk, pk | — | sí |
| `disposal_substance` | `/lab/<int:org_pk>/search/disposal/` | pagina | `laboratory.search.SearchDisposalObject` | `laboratory/disposal_substance.html` | org_pk | — | sí |
| `edit_period_scheduler` | `/inform_manager/<int:org_pk>/edit/<int:pk>/` | pagina | `laboratory.views.inform_period.InformSchedulerEdit` | `informs/informscheduler_edit.html` | org_pk, pk | — | sí |
| `equipment_list` | `/lab/<int:org_pk>/<int:lab_pk>/equipment/` | pagina | `laboratory.views.objects.view_equipment_list` | `laboratory/equipment/list.html` | org_pk, lab_pk | sí | sí |
| `equipment_shelfobject_detail` | `/lab/<int:org_pk>/<int:lab_pk>/shelfobject/<int:pk>/edit/` | pagina | `laboratory.views.shelfobject.view_equipment_shelfobject_detail` | `laboratory/shelfobject/equipment_edit.html` | org_pk, lab_pk, pk | — | — |
| `equipmenttype_list` | `/lab/<int:org_pk>/<int:lab_pk>/equipment/equipmenttype/` | pagina | `laboratory.views.catalogs.view_equipmenttype_list` | `laboratory/equipmenttype/list.html` | org_pk, lab_pk | — | — |
| `furniture_create` | `/lab/<int:org_pk>/<int:lab_pk>/furniture/create/<int:labroom>/` | pagina | `laboratory.views.furniture.FurnitureCreateView` | `laboratory/furniture_form.html` | org_pk, lab_pk, labroom | — | sí |
| `furniture_delete` | `/lab/<int:org_pk>/<int:lab_pk>/furniture/delete/<int:pk>/` | pagina | `laboratory.views.furniture.FurnitureDelete` | `laboratory/furniture_confirm_delete.html` | org_pk, lab_pk, pk | — | sí |
| `get_informs` | `/lab/<int:org_pk>/<int:lab_pk>/informs/get_list/` | pagina | `laboratory.views.informs.get_informs` | `laboratory/inform.html` | org_pk, lab_pk | sí | sí |
| `h_code_reports` | `/<int:org_pk>/reports/hcode` | pagina | `laboratory.views.laboratory.HCodeReports` | `laboratory/h_code_report.html` | org_pk | — | sí |
| `inform_index` | `/inform_manager/<int:org_pk>/index/` | pagina | `laboratory.views.inform_period.get_inform_index` | `informs/index.html` | org_pk | — | sí |
| `instrumentalfamily_list` | `/lab/<int:org_pk>/<int:lab_pk>/equipment/instrumental/` | pagina | `laboratory.views.catalogs.view_instrumental_family_list` | `laboratory/instrumentalfamily/list.html` | org_pk, lab_pk | — | — |
| `lab_or_org_request_list` | `/<int:org_pk>/requests/my/` | pagina | `laboratory.views.lab_or_org_request.lab_or_org_request_view` | `laboratory/lab_or_org_request/list.html` | org_pk | — | — |
| `lab_or_org_request_review` | `/<int:org_pk>/requests/review/` | pagina | `laboratory.views.lab_or_org_request.lab_or_org_request_review_view` | `laboratory/lab_or_org_request/review.html` | org_pk | — | — |
| `labindex` | `/<int:org_pk>/labindex/<int:lab_pk>` | pagina | `laboratory.views.lab_index` | `laboratory/index.html` | org_pk, lab_pk | sí | sí |
| `laboratory_delete` | `/lab/<int:org_pk>/<int:pk>/delete/` | pagina | `laboratory.views.laboratory.LaboratoryDeleteView` | `laboratory/laboratory_delete.html` | org_pk, pk | — | sí |
| `laboratory_process_list` | `/<int:org_pk>/<int:lab_pk>/processes/list/` | pagina | `laboratory.views.laboratory.laboratory_process_list` | `laboratory/laboratory_process/list.html` | org_pk, lab_pk | — | — |
| `laboratory_update` | `/<int:org_pk>/laboratory/<int:pk>/edit/` | pagina | `laboratory.views.laboratory.LaboratoryEdit` | `laboratory/edit.html` | org_pk, pk | — | sí |
| `labview` | `/lab/<int:org_pk>/<int:lab_pk>/rooms/labview/` | pagina | `laboratory.views.labview.LabView` | `laboratory/labview/labview.html` | org_pk, lab_pk | — | sí |
| `list_register_user_qr` | `/register_user_qr/<int:org_pk>/<int:lab_pk>/list/` | pagina | `laboratory.views.laboratory.RegisterUserQRList` | `laboratory/register_user_qr/register_user_qr_list.html` | org_pk, lab_pk | sí | sí |
| `load_archive` | `/<int:org_pk>/<int:lab_pk>/load_archive/` | pagina | `laboratory.views.loadArchive.load_archive` | `laboratory/load_archive/load_archive.html` | org_pk, lab_pk | — | — |
| `load_archive_create_shelfobjects` | `/<int:org_pk>/<int:lab_pk>/load_archive/create_shelfobjects/<uuid:key>/` | pagina | `laboratory.views.loadArchive.upload_reactives` | `laboratory/load_archive/create_shelfobjects.html` | org_pk, lab_pk, key | — | — |
| `logentry_list` | `/logentry/<int:org_pk>` | pagina | `laboratory.views.logentry.get_logentry_from_organization` | `laboratory/logentry_list.html` | org_pk | — | sí |
| `logentry_register_user_qr` | `/register_user_qr/<int:org_pk>/<int:lab_pk>/logentry/<int:pk>/` | pagina | `laboratory.views.laboratory.get_logentry_from_registeruserqr` | `laboratory/register_user_qr/logentry_list.html` | org_pk, lab_pk, pk | — | — |
| `login_register_user_qr` | `/register_user_qr/<int:org_pk>/<int:lab_pk>/login/<int:pk>/` | pagina | `laboratory.views.laboratory.login_register_user_qr` | `laboratory/register_user_qr/login_register_user.html` | org_pk, lab_pk, pk | — | — |
| `manage_register_user_qr` | `/register_user_qr/<int:org_pk>/<int:lab_pk>/manage/<int:pk>/` | pagina | `laboratory.views.laboratory.manage_register_qr` | `laboratory/register_user_qr/manage_register_qr.html` | org_pk, lab_pk, pk | sí | — |
| `my_reservations` | `/<int:org_pk>/my_reservations/<int:lab_pk>` | pagina | `laboratory.views.my_reservations.MyReservationView` | `laboratory/my_reservations_list.html` | org_pk, lab_pk | — | sí |
| `mylabs` | `/<int:org_pk>/my_labs/` | pagina | `laboratory.views.laboratory.LaboratoryListView` | `laboratory/laboratory_list.html` | org_pk | — | sí |
| `object_reservation` | `/reserve_object/<int:modelpk>` | pagina | `laboratory.reservation.ShelfObjectReservation` | `djreservation/product_form.html` | modelpk | — | — |
| `object_view` | `/lab/<int:org_pk>/<int:lab_pk>/object/list/` | pagina | `laboratory.views.objects.object_view` | `laboratory/object_list.html` | org_pk, lab_pk | sí | sí |
| `objectfeatures_view` | `/lab/<int:org_pk>/<int:lab_pk>/features/list/` | pagina | `laboratory.views.objectfeature.objectfeatures_view` | `laboratory/objectfeatures_list.html` | org_pk, lab_pk | sí | — |
| `objectview_create` | `/lab/<int:org_pk>/<int:lab_pk>/objects/create` | pagina | `laboratory.views.objects.ObjectView.__init__.<locals>.ObjectCreateView` | `laboratory/objectview_form.html` | org_pk, lab_pk | — | sí |
| `objectview_delete` | `/lab/<int:org_pk>/<int:lab_pk>/objects/delete/<int:pk>` | pagina | `laboratory.views.objects.ObjectView.__init__.<locals>.ObjectDeleteView` | `laboratory/objectview_delete.html` | org_pk, lab_pk, pk | — | sí |
| `objectview_update` | `/lab/<int:org_pk>/<int:lab_pk>/objects/edit/<int:pk>` | pagina | `laboratory.views.objects.ObjectView.__init__.<locals>.ObjectUpdateView` | `laboratory/objectview_form.html` | org_pk, lab_pk, pk | — | sí |
| `organizationreactivepresence` | `/<int:org_pk>/organizationreactivepresence/` | pagina | `laboratory.views.reports.OrganizationReactivePresenceList` | `report/base_report_form_view.html` | org_pk | — | sí |
| `profile` | `/profile/<int:pk>/info` | pagina | `authentication.users.ChangeUser` | `auth/change_user.html` | pk | — | sí |
| `profile_detail` | `/profile/info/<int:org_pk>/<int:pk>` | pagina | `authentication.users.get_profile` | `laboratory/profile_detail.html` | org_pk, pk | — | sí |
| `protocol_create` | `/lab/<int:org_pk>/<int:lab_pk>/protocols/create` | pagina | `laboratory.protocol.views.ProtocolCreateView` | `laboratory/protocol/create.html` | org_pk, lab_pk | — | sí |
| `protocol_delete` | `/lab/<int:org_pk>/<int:lab_pk>/protocols/delete/<int:pk>/` | pagina | `laboratory.protocol.views.ProtocolDeleteView` | `laboratory/protocol/delete.html` | org_pk, lab_pk, pk | — | sí |
| `protocol_list` | `/lab/<int:org_pk>/<int:lab_pk>/protocols/list` | pagina | `laboratory.protocol.views.protocol_list` | `laboratory/protocol/protocol_list.html` | org_pk, lab_pk | sí | sí |
| `protocol_update` | `/lab/<int:org_pk>/<int:lab_pk>/protocols/update/<int:pk>/` | pagina | `laboratory.protocol.views.ProtocolUpdateView` | `laboratory/protocol/update.html` | org_pk, lab_pk, pk | — | sí |
| `provider_view` | `/lab/<int:org_pk>/<int:lab_pk>/provider/list/` | pagina | `laboratory.views.provider.provider_view` | `laboratory/provider_list.html` | org_pk, lab_pk | sí | sí |
| `reactive_stock_list` | `/lab/<int:org_pk>/<int:lab_pk>/sustance/reactive_stock/` | pagina | `laboratory.views.objectlimits.ReactiveStockDashboard` | `laboratory/objectlimit/dashboard.html` | org_pk, lab_pk | — | — |
| `reports` | `/reports/<int:org_pk>/` | pagina | `laboratory.views.reports.report_index` | `laboratory/reports/report_index.html` | org_pk | — | sí |
| `reports_laboratory` | `/lab/<int:org_pk>/<int:lab_pk>/reports/list/laboratory/` | pagina | `laboratory.views.labroom.LaboratoryRoomReportView` | `report/base_report_form_view.html` | org_pk, lab_pk | — | sí |
| `rooms_create` | `/lab/<int:org_pk>/<int:lab_pk>/rooms/create` | pagina | `laboratory.views.labroom.LabroomCreate` | `laboratory/laboratoryroom_form.html` | org_pk, lab_pk | sí | sí |
| `rooms_delete` | `/lab/<int:org_pk>/<int:lab_pk>/rooms/<int:pk>/delete` | pagina | `laboratory.views.labroom.LaboratoryRoomDelete` | `laboratory/laboratoryroom_confirm_delete.html` | org_pk, lab_pk, pk | — | sí |
| `rooms_list` | `/lab/<int:org_pk>/<int:lab_pk>/rooms/` | pagina | `laboratory.views.labroom.LaboratoryRoomsList` | `laboratory/laboratoryroom_list.html` | org_pk, lab_pk | sí | sí |
| `rooms_update` | `/lab/<int:org_pk>/<int:lab_pk>/rooms/<int:pk>/edit` | pagina | `laboratory.views.labroom.LabroomUpdate` | `laboratory/laboratoryroom_form.html` | org_pk, lab_pk, pk | — | sí |
| `shel_objects_reactives` | `/lab/<int:org_pk>/<int:lab_pk>/reports/reactives/` | pagina | `laboratory.views.shelfobject.shelf_object_reagents` | `laboratory/shelfobject/reactive.html` | org_pk, lab_pk | sí | — |
| `shelf_containers` | `/lab/<int:org_pk>/<int:lab_pk>/shelf/containers/` | pagina | `laboratory.shelfobject_container.views.show_shelf_container` | `laboratory/containers/container_list.html` | org_pk, lab_pk | — | — |
| `shelf_object_hcode` | `/<int:org_pk>/<int:lab_pk>/shelfobject/hcode/list/` | pagina | `laboratory.views.shelfobject.shelf_object_hcode` | `laboratory/shelfobject/shelfobject_code.html` | org_pk, lab_pk | sí | — |
| `sustance_list` | `/lab/<int:org_pk>/<int:lab_pk>/sustance/` | pagina | `laboratory.views.objects.view_reactive_list` | `laboratory/sustance/list.html` | org_pk, lab_pk | sí | sí |
| `trash_list` | `/trash/<int:org_pk>` | pagina | `laboratory.views.trash.get_trash_from_organization` | `laboratory/trash_list.html` | org_pk | — | — |
| `update_organization` | `/organization/<int:pk>/update` | pagina | `laboratory.views.organizations.OrganizationUpdateView` | `laboratory/organizationstructure_form.html` | pk | — | sí |
| `furniture_update` | `/lab/<int:org_pk>/<int:lab_pk>/furniture/edit/<int:pk>/` | parcial | `laboratory.views.furniture.FurnitureUpdateView` | — | org_pk, lab_pk, pk | — | sí |

### msds — 3 páginas, 0 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `sds_create` | `/msds/<int:org_pk>/sds/create/` | accion | `msds.views.sds_create` | — | org_pk | — | sí |
| `download_all_regulations` | `/regulations/download/all` | descarga | `msds.views.download_all_regulations` | — | — | — | — |
| `list_msds` | `/msds/<int:org_pk>/list/` | json | `msds.views.get_list_msds` | — | org_pk | — | sí |
| `index_msds` | `/msds/<int:org_pk>/index_msds/` | pagina | `msds.views.index_msds` | `index_msds.html` | org_pk | sí | sí |
| `regulation_docs` | `/regulations/` | pagina | `msds.views.regulation_view` | `regulation/regulations_document.html` | — | sí | sí |
| `verified_sds` | `/msds/<int:org_pk>/verified_sds/` | pagina | `msds.views.verified_sds` | `msds/verified_sds.html` | org_pk | sí | — |

### pending_tasks — 1 páginas, 0 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `view_task` | `/pending_tasks/view-tasks` | pagina | `pending_tasks.views.view_task` | `tasks/tasks-view.html` | — | — | sí |

### presentation — 5 páginas, 0 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `tutorial_progress_api` | `/index/tutorial/api/progress/` | json | `presentation.views.tutorial_progress_api` | — | — | — | — |
| `tutorial_reactivate_api` | `/index/tutorial/api/reactivate/` | json | `presentation.views.tutorial_reactivate_api` | — | — | — | — |
| `tutorial_toggle_api` | `/index/tutorial/api/toggle/` | json | `presentation.views.tutorial_toggle_api` | — | — | — | — |
| `error_view` | `/index/error` | pagina | `presentation.views.error_view` | `error_view.html` | — | sí | — |
| `feedback` | `/index/feedback` | pagina | `presentation.views.FeedbackView` | `feedback/feedbackentry_form.html` | — | — | sí |
| `general_info` | `/general_info` | pagina | `presentation.views.general_information` | `general_information.html` | — | sí | — |
| `index` | `/index/` | pagina | `presentation.views.index_organilab` | `index.html` | — | sí | sí |
| `tutorials` | `/index/tutorial/<int:org_pk>` | pagina | `presentation.views.index_tutorial` | `tutorial.html` | org_pk | sí | — |

### report — 18 páginas, 10 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `create_organization_report_request` | `/report/<int:org_pk>/create/organization/` | json | `report.views.base.create_organization_request_by_report` | — | org_pk | — | — |
| `create_report_request` | `/report/<int:org_pk>/create/` | json | `report.views.base.create_request_by_report` | — | org_pk | — | — |
| `generate_organization_report` | `/report/<int:org_pk>/download/organization/` | json | `report.views.base.download__organization_report` | — | org_pk | — | — |
| `generate_report` | `/report/<int:org_pk>/download/` | json | `report.views.base.download_report` | — | org_pk | — | — |
| `report_organization_status` | `/report/<int:org_pk>/status/` | json | `report.views.base.report_status` | — | org_pk | — | — |
| `report_status` | `/report/<int:org_pk>/status/` | json | `report.views.base.report_status` | — | org_pk | — | — |
| `compatibility_report` | `/report/reports/<int:org_pk>/compatibility/` | pagina | `report.views.reports_org.CompatibilityReport` | `report/base_report_form_view.html` | org_pk | — | — |
| `donations_report` | `/report/reports/<int:org_pk>/donations-report/` | pagina | `report.views.reports_org.DonationReportView` | `report/base_report_form_view.html` | org_pk | — | — |
| `hazard_map_report` | `/report/reports/<int:org_pk>/hazard_map/` | pagina | `report.views.reports_org.HazardMapReport` | `report/base_report_form_view.html` | org_pk | — | — |
| `hazard_map_visual` | `/report/reports/<int:org_pk>/hazard_map/visual/` | pagina | `report.views.riskzones.hazard_map_visual_view` | `report/hazard_map_visual.html` | org_pk | sí | — |
| `object_change_logs` | `/report/reports/<int:org_pk>/objectchanges/` | pagina | `report.views.reports_org.LogObjectView` | `report/base_report_form_view.html` | org_pk | sí | — |
| `precursor_report` | `/report/reports/<int:org_pk>/precursors/` | pagina | `report.views.reports_org.PrecursorsView` | `report/precursor_report.html` | org_pk | sí | sí |
| `precursor_report_values_view` | `/report/reports/<int:org_pk>/precursor-values-list/<int:precusor_pk>/` | pagina | `report.views.reports_org.PrecursorReportValuesView` | `report/precursor_report_values_view.html` | org_pk, precusor_pk | — | — |
| `reactive_precursor_object_list` | `/report/reports/<int:org_pk>/list/reactive_precursor_objects/` | pagina | `report.views.reports_org.ReactivePrecursorObjectList` | `report/base_report_form_view.html` | org_pk | — | — |
| `reactive_report` | `/report/reports/<int:org_pk>/list/reactive/report` | pagina | `report.views.reports_org.ReactiveReport` | `report/base_report_form_view.html` | org_pk | — | — |
| `reactive_stock_report` | `/report/reports/<int:org_pk>/reactive/stock/` | pagina | `report.views.reports_org.ReactiveStockReport` | `report/base_report_form_view.html` | org_pk | sí | — |
| `regency_report` | `/report/reports/<int:org_pk>/regency/` | pagina | `report.views.base.regency_report` | `report/regency_report.html` | org_pk | sí | — |
| `report_organization_table` | `/report/<int:org_pk>/table/organization/<int:pk>/` | pagina | `report.views.base.report_organization_table` | `report/general_organization_report.html` | org_pk, pk | — | — |
| `report_table` | `/report/<int:org_pk>/table/<int:pk>/` | pagina | `report.views.base.report_table` | `report/general_reports.html` | org_pk, pk | — | — |
| `reports_furniture_detail` | `/report/reports/<int:org_pk>/list/furniture/` | pagina | `report.views.reports_org.FurnitureReportView` | `report/base_report_form_view.html` | org_pk | — | sí |
| `reports_limited_shelf_objects_list` | `/report/reports/<int:org_pk>/list/limited_shelf_objects/` | pagina | `report.views.reports_org.LimitedShelfObjectList` | `report/base_report_form_view.html` | org_pk | — | — |
| `reports_objects_list` | `/report/reports/<int:org_pk>/list/objects/` | pagina | `report.views.reports_org.ObjectList` | `report/base_report_form_view.html` | org_pk | sí | sí |
| `risk_zone_report` | `/report/reports/<int:org_pk>/risk_zone/` | pagina | `report.views.reports_org.RiskZoneReport` | `report/base_report_form_view.html` | org_pk | — | — |
| `waste_report` | `/report/reports/<int:org_pk>/list/waste/report` | pagina | `report.views.reports_org.DiscardShelfReportView` | `report/base_report_form_view.html` | org_pk | sí | — |

### reservations_management — 2 páginas, 0 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `close_reservation` | `/reservations_management/<int:org_pk>/reservations/<int:pk>/close/` | accion | `reservations_management.views.CloseReservationView` | — | org_pk, pk | — | — |
| `product_action` | `/reservations_management/<int:org_pk>/reservations/<int:pk>/product/<int:product_pk>/action/` | accion | `reservations_management.views.ProductActionView` | — | org_pk, pk, product_pk | — | — |
| `get_product_name_and_quantity` | `/reservations_management/<int:org_pk>/reservedproduct/get_product_name_and_quantity/` | json | `reservations_management.functions.get_product_name_and_quantity` | — | org_pk | — | sí |
| `increase_stock` | `/reservations_management/<int:org_pk>/reservedproduct/increase_stock/` | json | `reservations_management.functions.increase_stock` | — | org_pk | — | sí |
| `return_product` | `/reservations_management/<int:org_pk>/reservations/<int:pk>/product/<int:product_pk>/return/` | json | `reservations_management.views.ReturnProductView` | — | org_pk, pk, product_pk | — | — |
| `validate_reservation` | `/reservations_management/<int:org_pk>/reservedproduct/validate_reservation/` | json | `reservations_management.functions.validate_reservation` | — | org_pk | — | sí |
| `manage_reservation` | `/reservations_management/<int:org_pk>/reservations/<int:pk>/manage/` | pagina | `reservations_management.views.ManageReservationView` | `reservations_management/manage_reservation.html` | org_pk, pk | — | sí |
| `reservations_list` | `/reservations_management/<int:org_pk>/reservations/list/<int:status>/` | pagina | `reservations_management.views.ReservationsListView` | `reservations_management/reservations_list.html` | org_pk, status | — | sí |

### rest_framework — 0 páginas, 0 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `api-root` | `/tableapi/` | autocomplete | `rest_framework.routers.APIRootView` | — | — | — | — |
| `api-root` | `/tableapi/<drf_format_suffix:format>` | autocomplete | `rest_framework.routers.APIRootView` | — | format | — | — |

### riskmanagement — 27 páginas, 6 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `iper_clone` | `/risk/<int:org_pk>/iper/<int:pk>/clone/` | accion | `risk_management.iper_views.iper_clone_for_update` | — | org_pk, pk | — | sí |
| `iper_hazard_create` | `/risk/<int:org_pk>/iper/<int:assessment_pk>/hazard/create/` | accion | `risk_management.iper_views.iper_hazard_action` | — | org_pk, assessment_pk | — | sí |
| `iper_hazard_delete` | `/risk/<int:org_pk>/iper/<int:assessment_pk>/hazard/<int:pk>/delete/` | accion | `risk_management.iper_views.iper_hazard_delete` | — | org_pk, assessment_pk, pk | — | — |
| `iper_hazard_update` | `/risk/<int:org_pk>/iper/<int:assessment_pk>/hazard/<int:pk>/update/` | accion | `risk_management.iper_views.iper_hazard_action` | — | org_pk, assessment_pk, pk | — | — |
| `iper_observation_add` | `/risk/<int:org_pk>/iper/<int:pk>/observation/` | accion | `risk_management.iper_views.iper_observation_add` | — | org_pk, pk | — | — |
| `iper_request_zone` | `/risk/<int:org_pk>/iper/zone/<int:risk_pk>/request/` | accion | `risk_management.iper_views.iper_request_for_zone` | — | org_pk, risk_pk | — | — |
| `iper_toggle_anonymous` | `/risk/<int:org_pk>/iper/<int:pk>/toggle-anonymous/` | accion | `risk_management.iper_views.iper_toggle_anonymous` | — | org_pk, pk | — | — |
| `iper_toggle_status` | `/risk/<int:org_pk>/iper/<int:pk>/toggle-status/` | accion | `risk_management.iper_views.iper_toggle_status` | — | org_pk, pk | — | — |
| `incident_report` | `/risk/<int:org_pk>/incident/report/<int:risk_pk>/<int:pk>/` | descarga | `risk_management.incidents.report_incidentreport` | `risk_management/incidentreport_pdf.html` | org_pk, risk_pk, pk | — | sí |
| `iper_lab_help` | `/risk/<int:org_pk>/iper/labdata/<int:lab_pk>/` | json | `risk_management.iper_views.iper_lab_help` | — | org_pk, lab_pk | — | sí |
| `buildings_create` | `/risk/<int:org_pk>/buildings/create/` | pagina | `risk_management.views.buildings_actions` | `risk_management/buildings.html` | org_pk | sí | — |
| `buildings_list` | `/risk/<int:org_pk>/buildings/` | pagina | `risk_management.views.buildings_view` | `risk_management/building_list.html` | org_pk | sí | — |
| `buildings_update` | `/risk/<int:org_pk>/buildings/update/<int:pk>/` | pagina | `risk_management.views.buildings_actions` | `risk_management/buildings.html` | org_pk, pk | sí | — |
| `incident_create` | `/risk/<int:org_pk>/incident/<int:building_pk>/create/` | pagina | `risk_management.incidents.IncidentReportCreate` | `risk_management/incidentreport_form.html` | org_pk, building_pk | sí | — |
| `incident_delete` | `/risk/<int:org_pk>/incident/<int:building_pk>/<int:pk>/delete/` | pagina | `risk_management.incidents.IncidentReportDelete` | `risk_management/incidentreport_confirm_delete.html` | org_pk, building_pk, pk | sí | — |
| `incident_detail` | `/risk/<int:org_pk>/incident/<int:building_pk>/<int:pk>/detail/` | pagina | `risk_management.incidents.IncidentReportDetail` | `risk_management/incidentreport_detail.html` | org_pk, building_pk, pk | — | — |
| `incident_list` | `/risk/<int:org_pk>/incident/<int:building_pk>/list/` | pagina | `risk_management.incidents.IncidentReportList` | `risk_management/incidentreport_list.html` | org_pk, building_pk | sí | — |
| `incident_update` | `/risk/<int:org_pk>/incident/<int:building_pk>/<int:pk>/update/` | pagina | `risk_management.incidents.IncidentReportEdit` | `risk_management/incidentreport_form.html` | org_pk, building_pk, pk | sí | — |
| `iper_create` | `/risk/<int:org_pk>/iper/create/` | pagina | `risk_management.iper_views.IPERAssessmentCreate` | `risk_management/iper_form.html` | org_pk | — | — |
| `iper_dashboard` | `/risk/<int:org_pk>/iper/dashboard/` | pagina | `risk_management.iper_views.IPERDashboard` | `risk_management/iper_dashboard.html` | org_pk | — | — |
| `iper_delete` | `/risk/<int:org_pk>/iper/<int:pk>/delete/` | pagina | `risk_management.iper_views.IPERAssessmentDelete` | `risk_management/iperassessment_confirm_delete.html` | org_pk, pk | — | — |
| `iper_detail` | `/risk/<int:org_pk>/iper/<int:pk>/detail/` | pagina | `risk_management.iper_views.IPERAssessmentDetail` | `risk_management/iper_detail.html` | org_pk, pk | sí | — |
| `iper_history` | `/risk/<int:org_pk>/iper/history/` | pagina | `risk_management.iper_views.IPERHistory` | `risk_management/iper_history.html` | org_pk | — | sí |
| `iper_list` | `/risk/<int:org_pk>/iper/list/` | pagina | `risk_management.iper_views.IPERAssessmentList` | `risk_management/iper_list.html` | org_pk | sí | sí |
| `iper_update` | `/risk/<int:org_pk>/iper/<int:pk>/update/` | pagina | `risk_management.iper_views.IPERAssessmentUpdate` | `risk_management/iper_form.html` | org_pk, pk | — | — |
| `regents` | `/risk/<int:org_pk>/regents/` | pagina | `risk_management.views.regent_view` | `risk_management/regents.html` | org_pk | sí | — |
| `risk_report` | `/risk/<int:org_pk>/reports/` | pagina | `risk_management.views.RiskZoneReport` | `report/base_report_organizations.html` | org_pk | — | — |
| `riskzone_create` | `/risk/<int:org_pk>/riskzone/create/` | pagina | `risk_management.views.ZoneCreate` | `risk_management/riskzone_form.html` | org_pk | sí | sí |
| `riskzone_delete` | `/risk/<int:org_pk>/riskzone/<int:pk>/delete/` | pagina | `risk_management.views.ZoneDelete` | `risk_management/riskzone_confirm_delete.html` | org_pk, pk | sí | sí |
| `riskzone_detail` | `/risk/<int:org_pk>/riskzone/<int:pk>/detail/` | pagina | `risk_management.views.ZoneDetail` | `risk_management/riskzone_detail.html` | org_pk, pk | sí | sí |
| `riskzone_list` | `/risk/<int:org_pk>/riskzone/list/` | pagina | `risk_management.views.ListZone` | `risk_management/riskzone_list.html` | org_pk | sí | sí |
| `riskzone_update` | `/risk/<int:org_pk>/riskzone/<int:pk>/update/` | pagina | `risk_management.views.ZoneEdit` | `risk_management/riskzone_form.html` | org_pk, pk | sí | sí |
| `structures_create` | `/risk/<int:org_pk>/structures/create/` | pagina | `risk_management.views.structure_actions` | `risk_management/structure_form.html` | org_pk | sí | — |
| `structures_list` | `/risk/<int:org_pk>/structures/` | pagina | `risk_management.views.structure_view` | `risk_management/structure_list.html` | org_pk | sí | — |
| `structures_update` | `/risk/<int:org_pk>/structures/update/<int:pk>/` | pagina | `risk_management.views.structure_actions` | `risk_management/structure_form.html` | org_pk, pk | sí | — |
| `workday_list` | `/risk/<int:org_pk>/workdays/<int:risk_zone>/` | pagina | `risk_management.views.workday_view` | `risk_management/workday_list.html` | org_pk, risk_zone | sí | — |
| `zone_dashboard` | `/risk/<int:org_pk>/dashboard/` | pagina | `risk_management.views.ZoneDashboard` | `risk_management/risk_graphics.html` | org_pk | sí | — |
| `iper_catalog_add` | `/risk/<int:org_pk>/iper/catalog/add/` | parcial | `risk_management.iper_views.iper_catalog_add` | — | org_pk | — | — |
| `zone_type_add` | `/risk/<int:org_pk>/zone_type/add/` | parcial | `risk_management.views.add_zone_type_view` | — | org_pk | — | sí |

### sga — 29 páginas, 6 sin prueba

| Nombre | Patrón | Categoría | Vista | Plantilla | kwargs | Selenium | Pruebas |
|---|---|---|---|---|---|:-:|:-:|
| `accept_substance` | `/sga/<int:org_pk>/accept_substance/<int:pk>/` | accion | `sga.views.substance.views.approve_substances` | — | org_pk, pk | sí | sí |
| `add_observation` | `/sga/<int:org_pk>/substance/add_observation/<int:substance>/` | accion | `sga.views.substance.views.add_observation` | — | org_pk, substance | — | sí |
| `delete_sgalabel` | `/sga/<int:org_pk>/delete_sgalabel/<int:pk>` | accion | `sga.views.editor.delete_sgalabel` | — | org_pk, pk | — | — |
| `delete_substance` | `/sga/<int:org_pk>/delete_substance/<int:pk>/` | accion | `sga.views.substance.views.delete_substance` | — | org_pk, pk | — | sí |
| `sgalabel_create` | `/sga/<int:org_pk>/sgalabel/create/` | accion | `sga.views.editor.create_sgalabel` | — | org_pk | — | — |
| `barcode_from_number` | `/sga/<int:org_pk>/barcode/<str:code>/` | descarga | `sga.views.editor.get_barcode_from_number` | — | org_pk, code | — | — |
| `engine_label_preview` | `/sga/<int:org_pk>/engine_label_preview/<int:pk>` | descarga | `sga.views.editor.engine_label_preview` | — | org_pk, pk | — | — |
| `generate_label` | `/sga/<int:org_pk>/generate_label/<int:pk>/` | descarga | `sga.views.substance.views.generate_label` | — | org_pk, pk | — | — |
| `security_leaf_pdf` | `/sga/<int:org_pk>/substance/get_security_leaf/<int:substance>/` | descarga | `sga.views.substance.views.security_leaf_pdf` | — | org_pk, substance | — | — |
| `add_sga_provider` | `/sga/<int:org_pk>/substance/provider/` | json | `sga.views.substance.views.add_sga_provider` | — | org_pk | — | sí |
| `delete_observation` | `/sga/<int:org_pk>/substance/deleta_observation/` | json | `sga.views.substance.views.delete_observation` | — | org_pk | — | sí |
| `get_company` | `/sga/<int:org_pk>/sgalabel/get_company/<int:pk>` | json | `sga.views.editor.get_company` | — | org_pk, pk | — | — |
| `get_preview` | `/sga/<int:org_pk>/get_preview/<int:pk>` | json | `sga.views.editor.get_preview` | — | org_pk, pk | — | — |
| `get_recipient_size` | `/sga/<int:org_pk>/sgalabel/get_recipient_size/<int:pk>` | json | `sga.views.editor.get_recipient_size` | — | org_pk, pk | — | — |
| `get_sgacomplement_by_substance` | `/sga/<int:org_pk>/sgalabel/get_sgacomplement_by_substance/<int:pk>` | json | `sga.views.editor.get_sgacomplement_by_substance` | — | org_pk, pk | — | — |
| `remove_company` | `/sga/<int:org_pk>/company/remove/<int:pk>/` | json | `sga.views.editor.remove_company` | — | org_pk, pk | — | — |
| `sds_task_status` | `/sga/<int:org_pk>/substance/sds_task_status/` | json | `sga.views.substance.views.sds_task_status` | — | org_pk | — | sí |
| `update_observation` | `/sga/<int:org_pk>/substance/update_observation/` | json | `sga.views.substance.views.update_observation` | — | org_pk | — | sí |
| `upload_sds` | `/sga/<int:org_pk>/substance/upload_sds/` | json | `sga.views.substance.views.upload_sds` | — | org_pk | — | sí |
| `upload_sds_pk` | `/sga/<int:org_pk>/substance/upload_sds/<int:pk>/` | json | `sga.views.substance.views.upload_sds` | — | org_pk, pk | — | sí |
| `add_company` | `/sga/<int:org_pk>/company/add/` | pagina | `sga.views.editor.create_company` | `company/add_company.html` | org_pk | — | — |
| `add_danger_indication` | `/sga/<int:org_pk>/substance/add_danger_indication/` | pagina | `sga.views.substance.views.add_sga_complements` | `sga/substance/sga_components.html` | org_pk | — | — |
| `add_personal` | `/sga/<int:org_pk>/labels/` | pagina | `sga.views.editor.create_personal_template` | `personal_template.html` | org_pk | sí | — |
| `add_prudence_advice` | `/sga/<int:org_pk>/substance/add_prudence_advice/` | pagina | `sga.views.substance.views.add_sga_complements` | `sga/substance/sga_components.html` | org_pk | — | sí |
| `add_recipient_size` | `/sga/<int:org_pk>/add_recipient_size/` | pagina | `sga.views.editor.create_recipient` | `add_recipient_size.html` | org_pk | — | — |
| `add_warning_word` | `/sga/<int:org_pk>/substance/add_warning_words/` | pagina | `sga.views.substance.views.add_sga_complements` | `sga/substance/sga_components.html` | org_pk | — | sí |
| `approved_substance` | `/sga/<int:org_pk>/approved_substance/` | pagina | `sga.views.substance.views.get_list_substances` | `sga/substance/check_substances.html` | org_pk | sí | sí |
| `create_sustance` | `/sga/<int:org_pk>/sustance/create/` | pagina | `sga.views.substance.views.create_edit_sustance` | `sga/substance/create_sustance.html` | org_pk | sí | sí |
| `danger_indications` | `/sga/<int:org_pk>/substance/danger_indications/` | pagina | `sga.views.substance.views.view_danger_indications` | `sga/substance/danger_indication.html` | org_pk | — | sí |
| `danger_substance` | `/sga/<int:org_pk>/danger_substance/` | pagina | `sga.views.danger_substance.views.danger_substance_view` | `danger_substance/danger_substance.html` | org_pk | sí | — |
| `danger_substance_category` | `/sga/<int:org_pk>/danger_subtance_category/` | pagina | `sga.views.danger_substance.views.danger_substance_category_view` | `danger_substance/danger_substance_category.html` | org_pk | sí | — |
| `detail_substance` | `/sga/<int:org_pk>/detail_substance/<int:pk>/` | pagina | `sga.views.substance.views.detail_substance` | `sga/substance/detail.html` | org_pk, pk | sí | sí |
| `edit_company` | `/sga/<int:org_pk>/company/edit/<int:pk>/` | pagina | `sga.views.editor.edit_company` | `company/add_company.html` | org_pk, pk | — | — |
| `edit_personal` | `/sga/<int:org_pk>/edit_personal/<int:pk>` | pagina | `sga.views.editor.edit_personal_template` | `template_edit.html` | org_pk, pk | sí | — |
| `editor` | `/sga/<int:org_pk>/template_editor` | pagina | `sga.views.editor.template_editor` | `template_editor.html` | org_pk | sí | — |
| `get_companies` | `/sga/<int:org_pk>/company/list/` | pagina | `sga.views.editor.get_companies` | `company/list_company.html` | org_pk | sí | — |
| `get_substance` | `/sga/<int:org_pk>/get_substance/` | pagina | `sga.views.substance.views.get_substances` | `sga/substance/list_substance.html` | org_pk | sí | sí |
| `prudence_advices` | `/sga/<int:org_pk>/substance/prudence_advices/` | pagina | `sga.views.substance.views.view_prudence_advices` | `sga/substance/prudence_advice.html` | org_pk | — | sí |
| `recipient_size` | `/sga/<int:org_pk>/substance/recipient/` | pagina | `sga.views.substance.views.view_recipient_size` | `sga/recipient_size.html` | org_pk | — | — |
| `send_to_review` | `/sga/<int:org_pk>/substance/send_to_review/<int:substance>/` | pagina | `sga.views.substance.views.sent_to_review` | `sga/substance/send_to_review.html` | org_pk, substance | — | sí |
| `sgalabel_step_one` | `/sga/<int:org_pk>/sgalabel/step_one/<int:pk>` | pagina | `sga.views.editor.sgalabel_step_one` | `sgalabel/step_one.html` | org_pk, pk | — | — |
| `sgalabel_step_two` | `/sga/<int:org_pk>/sgalabel/step_two/<int:pk>` | pagina | `sga.views.editor.sgalabel_step_two` | `sgalabel/step_two.html` | org_pk, pk | sí | — |
| `step_four` | `/sga/<int:org_pk>/substance/step_four/<int:substance>/` | pagina | `sga.views.substance.views.step_four` | `sga/substance/step_four.html` | org_pk, substance | — | sí |
| `step_one` | `/sga/<int:org_pk>/substance/step_one/<int:pk>/` | pagina | `sga.views.substance.views.create_edit_sustance` | `sga/substance/create_sustance.html` | org_pk, pk | sí | sí |
| `update_danger_indication` | `/sga/<int:org_pk>/substance/update_danger_indication/<str:pk>/` | pagina | `sga.views.substance.views.change_danger_indication` | `sga/substance/sga_components.html` | org_pk, pk | — | sí |
| `update_prudence_advice` | `/sga/<int:org_pk>/substance/update_prudence_advice/<int:pk>/` | pagina | `sga.views.substance.views.change_prudence_advice` | `sga/substance/sga_components.html` | org_pk, pk | — | sí |
| `update_substance` | `/sga/<int:org_pk>/update_substance/<int:pk>/` | pagina | `sga.views.substance.views.create_edit_sustance` | `sga/substance/create_sustance.html` | org_pk, pk | — | sí |
| `update_warning_word` | `/sga/<int:org_pk>/substance/update_warning_words/<int:pk>/` | pagina | `sga.views.substance.views.change_warning_word` | `sga/substance/sga_components.html` | org_pk, pk | — | sí |
| `warning_words` | `/sga/<int:org_pk>/substance/warning_words/` | pagina | `sga.views.substance.views.view_warning_words` | `sga/substance/warning_words.html` | org_pk | sí | sí |
| `index_editor` | `/sga/<int:org_pk>/editor_sga` | parcial | `sga.views.editor.render_editor_sga` | — | org_pk | — | — |

