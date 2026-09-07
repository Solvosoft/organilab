# encoding: utf-8
"""Organizaciones, roles, usuarios y autenticación: el módulo que define el eje.

Aquí se construye lo que el resto del catálogo da por supuesto: el árbol de
organizaciones, los `Rol` con sus permisos, y la asignación de personas a organizaciones
y laboratorios. Si esto se configura mal, ningún permiso del resto del sistema significa
lo que dice.

Contiene además la suplantación de identidad, que es un actor por derecho propio y el
único que puede convertirse en cualquier otro.
"""

from presentation.feature_catalog import Feature, Step

ADMINISTRADORES = ("administrativo_superior", "organization_management",
                   "administrador_laboratorio", "administrativo_centro_trabajo")

FEATURES = (
    Feature(
        id="ORG-01",
        name="Elegir organización y orientarse en el árbol",
        module="auth_and_perms",
        kind="ui",
        description=(
            "La puerta de entrada del sistema multiinquilino: el usuario elige en qué "
            "organización trabaja, y a partir de ahí todo lleva `org_pk` en la URL. "
            "También el mapa de laboratorios y el listado de organizaciones y sus labs."
        ),
        priority="P1",
        steps=(
            Step(
                id="elegir_org",
                name="Elegir la organización con la que se trabaja",
                actors=("estudiante", "profesor", "tecnico_laboratorio",
                        "administrador_laboratorio", "administrativo_superior",
                        "regente", "solo_lectura"),
                routes=("auth_and_perms:select_organization_by_user",),
                permissions=(),
                source="src/auth_and_perms/views/select_organization.py",
            ),
            Step(
                id="mapa_labs",
                name="Ver el mapa de laboratorios",
                actors=("administrador_laboratorio", "administrativo_superior",
                        "regente"),
                routes=("auth_and_perms:map_of_laboratories",),
                permissions=("risk_management.view_riskzone",),
                source="src/auth_and_perms/views/select_organization.py",
            ),
            Step(
                id="listar_org",
                name="Listar organizaciones y sus laboratorios",
                actors=ADMINISTRADORES,
                routes=("auth_and_perms:lab_org_list",),
                permissions=("laboratory.view_organizationstructure",),
                source="src/auth_and_perms/views/organizationstructure.py get_labs_orgs",
            ),
        ),
        notes=(
            "El mapa de laboratorios exige `risk_management.view_riskzone`: para ver "
            "dónde están los laboratorios hace falta un permiso del módulo de riesgo.",
        ),
    ),
    Feature(
        id="ORG-02",
        name="Administrar la organización: usuarios, roles y estructura",
        module="auth_and_perms",
        kind="ui",
        description=(
            "La pantalla desde la que un administrador arma su inquilino: da de alta "
            "usuarios, crea y edita roles, copia el juego de roles a otra organización, "
            "habilita las organizaciones hijas y relaciona modelos con la organización. "
            "Es donde se materializa el eje de roles que este catálogo usa."
        ),
        priority="P1",
        doc="docs/source/administrative_usage/perms.rst",
        steps=(
            Step(
                id="panel",
                name="Abrir el gestor de la organización",
                actors=ADMINISTRADORES,
                routes=("auth_and_perms:organizationManager",),
                permissions=("laboratory.can_manage_org_permissions",),
                source="src/auth_and_perms/views/organizationstructure.py:53",
            ),
            Step(
                id="usuarios",
                name="Añadir usuarios a la organización",
                actors=ADMINISTRADORES,
                routes=("auth_and_perms:add_user",
                        "auth_and_perms:addusersorganization",
                        "auth_and_perms:get_users"),
                permissions=("auth.add_user",
                             "laboratory.change_organizationstructure",
                             "auth_and_perms.view_profile"),
                source="src/auth_and_perms/views/organizationstructure.py AddUser",
            ),
            Step(
                id="roles",
                name="Consultar, crear y editar los roles de la organización",
                actors=ADMINISTRADORES,
                routes=("auth_and_perms:list_rol_by_org", "auth_and_perms:update_rol",
                        "auth_and_perms:get_rol",
                        "auth_and_perms:get_roles_by_organization",
                        "auth_and_perms:add_rol_by_laboratory"),
                permissions=("auth_and_perms.change_rol", "auth_and_perms.view_rol"),
                source="src/auth_and_perms/views/organizationstructure.py",
            ),
            Step(
                id="borrar_rol",
                name="Quitar un rol de la organización",
                actors=ADMINISTRADORES,
                routes=("auth_and_perms:del_rol_by_org",),
                permissions=("auth_and_perms.delete_rol",),
                source="src/auth_and_perms/views/organizationstructure.py",
            ),
            Step(
                id="copiar_roles",
                name="Copiar el juego de roles a otra organización",
                actors=ADMINISTRADORES,
                routes=("auth_and_perms:copy_rols",),
                permissions=("laboratory.change_organizationstructure",),
                source="src/auth_and_perms/views/organizationstructure.py copy_rols",
            ),
            Step(
                id="estructura",
                name="Habilitar organizaciones hijas y relacionar modelos",
                actors=ADMINISTRADORES,
                routes=("auth_and_perms:enable_child_organizations",
                        "auth_and_perms:add_contenttype_to_org"),
                permissions=("laboratory.change_organizationstructure",),
                source="src/auth_and_perms/views/organizationstructure.py",
            ),
            Step(
                id="administradores",
                name="Consultar quién administra la organización",
                actors=ADMINISTRADORES,
                routes=("auth_and_perms:get_org_administrators",),
                permissions=(),
                source="src/auth_and_perms/views/organizationstructure.py:542",
            ),
        ),
        notes=(
            "HALLAZGO-ORG-1: `get_org_administrators` (`:542`) filtra por "
            '`rol__name="Administrativo superior"`, una **cadena literal**. Renombrar '
            "ese rol deja la consulta vacía sin que nada falle.",
            "Listar roles exige `change_rol`, no `view_rol`: no se puede dar consulta "
            "de roles sin dar edición.",
        ),
    ),
    Feature(
        id="ORG-03",
        name="Entrar con firma digital o segundo factor",
        module="auth_and_perms",
        kind="ui",
        description=(
            "El acceso por firma digital del BCCR —el usuario se crea si no existe— y "
            "el código QR del segundo factor TOTP."
        ),
        priority="P3",
        steps=(
            Step(
                id="firma_digital",
                name="Autenticarse con la firma digital del BCCR",
                actors=("anonimo",),
                routes=("auth_and_perms:login_with_bccr",
                        "auth_and_perms:check_signature_window_status_register"),
                permissions=(),
                source="src/auth_and_perms/views/fva_rest_authentication.py",
            ),
            Step(
                id="totp",
                name="Obtener el QR del segundo factor",
                actors=("estudiante", "profesor", "administrador_laboratorio"),
                routes=("auth_and_perms:show_qr_img",),
                permissions=(),
                source="src/auth_and_perms/views/user_org_creation.py show_QR_img",
            ),
        ),
        notes=(
            "`login_with_bccr` está excluida del smoke a propósito "
            "(`url_smoke.py` `SMOKE_EXCLUDES`): abre la ventana de firma digital.",
        ),
    ),
    Feature(
        id="ORG-04",
        name="Suplantar a otro usuario para dar soporte",
        module="auth_and_perms",
        kind="ui",
        description=(
            "Quien tiene el permiso entra en la sesión de otro usuario de su misma "
            "organización para reproducir lo que ese usuario ve, y luego sale. Queda "
            "registrado en `ImpostorLog` con IP y token."
        ),
        priority="P1",
        steps=(
            Step(
                id="suplantar",
                name="Entrar como otro usuario",
                actors=("administrativo_superior", "organization_management"),
                routes=("auth_and_perms:change_to_impostor",),
                permissions=("auth_and_perms.change_impostorlog",),
                transition="crea ImpostorLog(logged_in) y la cookie impostor_token",
                source="src/auth_and_perms/views/impostor.py:19-63",
            ),
            Step(
                id="salir",
                name="Volver a la identidad propia",
                actors=("administrativo_superior", "organization_management"),
                routes=("auth_and_perms:remove_impostor",),
                permissions=(),
                transition="cierra el ImpostorLog",
                source="src/auth_and_perms/views/impostor.py:66-88",
            ),
        ),
        notes=(
            "HALLAZGO-ORG-2: **no hay restricción de privilegio.** Las cuatro guardas "
            "(`impostor.py:19-63`) comprueban que el suplantado pertenezca a la misma "
            "organización, que no sea uno mismo y que no haya otra sesión activa — "
            "pero no que el suplantador tenga al menos tantos permisos como el "
            "suplantado. Quien tenga `change_impostorlog` puede entrar como el "
            "administrador de su organización. Es una escalada de privilegios por "
            "diseño, y la auditoría en `ImpostorLog` es el único control.",
            "Las dos rutas están fuera del smoke porque rompen la sesión de la "
            "corrida; necesitan prueba propia.",
        ),
    ),
)
