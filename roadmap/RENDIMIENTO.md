# Rendimiento de Organilab

Generado con `make perf-report` a partir de `roadmap/.perf/`. No editar a mano.
Los tiempos son de la suite de pruebas (base pequeña, live server de Django): sirven para **comparar** vistas entre sí, no como latencia de producción. Si la corrida fue `make coverage-perf`, los tiempos incluyen la sobrecarga del trazado de coverage (2–3×); el número de consultas SQL no se ve afectado.

- Fecha: 2026-10-13 13:07 · commit `e497e186a` · x86_64, 8 núcleos, Python 3.13.5
- 5993 peticiones medidas sobre 791 rutas; 2989 pruebas.

## Vistas más lentas (p95)

| Ruta | Método | n | p50 ms | p95 ms | máx ms | CPU p95 ms | SQL p95 ms | consultas máx |
|------|--------|--:|-------:|-------:|-------:|-----------:|-----------:|--------------:|
| `laboratory:reports_shelf_objects` | GET | 5 | 182.5 | 5586.6 | 5586.6 | 5025.3 | 130.8 | 161 |
| `laboratory:generate_shelfobject_label` | GET | 3 | 78.6 | 4911.9 | 4911.9 | 2254.4 | 28.5 | 27 |
| `sga:generate_label` | GET | 6 | 131.2 | 4052.4 | 4052.4 | 942.5 | 59.2 | 21 |
| `sga:security_leaf_pdf` | GET | 2 | 36.8 | 2199.1 | 2199.1 | 2139.7 | 12.3 | 14 |
| `platform:alertrule_list` | GET | 4 | 1875.3 | 2185.3 | 2185.3 | 2036.8 | 117.2 | 58 |
| `report:create_organization_report_request` | GET | 5 | 479.7 | 1707.6 | 1707.6 | 1513.4 | 115.2 | 42 |
| `laboratory:rooms_list` | GET | 47 | 1316.2 | 1660.1 | 1782.3 | 1237.8 | 116.0 | 108 |
| `academic:update_step` | GET | 9 | 1039.8 | 1567.5 | 1567.5 | 1393.8 | 76.5 | 55 |
| `sga:create_sustance` | POST | 4 | 350.1 | 1520.8 | 1520.8 | 1365.1 | 47.9 | 52 |
| `laboratory:mylabs` | GET | 6 | 209.8 | 1497.7 | 1497.7 | 1404.2 | 56.4 | 57 |
| `sga:sgalabel_step_one` | POST | 2 | 361.3 | 1426.4 | 1426.4 | 1251.2 | 85.8 | 47 |
| `laboratory:labview` | GET | 20 | 1179.2 | 1351.0 | 1585.0 | 1196.5 | 73.9 | 79 |
| `ambiental:consumptionrecord_list` | GET | 5 | 384.7 | 1079.8 | 1079.8 | 934.3 | 71.4 | 60 |
| `sga:add_personal` | GET | 4 | 352.9 | 1064.8 | 1064.8 | 961.5 | 71.9 | 42 |
| `ambiental:ambiental_dashboard` | GET | 6 | 362.5 | 1017.5 | 1017.5 | 832.7 | 73.3 | 74 |
| `ambiental:report_consumption_cost` | GET | 4 | 277.2 | 884.1 | 884.1 | 789.1 | 47.7 | 45 |
| `laboratory:sustance_list` | GET | 13 | 647.8 | 871.5 | 1003.1 | 691.0 | 67.3 | 62 |
| `admin:django_celery_beat_periodictask_changelist` | GET | 1 | 832.4 | 832.4 | 832.4 | 776.4 | 14.5 | 9 |
| `laboratory:load_archive_create_shelfobjects` | POST | 2 | 264.6 | 829.7 | 829.7 | 742.3 | 106.9 | 109 |
| `sga:step_four` | GET | 9 | 477.2 | 809.7 | 809.7 | 611.4 | 56.1 | 42 |
| `sga:create_sustance` | GET | 6 | 421.5 | 809.3 | 809.3 | 700.0 | 80.3 | 50 |
| `sga:add_danger_indication` | GET | 1 | 800.4 | 800.4 | 800.4 | 733.2 | 28.0 | 34 |
| `laboratory:equipment_shelfobject_detail` | GET | 6 | 677.8 | 797.9 | 797.9 | 746.7 | 64.3 | 63 |
| `reservations_management:manage_reservation` | GET | 7 | 350.6 | 747.8 | 747.8 | 262.2 | 83.3 | 53 |
| `sga:sgalabel_step_two` | POST | 2 | 248.9 | 725.0 | 725.0 | 610.3 | 41.2 | 19 |

## Vistas con más consultas SQL

Más de 50 consultas en una petición, o un rango min–máx amplio entre peticiones de la misma ruta, sugiere N+1 (consultas que crecen con los datos).

| Ruta | Método | n | consultas min–máx | SQL p95 ms | N+1? |
|------|--------|--:|------------------:|-----------:|:----:|
| `laboratory:reports_shelf_objects` | GET | 5 | 16–161 | 130.8 | ⚠ |
| `laboratory:organization_actions` | POST | 8 | 6–144 | 120.4 | ⚠ |
| `admin:auth_user_changelist` | POST | 1 | 135–135 | 157.7 | ⚠ |
| `laboratory:delete_organization` | POST | 2 | 63–135 | 162.7 | ⚠ |
| `laboratory:api-shelfobject-move-shelfobject-to-shelf` | POST | 18 | 14–128 | 161.8 | ⚠ |
| `admin:auth_user_delete` | POST | 1 | 127–127 | 107.1 | ⚠ |
| `laboratory:load_archive_create_shelfobjects` | POST | 2 | 54–109 | 106.9 | ⚠ |
| `laboratory:rooms_list` | GET | 47 | 62–108 | 116.0 | ⚠ |
| `laboratory:api-dangers-table-list` | GET | 4 | 0–108 | 64.0 | ⚠ |
| `laboratory:api-danger-indication-list` | GET | 3 | 8–106 | 57.3 | ⚠ |
| `laboratory:api-shelfobject-transfer-in-approve` | POST | 10 | 34–100 | 165.4 | ⚠ |
| `auth_and_perms:api_organization_buttons` | GET | 6 | 5–95 | 96.7 | ⚠ |
| `auth_and_perms:organizationManager` | GET | 49 | 41–85 | 95.5 | ⚠ |
| `laboratory:labview` | GET | 20 | 12–79 | 73.9 | ⚠ |
| `laboratory:laboratory_delete` | POST | 3 | 57–76 | 79.3 | ⚠ |
| `ambiental:ambiental_dashboard` | GET | 6 | 32–74 | 73.3 | ⚠ |
| `laboratory:my_reservations` | GET | 5 | 36–73 | 104.1 | ⚠ |
| `laboratory:api-shelfobject-create-shelfobject` | POST | 40 | 0–72 | 108.9 | ⚠ |
| `report:hazard_map_visual` | GET | 7 | 21–72 | 70.6 | ⚠ |
| `sga:update_substance` | POST | 4 | 49–72 | 51.0 | ⚠ |
| `laboratory:shelfobject_create` | POST | 7 | 31–70 | 66.6 | ⚠ |
| `laboratory:load_archive` | POST | 5 | 21–70 | 130.9 | ⚠ |
| `laboratory:furniture_update` | POST | 12 | 26–69 | 45.5 | ⚠ |
| `sga:update_substance` | GET | 4 | 54–69 | 74.3 | ⚠ |
| `laboratory:api-reactive-list` | GET | 9 | 56–69 | 103.8 | ⚠ |

