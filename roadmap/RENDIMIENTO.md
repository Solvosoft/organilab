# Rendimiento de Organilab

Generado con `make perf-report` a partir de `roadmap/.perf/`. No editar a mano.
Los tiempos son de la suite de pruebas (base pequeña, live server de Django): sirven para **comparar** vistas entre sí, no como latencia de producción. Si la corrida fue `make coverage-perf`, los tiempos incluyen la sobrecarga del trazado de coverage (2–3×); el número de consultas SQL no se ve afectado.

- Fecha: 2026-10-12 22:01 · commit `362ac77bd` · x86_64, 8 núcleos, Python 3.13.5
- 5853 peticiones medidas sobre 787 rutas; 2876 pruebas.

## Vistas más lentas (p95)

| Ruta | Método | n | p50 ms | p95 ms | máx ms | CPU p95 ms | SQL p95 ms | consultas máx |
|------|--------|--:|-------:|-------:|-------:|-----------:|-----------:|--------------:|
| `laboratory:reports_shelf_objects` | GET | 5 | 320.5 | 7667.4 | 7667.4 | 7245.4 | 127.1 | 159 |
| `laboratory:generate_shelfobject_label` | GET | 3 | 68.7 | 4571.2 | 4571.2 | 2248.3 | 26.6 | 25 |
| `sga:security_leaf_pdf` | GET | 2 | 22.9 | 4375.9 | 4375.9 | 3944.0 | 10.5 | 12 |
| `laboratory:api-labview-tree-list` | GET | 90 | 2912.9 | 4110.0 | 4219.0 | 3826.7 | 165.8 | 53 |
| `laboratory:rooms_list` | GET | 47 | 1693.3 | 3282.4 | 3353.8 | 3074.7 | 226.2 | 157 |
| `sga:generate_label` | GET | 6 | 140.9 | 2655.7 | 2655.7 | 796.6 | 20.5 | 19 |
| `platform:alertrule_list` | GET | 4 | 1827.8 | 1864.6 | 1864.6 | 1798.7 | 112.8 | 61 |
| `sga:create_sustance` | POST | 4 | 373.5 | 1359.1 | 1359.1 | 1325.5 | 37.6 | 50 |
| `laboratory:api-reactive-detail` | DELETE | 2 | 243.7 | 1332.0 | 1332.0 | 203.5 | 1115.9 | 70 |
| `admin:sga_dangerindication_add` | GET | 1 | 1261.4 | 1261.4 | 1261.4 | 1210.8 | 87.2 | 160 |
| `laboratory:labview` | GET | 20 | 1091.8 | 1255.7 | 1343.1 | 1135.9 | 97.8 | 80 |
| `laboratory:mylabs` | GET | 6 | 270.8 | 1234.9 | 1234.9 | 1120.8 | 65.4 | 66 |
| `sga:editor` | GET | 4 | 249.1 | 1193.6 | 1193.6 | 1162.8 | 99.6 | 47 |
| `sga:update_danger_indication` | GET | 2 | 1102.7 | 1156.9 | 1156.9 | 998.9 | 223.7 | 354 |
| `sga:editor` | POST | 2 | 124.7 | 1113.0 | 1113.0 | 1071.6 | 61.2 | 43 |
| `laboratory:api-shelfobject-hcode-detail` | PUT | 1 | 1110.8 | 1110.8 | 1110.8 | 67.6 | 1036.7 | 20 |
| `sga:add_danger_indication` | GET | 1 | 1068.6 | 1068.6 | 1068.6 | 951.5 | 221.6 | 344 |
| `riskmanagement:riskzone_list` | GET | 19 | 203.1 | 1025.8 | 1060.4 | 941.6 | 64.4 | 69 |
| `laboratory:api-labview-furniture-detail` | GET | 4 | 738.0 | 981.3 | 981.3 | 930.5 | 54.5 | 33 |
| `admin:auth_user_delete` | POST | 1 | 979.1 | 979.1 | 979.1 | 928.1 | 85.9 | 127 |
| `dangerindicationchart-detail` | GET | 5 | 848.5 | 974.6 | 974.6 | 736.1 | 557.0 | 129 |
| `laboratory:equipment_shelfobject_detail` | GET | 5 | 667.5 | 918.2 | 918.2 | 824.0 | 70.3 | 64 |
| `academic:update_step` | GET | 9 | 520.8 | 909.3 | 909.3 | 877.4 | 41.9 | 54 |
| `laboratory:api-labview-furniture-remove-row` | POST | 3 | 103.6 | 867.8 | 867.8 | 802.6 | 58.3 | 37 |
| `laboratory:load_archive_create_shelfobjects` | POST | 2 | 321.4 | 850.2 | 850.2 | 759.2 | 104.0 | 110 |

## Vistas con más consultas SQL

Más de 50 consultas en una petición, o un rango min–máx amplio entre peticiones de la misma ruta, sugiere N+1 (consultas que crecen con los datos).

| Ruta | Método | n | consultas min–máx | SQL p95 ms | N+1? |
|------|--------|--:|------------------:|-----------:|:----:|
| `sga:update_danger_indication` | GET | 2 | 348–354 | 223.7 | ⚠ |
| `sga:add_danger_indication` | GET | 1 | 344–344 | 221.6 | ⚠ |
| `laboratory:api-shelfobject-move-shelfobject-to-shelf` | POST | 18 | 14–168 | 209.9 | ⚠ |
| `laboratory:organization_actions` | POST | 8 | 6–165 | 126.5 | ⚠ |
| `admin:sga_dangerindication_add` | GET | 1 | 160–160 | 87.2 | ⚠ |
| `laboratory:reports_shelf_objects` | GET | 5 | 14–159 | 127.1 | ⚠ |
| `laboratory:rooms_list` | GET | 47 | 69–157 | 226.2 | ⚠ |
| `admin:auth_user_changelist` | POST | 1 | 135–135 | 143.4 | ⚠ |
| `laboratory:delete_organization` | POST | 2 | 61–133 | 131.5 | ⚠ |
| `dangerindicationchart-detail` | GET | 5 | 6–129 | 557.0 | ⚠ |
| `admin:auth_user_delete` | POST | 1 | 127–127 | 85.9 | ⚠ |
| `laboratory:api-shelfobject-transfer-in-approve` | POST | 9 | 44–117 | 139.5 | ⚠ |
| `auth_and_perms:list_rol_by_org` | GET | 7 | 5–116 | 90.6 | ⚠ |
| `laboratory:load_archive_create_shelfobjects` | POST | 2 | 53–110 | 104.0 | ⚠ |
| `laboratory:api-dangers-table-list` | GET | 4 | 0–106 | 57.2 | ⚠ |
| `laboratory:api-danger-indication-list` | GET | 3 | 6–104 | 53.9 | ⚠ |
| `auth_and_perms:api_organization_buttons` | GET | 6 | 5–93 | 88.8 | ⚠ |
| `auth_and_perms:organizationManager` | GET | 49 | 42–91 | 77.0 | ⚠ |
| `whiteorganchart-detail` | GET | 5 | 6–88 | 480.3 | ⚠ |
| `laboratory:labview` | GET | 20 | 12–80 | 97.8 | ⚠ |
| `laboratory:my_reservations` | GET | 5 | 37–77 | 70.5 | ⚠ |
| `report:create_report_request` | GET | 19 | 11–75 | 79.0 | ⚠ |
| `reservations_management:reservations_list` | GET | 10 | 59–75 | 80.5 | ⚠ |
| `furniture-list` | GET | 64 | 5–74 | 54.1 | ⚠ |
| `shelf-list` | GET | 64 | 5–74 | 51.2 | ⚠ |

