# Cobertura de código

Generado con `make coverage-all` (suite sin navegador + Selenium headless, unidas con `coverage combine`). No editar a mano: `make coverage-summary` lo regenera.

- Fecha: 2026-10-12 11:17
- Commit: `a50bb3190`
- **Total: 75.5%** — 33380 sentencias, 8187 sin cubrir, 373 archivos

## Por app

| App | Archivos | Sentencias | Sin cubrir | Cobertura |
|-----|---------:|-----------:|-----------:|----------:|
| `laboratory` | 90 | 13274 | 3310 | 75.1% |
| `report` | 28 | 3257 | 1272 | 60.9% |
| `risk_management` | 23 | 3235 | 916 | 71.7% |
| `sga` | 56 | 4482 | 813 | 81.9% |
| `auth_and_perms` | 27 | 2561 | 539 | 79.0% |
| `reservations_management` | 13 | 706 | 377 | 46.6% |
| `presentation` | 41 | 1744 | 343 | 80.3% |
| `academic` | 15 | 1131 | 178 | 84.3% |
| `authentication` | 11 | 378 | 117 | 69.0% |
| `msds` | 10 | 330 | 108 | 67.3% |
| `api` | 9 | 116 | 72 | 37.9% |
| `ambiental` | 22 | 1500 | 71 | 95.3% |
| `pending_tasks` | 12 | 271 | 40 | 85.2% |
| `derb` | 13 | 344 | 23 | 93.3% |
| `organilab` | 3 | 51 | 8 | 84.3% |

## Archivos con más líneas sin cubrir (top 40)

| Archivo | Sentencias | Sin cubrir | Cobertura |
|---------|-----------:|-----------:|----------:|
| `laboratory/api/shelfobject.py` | 1012 | 442 | 56.3% |
| `laboratory/shelfobject/serializers.py` | 1547 | 379 | 75.5% |
| `laboratory/utils_pdf.py` | 327 | 273 | 16.5% |
| `risk_management/utils_risk.py` | 321 | 271 | 15.6% |
| `report/utils.py` | 328 | 244 | 25.6% |
| `laboratory/views/shelfobject.py` | 392 | 235 | 40.1% |
| `reservations_management/functions.py` | 270 | 188 | 30.4% |
| `laboratory/gtselects.py` | 563 | 187 | 66.8% |
| `report/views/base.py` | 370 | 178 | 51.9% |
| `risk_management/compatibility_utils.py` | 266 | 177 | 33.5% |
| `laboratory/api/serializers.py` | 1144 | 176 | 84.6% |
| `laboratory/api/views.py` | 940 | 170 | 81.9% |
| `risk_management/iper_views.py` | 432 | 161 | 62.7% |
| `sga/views/editor.py` | 330 | 140 | 57.6% |
| `risk_management/gtcharts.py` | 565 | 136 | 75.9% |
| `report/views/regency.py` | 153 | 132 | 13.7% |
| `report/views/objects.py` | 345 | 130 | 62.3% |
| `laboratory/tasks.py` | 227 | 123 | 45.8% |
| `report/views/riskzones.py` | 271 | 118 | 56.5% |
| `laboratory/forms.py` | 706 | 111 | 84.3% |
| `laboratory/shelfobject/utils.py` | 362 | 103 | 71.5% |
| `report/api/views.py` | 254 | 101 | 60.2% |
| `presentation/feature_catalog.py` | 162 | 96 | 40.7% |
| `laboratory/views/laboratory.py` | 361 | 95 | 73.7% |
| `sga/label_engine/layout/planner.py` | 515 | 95 | 81.6% |
| `laboratory/views/organizations.py` | 208 | 93 | 55.3% |
| `report/views/object_changes.py` | 134 | 93 | 30.6% |
| `sga/label_engine/resources.py` | 169 | 93 | 45.0% |
| `reservations_management/tasks.py` | 107 | 89 | 16.8% |
| `authentication/oidc_backend.py` | 88 | 88 | 0.0% |
| `laboratory/models.py` | 810 | 87 | 89.3% |
| `presentation/views.py` | 221 | 87 | 60.6% |
| `auth_and_perms/api/viewsets.py` | 563 | 86 | 84.7% |
| `laboratory/admin.py` | 340 | 83 | 75.6% |
| `academic/views.py` | 401 | 78 | 80.5% |
| `laboratory/utils.py` | 327 | 74 | 77.4% |
| `auth_and_perms/gtselects.py` | 390 | 70 | 82.1% |
| `auth_and_perms/views/user_org_creation.py` | 114 | 67 | 41.2% |
| `laboratory/views/loadArchive.py` | 100 | 65 | 35.0% |
| `academic/convertions.py` | 71 | 62 | 12.7% |

## Archivos nunca ejecutados (7)

Candidatos a código muerto antes que a pruebas nuevas.

- `api/views.py` (1 sentencias)
- `auth_and_perms/authBackend.py` (21 sentencias)
- `authentication/oidc_backend.py` (88 sentencias)
- `laboratory/sustance/forms.py` (16 sentencias)
- `laboratory/sustance/views.py` (53 sentencias)
- `presentation/tasks.py` (16 sentencias)
- `risk_management/utils.py` (3 sentencias)
