# encoding: utf-8
"""Sustancias, clasificación GHS/SGA, fichas de seguridad y etiquetado.

El módulo con el flujo de aprobación más explícito del sistema —una sustancia nace en
borrador, se manda a revisión y alguien la aprueba— y, a la vez, el que peor encaja en
el eje de roles: **quien revisa no se define por un `Rol`, sino por pertenecer al grupo
de Django `RegisterOrganization`** (`sga/utils.py:52-57`). Ver SGA-01.

Casi todo el módulo exige además `auth_and_perms.institution_can_access`, un permiso
transversal que actúa de portero: sin él no se entra aunque se tengan los permisos
concretos.
"""

from presentation.feature_catalog import Feature, Step

SUBSTANCE_STATES = (
    "Substance.status: DRAFT(0) → UNDER_REVIEW(1) → APPROVED(2) "
    "(`sga/models.py:129-136`)",
    "ReviewSubstance.is_approved: False → True (`sga/models.py:900`)",
)

#: El portero transversal del módulo.
GATE = "auth_and_perms.institution_can_access"

REDACTORES = ("sga", "administrador_laboratorio", "tecnico_laboratorio",
              "lectura_agregado_sustancias", "manejo_sustancias")
REVISORES = ("administrativo_superior", "sga", "organization_management")
CONSULTA = ("sga", "administrador_laboratorio", "tecnico_laboratorio", "regente",
            "solo_lectura", "estudiante")