## Tiempo total acumulado por ruta

Dónde se va el tiempo de la suite: una ruta barata pero muy llamada pesa más que una cara llamada una vez.

| Ruta | Método | n | total s | p50 ms |
|------|--------|--:|--------:|-------:|
| `laboratory:api-labview-tree-list` | GET | 90 | 193.32 | 2912.9 |
| `laboratory:rooms_list` | GET | 47 | 83.31 | 1693.3 |
| `pending_tasks:view_task` | GET | 287 | 40.16 | 136.3 |
| `notifications` | GET | 759 | 34.68 | 43.9 |
| `index` | GET | 461 | 20.31 | 37.9 |
| `pending_tasks:api-pending_tasks-list` | GET | 280 | 19.65 | 68.1 |
| `laboratory:labview` | GET | 20 | 18.23 | 1091.8 |
| `auth_and_perms:organizationManager` | GET | 49 | 15.86 | 317.8 |
| `laboratory:api-equipment-list` | GET | 40 | 12.35 | 342.6 |
| `laboratory:labindex` | GET | 55 | 11.12 | 197.7 |
| `laboratory:api-shelfobjecttable-list` | GET | 97 | 10.06 | 97.0 |
| `laboratory:api-shelfobject-create-shelfobject` | POST | 40 | 8.93 | 190.9 |
| `laboratory:reports_shelf_objects` | GET | 5 | 8.83 | 320.5 |
| `laboratory:rooms_create` | GET | 34 | 8.63 | 248.9 |
| `home` | GET | 247 | 7.84 | 24.6 |
| `academic:procedure_list` | GET | 34 | 7.47 | 183.1 |
| `laboratory:sustance_list` | GET | 13 | 7.44 | 541.2 |
| `riskmanagement:riskzone_list` | GET | 19 | 7.42 | 203.1 |
| `djgentelella-js-catalog` | GET | 102 | 7.04 | 63.8 |
| `furniture-list` | GET | 64 | 6.79 | 122.4 |
| `shelf-list` | GET | 64 | 6.58 | 120.5 |
| `javascript-catalog` | GET | 102 | 6.38 | 58.9 |
| `available-container-search-list` | GET | 59 | 5.82 | 107.7 |
| `lab_room-list` | GET | 58 | 5.55 | 104.4 |
| `sga:generate_label` | GET | 6 | 5.23 | 140.9 |

## Pruebas más lentas

| Prueba | Selenium | s | CPU s | RSS después MiB |
|--------|:--------:|--:|------:|----------------:|
| `laboratory.tests.labview.test_permission_matrix.LabviewPermissionMatrixTest.test_the_tree_announces_exactly_the_capabilities_the_user_has` |  | 93.792 | 87.097 | 361.3 |
| `academic.tests.selenium_tests.test_procedure_template.ProcedureTemplateSeleniumTest.test_procedure_crud` | ✓ | 86.531 | 21.249 | 299.6 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_objects.ObjectSeleniumTest.test_add_reactive_object_classification` | ✓ | 51.588 | 8.949 | 339.2 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_catalog_crud.LaboratoryCatalogsCrudTest.test_lab_catalogs_flow` | ✓ | 40.122 | 11.709 | 299.5 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column.ButtonsActionsTableColumn.test_reserve_shelfobject` | ✓ | 38.448 | 12.047 | 331.3 |
| `laboratory.tests.selenium_tests.manage_organizations.test_collapse_org_name_buttons_box.ButtonBoxCollapseOrgNameTest.test_add_laboratory_to_org` | ✓ | 35.309 | 10.639 | 316.7 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column.ButtonsActionsTableColumn.test_move_shelfobject_with_use_source_container` | ✓ | 34.741 | 14.529 | 331.3 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column.ButtonsActionsTableColumn.test_move_shelfobject_with_clone_container` | ✓ | 34.629 | 13.298 | 331.2 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_wrapper_top.CreateShelfObject.test_create_shelfobject_reactive_with_clone_container` | ✓ | 34.458 | 14.162 | 338.9 |
| `laboratory.tests.selenium_tests.informs.test_inform_template.InformsSeleniumTest.test_add_radio_derb` | ✓ | 33.631 | 9.002 | 298.7 |
| `laboratory.tests.selenium_tests.informs.test_inform_template.InformsSeleniumTest.test_add_checkbox_derb` | ✓ | 33.347 | 8.713 | 296.6 |
| `laboratory.tests.selenium_tests.manage_organizations.test_collapse_org_name_buttons_box.ButtonBoxCollapseOrgNameTest.test_add_role_to_org_copy_permissions_from_others_roles` | ✓ | 33.246 | 8.06 | 316.7 |
| `sga.tests.selenium_tests.test_danger_substance.DangerSubstanceCrudTest.test_danger_substance_catalog_flow` | ✓ | 32.855 | 6.607 | 352.1 |
| `laboratory.tests.selenium_tests.informs.test_inform_template.InformsSeleniumTest.test_add_password_derb` | ✓ | 32.787 | 8.366 | 298.6 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column.ButtonsActionsTableColumn.test_move_shelfobject_with_available_container` | ✓ | 32.259 | 13.372 | 331.2 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_wrapper_top.CreateShelfObject.test_create_shelfobject_reactive_with_use_selected_container` | ✓ | 32.169 | 12.177 | 338.9 |
| `laboratory.tests.selenium_tests.informs.test_inform_template.InformsSeleniumTest.test_add_number_derb` | ✓ | 31.853 | 7.659 | 298.3 |
| `laboratory.tests.selenium_tests.manage_organizations.test_buttons_box_org.ButtonBoxOrgTest.test_change_org_parent` | ✓ | 31.369 | 10.296 | 340.0 |
| `laboratory.tests.selenium_tests.laboratory_view.test_shelfobject_detail_actions.ShelfObjectInfoButtonsActions.test_change_shelfobject_status` | ✓ | 30.721 | 10.757 | 328.3 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_objects.ObjectSeleniumTest.test_add_reactive_object_precursor` | ✓ | 30.556 | 7.884 | 339.5 |
| `laboratory.tests.selenium_tests.manage_organizations.test_laboratory_tab.LaboratoryTabTest.test_relate_user_to_org_and_lab_from_tab_lab` | ✓ | 29.631 | 6.801 | 334.0 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap5_reservaciones.Cap5ManageReservationsTest.test_approve_reject_reservation` | ✓ | 29.361 | 8.931 | 336.7 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column.ButtonsActionsTableColumn.test_move_shelfobject_with_new_based_source_container` | ✓ | 29.36 | 12.468 | 331.3 |
| `laboratory.tests.selenium_tests.manage_organizations.test_laboratory_tab.LaboratoryTabTest.test_add_permission_rol_to_user_from_tab_lab` | ✓ | 29.122 | 7.574 | 333.9 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_laboratoryroom.LabRoomSeleniumTest.test_laboratory_room_crud` | ✓ | 28.491 | 13.614 | 339.3 |

