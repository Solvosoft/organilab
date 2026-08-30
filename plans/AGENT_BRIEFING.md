# Organilab — Agent Briefing

> **Read this first.** This document exists so you don't have to explore the whole
> codebase before you can work in it. It maps the architecture and points you at the
> exact files where things live, so you can jump straight to the relevant code and
> search from there. It complements `CLAUDE.md` (which covers commands and a high-level
> overview); this briefing goes deeper on *where things are* and *how the pieces connect*.
>
> All paths are relative to the repo root. **All application code lives under `src/`.**

---

## 1. What Organilab is

A Django-based **laboratory management system** for Costa Rican institutions
(Spanish-first UI, version `2.0.0`). It supports multi-lab management, inventory
tracking (reactives / materials / equipment), reservations, chemical safety (SGA/GHS),
risk management, MSDS, academic procedures, and reporting. It is **multi-tenant**: data
is partitioned by organization.

---

## 2. The mental model (internalize this)

```
OrganizationStructure (tree)  +  AbstractOrganizationRef (scoping)  +  ProfilePermission (RBAC)
        = multi-tenant lab management
```

- **`OrganizationStructure`** is a tree of organizations (a `TreeNode`). Almost
  everything belongs to an org.
- Most domain models inherit **`AbstractOrganizationRef`**, which gives them an
  `organization` FK. Data access is scoped by filtering on `organization`.
- The current org is carried in the URL as **`org_pk`**: most routes look like
  `/<app>/<int:org_pk>/...`. Middleware reads `org_pk` and resolves what the user is
  allowed to do *in that org*.