## Tiempo total acumulado por ruta

Dónde se va el tiempo de la suite: una ruta barata pero muy llamada pesa más que una cara llamada una vez.

| Ruta | Método | n | total s | p50 ms |
|------|--------|--:|--------:|-------:|
| `laboratory:rooms_list` | GET | 47 | 62.0 | 1316.2 |
| `pending_tasks:view_task` | GET | 287 | 54.18 | 187.4 |
| `notifications` | GET | 771 | 51.48 | 56.4 |
| `index` | GET | 461 | 35.02 | 51.1 |
| `pending_tasks:api-pending_tasks-list` | GET | 280 | 27.1 | 91.2 |
| `laboratory:labview` | GET | 20 | 20.8 | 1179.2 |
| `auth_and_perms:organizationManager` | GET | 49 | 20.08 | 395.0 |
| `laboratory:node_qr_svg` | GET | 59 | 16.74 | 278.0 |
| `laboratory:api-equipment-list` | GET | 40 | 15.01 | 365.3 |
| `home` | GET | 247 | 13.73 | 33.4 |
| `laboratory:api-shelfobjecttable-list` | GET | 97 | 13.15 | 139.7 |
| `laboratory:api-labview-tree-list` | GET | 90 | 13.11 | 140.3 |
| `laboratory:labindex` | GET | 55 | 12.71 | 220.9 |
| `djgentelella-js-catalog` | GET | 103 | 10.99 | 104.8 |
| `laboratory:rooms_create` | GET | 34 | 9.84 | 280.4 |
| `javascript-catalog` | GET | 103 | 9.83 | 84.8 |
| `laboratory:api-shelfobject-create-shelfobject` | POST | 40 | 9.8 | 287.8 |
| `academic:update_step` | GET | 9 | 9.43 | 1039.8 |
| `academic:procedure_list` | GET | 34 | 8.89 | 231.9 |
| `sga:generate_label` | GET | 6 | 8.54 | 131.2 |
| `laboratory:sustance_list` | GET | 13 | 7.97 | 647.8 |
| `derb:form_list` | GET | 29 | 7.05 | 222.6 |
| `auth_and_perms:api-userinorg-list` | GET | 65 | 7.01 | 80.2 |
| `laboratory:reports_shelf_objects` | GET | 5 | 6.78 | 182.5 |
| `lab_room-list` | GET | 58 | 6.74 | 106.5 |

## Pruebas más lentas

| Prueba | Selenium | s | CPU s | RSS después MiB |
|--------|:--------:|--:|------:|----------------:|
| `academic.tests.selenium_tests.test_procedure_template.ProcedureTemplateSeleniumTest.test_procedure_crud` | ✓ | 119.24 | 30.61 | 329.3 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_objects.ObjectSeleniumTest.test_add_reactive_object_classification` | ✓ | 56.726 | 11.038 | 330.5 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_catalog_crud.LaboratoryCatalogsCrudTest.test_lab_catalogs_flow` | ✓ | 43.779 | 12.371 | 331.3 |
| `laboratory.tests.selenium_tests.manage_organizations.test_collapse_org_name_buttons_box.ButtonBoxCollapseOrgNameTest.test_add_role_to_org_copy_permissions_from_others_roles` | ✓ | 37.76 | 10.297 | 342.8 |
| `laboratory.tests.selenium_tests.manage_organizations.test_laboratory_tab.LaboratoryTabTest.test_relate_user_to_org_and_lab_from_tab_lab` | ✓ | 37.715 | 10.369 | 340.5 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_objects.ObjectSeleniumTest.test_add_reactive_object_precursor` | ✓ | 36.857 | 11.153 | 330.8 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap5_reservaciones.Cap5ManageReservationsTest.test_approve_reject_reservation` | ✓ | 36.406 | 10.662 | 337.3 |
| `laboratory.tests.selenium_tests.manage_organizations.test_collapse_org_name_buttons_box.ButtonBoxCollapseOrgNameTest.test_relate_user_to_org_from_button_box` | ✓ | 36.286 | 10.91 | 342.9 |
| `laboratory.tests.selenium_tests.informs.test_inform_template.InformsSeleniumTest.test_add_checkbox_derb` | ✓ | 36.024 | 14.386 | 327.1 |
| `laboratory.tests.selenium_tests.manage_organizations.test_collapse_org_name_buttons_box.ButtonBoxCollapseOrgNameTest.test_add_laboratory_to_org` | ✓ | 36.002 | 10.879 | 342.8 |
| `laboratory.tests.selenium_tests.laboratory_view.test_shelfobject_detail_actions.ShelfObjectInfoButtonsActions.test_change_shelfobject_status` | ✓ | 35.563 | 11.495 | 336.0 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_laboratoryroom.LabRoomSeleniumTest.test_laboratory_room_crud` | ✓ | 35.353 | 15.991 | 339.4 |
| `laboratory.tests.selenium_tests.manage_organizations.test_laboratory_tab.LaboratoryTabTest.test_add_permission_rol_to_user_from_tab_lab` | ✓ | 34.841 | 11.086 | 340.4 |
| `laboratory.tests.selenium_tests.manage_organizations.test_collapse_org_name_buttons_box.ButtonBoxCollapseOrgNameTest.test_add_user_to_org_from_button_box` | ✓ | 34.809 | 10.107 | 342.9 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_wrapper_top.CreateShelfObject.test_create_shelfobject_reactive_with_clone_container` | ✓ | 34.804 | 13.353 | 338.1 |
| `laboratory.tests.selenium_tests.manage_organizations.test_laboratory_tab.LaboratoryTabTest.test_remove_permission_rol_to_user_from_tab_lab` | ✓ | 34.797 | 10.229 | 340.5 |
| `laboratory.tests.selenium_tests.manage_organizations.test_laboratory_tab.LaboratoryTabTest.test_use_selected_permission_rol_to_user_from_tab_lab` | ✓ | 34.683 | 11.109 | 340.5 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap5_reservaciones.Cap5MyReservationsTest.test_my_reservations_and_reserve` | ✓ | 34.61 | 10.855 | 339.4 |
| `laboratory.tests.selenium_tests.manage_organizations.test_collapse_org_name_buttons_box.ButtonBoxCollapseOrgNameTest.test_add_role_to_org_without_copy_permissions_from_others_roles` | ✓ | 34.459 | 9.257 | 342.7 |
| `laboratory.tests.selenium_tests.manage_organizations.test_organization_tab.OrganizationTabTest.test_relate_user_to_org_and_lab_from_tab_org` | ✓ | 34.441 | 10.04 | 338.6 |
| `laboratory.tests.selenium_tests.manage_organizations.test_collapse_org_name_buttons_box.ButtonBoxCollapseOrgNameTest.test_relate_external_laboratory_to_org` | ✓ | 34.405 | 10.363 | 342.9 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column.ButtonsActionsTableColumn.test_move_shelfobject_with_clone_container` | ✓ | 34.402 | 12.536 | 336.8 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_wrapper_top.CreateShelfObject.test_create_shelfobject_reactive_with_use_selected_container` | ✓ | 34.376 | 13.649 | 338.1 |
| `laboratory.tests.selenium_tests.informs.test_inform_template.InformsSeleniumTest.test_add_radio_derb` | ✓ | 34.121 | 11.489 | 329.2 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column.ButtonsActionsTableColumn.test_move_shelfobject_with_new_based_source_container` | ✓ | 33.645 | 12.899 | 337.0 |