## Pruebas que más memoria dejan en el proceso

Crecimiento de RSS durante la prueba (lo que no se libera se acumula en el worker).

| Prueba | Δ RSS MiB | RSS después MiB |
|--------|----------:|----------------:|
| `laboratory.tests.labview.test_permission_matrix.LabviewPermissionMatrixTest.test_the_tree_announces_exactly_the_capabilities_the_user_has` | 63.9 | 361.3 |
| `laboratory.tests.labview.test_tree_queries.TreeQueryShapeTest.test_the_tree_does_not_grow_with_the_map` | 19.7 | 329.9 |
| `academic.tests.selenium_tests.test_my_procedure.MyProcedureSeleniumTest.test_download_myprocedure_pdf` | 16.3 | 314.7 |
| `organilab_test.tests.test_url_smoke.LaboratoryUrlSmokeTest.test_paginas_responden` | 16.3 | 319.4 |
| `laboratory.tests.test_cov_views_reports.ReportShelfObjectsTest.test_pk_cero_incluye_todos_los_objetos_del_laboratorio` | 13.2 | 306.3 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_wrapper_top.CreateShelfObject.test_approve_transfer_in_shelfobject_with_available_container` | 12.7 | 314.0 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_register_users.RegisterUserQRSeleniumTest.test_downlooad_register_user_qr` | 12.6 | 316.7 |
| `report.tests.test_riskzones_report.HazardMapReportTest.test_html_y_pdf` | 11.8 | 320.7 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_download_incident` | 11.5 | 361.5 |
| `academic.tests.selenium_tests.test_procedure_template.ProcedureTemplateSeleniumTest.test_procedure_crud` | 10.7 | 299.6 |
| `laboratory.tests.selenium_tests.labview_new.test_smoke_navigation.LabviewSmokeNavigationTest.test_a_deep_link_lands_on_the_shelf_without_a_single_click` | 10.3 | 331.2 |
| `laboratory.tests.test_cov_views_djgeneric.ReportListViewFormatosTest.test_exporta_pdf` | 10.0 | 303.3 |
| `laboratory.tests.selenium_tests.labview_new.test_smoke_navigation.LabviewSmokeNavigationTest.test_collapse_all_folds_every_room` | 9.7 | 341.4 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_wrapper_top.CreateShelfObject.test_create_shelfobject_material` | 9.7 | 338.7 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_wrapper_top.CreateShelfObject.test_create_shelfobject_equipment` | 9.7 | 329.0 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap3_cajas.Cap3BoxesTest.test_create_box` | 9.7 | 326.4 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column.ButtonsActionsTableColumn.test_download_shelfobject_info` | 9.4 | 330.6 |
| `laboratory.tests.labview.test_tree_queries.TreeQueryShapeTest.test_a_missing_qr_is_created_once_and_never_again` | 8.7 | 299.6 |
| `laboratory.tests.selenium_tests.informs.test_informs.InformSeleniumTest.test_add_inform` | 8.5 | 296.6 |
| `laboratory.tests.selenium_tests.informs.test_inform_template.InformsSeleniumTest.test_add_checkbox_derb` | 8.4 | 296.6 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column.ButtonsActionsTableColumn.test_decrease_shelfobject` | 8.4 | 307.1 |
| `academic.tests.selenium_tests.test_my_procedure.MyProcedureSeleniumTest.test_add_my_procedure` | 8.4 | 296.5 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap3_cajas.Cap3BoxesTest.test_increase_box` | 8.3 | 334.9 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap2_laboratorios.Cap2InventoryTest.test_view_shelf_object_details` | 8.3 | 358.0 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap2_laboratorios.Cap2LabStructureTest.test_view_lab_structure` | 8.2 | 348.4 |

## Memoria del navegador (chromedriver + Chrome)

| Prueba | RSS navegador MiB |
|--------|------------------:|
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_wrapper_top.CreateShelfObject.test_view_containers_by_shelf` | 2360.3 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_download_incident` | 2142.5 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column.ButtonsActionsTableColumn.test_view_shelfobject_logs` | 2126.5 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_wrapper_top.CreateShelfObject.test_go_to_objects_by_furniture_report` | 2120.4 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap5_reservaciones.Cap5ManageReservationsTest.test_return_product_flow` | 2086.5 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap2_laboratorios.Cap2InventoryTest.test_view_shelf_object_logs` | 2054.7 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap5_reservaciones.Cap5ManageReservationsTest.test_return_products` | 2054.2 |
| `laboratory.tests.selenium_tests.laboratory_view.test_shelfobject_detail_actions.ShelfObjectInfoButtonsActions.test_view_equipment_details` | 2054.0 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_objects.ObjectSeleniumTest.test_search_reactive` | 2041.1 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_edit_regent` | 2039.8 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap3_cajas.Cap3BoxesTest.test_increase_box` | 2031.1 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_remove_risk` | 2029.5 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_edit_risk` | 2017.7 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap2_laboratorios.Cap2InventoryTest.test_view_shelf_objects` | 2012.0 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_add_regent` | 1983.7 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_objects.ObjectFeaturesSeleniumTest.test_view_object_features` | 1969.4 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_update_risk_two` | 1961.3 |
| `academic.tests.selenium_tests.test_my_procedure.MyProcedureSeleniumTest.test_delete_observation_my_procedure` | 1951.3 |
| `academic.tests.selenium_tests.test_my_procedure.MyProcedureSeleniumTest.test_delete_myprocedure` | 1946.2 |
| `laboratory.tests.selenium_tests.informs.test_inform_template.InformsSeleniumTest.test_delete_inform_template` | 1940.9 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_delete_building` | 1931.7 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_delete_structure` | 1917.0 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_delete_regent` | 1903.4 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_objects.ObjectSeleniumTest.test_view_material` | 1897.0 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_add_risk` | 1895.2 |