- Permissions are role-based per org via **`ProfilePermission`** + **`Rol`** (a custom
  role model — **not** Django's `Group`).

If you understand those four sentences, the rest of the codebase follows.

---

## 3. Repository layout

Everything is under `src/`. Django apps:

| App | Purpose |
|-----|---------|
| `laboratory` | **Core domain.** Inventory: `Object`, `ShelfObject`, `Shelf`, `Furniture`, `LaboratoryRoom`, `Laboratory`, and the `OrganizationStructure` org tree. |
| `auth_and_perms` | User `Profile`, custom roles (`Rol`), fine-grained `ProfilePermission`, org-user management. |
| `presentation` | Abstract base models, main UI/landing, tutorials, feedback, QR. |
| `sga` | Chemical safety (Sistema Global Armonizado / GHS): substances, pictograms, danger indications, labels. |
| `risk_management` | Risk zones, incidents, buildings, regents, workdays. |
| `reservations_management` | Equipment/material reservation system. |
| `academic` | Academic procedures and training workflows. |
| `derb` | Dynamic form builder (Formio.js-based custom forms). |
| `msds` | Material Safety Data Sheet structure (doc tree + regulations). |
| `report` | Report generation & export pipeline. |
| `api` | Thin REST entry point; most API code lives in each app's `api/` submodule. |
| `authentication` | Auth backends (OIDC), request middleware, error handling. |
| `pending_tasks` | Workflow/pending-task management for users and roles. |

Non-app directories:

| Path | Purpose |
|------|---------|
| `src/organilab/` | Django project config: `settings.py`, `test_settings.py`, `urls.py`, `celery.py`, `wsgi.py`/`asgi.py`. `__init__.py` exports version + Celery app. |
| `src/locale/` | i18n translation files (`es`, `en`). |
| `src/organilab_test/` | Shared test infrastructure (base classes, fixtures). |
| `docs/` | Sphinx documentation. |
| `docker/` | `docker-compose.yml` and Dockerfile for local stack. |
| `Makefile` (root) | All dev commands (see §14). |

---

## 4. Core domain models & where they live

### `laboratory` — `src/laboratory/models.py` (the heart of the system)

| Model | What it is |
|-------|------------|
| `Object` | Catalog entry for a reactive / material / equipment (type discriminator). Org-scoped. |
| `ShelfObject` | A physical instance of an `Object` on a `Shelf`: quantity, expiration, batch, status, concentration. |
| `Shelf` | Container inside `Furniture`; has capacity/units; can restrict object types; supports nesting. |
| `Furniture` | Cabinet/case holding shelves; belongs to a `LaboratoryRoom`; has grid position. |
| `LaboratoryRoom` | A room within a `Laboratory`. |
| `Laboratory` | A lab unit; FK to `OrganizationStructure`; responsible user, coordinates, geolocation. |
| `OrganizationStructure` | **The org tree** (`TreeNode`). Nested orgs; users via `UserOrganization`; roles via `Rol`. |
| `UserOrganization` | Through-model: User ↔ Organization with a membership type (administrator / manager / user). |
| `OrganizationStructureRelations` | Generic relation linking an org to any model (e.g. a `Laboratory`) via `ContentType`. |

Related satellites worth knowing: `SustanceCharacteristics`, `ObjectFeatures`,
`ShelfObjectLog`, `ShelfObjectMaintenance`, `TranferObject`, `PrecursorReport`,
`Protocol`.

### `auth_and_perms` — `src/auth_and_perms/models.py`

| Model | What it is |
|-------|------------|
| `Profile` | One-to-one with Django `User`; phone, id_card, labs (M2M), workplace (M2M org), language, `show_tutorials`. |
| `Rol` | Custom role; M2M to Django `Permission`; name, color, description. **Not** a Django `Group`. |
| `ProfilePermission` | The RBAC join: `Profile` → `Rol` (M2M) → `OrganizationStructure`, plus a GenericFK to any object. This is how a user gets a role in a given org/object. |

### `presentation` — `src/presentation/models.py`

Home of the abstract base models (see §5), plus `Tutorial`/`TutorialStep`/
`TutorialProgress`, `FeedbackEntry`, `Donation`, `QRModel`.

### Other apps — key models (one-liners)

| App | File | Key models |
|-----|------|-----------|
| `sga` | `src/sga/models.py` | `Substance` (+ `SubstanceCharacteristics`), `DangerIndication`, `WarningClass` (tree), `PrudenceAdvice`, `Pictogram`, `Label`, `TemplateSGA`. |
| `risk_management` | `src/risk_management/models.py` | `RiskZone`, `IncidentReport`, `Buildings`, `Regent`, `Workday`, `ZoneType`, `PriorityConstrain`. |
| `reservations_management` | `src/reservations_management/models.py` | `Reservations`, `ReservedProducts`, `ReservationTasks`, `ReservationRange`. |
| `academic` | `src/academic/models.py` | `Procedure`, `MyProcedure`, `ProcedureStep`, `CommentProcedureStep`. |
| `derb` | `src/derb/models.py` | `CustomForm`, `Section`/`Subsection`, `CustomFormField`, `FieldType`, `WidgetType`, `Validator`. |
| `msds` | `src/msds/models.py` | `OrganilabNode` (doc tree), `RegulationDocument`. |
| `report` | `src/report/models.py` | `TaskReport`, `DocumentReportStatus`, `ObjectChangeLogReport`, `RegencyReport`. |
| `pending_tasks` | `src/pending_tasks/models.py` | `PendingTask`, `PendingTaskManager`. |

---

## 5. Base / abstract model patterns

Recognize these three mixins — most models inherit one of them:

| Mixin | Location | Provides |
|-------|----------|----------|
| `AbstractOrganizationRef` | `src/presentation/models.py` | `organization` (FK `OrganizationStructure`), `created_by`, `creation_date`, `last_update`. **The primary org-scoping mixin.** |
| `AbstractRegistry` | `src/presentation/models.py` | `created_by`, `creation_date`, `last_update`. Audit only, **no** org scope. |
| `BaseCreationObj` | `src/laboratory/models.py` | `created_by`, `creation_date`, `last_update`. Used by lab-domain models. |

When adding a new model, ask: *should it be org-scoped?* If yes, inherit
`AbstractOrganizationRef`.

### `DeletedWithTrash` — soft delete into the trash

A fourth mixin, `DeletedWithTrash` (from `djgentelella.models`), turns a model's
delete into a recoverable one. Pilots: `Protocol` (`src/laboratory/models.py`)
and `Procedure` (`src/academic/models.py`).

**The rule that matters:** delete with
`obj.delete(user=request.user, related_objects=[organization, laboratory])`.
`related_objects` must be **model instances** (a bare pk raises `ValueError`),
and they are what makes the row visible in the org-scoped trash screen — its
`scope_queryset()` joins `TrashRelation` against the organization in the URL.
**A plain `obj.delete()` still soft-deletes, but with no relation the object is
invisible and unrecoverable.** The same trap applies to
`Model.objects.filter(...).delete()` and `parent.child_set.all().delete()`,
whose `delete()` is also soft once the mixin is on: use `hard_delete()` for
technical cleanups.

Django's CASCADE collector and the admin's "delete selected" bypass the model's
`delete()` entirely — those are hard deletes.

---

## 6. Multi-tenancy & permission flow (end to end)

How a request gets scoped and authorized:

1. **URL carries `org_pk`** (and often `lab_pk`): `/<app>/<int:org_pk>/...`.
2. **`ProfileMiddleware`** (`src/authentication/middleware.py`) runs `process_view()`:
   reads `org_pk`/`lab_pk`, queries `ProfilePermission` for the user in that org,
   collects all `Rol` permissions, and builds `request.user._perm_cache` (combined
   ProfilePermission + direct user perms + group perms). This makes
   `user.has_perm(...)` work for org-scoped permissions.
3. **Views validate access** with helpers — `user_is_allowed_on_organization(user, org)`
   and `organization_can_change_laboratory(lab, org)` — and/or
   `@permission_required(...)` decorators.
4. **ORM is filtered by org**, e.g. `Substance.objects.filter(organization_id=org_pk)`.

Key supporting models: `ProfilePermission`, `Rol`, `UserOrganization` (membership
types: administrator / laboratory manager / laboratory user). Shared permission
utilities live in `src/auth_and_perms/organization_utils.py` (reused heavily across
the codebase — look here before writing a new access check).

---

## 7. URL routing

Root: **`src/organilab/urls.py`**. Apps are `include()`d, most under the
`<app>/<int:org_pk>/` convention. Main prefixes:

| Prefix | App |
|--------|-----|
| `/laboratory/` | laboratory |
| `/sga/<org_pk>/` | sga |
| `/risk/<org_pk>/` | risk_management |
| `/msds/<org_pk>/` | msds |
| `/derb/<org_pk>/` | derb |
| `/academic/<org_pk>/` | academic |
| `/reservations_management/<org_pk>/` | reservations_management |
| `/perms/` | auth_and_perms (permission/org management) |
| `/report/` | report |
| `/pending_tasks/` | pending_tasks |
| `/api/` | api (per-app routers add their own paths) |

Each app has its own `urls.py`.

---

## 8. View layer conventions

- **Class-based views** are the norm. Custom base views live in
  **`src/laboratory/views/djgeneric.py`**: `CreateView`, `UpdateView`, `ListView`,
  `DeleteView` — they extract `org_pk`/`lab_pk` from the URL and enforce access via
  `user_is_allowed_on_organization()` / `organization_can_change_laboratory()`. Inherit
  these to get org/lab checks for free.
- Views live in either `views.py` or a `views/` package per app (e.g.
  `src/laboratory/views/` has 15+ modules: `furniture.py`, `shelfs.py`,
  `organizations.py`, …; `src/sga/views/`, `src/derb/views/`, `src/auth_and_perms/views/`).
- Some **function-based views** remain, decorated with `@login_required` and
  `@permission_required("app.perm")`.
- Reuse permission utilities from `src/auth_and_perms/organization_utils.py`.

---

## 9. REST API (Django REST Framework)

- The `api` app itself is thin (`src/api/`); the real API code is in each app's
  **`api/` submodule**. The largest is **`src/laboratory/api/`** (e.g. `ObjectViewSet`,
  `ProtocolViewSet`, `ProviderViewSet`, `LogEntryViewSet`). Others: `src/sga/api/`,
  `src/derb/api/`, `src/reservations_management/api/`, `src/risk_management/api/`,
  `src/academic/api/`, `src/report/api/`, `src/pending_tasks/api/`.
- ViewSets commonly extend **`AuthAllPermBaseObjectManagement`** from `djgentelella`.
- They are registered with DRF's `DefaultRouter()` inside each app's `urls.py`.
- Serializers live in each app's `api/serializers.py`.
- DRF config in `settings.py`: `TokenAuthentication` + `SessionAuthentication`,
  `LimitOffsetPagination`, `PAGE_SIZE = 100`. `DjangoFilterBackend` / `SearchFilter` /
  `OrderingFilter` are used.

To add an endpoint: add a ViewSet/serializer under the app's `api/`, register it on a
router in the app's `urls.py`.

---

## 10. Authentication

- **Backends:**
  - `src/auth_and_perms/authBackend.py` — `BCCRBackend`, Costa Rican digital-signature
    auth (creates the user if missing).
  - `src/authentication/oidc_backend.py` — `OrganiLabOIDCBackend` (extends
    `mozilla_django_oidc`). On first login it creates a `Profile`, assigns a default org
    (`DEFAULT_ORG_PK`) and default role (`DEFAULT_ROL_NAME`), and adds default groups.
    Enabled when `OIDC_RP_CLIENT_ID` is configured.
- **Middleware highlights** (full stack in `settings.py`):
  - `ProfileLanguageMiddleware` (`src/auth_and_perms/middleware.py`) — applies the
    user's language; redirects users without a complete `Profile`.
  - `ProfileMiddleware` (`src/authentication/middleware.py`) — caches org-scoped
    permissions (see §6).
  - `HandleErrorMiddleware` (`src/authentication/middleware.py`) — routes 403/404 to a
    custom error page (skips JSON/XHR responses).

---

## 11. Frontend

- Admin UI uses **djgentelella 0.6.0** (Gentelella template; checkout editable de
  `~/Desktop/desarrollo/django-gentelella-widgets`, rama `development` — ver
  `roadmap/README.md`). Base template: `src/presentation/templates/base.html`
  (extends `gentelella/base.html`).
- Stack UI post-migración: **Bootstrap 5** (inputs nativos, sin iCheck/switchery),
  **DataTables 2** (`layout`, clases `dt-*`), **Chart.js 4**, **TinyMCE 8**,
  **Leaflet** vía `GTPointField`/`MapPointInput` (sin django-location-field).
- Modales y tablas nuevas siguen el patrón `AuthAllPermBaseObjectManagement` +
  `ObjectCRUD` (`gentelella/blocks/modal_template*.html`); variantes propias en
  `src/presentation/templates/modal_template*.html`. Inline CRUD de hijos:
  `BaseInlineObjectManagement` (ej. `academic/api/views.py`).
- Correos/notificaciones: `djgentelella.async_notification` (el paquete standalone
  `async_notifications` y markitup salieron en la migración).
- Per-app `templates/` and `static/{css,js,img}` directories; shared assets in
  `src/presentation/static/` (incluye `django_ajax/` vendorizado, pendiente de
  salida total con el sub-proyecto labview).
- **Dynamic forms** use **Formio.js** in `derb`: `src/derb/static/formio/`
  (`FormioController.js`, plus custom components `CustomSelect.js`,
  `CustomTextInput.js`, `CustomSection.js`, and `formio.full.min.js`).
- **JS translations** via Django's `javascript-catalog` view; strings live in
  `src/locale/{es,en}/LC_MESSAGES/djangojs.po` (compiled `.mo`).
- Custom template tags live in app-level `templatetags/` dirs.

---

## 12. Settings & infrastructure

- Settings: `src/organilab/settings.py`; test overrides in
  `src/organilab/test_settings.py`.
- **Database:** PostgreSQL, configured via env vars — `DBNAME` (default `organilab`),
  `DBUSER` (default `organilab_user`), `DBPASSWORD`, `DBHOST` (`127.0.0.1`), `DBPORT`
  (`5432`).
- **Celery:** RabbitMQ broker (`BROKER_URL`), `django-db` result backend,
  `django-celery-beat` for scheduling. In tests, `CELERY_TASK_ALWAYS_EAGER = True`.
- **Notable third-party libs:** `djgentelella` (UI + base object-management viewsets),
  `djangorestframework`, `tree_queries` (TreeNode hierarchies), `mozilla_django_oidc`,
  `django-otp` (TOTP), `weasyprint` (PDF), Sentry/Glitchtip. (`location_field` y
  `async_notifications` se retiraron en la migración a djgentelella 0.6.0.)
- **Scheduled tasks** (`CELERYBEAT_SCHEDULE`): daily emails, product-limit checks,
  precursor reports (monthly), max-stock registration, shelf-object expiration emails,
  establishment logs, org-lab relation cleanup.
- **i18n:** Spanish (`es`) is the production default; timezone `America/Costa_Rica`.

---

## 13. Testing

- Tests live in `src/<app>/tests/`. Most extend Django's `TestCase` (or a custom
  `BaseLaboratorySetUpTest`). Shared base classes / fixtures in
  `src/organilab_test/`.
