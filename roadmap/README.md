# Roadmap — Organilab sobre djgentelella 0.6

La migración a djgentelella 0.6 (etapas 0–13: limpieza, django_ajax vendorizado,
`async_notification`, iCheck → nativos, DataTables 2, Chart.js 4, overrides, TinyMCE 8,
modernización a `ObjectCRUD`, Selenium, validación y history/Trash) está **cerrada**. Sus
documentos de etapa se borraron el 2026-09-16; el detalle queda en el historial de git. Los
cambios hechos a la biblioteca (fix min/max y orden `get_labels` en `chartjs.py`, acciones
`link:true` en `obj_api_management.js`, `form-text` en los formularios, `HistoryRelation`,
`TrashRelation`, `PositionsGrid` y `BreadcrumbNav`) están publicados desde **v0.6.0** (PyPI sirve
0.6.2).

## Qué hay aquí

| Documento | Qué es | Estado |
|---|---|---|
| [`PENDIENTES.md`](PENDIENTES.md) | Restos de las etapas cerradas: smoke manual, seguridad en risk_management, correos sin marca, biblioteca | abierto |
| [`13D_FASE_D_PAPELERA.md`](13D_FASE_D_PAPELERA.md) | Diseño para extender `DeletedWithTrash` más allá de `Protocol`/`Procedure` | diseñado, sin implementar |
| [`14_ETAPA_LABVIEW.md`](14_ETAPA_LABVIEW.md) | labview sobre API y salida total de django_ajax | F0–F6 hechas; falta regresión y F7 |
| [`14_ARQUITECTURA_LABVIEW.md`](14_ARQUITECTURA_LABVIEW.md) + [`14_labview_prototipo.svg`](14_labview_prototipo.svg) | Porqués de la arquitectura del labview | referencia |
| [`ESTRATEGIA_PRUEBAS.md`](ESTRATEGIA_PRUEBAS.md) | Política Selenium vs. cliente/unit y backlog de pruebas | abierto |

**Generados — no editar a mano** (CI los compara con el código):

| Archivo | Se regenera con |
|---|---|
| `INVENTARIO_URLS.md`, `inventario_urls.csv` | `make url-inventory` (check: `make url-inventory-check`) |
| `INVENTARIO_FUNCIONALIDADES.md` | `make feature-catalog` (check: `make feature-catalog-check`) |
| `COBERTURA_POR_ROL.md`, `cobertura_por_rol.json` | `make feature-coverage` / `feature-coverage-fast` |
| `.feature_probe/` | temporal de la sonda (ignorado por git) |

## Entorno

venv `~/entornos/organilab` con la biblioteca instalada editable desde
`~/Desktop/desarrollo/django-gentelella-widgets` (rama `master`). Reinstalar desde
`requirements.txt` puede pisar la editable con la versión de PyPI; se restaura con
`pip install -e ~/Desktop/desarrollo/django-gentelella-widgets`.

## Principios

1. **djgentelella es genérica**: los arreglos que se le hagan van al checkout sin conocimiento de
   organilab (con prueba en su demo). Lo multi-tenant se implementa en organilab como
   subclases/configuración.
2. **Pruebas**: durante el trabajo, solo los tests del área (`make single-test` /
   `make test-selenium-single-fast TEST=...`); la corrida completa (unit + Selenium) una vez al
   cierre.
3. Cada proyecto actualiza su documento al cerrarse; lo terminado se borra y queda en git.
