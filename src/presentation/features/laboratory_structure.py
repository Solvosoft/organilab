# encoding: utf-8
"""La estructura física y organizativa: organización, laboratorio, sala, mueble, estante.

Es la jerarquía sobre la que se apoya todo lo demás. Un `ShelfObject` no existe sin un
`Shelf`, que no existe sin un `Furniture`, que vive en un `LaboratoryRoom` de un
`Laboratory` que pertenece a una `OrganizationStructure`. Catalogado aparte del
inventario porque son dos trabajos distintos: montar el laboratorio y usarlo.
"""

from presentation.feature_catalog import Feature, Step

MONTADORES = ("administrativo_superior", "administrador_laboratorio",
              "creador_laboratorio", "asistente_laboratorio")
USUARIOS_LAB = MONTADORES + ("tecnico_laboratorio", "estudiante", "profesor",
                             "regente", "solo_lectura")

FEATURES = (
    Feature(
        id="LAB-01",
        name="Crear y administrar una organización",
        module="laboratory",
        kind="ui",
        description=(
            "El inquilino: se crea la organización, se edita, se le asocian acciones y "
            "eventualmente se borra. Todo lo demás cuelga de aquí, y el `org_pk` de "
            "cada URL del sistema es esta fila."
        ),
        priority="P1",
        doc="docs/source/desc_funcionalidades/gestion_lab.rst",
        steps=(
            Step(
                id="crear",
                name="Crear la organización",
                actors=("administrativo_superior", "organization_management"),
                routes=("laboratory:create_organization",),
                permissions=("laboratory.add_organizationstructure",),
                source="src/laboratory/views/organizations.py OrganizationCreateView",
            ),
            Step(
                id="editar",
                name="Editar la organización y sus acciones",
                actors=("administrativo_superior", "organization_management"),
                routes=("laboratory:update_organization",
                        "laboratory:organization_actions"),
                permissions=("laboratory.change_organizationstructure",),
                source="src/laboratory/views/organizations.py",
            ),
            Step(
                id="borrar",
                name="Borrar la organización",
                actors=("administrativo_superior", "organization_management"),
                routes=("laboratory:delete_organization",),
                permissions=("laboratory.delete_organizationstructure",),
                source="src/laboratory/views/organizations.py OrganizationDeleteView",
            ),
        ),
    ),
    Feature(
        id="LAB-02",
        name="Solicitar un laboratorio u organización y aprobarlo",
        module="laboratory",
        kind="ui",
        description=(
            "Quien no puede crear un laboratorio lo **solicita**, y alguien con "
            "autoridad revisa la solicitud y la aprueba o la rechaza dejando una nota. "
            "Es uno de los pocos flujos del sistema con dos actores separados por un "
            "permiso propio."
        ),
        states=(
            'LabOrOrgRequest.status: "pending" → "approved" | "rejected" '
            "(`laboratory/models.py:1897-1908`)",
        ),
        priority="P1",
        steps=(
            Step(
                id="solicitar",
                name="Pedir un laboratorio nuevo o una organización nueva",
                actors=("tecnico_laboratorio", "profesor", "asistente_laboratorio",
                        "administrador_laboratorio"),
                routes=("laboratory:lab_or_org_request_list",),
                permissions=("laboratory.add_labororgrequest",),
                transition='crea LabOrOrgRequest en "pending", con `requested_by`',
                source="src/laboratory/views/lab_or_org_request.py:11",
            ),
            Step(
                id="revisar",
                name="Revisar la solicitud y aprobarla o rechazarla",
                # Solo el administrativo superior: a «Administrador de Laboratorio»
                # `update_roles.py:259` le QUITA este permiso. Ver la nota.
                actors=("administrativo_superior",),
                routes=("laboratory:lab_or_org_request_review",),
                permissions=("laboratory.can_approve_labororgrequest",),
                transition='"pending" → "approved" | "rejected", con `review_notes`',
                source="src/laboratory/views/lab_or_org_request.py:34",
            ),
        ),
        notes=(
            "**Un solo rol puede aprobar**: «Administrativo superior» "
            "(`update_roles.py:1018`, dentro de `add_permissions`). A «Administrador de "
            "Laboratorio» el mismo comando le **quita** `can_approve_labororgrequest` "
            "(`:259`, dentro de `remove_permissions`), así que quien manda en el "
            "laboratorio puede pedir pero no aprobar. Es el permiso de aprobación mejor "
            "acotado del sistema, y conviene no confundirse: `update_roles.py` aplica "
            "**deltas**, y una línea con el nombre de un permiso puede estar "
            "concediéndolo o retirándolo.",
            "**Ninguna de las dos rutas tiene prueba unitaria.**",
        ),
    ),
    Feature(
        id="LAB-03",
        name="Crear un laboratorio y entrar a trabajar en él",
        module="laboratory",
        kind="ui",
        description=(
            "Alta y edición del laboratorio, listado de los propios, y la entrada al "
            "espacio de trabajo (`labindex`, `labview`) desde donde se opera todo lo "
            "demás."
        ),
        priority="P1",
        doc="docs/source/administrative_usage/laboratory.rst",
        steps=(
            Step(
                id="crear_lab",
                name="Crear el laboratorio",
                actors=MONTADORES,
                routes=("laboratory:create_lab",),
                permissions=("laboratory.add_laboratory",),
                source="src/laboratory/views/laboratory.py CreateLaboratoryFormView",
            ),
            Step(
                id="mis_labs",
                name="Ver mis laboratorios y entrar en uno",
                actors=USUARIOS_LAB,
                routes=("laboratory:mylabs", "laboratory:labindex",
                        "laboratory:redirect_user_to_labindex"),
                permissions=("laboratory.view_laboratory",),
                source="src/laboratory/views/laboratory.py LaboratoryListView",
            ),
            Step(
                id="labview",
                name="Abrir la vista del laboratorio con su árbol de salas y estantes",
                actors=USUARIOS_LAB,
                routes=("laboratory:labview",),
                permissions=("laboratory.view_laboratoryroom",),
                source="src/laboratory/views/labview.py LabView",
            ),
            Step(
                id="editar_lab",
                name="Editar o borrar el laboratorio",
                actors=MONTADORES,
                routes=("laboratory:laboratory_update", "laboratory:laboratory_delete"),
                permissions=("laboratory.change_laboratory",
                             "laboratory.delete_laboratory"),
                source="src/laboratory/views/laboratory.py LaboratoryEdit, Delete",
            ),
            Step(
                id="procesos",
                name="Consultar los procesos del laboratorio",
                actors=USUARIOS_LAB,
                routes=("laboratory:laboratory_process_list",),
                permissions=("laboratory.view_laboratoryprocess",),
                source="src/laboratory/views/laboratory.py laboratory_process_list",
            ),
        ),
        notes=(
            "El árbol del labview y sus capacidades ya tienen matriz de permisos y "
            "prueba de aislamiento entre inquilinos "
            "(`laboratory/tests/labview/test_permission_matrix.py`, "
            "`test_tenant_isolation.py`). Es el único sitio del proyecto donde eso "
            "existe, y el modelo a copiar para el resto.",
        ),
    ),
    Feature(
        id="LAB-04",
        name="Montar salas, muebles y estantes",
        module="laboratory",
        kind="ui",
        description=(
            "La estructura física dentro del laboratorio: salas, los muebles que "
            "contienen y los estantes de cada mueble, con su capacidad, unidad y "
            "porcentaje de ocupación. Incluye el QR propio de cada nivel."
        ),
        priority="P1",
        doc="docs/source/desc_funcionalidades/salas_muebl.rst",
        steps=(
            Step(
                id="salas",
                name="Listar, crear, editar y borrar salas",
                actors=MONTADORES,
                routes=("laboratory:rooms_list", "laboratory:rooms_create",
                        "laboratory:rooms_update", "laboratory:rooms_delete"),
                permissions=("laboratory.view_laboratoryroom",
                             "laboratory.change_laboratoryroom",
                             "laboratory.delete_laboratoryroom"),
                source="src/laboratory/views/labroom.py",
            ),
            Step(
                id="qr_sala",
                name="Regenerar el QR de la sala",
                actors=MONTADORES,
                routes=("laboratory:rebuild_laboratory_qr",),
                permissions=("laboratory.change_laboratoryroom",),
                source="src/laboratory/views/labroom.py rebuild_laboratory_qr",
            ),
            Step(
                id="muebles",
                name="Listar, crear, editar y borrar muebles",
                actors=MONTADORES,
                routes=("laboratory:furniture_list", "laboratory:furniture_create",
                        "laboratory:furniture_update", "laboratory:furniture_delete"),
                permissions=("laboratory.add_furniture",
                             "laboratory.delete_furniture"),
                source="src/laboratory/views/furniture.py",
            ),
            Step(
                id="estantes",
                name="Crear, editar y borrar estantes",
                actors=MONTADORES,
                routes=("laboratory:shelf_create", "laboratory:shelf_edit",
                        "laboratory:shelf_delete", "laboratory:get_lab_id"),
                permissions=("laboratory.add_shelf", "laboratory.change_shelf",
                             "laboratory.delete_shelf"),
                source="src/laboratory/views/shelfs.py",
            ),
            Step(
                id="contenedores",
                name="Ver los contenedores de un estante",
                actors=USUARIOS_LAB,
                routes=("laboratory:shelf_containers",),
                permissions=(),
                source="src/laboratory/shelfobject_container/views.py",
            ),
            Step(
                id="reporte_sala",
                name="Descargar el reporte de la sala",
                actors=USUARIOS_LAB,
                routes=("laboratory:reports_laboratory",),
                permissions=("laboratory.view_report",),
                source="src/laboratory/views/labroom.py LaboratoryRoomReportView",
            ),
        ),
    ),
    Feature(
        id="LAB-05",
        name="Mantener los catálogos del laboratorio",
        module="laboratory",
        kind="ui",
        description=(
            "Los desplegables que el resto de pantallas consume: tipos de mueble, de "
            "estante, de estructura, de puesto de trabajo, estados de objeto en "
            "estante, tipos de equipo y familias instrumentales."
        ),
        priority="P3",
        steps=(
            Step(
                id="alta_catalogo",
                name="Dar de alta una entrada de catálogo desde el formulario",
                actors=MONTADORES,
                routes=("laboratory:add_furniture_type_catalog",
                        "laboratory:add_shelf_type_catalog",
                        "laboratory:add_structure_type_catalog",
                        "laboratory:add_workplace_type_catalog",
                        "laboratory:add_shelfobject_status"),
                permissions=(),
                source="src/laboratory/views/furniture.py add_catalog",
            ),
            Step(
                id="consultar_catalogo",
                name="Consultar tipos de equipo y familias instrumentales",
                actors=USUARIOS_LAB,
                routes=("laboratory:equipmenttype_list",
                        "laboratory:instrumentalfamily_list"),
                permissions=("laboratory.view_object", "laboratory.view_catalog"),
                source="src/laboratory/views/catalogs.py",
            ),
        ),
        notes=(
            "Las cinco altas de catálogo comparten vista (`add_catalog`) y **ninguna "
            "declara permiso**: cualquiera que llegue al formulario puede añadir "
            "entradas al catálogo de la organización.",
        ),
    ),
    Feature(
        id="LAB-06",
        name="Dar de alta usuarios del laboratorio por código QR",
        module="laboratory",
        kind="ui",
        description=(
            "El alta rápida en el laboratorio: se genera un QR, se imprime, y quien lo "
            "escanea entra y queda registrado. Incluye su bitácora propia."
        ),
        priority="P2",
        steps=(
            Step(
                id="generar",
                name="Generar y administrar los QR de registro",
                actors=MONTADORES,
                routes=("laboratory:create_user_qr", "laboratory:manage_register_user_qr",
                        "laboratory:list_register_user_qr"),
                permissions=("laboratory.add_registeruserqr",
                             "laboratory.view_registeruserqr"),
                source="src/laboratory/views/laboratory.py create_user_qr, manage_register_qr",
            ),
            Step(
                id="imprimir",
                name="Descargar el PDF con el QR",
                actors=MONTADORES,
                routes=("laboratory:download_register_user_qr",),
                permissions=("laboratory.view_registeruserqr",),
                source="src/laboratory/views/laboratory.py get_pdf_register_user_qr",
            ),
            Step(
                id="registrarse",
                name="Escanear el QR y quedar registrado en el laboratorio",
                actors=("estudiante", "profesor", "anonimo"),
                routes=("laboratory:login_register_user_qr",),
                permissions=(),
                source="src/laboratory/views/laboratory.py login_register_user_qr",
            ),
            Step(
                id="bitacora_qr",
                name="Consultar quién entró por el QR",
                actors=MONTADORES,
                routes=("laboratory:logentry_register_user_qr",),
                permissions=(),
                source="src/laboratory/views/laboratory.py get_logentry_from_registeruserqr",
            ),
            Step(
                id="borrar_qr",
                name="Retirar un QR de registro",
                actors=MONTADORES,
                routes=("laboratory:delete_register_user_qr",),
                permissions=("laboratory.delete_registeruserqr",),
                source="src/laboratory/views/laboratory.py RegisterUserQRDeleteView",
            ),
        ),
        notes=(
            "`laboratory:create_user_qr` es el **único nombre duplicado** admitido en "
            "todo el proyecto: dos firmas de la misma vista, con y sin `<int:user>` "
            "(lista blanca de `test_url_inventory.py`).",
        ),
    ),
    Feature(
        id="LAB-07",
        name="Consultar la bitácora y recuperar lo borrado",
        module="laboratory",
        kind="ui",
        description=(
            "La trazabilidad de la organización: quién cambió qué, y la papelera desde "
            "la que se recupera lo que se borró con borrado lógico."
        ),
        priority="P2",
        steps=(
            Step(
                id="bitacora",
                name="Consultar la bitácora de la organización",
                actors=("administrativo_superior", "administrador_laboratorio",
                        "regente", "solo_lectura"),
                routes=("laboratory:logentry_list",),
                permissions=(),
                source="src/laboratory/views/logentry.py",
            ),
            Step(
                id="papelera",
                name="Ver la papelera y recuperar un elemento",
                actors=("administrativo_superior", "administrador_laboratorio"),
                routes=("laboratory:trash_list",),
                permissions=("djgentelella.view_trash",),
                source="src/laboratory/views/trash.py",
            ),
        ),
        notes=(
            "La papelera solo muestra lo que se borró pasando `related_objects=[org, "
            "lab]`: un `obj.delete()` pelado borra lógicamente pero deja el objeto "
            "invisible e irrecuperable.",
        ),
    ),
    Feature(
        id="LAB-08",
        name="Consultar y editar el perfil propio",
        module="laboratory",
        kind="ui",
        description=(
            "Los datos de la persona: teléfono, cédula, idioma, si quiere ver los "
            "tutoriales, y el cambio de contraseña."
        ),
        priority="P3",
        steps=(
            Step(
                id="ver_editar",
                name="Ver y editar el perfil",
                actors=USUARIOS_LAB,
                routes=("laboratory:profile", "laboratory:profile_detail"),
                permissions=("auth_and_perms.change_own_profile",
                             "auth_and_perms.view_profile"),
                source="src/authentication/users.py ChangeUser, get_profile",
            ),
            Step(
                id="password",
                name="Cambiar la contraseña",
                actors=USUARIOS_LAB,
                routes=("laboratory:password_change",),
                permissions=("auth_and_perms.change_own_profile",),
                source="src/authentication/users.py password_change",
            ),
        ),
    ),
)
