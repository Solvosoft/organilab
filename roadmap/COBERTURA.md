# Cobertura de código

Generado con `make coverage-all` (suite sin navegador + Selenium headless, unidas con `coverage combine`). No editar a mano: `make coverage-summary` lo regenera.

- Fecha: 2026-10-12 16:11
- Commit: `e18a8f03a`
- **Total: 96.7%** — 33406 sentencias, 1096 sin cubrir, 372 archivos

## Por app

| App | Archivos | Sentencias | Sin cubrir | Cobertura |
|-----|---------:|-----------:|-----------:|----------:|
| `laboratory` | 90 | 13322 | 399 | 97.0% |
| `report` | 28 | 3267 | 336 | 89.7% |
| `auth_and_perms` | 27 | 2572 | 153 | 94.1% |
| `sga` | 56 | 4488 | 86 | 98.1% |
| `academic` | 15 | 1131 | 71 | 93.7% |
| `risk_management` | 23 | 3244 | 36 | 98.9% |
| `presentation` | 41 | 1744 | 6 | 99.7% |
| `ambiental` | 22 | 1500 | 2 | 99.9% |
| `derb` | 13 | 345 | 2 | 99.4% |
| `msds` | 10 | 330 | 2 | 99.4% |
| `api` | 8 | 48 | 1 | 97.9% |
| `pending_tasks` | 12 | 271 | 1 | 99.6% |
| `reservations_management` | 13 | 709 | 1 | 99.9% |
| `authentication` | 11 | 384 | 0 | 100.0% |
| `organilab` | 3 | 51 | 0 | 100.0% |

## Archivos con más líneas sin cubrir (top 40)

| Archivo | Sentencias | Sin cubrir | Cobertura |
|---------|-----------:|-----------:|----------:|
| `report/utils.py` | 328 | 149 | 54.6% |
| `laboratory/views/shelfobject.py` | 397 | 66 | 83.4% |
| `academic/convertions.py` | 71 | 62 | 12.7% |
| `report/views/base.py` | 370 | 61 | 83.5% |
| `auth_and_perms/views/user_org_creation.py` | 114 | 59 | 48.2% |
| `laboratory/sustance/views.py` | 53 | 53 | 0.0% |
| `report/views/objects.py` | 345 | 50 | 85.5% |
| `report/views/regency.py` | 153 | 42 | 72.5% |
| `laboratory/views/organizations.py` | 208 | 39 | 81.2% |
| `sga/views/editor.py` | 337 | 34 | 89.9% |
| `laboratory/forms.py` | 710 | 33 | 95.4% |
| `laboratory/api/views.py` | 942 | 25 | 97.3% |
| `auth_and_perms/authBackend.py` | 21 | 21 | 0.0% |
| `laboratory/utils.py` | 327 | 21 | 93.6% |
| `auth_and_perms/views/organizationstructure.py` | 282 | 18 | 93.6% |
| `laboratory/shelfobject/utils.py` | 362 | 18 | 95.0% |
| `report/api/views.py` | 263 | 18 | 93.2% |
| `laboratory/api/serializers.py` | 1144 | 17 | 98.5% |
| `laboratory/api/shelfobject.py` | 1013 | 17 | 98.3% |
| `laboratory/sustance/forms.py` | 16 | 16 | 0.0% |
| `auth_and_perms/utils.py` | 62 | 15 | 75.8% |
| `laboratory/views/laboratory.py` | 365 | 14 | 96.2% |
| `laboratory/shelfobject/serializers.py` | 1552 | 13 | 99.2% |
| `risk_management/utils_risk.py` | 310 | 13 | 95.8% |
| `sga/api/sga_components_viewsets.py` | 251 | 13 | 94.8% |
| `laboratory/reactive.py` | 19 | 12 | 36.8% |
| `sga/forms.py` | 203 | 12 | 94.1% |
| `auth_and_perms/gtselects.py` | 390 | 11 | 97.2% |
| `auth_and_perms/api/serializers.py` | 396 | 9 | 97.7% |
| `auth_and_perms/forms.py` | 127 | 9 | 92.9% |
| `laboratory/admin.py` | 340 | 9 | 97.4% |
| `laboratory/limit_shelfobject.py` | 18 | 8 | 55.6% |
| `laboratory/views/reports.py` | 198 | 8 | 96.0% |
| `laboratory/views/shelfs.py` | 235 | 8 | 96.6% |
| `report/forms.py` | 279 | 8 | 97.1% |
| `laboratory/views/__init__.py` | 20 | 6 | 70.0% |
| `presentation/views.py` | 221 | 6 | 97.3% |
| `risk_management/tasks.py` | 46 | 6 | 87.0% |
| `sga/api/serializers.py` | 401 | 6 | 98.5% |
| `sga/templatetags/label_tags.py` | 13 | 6 | 53.8% |

## Archivos nunca ejecutados (4)

Candidatos a código muerto antes que a pruebas nuevas.

- `api/views.py` (1 sentencias)
- `auth_and_perms/authBackend.py` (21 sentencias)
- `laboratory/sustance/forms.py` (16 sentencias)
- `laboratory/sustance/views.py` (53 sentencias)
