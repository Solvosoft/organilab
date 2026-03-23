from django.db import migrations


TUTORIALS = [
    {
        'title': 'Bienvenida a Organilab',
        'slug': 'bienvenida',
        'description': 'Introducción al sistema y navegación básica',
        'url_name': 'auth_and_perms:select_organization_by_user',
        'chapter': 'GENERAL',
        'auto_start': True,
        'order': 0,
        'roles': [],
        'steps': [
            {
                'order': 1, 'step_key': 'bienvenida-modal', 'step_type': 'MODAL',
                'title': 'Bienvenida a Organilab',
                'content': 'Organilab es un sistema de gestión de laboratorios diseñado para universidades con múltiples sedes. Le permite gestionar inventario, sustancias químicas, procedimientos, reservaciones y seguridad desde una sola plataforma.',
            },
            {
                'order': 2, 'step_key': 'seleccionar-org', 'step_type': 'MODAL',
                'title': 'Seleccione su organización',
                'content': 'Cada usuario pertenece a una o más organizaciones (sede, facultad, escuela). Seleccione la organización donde desea trabajar. Puede cambiar de organización en cualquier momento desde el menú.',
            },
            {
                'order': 3, 'step_key': 'estructura-sistema', 'step_type': 'MODAL',
                'title': 'Estructura del sistema',
                'content': 'El sistema se organiza así: <strong>Organización</strong> → <strong>Laboratorio</strong> → <strong>Sala</strong> → <strong>Mueble</strong> → <strong>Estante</strong> → <strong>Objetos</strong> (reactivos, materiales, equipos). Los permisos y tutoriales dependen de sus roles en cada organización.',
            },
        ],
    },
    {
        'title': 'Gestión de Organizaciones',
        'slug': 'gestion-organizaciones',
        'description': 'Jerarquía organizacional y herencia de permisos',
        'url_name': 'auth_and_perms:organizationManager',
        'chapter': 'PERMISOS',
        'auto_start': False,
        'order': 1,
        'roles': [11, 6, 10, 14],
        'steps': [
            {
                'order': 1, 'step_key': 'org-arbol', 'step_type': 'MODAL',
                'title': 'Jerarquía organizacional',
                'content': 'Las organizaciones se estructuran en forma de árbol. La <strong>organización raíz</strong> puede crear laboratorios y registrar usuarios. Las <strong>organizaciones hijas</strong> pueden relacionar laboratorios existentes y asignar roles dentro de su ámbito.',
            },
            {
                'order': 2, 'step_key': 'org-crear', 'step_type': 'MODAL',
                'title': 'Crear organización',
                'content': 'Puede crear organizaciones hijas para representar su estructura institucional. Ejemplo: Universidad → Sede Central → Facultad de Ciencias.',
            },
            {
                'order': 3, 'step_key': 'org-herencia', 'step_type': 'MODAL',
                'title': 'Herencia de permisos',
                'content': 'Los permisos asignados en una organización superior se heredan automáticamente a todas las organizaciones y laboratorios debajo. Un rol asignado en "Sede Central" aplica a todos los laboratorios de esa sede.',
            },
        ],
    },
    {
        'title': 'Roles y Permisos',
        'slug': 'roles-permisos',
        'description': 'Crear roles, asignar permisos y gestionar acceso',
        'url_name': 'auth_and_perms:list_rol_by_org',
        'chapter': 'PERMISOS',
        'auto_start': False,
        'order': 2,
        'roles': [11, 1, 6, 10],
        'steps': [
            {
                'order': 1, 'step_key': 'roles-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son los roles?',
                'content': 'Un <strong>Rol</strong> es un conjunto de permisos con un nombre descriptivo (ej: "Regente Químico", "Técnico de Laboratorio"). Los permisos determinan qué acciones puede realizar el usuario: ver inventario, agregar sustancias, gestionar reservaciones, etc.',
            },
            {
                'order': 2, 'step_key': 'roles-multiples', 'step_type': 'MODAL',
                'title': 'Roles múltiples',
                'content': 'Un usuario puede tener <strong>varios roles</strong> simultáneamente. Los permisos se suman: si tiene rol "Técnico" (gestión de inventario) y rol "SGA" (seguridad química), podrá hacer ambas cosas.',
            },
            {
                'order': 3, 'step_key': 'roles-crear', 'step_type': 'MODAL',
                'title': 'Crear un rol',
                'content': 'Para crear un rol, asígnele un nombre descriptivo y seleccione los permisos necesarios. Los permisos están agrupados por módulo (Laboratorio, SGA, Reservaciones, etc.).',
            },
            {
                'order': 4, 'step_key': 'roles-asignar', 'step_type': 'MODAL',
                'title': 'Asignar roles a usuarios',
                'content': 'Después de crear roles, vaya a la gestión de usuarios de la organización para asignar roles a cada persona. Un mismo usuario puede tener diferentes roles en diferentes organizaciones.',
            },
        ],
    },
    {
        'title': 'Gestión de Usuarios',
        'slug': 'gestion-usuarios',
        'description': 'Registrar usuarios y asignar tipos en la organización',
        'url_name': 'auth_and_perms:organizationManager',
        'chapter': 'PERMISOS',
        'auto_start': False,
        'order': 3,
        'roles': [11, 1, 6, 10],
        'steps': [
            {
                'order': 1, 'step_key': 'usuarios-tipos', 'step_type': 'MODAL',
                'title': 'Tipos de usuario en la organización',
                'content': 'Al agregar un usuario a la organización, se le asigna un tipo: <strong>Administrador</strong> (gestión completa), <strong>Gestor de laboratorio</strong> (administra labs específicos), o <strong>Usuario de laboratorio</strong> (acceso básico).',
            },
            {
                'order': 2, 'step_key': 'usuarios-agregar', 'step_type': 'MODAL',
                'title': 'Registrar usuarios',
                'content': 'Puede agregar usuarios existentes del sistema o registrar nuevos. Al registrar, defina el tipo de relación con la organización y luego asigne los roles que correspondan.',
            },
            {
                'order': 3, 'step_key': 'usuarios-contexto', 'step_type': 'MODAL',
                'title': 'Contexto organizacional',
                'content': 'Recuerde: un usuario puede pertenecer a múltiples organizaciones con diferentes roles en cada una. Cuando el usuario navega, el sistema filtra por la organización activa (visible en la URL y el menú).',
            },
        ],
    },
    {
        'title': 'Mi Laboratorio',
        'slug': 'mi-laboratorio',
        'description': 'Estructura física del laboratorio',
        'url_name': 'laboratory:labindex',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 4,
        'roles': [1, 6, 10, 5, 15, 14, 13],
        'steps': [
            {
                'order': 1, 'step_key': 'lab-estructura', 'step_type': 'MODAL',
                'title': 'Estructura del laboratorio',
                'content': 'Su laboratorio se organiza en: <strong>Salas</strong> (áreas funcionales), <strong>Muebles</strong> (gabinetes, refrigeradores, campanas), <strong>Estantes</strong> (posiciones dentro del mueble) y <strong>Objetos</strong> (reactivos, materiales, equipos almacenados).',
            },
            {
                'order': 2, 'step_key': 'lab-salas', 'step_type': 'MODAL',
                'title': 'Salas del laboratorio',
                'content': 'Las salas representan áreas funcionales de su laboratorio: Almacenamiento, Análisis, Instrumentación, Bodega, etc. Desde aquí puede navegar a cada sala para ver sus muebles y estantes.',
            },
            {
                'order': 3, 'step_key': 'lab-admin', 'step_type': 'MODAL',
                'title': 'Administración',
                'content': 'Desde el menú de administración puede crear salas, agregar muebles, configurar estantes y gestionar el inventario de objetos.',
            },
        ],
    },
    {
        'title': 'Salas y Muebles',
        'slug': 'salas-muebles',
        'description': 'Crear salas, muebles y configurar la grilla',
        'url_name': 'laboratory:rooms_list',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 5,
        'roles': [1, 6, 10, 15, 14],
        'steps': [
            {
                'order': 1, 'step_key': 'salas-crear', 'step_type': 'MODAL',
                'title': 'Crear salas',
                'content': 'Una sala es un área funcional del laboratorio. Ejemplos: "Sala de almacenamiento", "Sala de análisis", "Bodega de reactivos". Nombre las salas según su función real.',
            },
            {
                'order': 2, 'step_key': 'muebles-crear', 'step_type': 'MODAL',
                'title': 'Crear muebles',
                'content': 'Dentro de cada sala, cree muebles (gabinetes, refrigeradores, campanas de extracción). Al crear un mueble, defina una <strong>grilla</strong> (filas × columnas) que generará los estantes automáticamente.',
            },
            {
                'order': 3, 'step_key': 'muebles-grilla', 'step_type': 'MODAL',
                'title': 'Planificar la grilla',
                'content': '<strong>Importante:</strong> Planifique bien la grilla antes de agregar objetos. Cada celda de la grilla es un estante. Modificar la grilla después puede afectar los estantes existentes. El sistema genera un código QR automático para cada mueble.',
            },
        ],
    },
    {
        'title': 'Gestión de Inventario',
        'slug': 'gestion-inventario',
        'description': 'Tipos de objetos, agregar al inventario y alertas',
        'url_name': 'laboratory:rooms_list',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 6,
        'roles': [1, 6, 10, 5, 15, 13, 14, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'inv-tipos', 'step_type': 'MODAL',
                'title': 'Tipos de objetos',
                'content': 'El inventario tiene tres tipos: <strong>Reactivos</strong> (sustancias químicas, con fecha de vencimiento y lote), <strong>Materiales</strong> (consumibles como guantes, pipetas) y <strong>Equipos</strong> (instrumentos como balanzas, espectrofotómetros).',
            },
            {
                'order': 2, 'step_key': 'inv-agregar', 'step_type': 'MODAL',
                'title': 'Agregar al inventario',
                'content': 'Para agregar un objeto: seleccione el estante destino, elija el tipo, ingrese cantidad y unidad de medida. Para reactivos, agregue fecha de vencimiento, lote y estado físico.',
            },
            {
                'order': 3, 'step_key': 'inv-limites', 'step_type': 'MODAL',
                'title': 'Alertas de inventario',
                'content': 'Configure límites mínimos y máximos por estante. Cuando el inventario baja del mínimo, el sistema genera alertas automáticas. Los objetos marcados como <strong>peligrosos</strong> requieren clasificación SGA, y los <strong>precursores</strong> requieren reporte regulatorio.',
            },
            {
                'order': 4, 'step_key': 'inv-qr', 'step_type': 'MODAL',
                'title': 'Códigos QR',
                'content': 'Cada objeto genera un código QR automático que permite escanear y consultar información desde un dispositivo móvil. Útil para inventarios rápidos y trazabilidad.',
            },
        ],
    },
    {
        'title': 'Transferencias entre Laboratorios',
        'slug': 'transferencias',
        'description': 'Flujo de transferencia de objetos',
        'url_name': 'laboratory:rooms_list',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 7,
        'roles': [1, 6, 10, 5, 14],
        'steps': [
            {
                'order': 1, 'step_key': 'transf-concepto', 'step_type': 'MODAL',
                'title': 'Transferencias entre laboratorios',
                'content': 'Las transferencias permiten mover objetos de un laboratorio a otro. El flujo es: <strong>Solicitud</strong> → <strong>Revisión</strong> → <strong>Aceptación</strong> → <strong>Movimiento</strong>. El laboratorio receptor debe aceptar antes de que se mueva el inventario.',
            },
            {
                'order': 2, 'step_key': 'transf-traza', 'step_type': 'MODAL',
                'title': 'Trazabilidad',
                'content': 'Cada transferencia queda registrada con fecha, usuario solicitante, usuario que acepta y cantidades transferidas. Esto permite auditoría completa del movimiento de sustancias.',
            },
        ],
    },
    {
        'title': 'Clasificación SGA',
        'slug': 'clasificacion-sga',
        'description': 'Sistema Global Armonizado de clasificación química',
        'url_name': 'sga:step_one',
        'chapter': 'SUSTANCIAS',
        'auto_start': False,
        'order': 8,
        'roles': [16, 1, 6, 10, 5, 14, 13],
        'steps': [
            {
                'order': 1, 'step_key': 'sga-concepto', 'step_type': 'MODAL',
                'title': 'Sistema Global Armonizado (SGA)',
                'content': 'El SGA es el sistema internacional de clasificación y etiquetado de productos químicos. En Costa Rica es obligatorio por el <strong>Decreto 44741</strong>. Organilab le ayuda a clasificar sustancias según este estándar.',
            },
            {
                'order': 2, 'step_key': 'sga-indicaciones', 'step_type': 'MODAL',
                'title': 'Indicaciones de peligro y prudencia',
                'content': 'Las <strong>indicaciones H</strong> (Hazard) describen el tipo de peligro (ej: H301 - Tóxico si se ingiere). Los <strong>consejos P</strong> (Precautionary) indican medidas de prevención (ej: P264 - Lavarse las manos después de manipular).',
            },
            {
                'order': 3, 'step_key': 'sga-pictogramas', 'step_type': 'MODAL',
                'title': 'Pictogramas',
                'content': 'Los 9 pictogramas SGA indican visualmente el tipo de peligro: llama, calavera, signo de exclamación, corrosión, medio ambiente, etc. Se asignan automáticamente según la clasificación de la sustancia.',
            },
            {
                'order': 4, 'step_key': 'sga-almacenamiento', 'step_type': 'MODAL',
                'title': 'Clases de almacenamiento',
                'content': 'Las clases de almacenamiento (1-8) determinan cómo debe guardarse la sustancia: explosivos, gases comprimidos, líquidos inflamables, etc. El sistema verifica compatibilidad para prevenir almacenamiento inadecuado.',
            },
        ],
    },
    {
        'title': 'Hojas de Seguridad (MSDS)',
        'slug': 'hojas-seguridad',
        'description': 'Gestión de hojas de seguridad de sustancias',
        'url_name': 'msds:index_msds',
        'chapter': 'SUSTANCIAS',
        'auto_start': False,
        'order': 10,
        'roles': [1, 6, 10, 5, 13, 7],
        'steps': [
            {
                'order': 1, 'step_key': 'msds-concepto', 'step_type': 'MODAL',
                'title': 'Hojas de Seguridad (MSDS)',
                'content': 'Las MSDS (Material Safety Data Sheets) contienen información sobre propiedades, peligros, manejo, almacenamiento y primeros auxilios de cada sustancia. Cada sustancia peligrosa debe tener su MSDS asociada.',
            },
            {
                'order': 2, 'step_key': 'msds-vincular', 'step_type': 'MODAL',
                'title': 'Vincular MSDS',
                'content': 'Suba archivos de MSDS y vincúlelos a las sustancias correspondientes. Las MSDS quedan disponibles para consulta de cualquier usuario con acceso al laboratorio.',
            },
        ],
    },
    {
        'title': 'Control de Precursores Químicos',
        'slug': 'precursores',
        'description': 'Trazabilidad y reportes de precursores',
        'url_name': 'laboratory:reports',
        'chapter': 'SUSTANCIAS',
        'auto_start': False,
        'order': 11,
        'roles': [11, 1, 7, 6, 10],
        'steps': [
            {
                'order': 1, 'step_key': 'prec-concepto', 'step_type': 'MODAL',
                'title': 'Control de precursores',
                'content': 'Los precursores químicos son sustancias con control regulatorio especial en Costa Rica. El sistema rastrea todos los movimientos: quién compró, quién usó, cantidades y fechas.',
            },
            {
                'order': 2, 'step_key': 'prec-reportes', 'step_type': 'MODAL',
                'title': 'Reportes automáticos',
                'content': 'El sistema genera reportes de precursores automáticamente mediante tareas programadas. Estos reportes son necesarios para cumplimiento regulatorio. Puede consultarlos desde la sección de Reportes.',
            },
        ],
    },
    {
        'title': 'Procedimientos de Laboratorio',
        'slug': 'procedimientos',
        'description': 'Crear, ejecutar y gestionar procedimientos',
        'url_name': 'academic:procedure_list',
        'chapter': 'PROCEDIMIENTOS',
        'auto_start': False,
        'order': 12,
        'roles': [2, 1, 6, 10, 4, 5, 13, 14],
        'steps': [
            {
                'order': 1, 'step_key': 'proc-concepto', 'step_type': 'MODAL',
                'title': 'Procedimientos',
                'content': 'Un procedimiento es una <strong>plantilla reutilizable</strong> con pasos secuenciales para realizar una actividad en el laboratorio. Cada paso puede tener instrucciones, advertencias de seguridad y objetos requeridos (reactivos, materiales, equipos).',
            },
            {
                'order': 2, 'step_key': 'proc-crear', 'step_type': 'MODAL',
                'title': 'Crear procedimiento',
                'content': 'Defina el título, agregue pasos con instrucciones detalladas y vincule los objetos necesarios con sus cantidades. El sistema verificará si el laboratorio tiene stock suficiente.',
            },
            {
                'order': 3, 'step_key': 'proc-ejecutar', 'step_type': 'MODAL',
                'title': 'Ejecutar procedimiento',
                'content': 'Al ejecutar un procedimiento se crea una <strong>instancia</strong> (Mis Procedimientos) que pasa por estados: Borrador → En Revisión → Finalizado. En cada paso puede completar formularios y agregar observaciones.',
            },
            {
                'order': 4, 'step_key': 'proc-reservar', 'step_type': 'MODAL',
                'title': 'Reservación automática',
                'content': 'Al finalizar un procedimiento, el sistema puede generar <strong>reservaciones automáticas</strong> para los objetos requeridos, asegurando disponibilidad.',
            },
        ],
    },
    {
        'title': 'Reservaciones',
        'slug': 'reservaciones',
        'description': 'Solicitar, gestionar y devolver reservaciones',
        'url_name': 'reservations_management:reservations_list',
        'chapter': 'RESERVACIONES',
        'auto_start': False,
        'order': 13,
        'roles': [1, 6, 10, 4, 5, 13, 14],
        'steps': [
            {
                'order': 1, 'step_key': 'res-concepto', 'step_type': 'MODAL',
                'title': 'Reservaciones',
                'content': 'Las reservaciones permiten solicitar equipos, materiales o sustancias del laboratorio. Pueden ser manuales o generadas automáticamente desde un procedimiento.',
            },
            {
                'order': 2, 'step_key': 'res-estados', 'step_type': 'MODAL',
                'title': 'Flujo de estados',
                'content': 'La reservación pasa por: <strong>Solicitada</strong> → <strong>Aceptada/Rechazada</strong> → <strong>Cerrada</strong>. Los ítems reservados tienen su propio flujo: <strong>En Tránsito</strong> → <strong>Prestado</strong> → <strong>Devuelto</strong>.',
            },
            {
                'order': 3, 'step_key': 'res-devolucion', 'step_type': 'MODAL',
                'title': 'Devolución',
                'content': 'Las devoluciones pueden ser parciales o completas. El inventario se actualiza automáticamente al registrar la devolución. Los códigos QR agilizan el proceso.',
            },
        ],
    },
    {
        'title': 'Gestión de Riesgo',
        'slug': 'gestion-riesgo',
        'description': 'Zonas de riesgo y reportes de incidentes',
        'url_name': 'riskmanagement:riskzone_list',
        'chapter': 'GENERAL',
        'auto_start': False,
        'order': 14,
        'roles': [11, 1, 6, 10, 4, 7],
        'steps': [
            {
                'order': 1, 'step_key': 'risk-zonas', 'step_type': 'MODAL',
                'title': 'Zonas de riesgo',
                'content': 'Las zonas de riesgo representan áreas del laboratorio donde existen peligros específicos. Cada zona tiene un tipo (químico, biológico, radiológico, etc.) y un nivel de riesgo.',
            },
            {
                'order': 2, 'step_key': 'risk-incidentes', 'step_type': 'MODAL',
                'title': 'Reportes de incidentes',
                'content': 'Registre incidentes que ocurran en las zonas de riesgo: tipo de incidente, descripción, personas involucradas y acciones tomadas. Esta información es vital para prevención y cumplimiento normativo.',
            },
        ],
    },
    {
        'title': 'Desechos y Residuos',
        'slug': 'desechos-residuos',
        'description': 'Gestión de residuos químicos y descarte',
        'url_name': 'laboratory:disposal_substance',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 15,
        'roles': [13, 14, 1, 6, 10, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'desc-concepto', 'step_type': 'MODAL',
                'title': 'Gestión de desechos',
                'content': 'Los estantes de descarte permiten registrar residuos químicos y material a desechar. Esto es esencial para cumplir con la normativa de manejo de desechos peligrosos.',
            },
            {
                'order': 2, 'step_key': 'desc-depositar', 'step_type': 'MODAL',
                'title': 'Depositar residuos',
                'content': 'Para depositar un residuo, seleccione un estante marcado como descarte, registre el tipo de residuo, cantidad y clasificación. El sistema mantiene trazabilidad completa de los desechos.',
            },
        ],
    },
    {
        'title': 'Reportes',
        'slug': 'reportes',
        'description': 'Generar reportes de inventario y auditoría',
        'url_name': 'laboratory:reports',
        'chapter': 'GENERAL',
        'auto_start': False,
        'order': 16,
        'roles': [11, 1, 7, 6, 10, 5],
        'steps': [
            {
                'order': 1, 'step_key': 'rep-tipos', 'step_type': 'MODAL',
                'title': 'Tipos de reportes',
                'content': 'El sistema genera varios tipos de reportes: inventario por laboratorio, uso de sustancias, precursores químicos, reportes de regencia, y auditoría de cambios.',
            },
            {
                'order': 2, 'step_key': 'rep-generar', 'step_type': 'MODAL',
                'title': 'Generar reportes',
                'content': 'Seleccione el tipo de reporte, el período y los filtros necesarios. Los reportes pueden exportarse para presentar a autoridades regulatorias o para auditorías internas.',
            },
        ],
    },
]


