# Cobertura de código

Generado con `make coverage-all` (suite sin navegador + Selenium headless, unidas con `coverage combine`). No editar a mano: `make coverage-summary` lo regenera.

- Fecha: 2026-10-12 10:33
- Commit: `877c9c09d`
- **Total: 66.8%** — 38795 sentencias, 12892 sin cubrir, 465 archivos

## Por app

| App | Archivos | Sentencias | Sin cubrir | Cobertura |
|-----|---------:|-----------:|-----------:|----------:|
| `laboratory` | 128 | 15775 | 5652 | 64.2% |
| `presentation` | 55 | 3132 | 1486 | 52.6% |
| `sga` | 66 | 5050 | 1327 | 73.7% |
| `report` | 28 | 3257 | 1268 | 61.1% |
| `auth_and_perms` | 47 | 3330 | 1220 | 63.4% |
| `risk_management` | 23 | 3234 | 903 | 72.1% |
| `reservations_management` | 13 | 706 | 377 | 46.6% |
| `academic` | 15 | 1131 | 178 | 84.3% |
| `authentication` | 12 | 384 | 123 | 68.0% |
| `msds` | 10 | 330 | 108 | 67.3% |
| `ambiental` | 25 | 1508 | 79 | 94.8% |
| `api` | 9 | 116 | 72 | 37.9% |
| `pending_tasks` | 12 | 271 | 40 | 85.2% |
| `organilab` | 9 | 227 | 36 | 84.1% |
| `derb` | 13 | 344 | 23 | 93.3% |

## Archivos con más líneas sin cubrir (top 40)

| Archivo | Sentencias | Sin cubrir | Cobertura |
|---------|-----------:|-----------:|----------:|
| `laboratory/api/shelfobject.py` | 1012 | 442 | 56.3% |
| `laboratory/shelfobject/serializers.py` | 1547 | 379 | 75.5% |
| `laboratory/utils_pdf.py` | 327 | 273 | 16.5% |
| `risk_management/utils_risk.py` | 320 | 258 | 19.4% |
| `report/utils.py` | 328 | 240 | 26.8% |
| `laboratory/views/shelfobject.py` | 392 | 235 | 40.1% |
| `laboratory/management/commands/update_sustance_from_security_sheet.py` | 215 | 215 | 0.0% |
| `presentation/perf.py` | 231 | 208 | 10.0% |
| `sga/management/commands/test_objs.py` | 234 | 206 | 12.0% |
| `laboratory/sds_sources/pubchem.py` | 225 | 201 | 10.7% |
| `presentation/management/commands/perf_report.py` | 191 | 191 | 0.0% |
| `reservations_management/functions.py` | 270 | 188 | 30.4% |
| `laboratory/gtselects.py` | 563 | 187 | 66.8% |
| `report/views/base.py` | 370 | 178 | 51.9% |
| `risk_management/compatibility_utils.py` | 266 | 177 | 33.5% |
| `laboratory/api/serializers.py` | 1144 | 176 | 84.6% |
| `laboratory/api/views.py` | 940 | 170 | 81.9% |
| `auth_and_perms/management/commands/update_roles.py` | 222 | 164 | 26.1% |
| `risk_management/iper_views.py` | 432 | 161 | 62.7% |
| `laboratory/management/commands/upload_org_and_users.py` | 154 | 154 | 0.0% |
| `laboratory/management/commands/validate_pubchem_sds.py` | 189 | 150 | 20.6% |
| `presentation/management/commands/perf_reports.py` | 143 | 143 | 0.0% |
| `sga/views/editor.py` | 330 | 140 | 57.6% |
| `risk_management/gtcharts.py` | 565 | 136 | 75.9% |
| `laboratory/sds_sources/merck.py` | 164 | 132 | 19.5% |
| `report/views/regency.py` | 153 | 132 | 13.7% |
| `report/views/objects.py` | 345 | 130 | 62.3% |
| `laboratory/management/commands/set_mediafiles_names.py` | 124 | 124 | 0.0% |
| `laboratory/tasks.py` | 227 | 123 | 45.8% |
| `presentation/management/commands/feature_catalog.py` | 233 | 123 | 47.2% |
| `presentation/perf_volume.py` | 121 | 121 | 0.0% |
| `report/views/riskzones.py` | 271 | 118 | 56.5% |
| `sga/tagsT.py` | 118 | 118 | 0.0% |
| `laboratory/management/commands/identify_sds_sources.py` | 113 | 113 | 0.0% |
| `laboratory/forms.py` | 706 | 111 | 84.3% |
| `laboratory/shelfobject/utils.py` | 362 | 103 | 71.5% |
| `laboratory/management/commands/clean_orphan_media.py` | 101 | 101 | 0.0% |
| `report/api/views.py` | 254 | 101 | 60.2% |
| `laboratory/management/commands/repair_laboratories.py` | 97 | 97 | 0.0% |
| `laboratory/management/commands/update_sds.py` | 96 | 96 | 0.0% |

## Archivos nunca ejecutados (71)

Candidatos a código muerto antes que a pruebas nuevas.