## Clases con setUpClass/tearDownClass más caros

Fixtures, arranque del navegador, live server. Se paga una vez por clase y por worker.

| Clase | veces | setUp s | tearDown s |
|-------|------:|--------:|-----------:|
| `reservations_management.tests.test_forms_signals_api.ApiProductoReservadoTest` | 1 | 25.96 | 0.01 |
| `organilab_test.tests.test_url_smoke.AmbientalUrlSmokeTest` | 1 | 20.82 | 0.0 |
| `organilab_test.tests.test_url_smoke.AcademicUrlSmokeTest` | 1 | 19.95 | 0.01 |
| `organilab_test.tests.test_url_smoke.RiskUrlSmokeTest` | 1 | 19.87 | 0.01 |
| `organilab_test.tests.test_url_smoke.SgaUrlSmokeTest` | 1 | 11.8 | 0.01 |
| `organilab_test.tests.test_url_smoke.LaboratoryUrlSmokeTest` | 1 | 10.94 | 0.01 |
| `organilab_test.tests.test_url_smoke.ReportUrlSmokeTest` | 1 | 10.88 | 0.01 |
| `organilab_test.tests.test_url_smoke.OrgUrlSmokeTest` | 1 | 10.83 | 0.01 |
| `academic.tests.selenium_tests.test_procedure_template.ProcedureTemplateSeleniumTest` | 1 | 10.34 | 0.31 |
| `reservations_management.tests.test_functions.TareaDeDescuentoTest` | 1 | 10.55 | 0.01 |
| `reservations_management.tests.test_tasks.DescontarStockTest` | 1 | 10.45 | 0.01 |
| `risk_management.tests.test_zonetype.RiskZoneTest` | 1 | 10.27 | 0.0 |
| `reservations_management.tests.test_functions.ProductoYCantidadTest` | 1 | 10.2 | 0.01 |
| `risk_management.tests.test_incident.IncidentReportTest` | 1 | 10.18 | 0.01 |
| `reservations_management.tests.test_forms_signals_api.FormularioDevolucionTest` | 1 | 10.16 | 0.01 |
| `reservations_management.tests.test_functions.AsignacionDeCajasTest` | 1 | 10.14 | 0.01 |
| `reservations_management.tests.test_views_management.GestionarReservacionTest` | 1 | 10.14 | 0.01 |
| `reservations_management.tests.test_functions.FechasYSuperposicionTest` | 1 | 10.13 | 0.01 |
| `reservations_management.tests.test_views_management.DevolverProductoTest` | 1 | 10.12 | 0.01 |
| `reservations_management.tests.test_views_management.CerrarReservacionTest` | 1 | 10.05 | 0.01 |
| `reservations_management.tests.test_forms_signals_api.SenalesTest` | 1 | 10.06 | 0.0 |
| `reservations_management.tests.test_functions.StockDisponibleTest` | 1 | 10.04 | 0.0 |
| `reservations_management.tests.test_functions.ValidarReservacionTest` | 1 | 10.01 | 0.01 |
| `risk_management.tests.test_iper.IPERViewTest` | 1 | 10.01 | 0.01 |
| `reservations_management.tests.test_tasks.DescontarCajasTest` | 1 | 9.97 | 0.01 |

## Reportes contra volumen de datos

Cada reporte registrado, generado con la base sembrada a varias escalas (`seed_volume`). «Crecimiento» compara la escala mayor con la menor frente al crecimiento de los datos: > 1 es superlineal.