## Pruebas que más memoria dejan en el proceso

Crecimiento de RSS durante la prueba (lo que no se libera se acumula en el worker).

| Prueba | Δ RSS MiB | RSS después MiB |
|--------|----------:|----------------:|
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_wrapper_top.CreateShelfObject.test_approve_transfer_in_shelfobject_with_available_container` | 10.6 | 332.1 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap3_etiquetas.Cap3LabelGenerationTest.test_generate_label_from_substance_detail` | 10.3 | 350.6 |
| `laboratory.tests.test_cov_core_utils_pdf.ExtraerMsdsDePdfTest.test_extrae_campos_de_un_pdf_real` | 10.1 | 354.0 |
| `academic.tests.selenium_tests.test_procedure_template.ProcedureTemplateSeleniumTest.test_procedure_crud` | 7.9 | 329.3 |
| `laboratory.tests.test_cov_views_shelfobject.ShelfObjectLabelTest.test_etiqueta_png_real` | 7.5 | 341.9 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column.ButtonsActionsTableColumn.test_decrease_shelfobject` | 6.6 | 328.0 |
| `report.tests.test_cov2_report_ramas.RegencyPdfTest.test_base_pdf_usa_la_tabla_de_regencia` | 6.0 | 340.2 |
| `laboratory.tests.selenium_tests.informs.test_informs.InformSeleniumTest.test_add_inform` | 5.7 | 327.2 |
| `laboratory.tests.selenium_tests.informs.test_inform_template.InformsSeleniumTest.test_add_checkbox_derb` | 5.7 | 327.1 |
| `organilab_test.tests.test_url_smoke.LaboratoryUrlSmokeTest.test_paginas_responden` | 5.7 | 334.2 |
| `risk_management.tests.test_clasificacion_regencia.GetInventoryCasosBordeTest.test_codigos_h_de_la_sustancia` | 5.7 | 352.2 |
| `risk_management.tests.test_clasificacion_regencia.ClasificarEstablecimientoTest.test_advertencias_llevan_el_nombre_de_la_sustancia` | 5.7 | 338.1 |
| `academic.tests.selenium_tests.test_my_procedure.MyProcedureSeleniumTest.test_add_my_procedure` | 5.6 | 327.0 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_furniture.FurnitureSeleniumTest.test_add_furniture_type` | 5.5 | 336.6 |
| `organilab_test.tests.test_url_smoke.SgaUrlSmokeTest.test_paginas_responden` | 5.3 | 338.0 |
| `academic.tests.test_procedure.AcademicTest.test_add_step_procedure` | 5.3 | 329.1 |
| `report.tests.selenium_tests.test_regency_and_precursor.RegencyReportTest.test_regency_report_flow` | 5.2 | 348.1 |
| `laboratory.tests.selenium_tests.laboratory_view.test_shelfobject_detail_actions.ShelfObjectInfoButtonsActions.test_add_shelfobject_observation` | 4.8 | 333.9 |
| `report.tests.test_regency_detail.RegencyReportDetailTest.test_ods_con_detalle` | 4.4 | 339.2 |
| `report.tests.test_regency_html.RegencyHtmlTest.test_el_pdf_reutiliza_lo_calculado` | 4.4 | 338.6 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap2_laboratorios.Cap2LabStructureTest.test_create_furniture` | 4.0 | 338.7 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap2_laboratorios.Cap2InventoryTest.test_view_shelf_object_details` | 3.9 | 335.6 |
| `risk_management.tests.test_utils_risk.CargarUmbralPorHTest.test_sin_categorias_devuelve_marco_vacio_con_columnas` | 3.8 | 342.4 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column.ButtonsActionsTableColumn.test_manage_shelfobject_container_available` | 3.8 | 335.3 |
| `sga.tests.test_label_engine.BlueprintFromSubstanceTest.test_blueprint_from_substance` | 3.7 | 339.8 |

## Memoria del navegador (chromedriver + Chrome)

| Prueba | RSS navegador MiB |
|--------|------------------:|
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_wrapper_top.CreateShelfObject.test_view_containers_by_shelf` | 2387.6 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_download_incident` | 2198.9 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column.ButtonsActionsTableColumn.test_view_shelfobject_logs` | 2170.9 |
| `laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_wrapper_top.CreateShelfObject.test_go_to_objects_by_furniture_report` | 2168.1 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap2_laboratorios.Cap2InventoryTest.test_view_shelf_object_logs` | 2116.3 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap2_laboratorios.Cap2InventoryTest.test_view_shelf_objects` | 2115.2 |
| `laboratory.tests.selenium_tests.laboratory_view.test_shelfobject_detail_actions.ShelfObjectInfoButtonsActions.test_view_equipment_details` | 2106.3 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_edit_regent` | 2101.8 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap5_reservaciones.Cap5ManageReservationsTest.test_return_product_flow` | 2091.2 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_objects.ObjectSeleniumTest.test_search_reactive` | 2090.3 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_remove_risk` | 2087.6 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap5_reservaciones.Cap5ManageReservationsTest.test_return_products` | 2086.2 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_edit_risk` | 2080.3 |
| `organilab_test.tests.selenium_tests.capacitacion.test_cap3_cajas.Cap3BoxesTest.test_increase_box` | 2075.8 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_add_regent` | 2042.2 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_update_risk_two` | 2021.9 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_objects.ObjectFeaturesSeleniumTest.test_view_object_features` | 2004.4 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_protocols.ProtocolsSeleniumTest.test_download_protocol` | 1999.3 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_delete_building` | 1982.7 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_delete_structure` | 1972.1 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_delete_regent` | 1960.9 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_add_risk` | 1959.6 |
| `risk_management.tests.selenium_tests.test_risk.RiskSeleniumTest.test_add_workday` | 1953.9 |
| `laboratory.tests.selenium_tests.manage_laboratory.test_objects.ObjectSeleniumTest.test_view_material` | 1943.9 |
| `academic.tests.selenium_tests.test_my_procedure.MyProcedureSeleniumTest.test_delete_observation_my_procedure` | 1942.9 |