- `ambiental/management/commands/seed_ambiental_catalog.py` (8 sentencias)
- `api/views.py` (1 sentencias)
- `auth_and_perms/authBackend.py` (21 sentencias)
- `auth_and_perms/management/commands/add_laboratory_profile_in_org.py` (19 sentencias)
- `auth_and_perms/management/commands/add_pendingtask_permissions_to_roles.py` (49 sentencias)
- `auth_and_perms/management/commands/add_static_rol.py` (15 sentencias)
- `auth_and_perms/management/commands/check_roles_permissions.py` (85 sentencias)
- `auth_and_perms/management/commands/clean_orphaned_profilepermissions.py` (18 sentencias)
- `auth_and_perms/management/commands/clean_permissions.py` (33 sentencias)
- `auth_and_perms/management/commands/clean_solo_lectura_permissions.py` (45 sentencias)
- `auth_and_perms/management/commands/create_demo_organizations.py` (77 sentencias)
- `auth_and_perms/management/commands/create_pendingtasks_group.py` (37 sentencias)
- `auth_and_perms/management/commands/groups_by_views_without_org_lab.py` (19 sentencias)
- `auth_and_perms/management/commands/load_urlname_permissions.py` (40 sentencias)
- `auth_and_perms/management/commands/remove_groups.py` (21 sentencias)
- `auth_and_perms/management/commands/update_profile.py` (26 sentencias)
- `auth_and_perms/management/commands/update_roles_permissions.py` (20 sentencias)
- `auth_and_perms/views/fva_receptor.py` (11 sentencias)
- `authentication/oidc_backend.py` (88 sentencias)
- `authentication/serializer.py` (6 sentencias)
- `laboratory/generic.py` (7 sentencias)
- `laboratory/import_cl_inventory.py` (8 sentencias)
- `laboratory/import_materiales.py` (48 sentencias)
- `laboratory/management/commands/add_shelfobject_id.py` (16 sentencias)
- `laboratory/management/commands/check_security_sheets.py` (62 sentencias)
- `laboratory/management/commands/clean_orphan_media.py` (101 sentencias)
- `laboratory/management/commands/cleanup_groups.py` (30 sentencias)
- `laboratory/management/commands/create_qr.py` (35 sentencias)
- `laboratory/management/commands/find_duplicate_objects.py` (77 sentencias)
- `laboratory/management/commands/fix_object_log_amounts.py` (38 sentencias)
- `laboratory/management/commands/fix_pubchem_revision_dates.py` (20 sentencias)
- `laboratory/management/commands/identify_sds_sources.py` (113 sentencias)
- `laboratory/management/commands/merge_organizations.py` (87 sentencias)
- `laboratory/management/commands/move_organization_data.py` (54 sentencias)
- `laboratory/management/commands/new_units.py` (10 sentencias)
- `laboratory/management/commands/precursor_report.py` (30 sentencias)
- `laboratory/management/commands/repair_laboratories.py` (97 sentencias)
- `laboratory/management/commands/repair_shelfobject_created_by.py` (22 sentencias)
- `laboratory/management/commands/set_mediafiles_names.py` (124 sentencias)
- `laboratory/management/commands/set_permissions.py` (39 sentencias)
- `laboratory/management/commands/set_subject_msg.py` (15 sentencias)
- `laboratory/management/commands/setup_sga_view_group.py` (25 sentencias)
- `laboratory/management/commands/sync_susta_charac.py` (46 sentencias)
- `laboratory/management/commands/update_sds.py` (96 sentencias)
- `laboratory/management/commands/update_sustance_from_security_sheet.py` (215 sentencias)
- `laboratory/management/commands/update_sustances_cha.py` (85 sentencias)
- `laboratory/management/commands/update_vitek.py` (23 sentencias)
- `laboratory/management/commands/upload_org_and_users.py` (154 sentencias)
- `laboratory/sustance/forms.py` (16 sentencias)
- `laboratory/sustance/views.py` (53 sentencias)
- `laboratory/views/upload_reactives.py` (6 sentencias)
- `organilab/asettings.py` (2 sentencias)
- `organilab/asgi.py` (2 sentencias)
- `organilab/aurls.py` (1 sentencias)
- `organilab/wsgi.py` (4 sentencias)
- `presentation/management/commands/clean_db.py` (30 sentencias)
- `presentation/management/commands/coverage_summary.py` (61 sentencias)
- `presentation/management/commands/export_sustances.py` (50 sentencias)
- `presentation/management/commands/import_sustances.py` (80 sentencias)
- `presentation/management/commands/organilab_install.py` (41 sentencias)
- `presentation/management/commands/perf_report.py` (191 sentencias)
- `presentation/management/commands/perf_reports.py` (143 sentencias)
- `presentation/perf_volume.py` (121 sentencias)
- `presentation/tasks.py` (16 sentencias)
- `risk_management/utils.py` (3 sentencias)
- `sga/management/commands/clean_orphan_characteristics.py` (19 sentencias)
- `sga/management/commands/load_danger_indications.py` (29 sentencias)
- `sga/management/commands/load_danger_substances.py` (55 sentencias)
- `sga/management/commands/load_danger_substances_category.py` (56 sentencias)
- `sga/management/commands/merge_duplicate_warning_words.py` (29 sentencias)
- `sga/tagsT.py` (118 sentencias)