def load_tutorials(apps, schema_editor):
    Tutorial = apps.get_model('presentation', 'Tutorial')
    TutorialStep = apps.get_model('presentation', 'TutorialStep')
    Rol = apps.get_model('auth_and_perms', 'Rol')

    for tdata in TUTORIALS:
        tutorial = Tutorial.objects.create(
            title=tdata['title'],
            slug=tdata['slug'],
            description=tdata['description'],
            url_name=tdata['url_name'],
            chapter=tdata['chapter'],
            auto_start=tdata['auto_start'],
            order=tdata['order'],
            is_active=True,
        )

        if tdata['roles']:
            roles = Rol.objects.filter(pk__in=tdata['roles'])
            tutorial.target_roles.set(roles)

        for sdata in tdata['steps']:
            TutorialStep.objects.create(
                tutorial=tutorial,
                order=sdata['order'],
                step_key=sdata['step_key'],
                title=sdata['title'],
                content=sdata['content'],
                step_type=sdata['step_type'],
                css_selector=sdata.get('css_selector', ''),
                position=sdata.get('position', 'bottom'),
                action_url=sdata.get('action_url', ''),
            )


def remove_tutorials(apps, schema_editor):
    Tutorial = apps.get_model('presentation', 'Tutorial')
    slugs = [t['slug'] for t in TUTORIALS]
    Tutorial.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('presentation', '0007_tutorial_tutorialprogress_tutorialstep'),
        ('auth_and_perms', '0026_remove_unused_roles'),
    ]

    operations = [
        migrations.RunPython(load_tutorials, remove_tutorials),
    ]