## Clases con setUpClass/tearDownClass más caros

Fixtures, arranque del navegador, live server. Se paga una vez por clase y por worker.

| Clase | veces | setUp s | tearDown s |
|-------|------:|--------:|-----------:|
| `reservations_management.tests.test_functions.ProductoYCantidadTest` | 1 | 26.21 | 0.01 |
| `organilab_test.tests.test_url_smoke.RiskUrlSmokeTest` | 1 | 19.82 | 0.01 |
| `organilab_test.tests.test_url_smoke.AmbientalUrlSmokeTest` | 1 | 19.71 | 0.01 |
| `organilab_test.tests.test_url_smoke.AcademicUrlSmokeTest` | 1 | 19.56 | 0.01 |
| `academic.tests.selenium_tests.test_procedure_template.ProcedureTemplateSeleniumTest` | 1 | 12.26 | 0.59 |
| `organilab_test.tests.test_url_smoke.LaboratoryUrlSmokeTest` | 1 | 11.86 | 0.01 |
| `organilab_test.tests.test_url_smoke.OrgUrlSmokeTest` | 1 | 11.6 | 0.01 |
| `organilab_test.tests.test_url_smoke.SgaUrlSmokeTest` | 1 | 11.27 | 0.01 |
| `organilab_test.tests.test_url_smoke.ReportUrlSmokeTest` | 1 | 11.24 | 0.01 |
| `risk_management.tests.test_incident.IncidentReportTest` | 1 | 10.62 | 0.01 |
| `reservations_management.tests.test_views_management.DevolverProductoTest` | 1 | 10.53 | 0.01 |
| `reservations_management.tests.test_functions.TareaDeDescuentoTest` | 1 | 10.51 | 0.01 |
| `reservations_management.tests.test_views_management.CerrarReservacionTest` | 1 | 10.51 | 0.01 |
| `reservations_management.tests.test_functions.ValidarReservacionTest` | 1 | 10.43 | 0.01 |
| `reservations_management.tests.test_forms_signals_api.ApiProductoReservadoTest` | 1 | 10.42 | 0.01 |
| `risk_management.tests.test_iper.IPERViewTest` | 1 | 10.37 | 0.01 |
| `reservations_management.tests.test_cov2_auth_reservations.DevolucionConCantidadNoFinitaTest` | 1 | 10.32 | 0.01 |
| `reservations_management.tests.test_tasks.DescontarCajasTest` | 1 | 10.22 | 0.01 |
| `reservations_management.tests.test_reservations.ReservationsTest` | 1 | 10.2 | 0.0 |
| `reservations_management.tests.test_views_management.GestionarReservacionTest` | 1 | 10.14 | 0.01 |
| `reservations_management.tests.test_functions.AumentarStockTest` | 1 | 10.11 | 0.0 |
| `risk_management.tests.test_zonetype.RiskZoneTest` | 1 | 10.06 | 0.01 |
| `reservations_management.tests.test_views_management.AccionSobreProductoTest` | 1 | 10.03 | 0.01 |
| `reservations_management.tests.test_functions.StockDeProductosReservadosTest` | 1 | 10.01 | 0.01 |
| `reservations_management.tests.test_forms_signals_api.SenalesTest` | 1 | 9.99 | 0.01 |

## Reportes contra volumen de datos

Cada reporte registrado, generado con la base sembrada a varias escalas (`seed_volume`). «Crecimiento» compara la escala mayor con la menor frente al crecimiento de los datos: > 1 es superlineal.

