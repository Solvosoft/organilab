# encoding: utf-8
"""Lo transversal: tareas pendientes, MSDS, formularios Formio y la portada.

Cuatro módulos pequeños que comparten una propiedad: **son el punto donde el resto del
sistema desemboca**. Las tareas pendientes son el buzón al que escriben SGA, riesgo y
laboratorio; MSDS es el archivo documental que la clasificación de sustancias alimenta;
los formularios de `derb` son las plantillas que el resto de módulos instancia.
"""

from presentation.feature_catalog import Feature, Step

TODOS_LOS_ROLES = (
    "estudiante", "profesor", "tecnico_laboratorio", "asistente_laboratorio",
    "administrador_laboratorio", "administrativo_superior", "regente", "solo_lectura",
)

FEATURES = (
    Feature(
        id="TASK-01",
        name="Recibir y atender una tarea pendiente",
        module="pending_tasks",
        kind="ui",
        description=(
            "El buzón de trabajo del usuario. Otros módulos crean tareas dirigidas a "
            "una persona **o a un conjunto de roles**, y quien las recibe las ve aquí "
            "con su enlace al sitio donde se resuelven."
        ),
        states=(
            "PendingTask.status: PENDING(0) → IN_PROCESS(1) → FINISHED(2) "
            "(`pending_tasks/models.py:14-22`)",
        ),
        priority="P2",
        steps=(
            Step(
                id="ver_bandeja",
                name="Ver mis tareas pendientes",
                actors=TODOS_LOS_ROLES,
                routes=("pending_tasks:view_task",),
                permissions=("pending_tasks.view_pendingtask",),
                source="src/pending_tasks/views.py:8",
            ),
        ),
        notes=(
            "**Es el único sitio del sistema donde el rol es dato de negocio, no solo "
            "autorización.** `PendingTask` se asigna a un `profile` *o* a un M2M de "
            "`Rol` (`models.py:32,39`), y `PendingTaskManager` resuelve destinatarios "
            "implícitos: los regentes del laboratorio (:67), su responsable (:99), los "
            "responsables de la organización (:109), los del edificio (:125), **todos "
            "los perfiles con un rol dado** (:138) y los de una organización filtrando "
            "por `type_in_organization` (:161).",
            "Que la app tenga una sola ruta esconde su alcance: los emisores están en "
            "`sga/utils.py:63`, `risk_management/tasks.py:67`, "
            "`risk_management/iper_views.py:575`, `laboratory/tasks.py:69,197`, "
            "`laboratory/task_utils.py:65` y `laboratory/limit_shelfobject.py:25`.",
        ),
    ),
    Feature(
        id="MSDS-01",
        name="Consultar y verificar las fichas de seguridad del laboratorio",
        module="msds",
        kind="ui",
        description=(
            "El archivo de hojas de datos de seguridad: se listan las disponibles, se "
            "registra una nueva y se revisa la trazabilidad de las que el sistema ha "
            "ido extrayendo de los PDF subidos en SGA."
        ),
        priority="P3",
        steps=(
            Step(
                id="consultar",
                name="Consultar el árbol de fichas",
                actors=TODOS_LOS_ROLES,
                routes=("msds:index_msds", "msds:list_msds"),
                permissions=("msds.view_msdsobject",),
                source="src/msds/views.py index_msds, get_list_msds",
            ),
            Step(
                id="registrar",
                name="Registrar una ficha",
                actors=("administrador_laboratorio", "tecnico_laboratorio", "sga"),
                routes=("msds:sds_create",),
                permissions=("msds.add_msdsobject",),
                source="src/msds/views.py sds_create",
            ),
            Step(
                id="verificar",
                name="Verificar la trazabilidad de las fichas extraídas",
                actors=("sga", "regente", "administrativo_superior"),
                routes=("msds:verified_sds",),
                permissions=("sga.view_sdstraceability",),
                source="src/msds/views.py verified_sds",
            ),
        ),
    ),
    Feature(
        id="DERB-01",
        name="Construir un formulario dinámico",
        module="derb",
        kind="ui",
        description=(
            "El constructor de formularios sobre Formio.js: se arrastran campos, se "
            "agrupan en secciones y se previsualiza el resultado. Todo el valor está "
            "en el arrastrar y soltar del navegador, así que es de los pocos sitios "
            "donde una prueba Selenium es la única que puede decir algo."
        ),
        priority="P3",
        steps=(
            Step(
                id="listar",
                name="Listar los formularios de la organización",
                actors=("administrador_laboratorio", "administrativo_superior",
                        "profesor"),
                routes=("derb:form_list",),
                permissions=("derb.view_customform",),
                source="src/derb/views/form_list.py FormList",
            ),
            Step(
                id="crear",
                name="Crear un formulario",
                actors=("administrador_laboratorio", "administrativo_superior"),
                routes=("derb:create_form",),
                permissions=("derb.add_customform",),
                source="src/derb/views/form_list.py CreateForm",
            ),
            Step(
                id="editar",
                name="Editar el formulario en el constructor",
                actors=("administrador_laboratorio", "administrativo_superior"),
                routes=("derb:edit_view", "derb:update_form"),
                permissions=("derb.change_customform",),
                source="src/derb/views/EditView.py",
            ),
            Step(
                id="previsualizar",
                name="Previsualizar el formulario tal como lo verá quien lo rellene",
                actors=("administrador_laboratorio", "administrativo_superior",
                        "profesor"),
                routes=("derb:preview_form",),
                permissions=("derb.view_customform",),
                source="src/derb/views/preview_form.py",
            ),
            Step(
                id="borrar",
                name="Borrar un formulario",
                actors=("administrador_laboratorio", "administrativo_superior"),
                routes=("derb:delete_form",),
                permissions=("derb.delete_customform",),
                source="src/derb/views/form_list.py DeleteForm",
            ),
        ),
    ),
    Feature(
        id="GEN-01",
        name="Entrar al sistema y orientarse",
        module="presentation",
        kind="ui",
        description=(
            "La portada, la información general, los documentos de regulación y la "
            "pantalla de acceso denegado. Es lo que ve alguien que todavía no ha "
            "elegido organización."
        ),
        priority="P4",
        steps=(
            Step(
                id="portada",
                name="Abrir la portada y la información general",
                actors=("anonimo",) + TODOS_LOS_ROLES,
                routes=("index", "general_info", "home"),
                permissions=(),
                source="src/presentation/views.py index_organilab, general_information",
            ),
            Step(
                id="regulacion",
                name="Consultar y descargar los documentos de regulación",
                actors=("anonimo",) + TODOS_LOS_ROLES,
                routes=("regulation_docs", "download_all_regulations"),
                permissions=(),
                source="src/msds/views.py regulation_view, download_all_regulations",
            ),
            Step(
                id="denegado",
                name="Ver la pantalla de acceso denegado",
                actors=("anonimo",) + TODOS_LOS_ROLES,
                routes=("permission_denied", "error_view"),
                permissions=(),
                source="src/authentication/views.py PermissionDeniedView",
            ),
        ),
        notes=(
            "`HandleErrorMiddleware` convierte los 403 y 404 de peticiones HTML en un "
            "302 hacia `error_view`. Es la razón por la que el smoke imprime el "
            "`Location` de cada redirección: sin verlo no se distingue «la página no "
            "existe» de «no tenés permiso».",
        ),
    ),
    Feature(
        id="GEN-02",
        name="Seguir los tutoriales guiados y dar retroalimentación",
        module="presentation",
        kind="ui",
        description=(
            "El sistema de tutoriales contextuales: se listan, se marca el progreso, se "
            "apagan si molestan y se pueden reactivar. Más el formulario de "
            "retroalimentación del producto."
        ),
        priority="P4",
        steps=(
            Step(
                id="ver_tutoriales",
                name="Ver los tutoriales disponibles",
                actors=TODOS_LOS_ROLES,
                routes=("tutorials",),
                permissions=("auth_and_perms.institution_can_access",),
                source="src/presentation/views.py index_tutorial",
            ),
            Step(
                id="progreso",
                name="Marcar progreso, apagar y reactivar un tutorial",
                actors=TODOS_LOS_ROLES,
                routes=("tutorial_progress_api", "tutorial_toggle_api",
                        "tutorial_reactivate_api"),
                permissions=(),
                source="src/presentation/views.py tutorial_*_api",
            ),
            Step(
                id="feedback",
                name="Enviar retroalimentación sobre el producto",
                actors=TODOS_LOS_ROLES,
                routes=("feedback",),
                permissions=("auth_and_perms.institution_can_access",),
                source="src/presentation/views.py FeedbackView",
            ),
        ),
    ),
)
