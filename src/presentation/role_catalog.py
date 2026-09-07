# encoding: utf-8
"""El eje de roles: quién puede hacer qué, y con qué nombre.

Organilab tiene **cuatro capas de autorización superpuestas más una implícita**, y
confundirlas es la causa de que "está probado" signifique cosas distintas según quién
lo diga:

1. ``User.is_superuser`` — no es un rol, es un cortocircuito. Se salta el middleware
   entero (``authentication/middleware.py:49-50``) y otros cinco puntos.
2. ``UserOrganization.type_in_organization`` (``laboratory/models.py:1272-1301``) — no
   concede permisos, filtra elegibilidad (solo ADMINISTRATOR y LABORATORY_MANAGER pueden
   ser responsables de un laboratorio, ``laboratory/forms.py:99-104``).
3. ``Rol`` → ``ProfilePermission`` — **la única capa que concede permisos de verdad**, y
   la que este módulo cataloga.
4. Grupos de Django (``Profile``, ``PendingTasks``, ``SGAView``, ``RegisterOrganization``).
5. Implícita: actores definidos por un campo (``Laboratory.responsible``, ``Regent.user``)
   o por el estado de un flujo (quien pidió algo frente a quien lo aprueba).

Este módulo **no duplica los permisos**: esos viven en
``auth_and_perms/management/commands/update_roles.py``, que es la autoridad. Aquí solo
está la identidad de cada rol —id estable, nombre canónico, alias y capa— para poder
decir "esta funcionalidad la ejecuta este rol" y "este rol no lo ejercita ninguna
prueba". El guardián comprueba que los dos ficheros no se separen.

Sobre los alias: las fixtures escriben los nombres a su manera —``capacitacion.json``
dice ``Docente`` donde el catálogo dice ``Profesor``, y ``Tecnico`` sin tilde—. Sin la
tabla de alias, una prueba que sí ejercita un rol se contaría como que no lo ejercita.
"""

from collections import namedtuple

#: ``layer`` dice de qué capa sale la autoridad: solo ``rol`` concede permisos.
Role = namedtuple(
    "Role",
    "id name layer canonical defined_in aliases counts_as_coverage description",
)


def _rol(id, name, defined_in, description, aliases=()):
    return Role(
        id=id, name=name, layer="rol", canonical=True, defined_in=defined_in,
        aliases=tuple(aliases), counts_as_coverage=True, description=description,
    )


#: Los roles institucionales. Orden: el de `update_roles.py:handle()`.
CANONICAL_ROLES = (
    _rol("estudiante", "Estudiante",
         "auth_and_perms/management/commands/update_roles.py:30",
         "Acceso básico: consulta el laboratorio y su perfil, agrega/retira objetos de "
         "estantes y permisos básicos de desechos. Es el rol de reserva del alta por "
         "OIDC (`authentication/oidc_backend.py:112`)."),
    _rol("depositante_residuos", "Depositante de residuos",
         "auth_and_perms/management/commands/update_roles.py:47",
         "Registra y gestiona desechos. Se le quitan explícitamente los permisos de "
         "edición de SGA (`update_roles.py:61-85`)."),
    _rol("creador_laboratorio", "Creador de laboratorio",
         "auth_and_perms/management/commands/update_roles.py:163",
         "Crea la estructura física: laboratorios, salas, muebles, estantes, objetos. "
         "Sin reportes, sin SGA y sin reservaciones."),
    _rol("administrador_laboratorio", "Administrador de Laboratorio",
         "auth_and_perms/management/commands/update_roles.py:212",
         "Máxima autoridad operativa del laboratorio. Único con "
         "`laboratory.can_manage_inform_status` (`update_roles.py:100`) y uno de los dos "
         "con `can_approve_labororgrequest`."),
    _rol("lectura_agregado_sustancias", "Lectura y agregado de sustancias",
         "auth_and_perms/management/commands/update_roles.py:265",
         "Consulta general más registrar y editar objetos de inventario y su "
         "trazabilidad."),
    _rol("asistente_laboratorio", "Asistente de laboratorio",
         "auth_and_perms/management/commands/update_roles.py:450",
         "Procedimientos, inventario, informes y reservaciones; puede crear estructura "
         "organizacional."),
    _rol("profesor", "Profesor",
         "auth_and_perms/management/commands/update_roles.py:531",
         "Crea y administra procedimientos académicos: plantillas, pasos, observaciones "
         "y objetos requeridos.",
         aliases=("Docente",)),
    _rol("tesista_desechos", "Tesista modulo desechos",
         "auth_and_perms/management/commands/update_roles.py:581",
         "Desechos y flujo de laboratorio. No gestiona usuarios, roles ni estructura."),
    _rol("solo_lectura", "Solo Lectura",
         "auth_and_perms/management/commands/update_roles.py:756",
         "Consulta amplia sin crear ni eliminar. Para auditoría y supervisión."),
    _rol("tecnico_laboratorio", "Técnico de Laboratorio",
         "auth_and_perms/management/commands/update_roles.py:828",
         "Opera el día a día: inventario, estantes, académico y reservaciones.",
         aliases=("Tecnico de Laboratorio",)),
    _rol("sga", "SGA",
         "auth_and_perms/management/commands/update_roles.py:948",
         "Acceso completo y exclusivo al módulo SGA, con etiquetado full."),
    _rol("regente", "Regente",
         "auth_and_perms/management/commands/update_roles.py:979",
         "Solo lectura con cobertura total, más los reportes de regencia y precursores. "
         "Diseñado para el Regente Químico.",
         aliases=("Regente Quimico", "Regente Químico")),
    _rol("administrativo_superior", "Administrativo superior",
         "auth_and_perms/management/commands/update_roles.py:1005",
         "Máxima autoridad administrativa. Único con IPER completo activo y el rol que "
         "`get_org_administrators` busca por nombre literal "
         "(`views/organizationstructure.py:542`)."),
    _rol("administrativo_centro_trabajo", "Administrativo de centro de trabajo",
         "auth_and_perms/management/commands/update_roles.py:1030",
         "Como el administrativo superior a nivel de centro, sin gestión de usuarios ni "
         "de roles."),
    _rol("auditor_iper", "Auditor IPER",
         "auth_and_perms/management/commands/update_roles.py:1231",
         "IPER en solo lectura más `view_all_iper` y `add_iperobservation`. Se le quita "
         "`view_riskzone` (`:1243`). Se autocrea si no existe."),
    _rol("administrador_iper", "Administrador IPER",
         "auth_and_perms/management/commands/update_roles.py:1254",
         "IPER completo, incluidos `manage_iper_catalog` y `request_iper`. Se autocrea "
         "si no existe."),
    _rol("manejo_sustancias", "Manejo de sustancias del laboratorio",
         "auth_and_perms/management/commands/add_static_rol.py:17",
         "Rol construido con PKs de permiso escritas a mano (`:19-51`): depende del "
         "orden de las migraciones y no sobrevive a una base distinta."),
    _rol("organization_management", "Organization Management",
         "auth_and_perms/views/user_org_creation.py:95",
         "Se crea una por organización raíz al registrarla, con todos los permisos del "
         "grupo `RegisterOrganization`. Es el superadministrador de la organización."),
)