| Reporte | Formato | Escala | filas base | s | consultas | pico MiB | archivo KiB | estado |
|---------|---------|-------:|-----------:|--:|----------:|---------:|------------:|--------|
| `reactive_precursor` | html | 1 | 255 | 0.09 | 28 | 7.6 | 1 | ok |
| `reactive_precursor` | xlsx | 1 | 255 | 0.1 | 29 | 10.2 | 5 | ok |
| `reactive_precursor` | pdf | 1 | 255 | 0.23 | 29 | 9.1 | 17 | ok |
| `report_laboratory_room` | html | 1 | 255 | 0.19 | 16 | 7.7 | 23 | ok |
| `report_laboratory_room` | xlsx | 1 | 255 | 0.16 | 16 | 10.4 | 12 | ok |
| `report_laboratory_room` | pdf | 1 | 255 | 3.41 | 17 | 11.3 | 74 | ok |
| `report_objects` | html | 1 | 255 | 0.16 | 17 | 7.7 | 41 | ok |
| `report_objects` | xlsx | 1 | 255 | 0.19 | 17 | 10.4 | 14 | ok |
| `report_objects` | pdf | 1 | 255 | 4.14 | 18 | 15.3 | 136 | ok |
| `report_limit_objects` | html | 1 | 255 | 0.09 | 12 | 7.7 | 3 | ok |
| `report_limit_objects` | xlsx | 1 | 255 | 0.15 | 12 | 10.4 | 6 | ok |
| `report_limit_objects` | pdf | 1 | 255 | 0.43 | 13 | 9.1 | 22 | ok |
| `report_objectschanges` | html | 1 | 255 | 0.1 | 18 | 7.8 | 0 | ok |
| `report_objectschanges` | xlsx | 1 | 255 | 0.09 | 16 | 10.5 | 10 | ok |
| `report_objectschanges` | pdf | 1 | 255 | 2.64 | 23 | 11.3 | 88 | ok |
| `report_furniture` | html | 1 | 255 | 0.15 | 16 | 7.7 | 27 | ok |
| `report_furniture` | xlsx | 1 | 255 | 0.2 | 16 | 10.4 | 14 | ok |
| `report_furniture` | pdf | 1 | 255 | 3.73 | 17 | 11.3 | 82 | ok |
| `report_organization_reactive_list` | html | 1 | 255 | 0.09 | 53 | 7.6 | 2 | ok |
| `report_organization_reactive_list` | xlsx | 1 | 255 | 0.09 | 53 | 10.2 | 5 | ok |
| `report_organization_reactive_list` | pdf | 1 | 255 | 0.32 | 54 | 9.1 | 19 | ok |
| `report_waste_objects` | html | 1 | 255 | 0.05 | 11 | 7.6 | 6 | ok |
| `report_waste_objects` | xlsx | 1 | 255 | 0.06 | 12 | 10.2 | 7 | ok |
| `report_waste_objects` | pdf | 1 | 255 | 0.73 | 12 | 9.1 | 28 | ok |
| `reactive_report` | html | 1 | 255 | 0.14 | 16 | 7.7 | 14 | ok |
| `reactive_report` | xlsx | 1 | 255 | 0.16 | 16 | 10.4 | 10 | ok |
| `reactive_report` | pdf | 1 | 255 | 2.1 | 17 | 11.3 | 56 | ok |
| `risk_zone_report` | html | 1 | 255 | 0.05 | 12 | 7.6 | 1 | ok |
| `risk_zone_report` | xlsx | 1 | 255 | 0.06 | 12 | 10.4 | 5 | ok |
| `risk_zone_report` | pdf | 1 | 255 | 0.24 | 13 | 9.1 | 17 | ok |
| `stock_reactive_report` | xlsx | 1 | 255 | 0.1 | 20 | 10.4 | 6 | ok |
| `regency_report` | html | 1 | 255 | 0.13 | 16 | 15.3 | 3 | ok |
| `regency_report` | xlsx | 1 | 255 | 0.15 | 18 | 17.8 | 7 | ok |
| `regency_report` | pdf | 1 | 255 | 0.43 | 17 | 16.4 | 23 | ok |
| `compatibility_report` | html | 1 | 255 | 0.09 | 12 | 7.7 | 181 | ok |
| `compatibility_report` | ods | 1 | 255 | 0.16 | 38 | 10.1 | 7 | ok |
| `compatibility_report` | pdf | 1 | 255 | 12.6 | 13 | 97.3 | 358 | ok |
| `hazard_map_report` | html | 1 | 255 | 0.2 | 80 | 7.7 | 48 | ok |
| `hazard_map_report` | pdf | 1 | 255 | 1.76 | 81 | 11.3 | 46 | ok |
| `chemicalinventory` | html | 1 | 255 | 0.08 | 11 | 7.7 | 9 | ok |
| `chemicalinventory` | xlsx | 1 | 255 | 0.09 | 11 | 10.4 | 8 | ok |
| `chemicalinventory` | pdf | 1 | 255 | 1.42 | 12 | 11.3 | 39 | ok |
| `donations_report` | html | 1 | 255 | 0.07 | 8 | 7.6 | 3 | ok |
| `donations_report` | xlsx | 1 | 255 | 0.06 | 8 | 10.2 | 6 | ok |
| `donations_report` | pdf | 1 | 255 | 0.37 | 9 | 9.1 | 21 | ok |
| `report_consumption_detail` | html | 1 | 255 | 0.07 | 12 | 7.8 | 13 | ok |
| `report_consumption_detail` | xlsx | 1 | 255 | 0.09 | 12 | 10.5 | 9 | ok |
| `report_consumption_detail` | pdf | 1 | 255 | 1.96 | 12 | 11.4 | 48 | ok |
| `report_consumption_summary` | html | 1 | 255 | 0.07 | 12 | 7.8 | 6 | ok |
| `report_consumption_summary` | xlsx | 1 | 255 | 0.09 | 12 | 10.5 | 7 | ok |
| `report_consumption_summary` | pdf | 1 | 255 | 1.34 | 12 | 11.4 | 33 | ok |
| `report_consumption_cost` | html | 1 | 255 | 0.06 | 12 | 7.6 | 0 | ok |
| `report_consumption_cost` | xlsx | 1 | 255 | 0.07 | 12 | 10.2 | 4 | ok |
| `report_consumption_cost` | pdf | 1 | 255 | 0.12 | 12 | 9.1 | 14 | ok |
| `report_environmental_indicators` | html | 1 | 255 | 0.11 | 62 | 7.7 | 2 | ok |
| `report_environmental_indicators` | xlsx | 1 | 255 | 0.13 | 62 | 10.4 | 5 | ok |
| `report_environmental_indicators` | pdf | 1 | 255 | 0.29 | 62 | 9.1 | 17 | ok |
| `report_consumption_comparison` | html | 1 | 255 | 0.1 | 45 | 7.7 | 1 | ok |
| `report_consumption_comparison` | xlsx | 1 | 255 | 0.1 | 45 | 10.4 | 5 | ok |
| `report_consumption_comparison` | pdf | 1 | 255 | 0.21 | 45 | 9.1 | 16 | ok |
| `report_waste_manifest` | html | 1 | 255 | 0.06 | 12 | 7.8 | 5 | ok |
| `report_waste_manifest` | xlsx | 1 | 255 | 0.12 | 12 | 10.5 | 6 | ok |
| `report_waste_manifest` | pdf | 1 | 255 | 0.53 | 12 | 9.2 | 27 | ok |
| `reactive_precursor` | html | 10 | 2415 | 0.35 | 109 | 7.7 | 6 | ok |
| `reactive_precursor` | xlsx | 10 | 2415 | 0.36 | 110 | 10.4 | 7 | ok |
| `reactive_precursor` | pdf | 10 | 2415 | 1.37 | 110 | 11.3 | 29 | ok |
| `report_laboratory_room` | html | 10 | 2415 | 1.3 | 16 | 14.5 | 216 | ok |
| `report_laboratory_room` | xlsx | 10 | 2415 | 1.48 | 16 | 16.9 | 71 | ok |
| `report_laboratory_room` | pdf | 10 | 2415 | 29.74 | 17 | 164.8 | 585 | ok |
| `report_objects` | html | 10 | 2415 | 1.41 | 17 | 14.7 | 389 | ok |
| `report_objects` | xlsx | 10 | 2415 | 1.65 | 17 | 17.0 | 88 | ok |
| `report_objects` | pdf | 10 | 2415 | 38.03 | 18 | 291.6 | 1207 | ok |
| `report_limit_objects` | html | 10 | 2415 | 0.32 | 21 | 7.7 | 29 | ok |
| `report_limit_objects` | xlsx | 10 | 2415 | 0.32 | 21 | 10.4 | 15 | ok |
| `report_limit_objects` | pdf | 10 | 2415 | 4.91 | 22 | 15.3 | 103 | ok |
| `report_objectschanges` | html | 10 | 2415 | 0.77 | 18 | 10.1 | 1 | ok |
| `report_objectschanges` | xlsx | 10 | 2415 | 0.28 | 16 | 10.5 | 61 | ok |
| `report_objectschanges` | pdf | 10 | 2415 | 21.75 | 23 | 121.5 | 783 | ok |
| `report_furniture` | html | 10 | 2415 | 1.3 | 16 | 14.8 | 254 | ok |
| `report_furniture` | xlsx | 10 | 2415 | 1.47 | 16 | 17.2 | 89 | ok |
| `report_furniture` | pdf | 10 | 2415 | 31.05 | 17 | 193.2 | 655 | ok |
| `report_organization_reactive_list` | html | 10 | 2415 | 0.43 | 395 | 7.7 | 21 | ok |
| `report_organization_reactive_list` | xlsx | 10 | 2415 | 0.42 | 395 | 10.4 | 12 | ok |
| `report_organization_reactive_list` | pdf | 10 | 2415 | 2.74 | 396 | 11.3 | 63 | ok |
| `report_waste_objects` | html | 10 | 2415 | 0.09 | 20 | 7.6 | 55 | ok |
| `report_waste_objects` | xlsx | 10 | 2415 | 0.14 | 21 | 10.2 | 23 | ok |
| `report_waste_objects` | pdf | 10 | 2415 | 6.77 | 21 | 27.3 | 158 | ok |
| `reactive_report` | html | 10 | 2415 | 1.08 | 16 | 10.1 | 127 | ok |
| `reactive_report` | xlsx | 10 | 2415 | 1.17 | 16 | 12.4 | 59 | ok |
| `reactive_report` | pdf | 10 | 2415 | 16.69 | 17 | 85.6 | 399 | ok |
| `risk_zone_report` | html | 10 | 2415 | 0.09 | 12 | 7.7 | 11 | ok |
| `risk_zone_report` | xlsx | 10 | 2415 | 0.12 | 12 | 10.4 | 9 | ok |
| `risk_zone_report` | pdf | 10 | 2415 | 2.09 | 13 | 11.3 | 48 | ok |
| `stock_reactive_report` | xlsx | 10 | 2415 | 0.32 | 56 | 10.4 | 17 | ok |
| `regency_report` | html | 10 | 2415 | 0.47 | 16 | 15.1 | 25 | ok |
| `regency_report` | xlsx | 10 | 2415 | 0.69 | 18 | 17.6 | 17 | ok |
| `regency_report` | pdf | 10 | 2415 | 4.41 | 17 | 20.9 | 84 | ok |
| `compatibility_report` | html | 10 | 2415 | 0.54 | 57 | 19.4 | 1845 | ok |
| `compatibility_report` | ods | 10 | 2415 | 1.24 | 324 | 31.7 | 57 | ok |
| `compatibility_report` | pdf | 10 | 2415 | 135.32 | 58 | 1204.4 | 3463 | ok |
| `hazard_map_report` | html | 10 | 2415 | 1.31 | 503 | 7.7 | 462 | ok |
| `hazard_map_report` | pdf | 10 | 2415 | 17.32 | 504 | 60.3 | 307 | ok |
| `chemicalinventory` | html | 10 | 2415 | 1.25 | 11 | 10.1 | 88 | ok |
| `chemicalinventory` | xlsx | 10 | 2415 | 1.45 | 11 | 12.4 | 40 | ok |
| `chemicalinventory` | pdf | 10 | 2415 | 13.25 | 12 | 52.3 | 266 | ok |
| `donations_report` | html | 10 | 2415 | 0.1 | 8 | 7.7 | 30 | ok |
| `donations_report` | xlsx | 10 | 2415 | 0.12 | 8 | 10.4 | 15 | ok |
| `donations_report` | pdf | 10 | 2415 | 4.17 | 9 | 11.3 | 87 | ok |
| `report_consumption_detail` | html | 10 | 2415 | 0.32 | 12 | 7.8 | 130 | ok |
| `report_consumption_detail` | xlsx | 10 | 2415 | 0.4 | 12 | 10.5 | 47 | ok |
| `report_consumption_detail` | pdf | 10 | 2415 | 16.86 | 12 | 86.4 | 351 | ok |
| `report_consumption_summary` | html | 10 | 2415 | 0.19 | 12 | 7.8 | 65 | ok |
| `report_consumption_summary` | xlsx | 10 | 2415 | 0.24 | 12 | 10.5 | 30 | ok |
| `report_consumption_summary` | pdf | 10 | 2415 | 9.04 | 12 | 39.1 | 208 | ok |
| `report_consumption_cost` | html | 10 | 2415 | 0.05 | 12 | 7.6 | 0 | ok |
| `report_consumption_cost` | xlsx | 10 | 2415 | 0.08 | 12 | 10.2 | 4 | ok |
| `report_consumption_cost` | pdf | 10 | 2415 | 0.13 | 12 | 9.1 | 14 | ok |
| `report_environmental_indicators` | html | 10 | 2415 | 0.93 | 494 | 7.7 | 14 | ok |
| `report_environmental_indicators` | xlsx | 10 | 2415 | 0.97 | 494 | 10.4 | 9 | ok |
| `report_environmental_indicators` | pdf | 10 | 2415 | 2.52 | 494 | 11.4 | 47 | ok |
| `report_consumption_comparison` | html | 10 | 2415 | 0.54 | 333 | 7.7 | 7 | ok |
| `report_consumption_comparison` | xlsx | 10 | 2415 | 0.52 | 333 | 10.4 | 7 | ok |
| `report_consumption_comparison` | pdf | 10 | 2415 | 1.61 | 333 | 11.4 | 32 | ok |
| `report_waste_manifest` | html | 10 | 2415 | 0.11 | 12 | 7.8 | 50 | ok |
| `report_waste_manifest` | xlsx | 10 | 2415 | 0.14 | 12 | 10.5 | 20 | ok |
| `report_waste_manifest` | pdf | 10 | 2415 | 5.56 | 12 | 20.3 | 136 | ok |
| `reactive_precursor` | html | 100 | 24015 | 1.9 | 919 | 7.7 | 51 | ok |
| `reactive_precursor` | xlsx | 100 | 24015 | 1.9 | 920 | 10.4 | 27 | ok |
| `reactive_precursor` | pdf | 100 | 24015 | 8.94 | 920 | 30.0 | 165 | ok |
| `report_laboratory_room` | html | 100 | 24015 | 9.08 | 16 | 370.4 | 2182 | ok |
| `report_laboratory_room` | xlsx | 100 | 24015 | 11.29 | 16 | 372.2 | 661 | ok |
| `report_laboratory_room` | pdf | 100 | 24015 | 294.06 | 17 | 2122.0 | 5699 | ok |
| `report_objects` | html | 100 | 24015 | 10.75 | 17 | 371.5 | 3873 | ok |
| `report_objects` | xlsx | 100 | 24015 | 11.44 | 17 | 372.4 | 829 | ok |
| `report_objects` | pdf | 100 | 24015 | — | — | — | — | tiempo |
| `report_limit_objects` | html | 100 | 24015 | 2.85 | 111 | 7.7 | 293 | ok |
| `report_limit_objects` | xlsx | 100 | 24015 | 3.65 | 111 | 10.4 | 109 | ok |
| `report_limit_objects` | pdf | 100 | 24015 | 45.14 | 112 | 307.5 | 913 | ok |
| `report_objectschanges` | html | 100 | 24015 | 2.7 | 20 | 22.6 | 18 | ok |
| `report_objectschanges` | xlsx | 100 | 24015 | 2.59 | 16 | 25.0 | 549 | ok |
| `report_objectschanges` | pdf | 100 | 24015 | — | — | — | — | tiempo |
| `report_furniture` | html | 100 | 24015 | 9.23 | 16 | 372.1 | 2558 | ok |
| `report_furniture` | xlsx | 100 | 24015 | 10.57 | 16 | 373.2 | 840 | ok |
| `report_furniture` | pdf | 100 | 24015 | — | — | — | — | tiempo |
| `report_organization_reactive_list` | html | 100 | 24015 | 3.04 | 3813 | 7.7 | 205 | ok |
| `report_organization_reactive_list` | xlsx | 100 | 24015 | 3.46 | 3813 | 10.4 | 74 | ok |
| `report_organization_reactive_list` | pdf | 100 | 24015 | 24.17 | 3814 | 131.7 | 497 | ok |
| `report_waste_objects` | html | 100 | 24015 | 0.57 | 110 | 7.7 | 557 | ok |
| `report_waste_objects` | xlsx | 100 | 24015 | 0.83 | 111 | 10.4 | 187 | ok |
| `report_waste_objects` | pdf | 100 | 24015 | 66.07 | 111 | 501.4 | 1465 | ok |
| `reactive_report` | html | 100 | 24015 | 5.24 | 16 | 141.3 | 1274 | ok |
| `reactive_report` | xlsx | 100 | 24015 | 6.0 | 16 | 136.1 | 541 | ok |
| `reactive_report` | pdf | 100 | 24015 | 166.52 | 17 | 1249.5 | 3855 | ok |
| `risk_zone_report` | html | 100 | 24015 | 0.69 | 12 | 10.1 | 116 | ok |
| `risk_zone_report` | xlsx | 100 | 24015 | 0.79 | 12 | 12.4 | 49 | ok |
| `risk_zone_report` | pdf | 100 | 24015 | 15.15 | 13 | 82.9 | 360 | ok |
| `stock_reactive_report` | xlsx | 100 | 24015 | 2.4 | 416 | 10.4 | 117 | ok |
| `regency_report` | html | 100 | 24015 | 3.78 | 16 | 16.9 | 247 | ok |
| `regency_report` | xlsx | 100 | 24015 | 6.1 | 18 | 19.2 | 119 | ok |
| `regency_report` | pdf | 100 | 24015 | 85.56 | 17 | 1572.5 | 708 | ok |
| `compatibility_report` | html | 100 | 24015 | 4.55 | 507 | 167.4 | 19301 | ok |
| `compatibility_report` | ods | 100 | 24015 | 10.4 | 3186 | 331.0 | 562 | ok |
| `compatibility_report` | pdf | 100 | 24015 | — | — | — | — | memoria |
| `hazard_map_report` | html | 100 | 24015 | 10.82 | 4378 | 37.1 | 4677 | ok |
| `hazard_map_report` | pdf | 100 | 24015 | 126.2 | 4379 | 947.5 | 2890 | ok |
| `chemicalinventory` | html | 100 | 24015 | 2.76 | 11 | 48.9 | 899 | ok |
| `chemicalinventory` | xlsx | 100 | 24015 | 3.25 | 11 | 50.9 | 352 | ok |
| `chemicalinventory` | pdf | 100 | 24015 | 102.46 | 12 | 832.4 | 2543 | ok |
| `donations_report` | html | 100 | 24015 | 0.46 | 8 | 7.7 | 305 | ok |
| `donations_report` | xlsx | 100 | 24015 | 0.64 | 8 | 10.4 | 109 | ok |
| `donations_report` | pdf | 100 | 24015 | 36.05 | 9 | 249.5 | 752 | ok |
| `report_consumption_detail` | html | 100 | 24015 | 1.67 | 12 | 36.1 | 1312 | ok |
| `report_consumption_detail` | xlsx | 100 | 24015 | 2.35 | 12 | 27.4 | 433 | ok |
| `report_consumption_detail` | pdf | 100 | 24015 | 153.91 | 12 | 1252.0 | 3404 | ok |
| `report_consumption_summary` | html | 100 | 24015 | 1.59 | 12 | 25.2 | 657 | ok |
| `report_consumption_summary` | xlsx | 100 | 24015 | 2.01 | 12 | 25.2 | 243 | ok |
| `report_consumption_summary` | pdf | 100 | 24015 | 86.8 | 12 | 648.9 | 1949 | ok |
| `report_consumption_cost` | html | 100 | 24015 | 0.06 | 12 | 7.6 | 0 | ok |
| `report_consumption_cost` | xlsx | 100 | 24015 | 0.07 | 12 | 10.2 | 4 | ok |
| `report_consumption_cost` | pdf | 100 | 24015 | 0.12 | 12 | 9.1 | 14 | ok |
| `report_environmental_indicators` | html | 100 | 24015 | 6.67 | 4814 | 7.8 | 141 | ok |
| `report_environmental_indicators` | xlsx | 100 | 24015 | 6.97 | 4814 | 10.5 | 45 | ok |
| `report_environmental_indicators` | pdf | 100 | 24015 | 21.64 | 4814 | 71.1 | 345 | ok |
| `report_consumption_comparison` | html | 100 | 24015 | 4.78 | 3213 | 7.8 | 65 | ok |
| `report_consumption_comparison` | xlsx | 100 | 24015 | 4.85 | 3213 | 10.5 | 27 | ok |
| `report_consumption_comparison` | pdf | 100 | 24015 | 12.71 | 3213 | 28.9 | 185 | ok |
| `report_waste_manifest` | html | 100 | 24015 | 0.55 | 12 | 7.8 | 498 | ok |
| `report_waste_manifest` | xlsx | 100 | 24015 | 0.89 | 12 | 10.5 | 162 | ok |
| `report_waste_manifest` | pdf | 100 | 24015 | 53.32 | 12 | 402.7 | 1249 | ok |

