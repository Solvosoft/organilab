# Pendientes del roadmap

> Restos de las etapas 0–13 de la migración a djgentelella 0.6, cuyos documentos se borraron
> (siguen en git). Verificado contra el código el 2026-09-16. Los proyectos abiertos tienen su
> propio documento: labview en [`14_ETAPA_LABVIEW.md`](14_ETAPA_LABVIEW.md), papelera fase D en
> [`13D_FASE_D_PAPELERA.md`](13D_FASE_D_PAPELERA.md), pruebas en
> [`ESTRATEGIA_PRUEBAS.md`](ESTRATEGIA_PRUEBAS.md).

---

## 1. Smoke manual con `runserver` (nunca se hizo)

La etapa 12 cerró con unit 902/902, Selenium ≈213/213, lint 0 y migrate limpio (2026-08-29),
pero nadie revisó en un navegador real. Checklist (heredada de las etapas 03, 07, 08, 09 y 12):

- [ ] Login, logout y reset de contraseña.
- [ ] Menú lateral y top-nav por debajo de 992px (drawer).
- [ ] DataTables en español; acciones de fila según permisos.
- [ ] TinyMCE dentro de un modal.
- [ ] Los 5 tableros de gráficos (Chart.js 4, datalabels en `risk_graphics.html`).
- [ ] Correos: la cola de `async_notification` se drena y llega a Mailhog (docker, UI 8025).
- [ ] Subida chunked de archivos.
- [ ] Mensaje "borrar fichero" en campos de archivo obligatorios.

## 2. Otros restos

| # | Pendiente | Evidencia |
|---|-----------|-----------|
| 1 | `migrate` sobre una **copia de la base real** (solo se probó sobre base limpia) | etapa 12 |
| 2 | ~~**Seguridad**: viewsets hermanos de risk_management con `permission_classes = ()`~~ ✅ añadido `permission_classes` a `BuildingViewSet` e `IPERAssessmentViewSet` | `src/risk_management/api/viewset.py` |
| 3 | ~~Ruta huérfana `riskmanagement:iper_delete` (`IPERAssessmentDelete`), sin plantilla ni JS que la use~~ ✅ ruta eliminada, referencia en features actualizada al viewset | `src/presentation/features/riskmanagement.py` |
| 4 | Correos sin plantilla de marca: `ASYNC_NOTIFICATION_BASE_TEMPLATES` / `_BRAND` no definidos | `src/organilab/settings.py` |
| 5 | `jquery-1.9.1.min.js` propio, vivo en la firma digital | `auth_and_perms/static/js/jquery-1.9.1.min.js`, usado en `create_user_organization_digital_signature.html:60` |
| 6 | ~~Biblioteca: bump 0.6.1 → 0.6.2 sin commitear en el checkout `~/Desktop/desarrollo/django-gentelella-widgets`~~ ⊘ obsoleto: el checkout ya no existe; versión 0.6.2 ya instalada, pin `>=0.6.0` la acepta | `requirements.txt:4` |
| 7 | ~~Rama local `dj060` obsoleta (su punta no está en la historia actual)~~ ✅ rama eliminada | `git branch` |
| 8 | ~~**Seguridad**: `report_table` no acota el `TaskReport` por organización ni por quien lo pidió; cualquier pk es visible con `do_report`~~ ✅ añadido filtro `data__org_pk=org_pk` en `report_table`, `download_report` y `report_organization_table` | `src/report/views/base.py` |
| 11 | ~~**Seguridad**: el `lab_pk` de la URL o del GET entra al alcance de permisos sin validar que el laboratorio pertenezca a `org_pk`~~ ✅ validación añadida en `ProfileMiddleware`: usa `organization_can_change_laboratory()` y descarta `lab_pk` si no pertenece a `org_pk` | `src/authentication/middleware.py` |
| 9 | Smoke en navegador de las pantallas `ambiental` y `platform` (ObjectCRUD, select2 filtrado, gráficos) | `plans/ENVIRONMENT_PLAN.md` §4 |
| 10 | `roadmap/cobertura_por_rol.json`: los pasos AMB-* y PLAT-* se midieron solo con sus pruebas y se mezclaron a mano; `COBERTURA_POR_ROL.md` no se regeneró. Correr `make feature-coverage` | `roadmap/cobertura_por_rol.json` |