- **Selenium** tests are tagged `@tag("selenium")` and excluded from normal runs;
  base class `SeleniumBase` (`src/organilab_test/tests/base.py`).
- `test_settings.py`: MD5 password hasher (fast), Celery eager, logging suppressed,
  appends `organilab_test` to `INSTALLED_APPS`, language `en`.
- Run:
  - `make test` — all tests except selenium.
  - `make single-test TEST=laboratory.tests.test_provider.ProviderViewTest` — one test.
  - `make test-selenium` — selenium suite.
- Fixtures: `src/sga/fixtures/` (`catalog.json` GHS data, `sga_components.json`); loaded
  via the `init_checks` management command.

---

## 14. Tooling & entry points

**Makefile** (root) — key targets:

| Target | Does |
|--------|------|
| `make database_config` | Migrate + load permissions/fixtures (first-time setup). |
| `make migrate` | Run migrations. |
| `make test` / `make single-test TEST=...` | Run tests (see §13). |
| `make lint` | pycodestyle, max line length 200, migrations excluded. |
| `make messages` / `make trans` | Extract / compile translations. Run both after editing translatable strings. |
| `make run_celery` | Start a Celery worker. |
| `make build_docker` | Build the Docker image. |
| `make docs` | Build Sphinx docs. |

**Management commands** (per-app `management/commands/`): `init_checks` (cache table +
fixtures), `load_urlname_permissions` (sync URL-based perms), and sga loaders
(`load_danger_substances`, `load_danger_indications`, `upload_pictograms`).