| Reporte | Formato | crecimiento tiempo | crecimiento memoria | veredicto |
|---------|---------|-------------------:|--------------------:|-----------|
| `chemicalinventory` | html | 0.37 | 0.07 | sublineal |
| `chemicalinventory` | pdf | 0.77 | 0.78 | lineal |
| `chemicalinventory` | xlsx | 0.38 | 0.05 | sublineal |
| `compatibility_report` | html | 0.54 | 0.23 | lineal |
| `compatibility_report` | ods | 0.69 | 0.35 | lineal |
| `compatibility_report` | pdf | — | — | no escala: memoria a escala 100 |
| `donations_report` | html | 0.07 | 0.01 | sublineal |
| `donations_report` | pdf | 1.03 | 0.29 | lineal |
| `donations_report` | xlsx | 0.11 | 0.01 | sublineal |
| `hazard_map_report` | html | 0.57 | 0.05 | lineal |
| `hazard_map_report` | pdf | 0.76 | 0.89 | lineal |
| `reactive_precursor` | html | 0.22 | 0.01 | sublineal |
| `reactive_precursor` | pdf | 0.41 | 0.04 | sublineal |
| `reactive_precursor` | xlsx | 0.2 | 0.01 | sublineal |
| `reactive_report` | html | 0.4 | 0.19 | sublineal |
| `reactive_report` | pdf | 0.84 | 1.17 | lineal |
| `reactive_report` | xlsx | 0.4 | 0.14 | sublineal |
| `regency_report` | html | 0.31 | 0.01 | sublineal |
| `regency_report` | pdf | 2.11 | 1.02 | superlineal |
| `regency_report` | xlsx | 0.43 | 0.01 | sublineal |
| `report_consumption_comparison` | html | 0.51 | 0.01 | lineal |
| `report_consumption_comparison` | pdf | 0.64 | 0.03 | lineal |
| `report_consumption_comparison` | xlsx | 0.51 | 0.01 | lineal |
| `report_consumption_cost` | html | 0.01 | 0.01 | sublineal |
| `report_consumption_cost` | pdf | 0.01 | 0.01 | sublineal |
| `report_consumption_cost` | xlsx | 0.01 | 0.01 | sublineal |
| `report_consumption_detail` | html | 0.25 | 0.05 | sublineal |
| `report_consumption_detail` | pdf | 0.83 | 1.16 | lineal |
| `report_consumption_detail` | xlsx | 0.28 | 0.03 | sublineal |
| `report_consumption_summary` | html | 0.24 | 0.03 | sublineal |
| `report_consumption_summary` | pdf | 0.69 | 0.6 | lineal |
| `report_consumption_summary` | xlsx | 0.24 | 0.03 | sublineal |
| `report_environmental_indicators` | html | 0.64 | 0.01 | lineal |
| `report_environmental_indicators` | pdf | 0.79 | 0.08 | lineal |
| `report_environmental_indicators` | xlsx | 0.57 | 0.01 | lineal |
| `report_furniture` | html | 0.65 | 0.51 | lineal |
| `report_furniture` | pdf | — | — | no escala: tiempo a escala 100 |
| `report_furniture` | xlsx | 0.56 | 0.38 | lineal |
| `report_laboratory_room` | html | 0.51 | 0.51 | lineal |
| `report_laboratory_room` | pdf | 0.92 | 1.99 | superlineal |
| `report_laboratory_room` | xlsx | 0.75 | 0.38 | lineal |
| `report_limit_objects` | html | 0.34 | 0.01 | sublineal |
| `report_limit_objects` | pdf | 1.11 | 0.36 | lineal |
| `report_limit_objects` | xlsx | 0.26 | 0.01 | sublineal |
| `report_objects` | html | 0.71 | 0.51 | lineal |
| `report_objects` | pdf | — | — | no escala: tiempo a escala 100 |
| `report_objects` | xlsx | 0.64 | 0.38 | lineal |
| `report_objectschanges` | html | 0.29 | 0.03 | sublineal |
| `report_objectschanges` | pdf | — | — | no escala: tiempo a escala 100 |
| `report_objectschanges` | xlsx | 0.31 | 0.03 | sublineal |
| `report_organization_reactive_list` | html | 0.36 | 0.01 | sublineal |
| `report_organization_reactive_list` | pdf | 0.8 | 0.15 | lineal |
| `report_organization_reactive_list` | xlsx | 0.41 | 0.01 | sublineal |
| `report_waste_manifest` | html | 0.1 | 0.01 | sublineal |
| `report_waste_manifest` | pdf | 1.07 | 0.47 | lineal |
| `report_waste_manifest` | xlsx | 0.08 | 0.01 | sublineal |
| `report_waste_objects` | html | 0.12 | 0.01 | sublineal |
| `report_waste_objects` | pdf | 0.96 | 0.59 | lineal |
| `report_waste_objects` | xlsx | 0.15 | 0.01 | sublineal |
| `risk_zone_report` | html | 0.15 | 0.01 | sublineal |
| `risk_zone_report` | pdf | 0.67 | 0.1 | lineal |
| `risk_zone_report` | xlsx | 0.14 | 0.01 | sublineal |
| `stock_reactive_report` | xlsx | 0.25 | 0.01 | sublineal |

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