FEATURES = (
    Feature(
        id="SGA-01",
        name="Registrar una sustancia y llevarla hasta su aprobación",
        module="sga",
        kind="ui",
        description=(
            "Un redactor abre el asistente, describe la sustancia y sus "
            "características, completa la ficha de seguridad y la manda a revisión. "
            "Un revisor la mira en la bandeja, deja observaciones si hace falta, y la "
            "aprueba: al aprobarla se emiten los códigos de sustancia-laboratorio y se "
            "crea el objeto de inventario correspondiente."
        ),
        states=SUBSTANCE_STATES,
        priority="P1",
        doc="docs/source/desc_funcionalidades/ingreso_sus.rst",
        steps=(
            Step(
                id="abrir_asistente",
                name="Abrir el asistente y describir la sustancia (paso 1)",
                actors=REDACTORES,
                routes=("sga:create_sustance", "sga:step_one", "sga:update_substance"),
                permissions=("laboratory.change_object", GATE),
                transition="crea Substance en DRAFT(0) en el primer POST válido",
                source="src/sga/views/substance/views.py:58-136",
            ),
            Step(
                id="ficha_seguridad",
                name="Completar la hoja de seguridad (paso 4)",
                actors=REDACTORES,
                routes=("sga:step_four",),
                permissions=("sga.change_securityleaf", GATE),
                source="src/sga/views/substance/views.py:313",
            ),
            Step(
                id="subir_sds",
                name="Subir la ficha de datos de seguridad y seguir la extracción",
                actors=REDACTORES,
                routes=("sga:upload_sds", "sga:upload_sds_pk", "sga:sds_task_status"),
                permissions=("sga.change_substancecharacteristics", GATE),
                transition="dispara la tarea de extracción; el estado se consulta por polling",
                source="src/sga/views/substance/views.py:900-985",
            ),
            Step(
                id="proveedor",
                name="Añadir el proveedor de la sustancia",
                actors=REDACTORES,
                routes=("sga:add_sga_provider",),
                permissions=("sga.add_provider",),
                source="src/sga/views/substance/views.py add_sga_provider",
            ),
            Step(
                id="enviar_revision",
                name="Enviar la sustancia a revisión",
                actors=REDACTORES,
                routes=("sga:send_to_review",),
                permissions=("sga.change_substance", GATE),
                transition="DRAFT(0) → UNDER_REVIEW(1); notifica a los revisores",
                source="src/sga/views/substance/views.py:771-826",
            ),
            Step(
                id="bandeja_revision",
                name="Ver la bandeja de sustancias por aprobar",
                actors=REVISORES,
                routes=("sga:approved_substance", "sga:get_substance"),
                permissions=("sga.view_substance", GATE),
                source="src/sga/views/substance/views.py:180-194",
            ),
            Step(
                id="observar",
                name="Dejar, editar o borrar observaciones sobre la sustancia",
                actors=REVISORES + ("administrador_laboratorio",),
                routes=("sga:add_observation", "sga:update_observation",
                        "sga:delete_observation"),
                permissions=("sga.view_substanceobservation",
                             "sga.change_substanceobservation",
                             "sga.delete_substanceobservation"),
                source="src/sga/views/substance/views.py:509-604",
            ),
            Step(
                id="revisar_detalle",
                name="Abrir el detalle de la sustancia en revisión",
                actors=REVISORES,
                routes=("sga:detail_substance",),
                permissions=("sga.change_substance", GATE),
                source="src/sga/views/substance/views.py detail_substance",
            ),
            Step(
                id="aprobar",
                name="Aprobar la sustancia",
                actors=REVISORES,
                routes=("sga:accept_substance",),
                permissions=("sga.change_substance", GATE),
                transition=(
                    "ReviewSubstance.is_approved=True y Substance.status=APPROVED(2); "
                    "emite códigos y crea el objeto de inventario"
                ),
                source="src/sga/views/substance/views.py:202-243",
            ),
            Step(
                id="eliminar",
                name="Eliminar la sustancia",
                actors=REVISORES + ("administrador_laboratorio",),
                routes=("sga:delete_substance",),
                permissions=("sga.delete_substance", GATE),
                source="src/sga/views/substance/views.py:245-250",
            ),
        ),
        notes=(
            "HALLAZGO-SGA-1: **el revisor no es un rol.** `notify_request_created` "
            "(`sga/utils.py:52-57`) busca a quién avisar en el grupo de Django "
            "`RegisterOrganization`, no en un `Rol` ni en un `ProfilePermission`. El "
            "actor que aprueba sustancias vive en la capa 4 del modelo de "
            "autorización, fuera del eje de roles, y por eso ninguna prueba de "
            "permisos por `Rol` puede cubrirlo.",
            "HALLAZGO-SGA-2: `approve_substances` es alcanzable por GET y la "
            "idempotencia depende de una guardia escrita a mano "
            "(`views.py:215-221`). Sin esa guardia, recargar la página volvería a "
            "emitir códigos. Merece su propia aserción.",
            "HALLAZGO-SGA-3: crear una sustancia exige `laboratory.change_object`, no "
            "`sga.add_substance` (`views.py:58`). El permiso que el nombre haría "
            "esperar no interviene, así que un rol con todo SGA pero sin permisos de "
            "laboratorio no puede registrar una sustancia.",
        ),
    ),
    Feature(
        id="SGA-02",
        name="Obtener la etiqueta GHS y la ficha de seguridad de una sustancia",
        module="sga",
        kind="ui",
        description=(
            "Desde el detalle de la sustancia se genera la etiqueta con sus "
            "pictogramas y frases H/P, y se descarga la hoja de seguridad en PDF. Es "
            "el producto final del módulo: lo que acaba pegado en el envase."
        ),
        priority="P1",
        steps=(
            Step(
                id="generar_etiqueta",
                name="Generar la etiqueta de la sustancia",
                actors=CONSULTA,
                routes=("sga:generate_label",),
                permissions=("sga.view_substance", GATE),
                source="src/sga/views/substance/views.py generate_label",
            ),
            Step(
                id="hoja_seguridad",
                name="Descargar la hoja de seguridad en PDF",
                actors=CONSULTA,
                routes=("sga:security_leaf_pdf",),
                permissions=(GATE,),
                source="src/sga/views/substance/views.py security_leaf_pdf",
            ),
            Step(
                id="complementos_por_sustancia",
                name="Consultar los complementos SGA de una sustancia",
                actors=CONSULTA,
                routes=("sga:get_sgacomplement_by_substance",),
                permissions=(),
                source="src/sga/views/editor.py get_sgacomplement_by_substance",
            ),
        ),
    ),
    Feature(
        id="SGA-03",
        name="Mantener el catálogo de clasificación GHS",
        module="sga",
        kind="ui",
        description=(
            "Alta y edición de las indicaciones de peligro (frases H), los consejos de "
            "prudencia (frases P), las palabras de advertencia y las categorías de "
            "sustancia peligrosa. Es el catálogo del que bebe toda la clasificación: "
            "sin él, ninguna etiqueta dice nada."
        ),
        priority="P2",
        steps=(
            Step(
                id="ver_catalogo",
                name="Consultar frases H, frases P y palabras de advertencia",
                actors=CONSULTA,
                routes=("sga:danger_indications", "sga:prudence_advices",
                        "sga:warning_words"),
                permissions=("sga.view_dangerindication", "sga.view_prudenceadvice",
                             "sga.view_warningword"),
                source="src/sga/views/substance/views.py view_* ",
            ),
            Step(
                id="alta_complemento",
                name="Dar de alta una frase o palabra de advertencia",
                actors=("sga", "administrativo_superior"),
                routes=("sga:add_danger_indication", "sga:add_prudence_advice",
                        "sga:add_warning_word"),
                permissions=(),
                source="src/sga/views/substance/views.py add_sga_complements",
            ),
            Step(
                id="editar_complemento",
                name="Editar una frase o palabra de advertencia",
                actors=("sga", "administrativo_superior"),
                routes=("sga:update_danger_indication", "sga:update_prudence_advice",
                        "sga:update_warning_word"),
                permissions=("sga.change_dangerindication",
                             "sga.change_prudenceadvice", "sga.change_warningword"),
                source="src/sga/views/substance/views.py change_*",
            ),
            Step(
                id="sustancias_peligrosas",
                name="Consultar sustancias peligrosas y sus categorías",
                actors=CONSULTA,
                routes=("sga:danger_substance", "sga:danger_substance_category"),
                permissions=("sga.view_dangersubstance",
                             "sga.view_dangersubstancecategory"),
                source="src/sga/views/danger_substance/views.py",
            ),
        ),
        notes=(
            "El alta de complementos (`add_sga_complements`) no declara permiso "
            "inspeccionable, mientras que la edición sí. Crear una frase H es más "
            "fácil que corregirla.",
        ),
    ),
    Feature(
        id="SGA-04",
        name="Diseñar plantillas de etiqueta en el editor SGA",
        module="sga",
        kind="ui",
        description=(
            "El editor visual con el que se compone una plantilla de etiqueta: se "
            "eligen los bloques, se previsualiza, se ajusta el tamaño del recipiente y "
            "se guarda como plantilla personal o de la organización. Es todo estado en "
            "el cliente, así que es de los pocos sitios donde Selenium se gana el "
            "sueldo."
        ),
        priority="P2",
        steps=(
            Step(
                id="abrir_editor",
                name="Abrir el editor de plantillas",
                actors=("sga", "administrativo_superior", "administrador_laboratorio"),
                routes=("sga:editor", "sga:index_editor"),
                permissions=(GATE,),
                source="src/sga/views/editor.py template_editor",
            ),
            Step(
                id="crear_plantilla",
                name="Crear una plantilla personal",
                actors=("sga", "administrativo_superior", "administrador_laboratorio"),
                routes=("sga:add_personal", "sga:sgalabel_create"),
                permissions=("sga.add_displaylabel", GATE),
                source="src/sga/views/editor.py:create_personal_template, create_sgalabel",
            ),
            Step(
                id="editar_plantilla",
                name="Editar la plantilla paso a paso",
                actors=("sga", "administrativo_superior", "administrador_laboratorio"),
                routes=("sga:edit_personal", "sga:sgalabel_step_one",
                        "sga:sgalabel_step_two"),
                permissions=("sga.change_displaylabel", GATE),
                source="src/sga/views/editor.py:256, sgalabel_step_one/two",
            ),
            Step(
                id="previsualizar",
                name="Previsualizar la etiqueta y su código de barras",
                actors=("sga", "administrativo_superior", "administrador_laboratorio"),
                routes=("sga:get_preview", "sga:engine_label_preview",
                        "sga:barcode_from_number"),
                permissions=(),
                source="src/sga/views/editor.py get_preview, engine_label_preview",
            ),
            Step(
                id="borrar_plantilla",
                name="Borrar una plantilla",
                actors=("sga", "administrativo_superior"),
                routes=("sga:delete_sgalabel",),
                permissions=("sga.delete_displaylabel", GATE),
                source="src/sga/views/editor.py delete_sgalabel",
            ),
        ),
    ),
    Feature(
        id="SGA-05",
        name="Gestionar empresas y tamaños de recipiente del etiquetado",
        module="sga",
        kind="ui",
        description=(
            "Los datos maestros que la etiqueta imprime: la empresa que figura como "
            "responsable y los tamaños de recipiente que determinan la escala de la "
            "etiqueta."
        ),
        priority="P3",
        steps=(
            Step(
                id="listar_empresas",
                name="Listar y consultar empresas",
                actors=("sga", "administrativo_superior", "administrador_laboratorio"),
                routes=("sga:get_companies", "sga:get_company"),
                permissions=("sga.view_builderinformation", GATE),
                source="src/sga/views/editor.py get_companies, get_company",
            ),
            Step(
                id="alta_empresa",
                name="Crear o editar una empresa",
                actors=("sga", "administrativo_superior"),
                routes=("sga:add_company", "sga:edit_company"),
                permissions=("sga.add_builderinformation",
                             "sga.change_builderinformation", GATE),
                source="src/sga/views/editor.py create_company, edit_company",
            ),
            Step(
                id="borrar_empresa",
                name="Quitar una empresa",
                actors=("sga", "administrativo_superior"),
                routes=("sga:remove_company",),
                permissions=("sga.delete_builderinformation", GATE),
                source="src/sga/views/editor.py remove_company",
            ),
            Step(
                id="recipientes",
                name="Consultar y dar de alta tamaños de recipiente",
                actors=("sga", "administrativo_superior", "administrador_laboratorio",
                        "depositante_residuos"),
                routes=("sga:recipient_size", "sga:add_recipient_size",
                        "sga:get_recipient_size"),
                permissions=("sga.view_recipientsize", "sga.view_builderinformation",
                             GATE),
                source="src/sga/views/substance/views.py view_recipient_size; editor.py",
            ),
        ),
    ),
)