#: Actores que **no** son un `Rol` pero ejecutan pasos de los flujos. Se catalogan para
#: poder nombrarlos en el catálogo sin fingir que conceden permisos.
PSEUDO_ROLES = (
    Role("superusuario", "Superusuario", "superusuario", False,
         "authentication/middleware.py:49-50", (), False,
         "No es un rol: es un cortocircuito. Se salta el middleware y otros cinco "
         "puntos (`laboratory/utils.py:92`, `templatetags/user_rol_tags.py:19`, "
         "`templatetags/laboratory.py:30`, `views/organizations.py:56`, "
         "`gtselects.py:646`). **Nunca cuenta como cobertura de ningún rol**: una "
         "prueba que corre con superusuario no prueba el permiso."),
    Role("org_administrator", "Administrador de la organización", "tipo_en_organizacion",
         False, "laboratory/models.py:1273", (), False,
         "`type_in_organization = 1`. No concede permisos; habilita ser responsable de "
         "un laboratorio (`laboratory/forms.py:99-104`)."),
    Role("org_lab_manager", "Gestor de laboratorio", "tipo_en_organizacion", False,
         "laboratory/models.py:1274", (), False,
         "`type_in_organization = 2`. Igual que el anterior: elegibilidad, no permisos."),
    Role("org_lab_user", "Usuario de laboratorio", "tipo_en_organizacion", False,
         "laboratory/models.py:1275", (), False,
         "`type_in_organization = 3`, el que asigna el alta por OIDC "
         "(`oidc_backend.py:97-101`)."),
    Role("responsable_lab", "Responsable del laboratorio", "campo", False,
         "laboratory/models.py Laboratory.responsible", (), False,
         "Actor por campo: destinatario natural de tareas pendientes "
         "(`pending_tasks/models.py:99`)."),
    Role("regente_lab", "Regente asignado al laboratorio", "campo", False,
         "risk_management/models.py:192-216", (), False,
         "`Regent.user`, con `type_regent` químico / ingeniero químico / veterinario. No "
         "confundir con el `Rol` «Regente», que es de solo lectura."),
    Role("sistema", "Sistema", "sistema", False,
         "organilab/settings.py CELERYBEAT_SCHEDULE", (), False,
         "Lo ejecuta Celery, sin usuario. Es el actor de siete transiciones de estado "
         "que ningún humano dispara."),
    Role("anonimo", "Anónimo", "sistema", False, "—", (), False,
         "Sin autenticar. Solo debería alcanzar el registro y la portada."),
)

ALL_ROLES = CANONICAL_ROLES + PSEUDO_ROLES

#: Los 22 `Rol` "Gestión de X" de `fixtures/selenium/base_selenium.json` son de fixture:
#: uno por modelo, no existen en producción y no corresponden a ningún rol institucional.
#: Se listan para que la sonda no los confunda con cobertura de rol real.
FIXTURE_ONLY_ROLE_PREFIX = "Gestión de "

_BY_ID = {role.id: role for role in ALL_ROLES}


def get_role(role_id):
    try:
        return _BY_ID[role_id]
    except KeyError:
        raise LookupError("No existe el rol %r en el eje" % role_id)


def resolve_name(name):
    """Del nombre tal cual está en la base o en una fixture, al rol del eje.

    Devuelve ``None`` para los nombres de fixture y para cualquier rol que no esté
    catalogado: son ruido, no cobertura.
    """
    for role in ALL_ROLES:
        if name == role.name or name in role.aliases:
            return role
    return None


def canonical_ids():
    return tuple(role.id for role in CANONICAL_ROLES)