| Reporte | Formato | Escala | filas base | s | consultas | pico MiB | archivo KiB | estado |
|---------|---------|-------:|-----------:|--:|----------:|---------:|------------:|--------|
| `reactive_precursor` | html | 1 | 255 | 0.13 | 54 | 7.5 | 1 | ok |
| `reactive_precursor` | xlsx | 1 | 255 | 0.18 | 55 | 10.2 | 5 | ok |
| `reactive_precursor` | pdf | 1 | 255 | 0.41 | 55 | 18.7 | 12 | ok |
| `report_laboratory_room` | html | 1 | 255 | 1.37 | 1550 | 7.5 | 23 | ok |
| `report_laboratory_room` | xlsx | 1 | 255 | 1.38 | 1550 | 10.2 | 12 | ok |
| `report_laboratory_room` | pdf | 1 | 255 | 4.52 | 1551 | 32.5 | 63 | ok |
| `report_objects` | html | 1 | 255 | 1.98 | 1780 | 7.6 | 41 | ok |
| `report_objects` | xlsx | 1 | 255 | 2.01 | 1780 | 10.4 | 14 | ok |
| `report_objects` | pdf | 1 | 255 | 5.89 | 1781 | 38.8 | 92 | ok |
| `report_limit_objects` | html | 1 | 255 | 0.32 | 357 | 7.6 | 3 | ok |
| `report_limit_objects` | xlsx | 1 | 255 | 0.31 | 357 | 10.4 | 6 | ok |
| `report_limit_objects` | pdf | 1 | 255 | 1.2 | 358 | 20.7 | 16 | ok |
| `report_objectschanges` | html | 1 | 255 | 1.41 | 998 | 7.7 | — | vacío |
| `report_objectschanges` | xlsx | 1 | 255 | 1.37 | 1263 | 10.4 | 10 | ok |
| `report_objectschanges` | pdf | 1 | 255 | 5.42 | 2054 | 34.7 | 73 | ok |
| `report_furniture` | html | 1 | 255 | 1.29 | 1550 | 7.6 | 27 | ok |
| `report_furniture` | xlsx | 1 | 255 | 1.31 | 1550 | 10.4 | 14 | ok |
| `report_furniture` | pdf | 1 | 255 | 5.07 | 1551 | 40.0 | 71 | ok |
| `report_organization_reactive_list` | html | 1 | 255 | 0.08 | 53 | 7.5 | 2 | ok |
| `report_organization_reactive_list` | xlsx | 1 | 255 | 0.09 | 53 | 10.2 | 5 | ok |
| `report_organization_reactive_list` | pdf | 1 | 255 | 0.44 | 54 | 18.7 | 13 | ok |
| `report_waste_objects` | html | 1 | 255 | 0.04 | 11 | 7.5 | 6 | ok |
| `report_waste_objects` | xlsx | 1 | 255 | 0.06 | 12 | 10.2 | 7 | ok |
| `report_waste_objects` | pdf | 1 | 255 | 1.23 | 12 | 20.7 | 21 | ok |
| `reactive_report` | html | 1 | 255 | 1.52 | 992 | 7.6 | 14 | ok |
| `reactive_report` | xlsx | 1 | 255 | 1.25 | 992 | 10.4 | 10 | ok |
| `reactive_report` | pdf | 1 | 255 | 3.32 | 993 | 21.8 | 54 | ok |
| `risk_zone_report` | html | 1 | 255 | 0.7 | 769 | 7.6 | 1 | ok |
| `risk_zone_report` | xlsx | 1 | 255 | 0.72 | 769 | 10.4 | 5 | ok |
| `risk_zone_report` | pdf | 1 | 255 | 1.0 | 770 | 18.7 | 11 | ok |
| `stock_reactive_report` | xlsx | 1 | 255 | 3.93 | 5458 | 10.4 | 11 | ok |
| `regency_report` | html | 1 | 255 | 0.06 | 10 | 12.9 | — | vacío |
| `regency_report` | xlsx | 1 | 255 | 0.07 | 13 | 15.5 | 6 | ok |
| `regency_report` | pdf | 1 | 255 | 0.24 | 16 | 23.9 | 10 | ok |
| `compatibility_report` | html | 1 | 255 | 0.6 | 488 | 7.6 | 181 | ok |
| `compatibility_report` | ods | 1 | 255 | 0.39 | 274 | 10.0 | 7 | ok |
| `compatibility_report` | pdf | 1 | 255 | 14.97 | 489 | 122.2 | 293 | ok |
| `hazard_map_report` | html | 1 | 255 | 0.22 | 167 | 7.6 | 46 | ok |
| `hazard_map_report` | pdf | 1 | 255 | 2.09 | 168 | 20.7 | 46 | ok |
| `chemicalinventory` | html | 1 | 255 | 5.7 | 3234 | 7.6 | 9 | ok |
| `chemicalinventory` | xlsx | 1 | 255 | 5.6 | 3234 | 10.4 | 8 | ok |
| `chemicalinventory` | pdf | 1 | 255 | 7.4 | 3235 | 20.7 | 30 | ok |
| `donations_report` | html | 1 | 255 | 0.17 | 176 | 7.5 | 3 | ok |
| `donations_report` | xlsx | 1 | 255 | 0.22 | 176 | 10.2 | 6 | ok |
| `donations_report` | pdf | 1 | 255 | 0.67 | 177 | 18.7 | 16 | ok |
| `report_consumption_detail` | html | 1 | 255 | 0.08 | 12 | 7.8 | 13 | ok |
| `report_consumption_detail` | xlsx | 1 | 255 | 0.09 | 12 | 10.5 | 9 | ok |
| `report_consumption_detail` | pdf | 1 | 255 | 2.01 | 12 | 20.8 | 41 | ok |
| `report_consumption_summary` | html | 1 | 255 | 0.07 | 12 | 7.8 | 6 | ok |
| `report_consumption_summary` | xlsx | 1 | 255 | 0.08 | 12 | 10.5 | 7 | ok |
| `report_consumption_summary` | pdf | 1 | 255 | 1.37 | 12 | 20.8 | 26 | ok |
| `report_consumption_cost` | html | 1 | 255 | 0.05 | 12 | 7.5 | 0 | ok |
| `report_consumption_cost` | xlsx | 1 | 255 | 0.06 | 12 | 10.2 | 4 | ok |
| `report_consumption_cost` | pdf | 1 | 255 | 0.21 | 12 | 18.6 | 7 | ok |
| `report_environmental_indicators` | html | 1 | 255 | 0.14 | 62 | 7.7 | 2 | ok |
| `report_environmental_indicators` | xlsx | 1 | 255 | 0.14 | 62 | 10.4 | 5 | ok |
| `report_environmental_indicators` | pdf | 1 | 255 | 0.42 | 62 | 18.8 | 12 | ok |
| `report_consumption_comparison` | html | 1 | 255 | 0.1 | 45 | 7.7 | 1 | ok |
| `report_consumption_comparison` | xlsx | 1 | 255 | 0.11 | 45 | 10.4 | 5 | ok |
| `report_consumption_comparison` | pdf | 1 | 255 | 0.32 | 45 | 18.8 | 10 | ok |
| `report_waste_manifest` | html | 1 | 255 | 0.05 | 12 | 7.8 | 5 | ok |
| `report_waste_manifest` | xlsx | 1 | 255 | 0.07 | 12 | 10.5 | 6 | ok |
| `report_waste_manifest` | pdf | 1 | 255 | 1.15 | 12 | 20.8 | 22 | ok |
| `reactive_precursor` | html | 10 | 2415 | 0.47 | 306 | 7.5 | 6 | ok |
| `reactive_precursor` | xlsx | 10 | 2415 | 0.49 | 307 | 10.2 | 7 | ok |
| `reactive_precursor` | pdf | 10 | 2415 | 1.79 | 307 | 20.7 | 24 | ok |
| `report_laboratory_room` | html | 10 | 2415 | 13.59 | 14564 | 7.6 | 216 | ok |
| `report_laboratory_room` | xlsx | 10 | 2415 | 12.67 | 14564 | 10.4 | 71 | ok |
| `report_laboratory_room` | pdf | 10 | 2415 | 43.78 | 14565 | 548.8 | 525 | ok |
| `report_objects` | html | 10 | 2415 | 19.49 | 16806 | 9.9 | 389 | ok |
| `report_objects` | xlsx | 10 | 2415 | 20.06 | 16806 | 12.3 | 88 | ok |
| `report_objects` | pdf | 10 | 2415 | 53.83 | 16807 | 643.7 | 801 | ok |
| `report_limit_objects` | html | 10 | 2415 | 3.07 | 3471 | 7.6 | 29 | ok |
| `report_limit_objects` | xlsx | 10 | 2415 | 2.7 | 3471 | 10.3 | 15 | ok |
| `report_limit_objects` | pdf | 10 | 2415 | 7.55 | 3472 | 63.1 | 90 | ok |
| `report_objectschanges` | html | 10 | 2415 | 15.07 | 10257 | 7.7 | — | vacío |
| `report_objectschanges` | xlsx | 10 | 2415 | 13.81 | 13000 | 10.4 | 64 | ok |
| `report_objectschanges` | pdf | 10 | 2415 | 54.43 | 21154 | 675.1 | 679 | ok |
| `report_furniture` | html | 10 | 2415 | 11.66 | 14564 | 7.6 | 254 | ok |
| `report_furniture` | xlsx | 10 | 2415 | 11.74 | 14564 | 10.4 | 89 | ok |
| `report_furniture` | pdf | 10 | 2415 | 45.93 | 14565 | 669.7 | 602 | ok |
| `report_organization_reactive_list` | html | 10 | 2415 | 0.37 | 395 | 7.6 | 21 | ok |
| `report_organization_reactive_list` | xlsx | 10 | 2415 | 0.4 | 395 | 10.4 | 12 | ok |
| `report_organization_reactive_list` | pdf | 10 | 2415 | 2.97 | 396 | 27.9 | 54 | ok |
| `report_waste_objects` | html | 10 | 2415 | 0.08 | 20 | 7.5 | 55 | ok |
| `report_waste_objects` | xlsx | 10 | 2415 | 0.13 | 21 | 10.2 | 23 | ok |
| `report_waste_objects` | pdf | 10 | 2415 | 7.77 | 21 | 118.4 | 139 | ok |
| `reactive_report` | html | 10 | 2415 | 13.25 | 9256 | 7.6 | 127 | ok |
| `reactive_report` | xlsx | 10 | 2415 | 11.91 | 9256 | 10.4 | 59 | ok |
| `reactive_report` | pdf | 10 | 2415 | 31.07 | 9257 | 359.6 | 435 | ok |
| `risk_zone_report` | html | 10 | 2415 | 6.73 | 7131 | 7.6 | 11 | ok |
| `risk_zone_report` | xlsx | 10 | 2415 | 6.59 | 7131 | 10.4 | 9 | ok |
| `risk_zone_report` | pdf | 10 | 2415 | 8.68 | 7132 | 20.7 | 40 | ok |
| `stock_reactive_report` | xlsx | 10 | 2415 | 37.6 | 47528 | 10.4 | 61 | ok |
| `regency_report` | html | 10 | 2415 | 0.06 | 10 | 12.9 | — | vacío |
| `regency_report` | xlsx | 10 | 2415 | 0.08 | 13 | 15.5 | 6 | ok |
| `regency_report` | pdf | 10 | 2415 | 0.27 | 16 | 23.9 | 10 | ok |
| `compatibility_report` | html | 10 | 2415 | 6.79 | 4701 | 19.7 | 1845 | ok |
| `compatibility_report` | ods | 10 | 2415 | 4.03 | 2626 | 27.9 | 57 | ok |
| `compatibility_report` | pdf | 10 | 2415 | 165.01 | 4702 | 1675.7 | 3030 | ok |
| `hazard_map_report` | html | 10 | 2415 | 1.56 | 1400 | 7.7 | 442 | ok |
| `hazard_map_report` | pdf | 10 | 2415 | 17.25 | 1401 | 247.1 | 342 | ok |
| `chemicalinventory` | html | 10 | 2415 | 62.58 | 32165 | 7.6 | 88 | ok |
| `chemicalinventory` | xlsx | 10 | 2415 | 56.22 | 32165 | 10.4 | 40 | ok |
| `chemicalinventory` | pdf | 10 | 2415 | 68.62 | 32166 | 206.3 | 226 | ok |
| `donations_report` | html | 10 | 2415 | 1.32 | 1688 | 7.6 | 30 | ok |
| `donations_report` | xlsx | 10 | 2415 | 1.35 | 1688 | 10.4 | 15 | ok |
| `donations_report` | pdf | 10 | 2415 | 5.47 | 1689 | 45.4 | 78 | ok |
| `report_consumption_detail` | html | 10 | 2415 | 0.18 | 12 | 7.8 | 130 | ok |
| `report_consumption_detail` | xlsx | 10 | 2415 | 0.3 | 12 | 10.5 | 47 | ok |
| `report_consumption_detail` | pdf | 10 | 2415 | 16.88 | 12 | 295.6 | 331 | ok |
| `report_consumption_summary` | html | 10 | 2415 | 0.18 | 12 | 7.8 | 65 | ok |
| `report_consumption_summary` | xlsx | 10 | 2415 | 0.23 | 12 | 10.5 | 30 | ok |
| `report_consumption_summary` | pdf | 10 | 2415 | 9.66 | 12 | 158.5 | 185 | ok |
| `report_consumption_cost` | html | 10 | 2415 | 0.06 | 12 | 7.5 | 0 | ok |
| `report_consumption_cost` | xlsx | 10 | 2415 | 0.06 | 12 | 10.2 | 4 | ok |
| `report_consumption_cost` | pdf | 10 | 2415 | 0.2 | 12 | 18.7 | 7 | ok |
| `report_environmental_indicators` | html | 10 | 2415 | 0.81 | 494 | 7.7 | 14 | ok |
| `report_environmental_indicators` | xlsx | 10 | 2415 | 0.79 | 494 | 10.4 | 9 | ok |
| `report_environmental_indicators` | pdf | 10 | 2415 | 2.75 | 494 | 20.8 | 40 | ok |
| `report_consumption_comparison` | html | 10 | 2415 | 0.54 | 333 | 7.7 | 7 | ok |
| `report_consumption_comparison` | xlsx | 10 | 2415 | 0.56 | 333 | 10.4 | 7 | ok |
| `report_consumption_comparison` | pdf | 10 | 2415 | 1.68 | 333 | 20.8 | 26 | ok |
| `report_waste_manifest` | html | 10 | 2415 | 0.11 | 12 | 7.8 | 50 | ok |
| `report_waste_manifest` | xlsx | 10 | 2415 | 0.14 | 12 | 10.5 | 20 | ok |
| `report_waste_manifest` | pdf | 10 | 2415 | 6.69 | 12 | 79.9 | 138 | ok |
| `reactive_precursor` | html | 100 | 24015 | 5.34 | 2826 | 7.6 | 51 | ok |
| `reactive_precursor` | xlsx | 100 | 24015 | 4.12 | 2827 | 10.4 | 27 | ok |
| `reactive_precursor` | pdf | 100 | 24015 | 12.06 | 2827 | 124.9 | 147 | ok |
| `report_laboratory_room` | html | 100 | 24015 | 132.41 | 144704 | 24.1 | 2182 | ok |
| `report_laboratory_room` | xlsx | 100 | 24015 | 132.57 | 144704 | 10.4 | 661 | ok |
| `report_laboratory_room` | pdf | 100 | 24015 | — | — | — | — | tiempo |
| `report_objects` | html | 100 | 24015 | 178.52 | 167032 | 71.9 | 3873 | ok |
| `report_objects` | xlsx | 100 | 24015 | 177.01 | 167032 | 51.0 | 829 | ok |
| `report_objects` | pdf | 100 | 24015 | — | — | — | — | tiempo |
| `report_limit_objects` | html | 100 | 24015 | 23.69 | 34620 | 7.6 | 293 | ok |
| `report_limit_objects` | xlsx | 100 | 24015 | 23.97 | 34620 | 10.4 | 109 | ok |
| `report_limit_objects` | pdf | 100 | 24015 | 69.53 | 34621 | 984.2 | 826 | ok |
| `report_objectschanges` | html | 100 | 24015 | 153.16 | 101852 | 7.7 | — | vacío |
| `report_objectschanges` | xlsx | 100 | 24015 | 156.03 | 128968 | 12.3 | 602 | ok |
| `report_objectschanges` | pdf | 100 | 24015 | — | — | — | — | tiempo |
| `report_furniture` | html | 100 | 24015 | 120.13 | 144704 | 28.3 | 2558 | ok |
| `report_furniture` | xlsx | 100 | 24015 | 122.3 | 144704 | 10.4 | 840 | ok |
| `report_furniture` | pdf | 100 | 24015 | — | — | — | — | memoria |
| `report_organization_reactive_list` | html | 100 | 24015 | 3.66 | 3813 | 9.9 | 205 | ok |
| `report_organization_reactive_list` | xlsx | 100 | 24015 | 3.8 | 3813 | 12.3 | 74 | ok |
| `report_organization_reactive_list` | pdf | 100 | 24015 | 27.47 | 3814 | 494.1 | 461 | ok |
| `report_waste_objects` | html | 100 | 24015 | 0.59 | 110 | 7.6 | 557 | ok |
| `report_waste_objects` | xlsx | 100 | 24015 | 0.86 | 111 | 10.4 | 187 | ok |
| `report_waste_objects` | pdf | 100 | 24015 | 74.62 | 111 | 1552.7 | 1330 | ok |
| `reactive_report` | html | 100 | 24015 | 121.35 | 91760 | 19.5 | 1274 | ok |
| `reactive_report` | xlsx | 100 | 24015 | 120.19 | 91760 | 20.4 | 541 | ok |
| `reactive_report` | pdf | 100 | 24015 | — | — | — | — | tiempo |
| `risk_zone_report` | html | 100 | 24015 | 66.27 | 70659 | 7.6 | 116 | ok |
| `risk_zone_report` | xlsx | 100 | 24015 | 69.65 | 70659 | 10.4 | 49 | ok |
| `risk_zone_report` | pdf | 100 | 24015 | 87.12 | 70660 | 323.1 | 330 | ok |
| `stock_reactive_report` | xlsx | 100 | 24015 | — | — | — | — | tiempo |
| `regency_report` | html | 100 | 24015 | 0.05 | 10 | 12.9 | — | vacío |
| `regency_report` | xlsx | 100 | 24015 | 0.07 | 13 | 15.5 | 6 | ok |
| `regency_report` | pdf | 100 | 24015 | 0.25 | 16 | 23.9 | 10 | ok |
| `compatibility_report` | html | 100 | 24015 | 53.66 | 46763 | 170.6 | 19301 | ok |
| `compatibility_report` | ods | 100 | 24015 | 33.66 | 26114 | 332.6 | 562 | ok |
| `compatibility_report` | pdf | 100 | 24015 | — | — | — | — | memoria |
| `hazard_map_report` | html | 100 | 24015 | 13.13 | 12310 | 39.2 | 4486 | ok |
| `hazard_map_report` | pdf | 100 | 24015 | 175.35 | 12311 | 2813.9 | 3298 | ok |
| `chemicalinventory` | html | 100 | 24015 | — | — | — | — | tiempo |
| `chemicalinventory` | xlsx | 100 | 24015 | — | — | — | — | tiempo |
| `chemicalinventory` | pdf | 100 | 24015 | — | — | — | — | tiempo |
| `donations_report` | html | 100 | 24015 | 12.89 | 16808 | 7.6 | 305 | ok |
| `donations_report` | xlsx | 100 | 24015 | 17.96 | 16808 | 10.4 | 109 | ok |
| `donations_report` | pdf | 100 | 24015 | 55.77 | 16809 | 801.2 | 696 | ok |
| `report_consumption_detail` | html | 100 | 24015 | 1.57 | 12 | 32.3 | 1312 | ok |
| `report_consumption_detail` | xlsx | 100 | 24015 | 2.49 | 12 | 27.4 | 433 | ok |
| `report_consumption_detail` | pdf | 100 | 24015 | 173.65 | 12 | 3329.6 | 3249 | ok |
| `report_consumption_summary` | html | 100 | 24015 | 1.71 | 12 | 25.2 | 657 | ok |
| `report_consumption_summary` | xlsx | 100 | 24015 | 2.11 | 12 | 25.2 | 243 | ok |
| `report_consumption_summary` | pdf | 100 | 24015 | 98.95 | 12 | 1961.3 | 1787 | ok |
| `report_consumption_cost` | html | 100 | 24015 | 0.05 | 12 | 7.5 | 0 | ok |
| `report_consumption_cost` | xlsx | 100 | 24015 | 0.06 | 12 | 10.2 | 4 | ok |
| `report_consumption_cost` | pdf | 100 | 24015 | 0.21 | 12 | 18.7 | 7 | ok |
| `report_environmental_indicators` | html | 100 | 24015 | 8.38 | 4814 | 7.8 | 141 | ok |
| `report_environmental_indicators` | xlsx | 100 | 24015 | 8.3 | 4814 | 10.5 | 45 | ok |
| `report_environmental_indicators` | pdf | 100 | 24015 | 24.35 | 4814 | 327.3 | 323 | ok |
| `report_consumption_comparison` | html | 100 | 24015 | 6.16 | 3213 | 7.8 | 65 | ok |
| `report_consumption_comparison` | xlsx | 100 | 24015 | 7.65 | 3213 | 10.5 | 27 | ok |
| `report_consumption_comparison` | pdf | 100 | 24015 | 16.86 | 3213 | 148.3 | 176 | ok |
| `report_waste_manifest` | html | 100 | 24015 | 0.59 | 12 | 7.8 | 498 | ok |
| `report_waste_manifest` | xlsx | 100 | 24015 | 0.93 | 12 | 10.5 | 162 | ok |
| `report_waste_manifest` | pdf | 100 | 24015 | 72.72 | 12 | 1172.6 | 1310 | ok |