**Docker:** `docker/docker-compose.yml` runs PostgreSQL (port 5431), RabbitMQ, Mailhog
(web UI on 8025), and the app. **CI:** `.github/workflows/tests.yml` runs `tox`
(Python 3.13 + PostgreSQL).

---

## 15. Quick navigation cheat-sheet

| I want to… | Start here |
|------------|-----------|
| Change inventory items | `src/laboratory/models.py` — `Object` / `ShelfObject` |
| Understand the org tree / multi-tenancy | `OrganizationStructure` + `UserOrganization` in `src/laboratory/models.py` |
| Add/modify a model | Pick a base mixin (§5); org-scoped → `AbstractOrganizationRef` (`src/presentation/models.py`) |
| Add a permission check | `src/auth_and_perms/organization_utils.py` + `ProfileMiddleware` (`src/authentication/middleware.py`) |
| Add a page/view | Inherit base views in `src/laboratory/views/djgeneric.py`; register in the app's `urls.py` |
| Add an API endpoint | App's `api/` submodule (viewset + serializer) + `DefaultRouter` in the app's `urls.py` |
| Touch chemical safety / labels | `src/sga/` |
| Touch dynamic forms | `src/derb/` + `src/derb/static/formio/` |
| Add a scheduled job | `CELERYBEAT_SCHEDULE` in `src/organilab/settings.py` + a task in the relevant app |
| Write to the audit log | `organilab_logentry()` in `src/laboratory/utils.py` — a bridge over `djgentelella.history.add_log`; pass `relobj=` instances so the entry shows in the org-scoped log (`laboratory:logentry_list`) |
| Delete something recoverably | `DeletedWithTrash` (§5) + `delete(user=…, related_objects=[org, lab])`; screen at `laboratory:trash_list` (`src/laboratory/views/trash.py`) |
| Add/run tests | `src/<app>/tests/`; `make single-test TEST=...` |
| Edit user-facing strings | wrap in `gettext`, then `make messages` + `make trans` (`src/locale/es/...`) |
| Find a URL | Root `src/organilab/urls.py` → app `urls.py` |

---

*Keep this file current as the architecture evolves — it's the first thing an agent
reads.*