| Reporte | Formato | crecimiento tiempo | crecimiento memoria | veredicto |
|---------|---------|-------------------:|--------------------:|-----------|
| `chemicalinventory` | html | — | — | no escala: tiempo a escala 100 |
| `chemicalinventory` | pdf | — | — | no escala: tiempo a escala 100 |
| `chemicalinventory` | xlsx | — | — | no escala: tiempo a escala 100 |
| `compatibility_report` | html | 0.95 | 0.24 | lineal |
| `compatibility_report` | ods | 0.92 | 0.35 | lineal |
| `compatibility_report` | pdf | — | — | no escala: memoria a escala 100 |
| `donations_report` | html | 0.81 | 0.01 | lineal |
| `donations_report` | pdf | 0.88 | 0.46 | lineal |
| `donations_report` | xlsx | 0.87 | 0.01 | lineal |
| `hazard_map_report` | html | 0.63 | 0.05 | lineal |
| `hazard_map_report` | pdf | 0.89 | 1.44 | lineal |
| `reactive_precursor` | html | 0.44 | 0.01 | sublineal |
| `reactive_precursor` | pdf | 0.31 | 0.07 | sublineal |
| `reactive_precursor` | xlsx | 0.24 | 0.01 | sublineal |
| `reactive_report` | html | 0.85 | 0.03 | lineal |
| `reactive_report` | pdf | — | — | no escala: tiempo a escala 100 |
| `reactive_report` | xlsx | 1.02 | 0.02 | lineal |
| `regency_report` | html | 0.01 | 0.01 | sublineal |
| `regency_report` | pdf | 0.01 | 0.01 | sublineal |
| `regency_report` | xlsx | 0.01 | 0.01 | sublineal |
| `report_consumption_comparison` | html | 0.65 | 0.01 | lineal |
| `report_consumption_comparison` | pdf | 0.56 | 0.08 | lineal |
| `report_consumption_comparison` | xlsx | 0.74 | 0.01 | lineal |
| `report_consumption_cost` | html | 0.01 | 0.01 | sublineal |
| `report_consumption_cost` | pdf | 0.01 | 0.01 | sublineal |
| `report_consumption_cost` | xlsx | 0.01 | 0.01 | sublineal |
| `report_consumption_detail` | html | 0.21 | 0.04 | sublineal |
| `report_consumption_detail` | pdf | 0.92 | 1.7 | superlineal |
| `report_consumption_detail` | xlsx | 0.29 | 0.03 | sublineal |
| `report_consumption_summary` | html | 0.26 | 0.03 | sublineal |
| `report_consumption_summary` | pdf | 0.77 | 1.0 | lineal |
| `report_consumption_summary` | xlsx | 0.28 | 0.03 | sublineal |
| `report_environmental_indicators` | html | 0.64 | 0.01 | lineal |
| `report_environmental_indicators` | pdf | 0.62 | 0.19 | lineal |
| `report_environmental_indicators` | xlsx | 0.63 | 0.01 | lineal |
| `report_furniture` | html | 0.99 | 0.04 | lineal |
| `report_furniture` | pdf | — | — | no escala: memoria a escala 100 |
| `report_furniture` | xlsx | 0.99 | 0.01 | lineal |
| `report_laboratory_room` | html | 1.03 | 0.03 | lineal |
| `report_laboratory_room` | pdf | — | — | no escala: tiempo a escala 100 |
| `report_laboratory_room` | xlsx | 1.02 | 0.01 | lineal |
| `report_limit_objects` | html | 0.79 | 0.01 | lineal |
| `report_limit_objects` | pdf | 0.62 | 0.51 | lineal |
| `report_limit_objects` | xlsx | 0.82 | 0.01 | lineal |
| `report_objects` | html | 0.96 | 0.1 | lineal |
| `report_objects` | pdf | — | — | no escala: tiempo a escala 100 |
| `report_objects` | xlsx | 0.94 | 0.05 | lineal |
| `report_objectschanges` | html | 1.15 | 0.01 | lineal |
| `report_objectschanges` | pdf | — | — | no escala: tiempo a escala 100 |
| `report_objectschanges` | xlsx | 1.21 | 0.01 | lineal |
| `report_organization_reactive_list` | html | 0.49 | 0.01 | sublineal |
| `report_organization_reactive_list` | pdf | 0.66 | 0.28 | lineal |
| `report_organization_reactive_list` | xlsx | 0.45 | 0.01 | sublineal |
| `report_waste_manifest` | html | 0.13 | 0.01 | sublineal |
| `report_waste_manifest` | pdf | 0.67 | 0.6 | lineal |
| `report_waste_manifest` | xlsx | 0.14 | 0.01 | sublineal |
| `report_waste_objects` | html | 0.16 | 0.01 | sublineal |
| `report_waste_objects` | pdf | 0.64 | 0.8 | lineal |
| `report_waste_objects` | xlsx | 0.15 | 0.01 | sublineal |
| `risk_zone_report` | html | 1.01 | 0.01 | lineal |
| `risk_zone_report` | pdf | 0.93 | 0.18 | lineal |
| `risk_zone_report` | xlsx | 1.03 | 0.01 | lineal |
| `stock_reactive_report` | xlsx | — | — | no escala: tiempo a escala 100 |

## Configuraciones de ejecución

Cada fila es una corrida completa; RSS pico suma todo el árbol de procesos (workers, Chrome, Xvfb).

| Suite | Configuración | pruebas | s | CPU s | RSS pico MiB | resultado |
|-------|---------------|--------:|--:|------:|-------------:|-----------|
| unit | `unit-serial` | 2641 | 758.7 | 621.8 | 459.0 | FAILED (failures=6) |
| unit | `unit-p2` | 2641 | 411.1 | 562.1 | 1097.5 | FAILED (failures=6) |
| unit | `unit-p4` | 2641 | 300.4 | 685.1 | 1729.6 | FAILED (failures=2) |
| unit | `unit-p8` | 2641 | 252.1 | 919.0 | 2916.3 | FAILED (failures=1) |
| unit | `unit-p4-keepdb` | 2641 | 324.1 | 761.5 | 1727.0 | FAILED (failures=1) |
| selenium | `sel-w2` | 235 | 1728.1 | 1563.0 | 5433.5 | FAILED (failures=1, errors=2) |
| selenium | `sel-w4` | 235 | 1377.8 | 2196.0 | 9395.4 | FAILED (errors=5) |
| selenium | `sel-w6` | 235 | 1142.3 | 2305.7 | 13237.2 | FAILED (errors=6) |
| selenium | `sel-w4-gif` | 235 | 5795.5 | 2435.1 | 9628.6 | FAILED (errors=7) |

**Mejor para selenium:** `sel-w6` — 1142 s, 13237 MiB pico; la más liviana es `sel-w2` (1728 s, 5433 MiB)

**Mejor para unit:** `unit-p8` — 252 s, 2916 MiB pico; la más liviana es `unit-serial` (759 s, 459 MiB)

