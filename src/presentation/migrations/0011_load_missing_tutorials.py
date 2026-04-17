from django.db import migrations


TUTORIALS = [
    # Gap 2: Gestión de Usuarios en el Laboratorio
    # (complemento de order 30 que cubre el QR; aquí se cubren estado, código,
    # modificación y desactivación de usuarios — cap. 6 del manual)
    {
        'title': 'Gestión de Usuarios en el Laboratorio',
        'slug': 'usuarios-laboratorio-gestion',
        'description': 'Estado, código de identificación, modificación y desactivación de usuarios del laboratorio',
        'url_name': 'laboratory:list_register_user_qr',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 41,
        'roles': [11, 1, 6, 10],
        'steps': [
            {
                'order': 1, 'step_key': 'usrlab-estado', 'step_type': 'MODAL',
                'title': 'Estado del usuario',
                'content': 'Cada usuario del laboratorio puede estar <strong>Activo</strong> o <strong>Inactivo</strong>. Solo los usuarios activos pueden ingresar y operar en el sistema. El estado se configura al momento del registro y puede modificarse en cualquier momento desde la gestión del usuario.',
            },
            {
                'order': 2, 'step_key': 'usrlab-codigo', 'step_type': 'MODAL',
                'title': 'Código / Identificador único',
                'content': 'El sistema solicita un <strong>código único</strong> por usuario que puede corresponder al número de identificación institucional, un código interno o un código de acceso. Este código se utiliza para generar el <strong>QR personal</strong> del usuario y para identificarlo en listas de control y reportes del laboratorio.',
            },
            {
                'order': 3, 'step_key': 'usrlab-qr', 'step_type': 'MODAL',
                'title': 'Código QR personal del usuario',
                'content': 'El QR generado para cada usuario sirve para: <strong>registro de ingreso</strong> al laboratorio, <strong>consulta de permisos</strong> asignados, <strong>validación de identidad</strong> y <strong>acceso a módulos autorizados</strong>. El QR puede imprimirse o mostrarse desde el dispositivo móvil.',
            },
            {
                'order': 4, 'step_key': 'usrlab-modificar', 'step_type': 'MODAL',
                'title': 'Modificar datos del usuario',
                'content': 'Desde la lista de usuarios registrados puede editar: <strong>estado</strong> (activo/inactivo), <strong>rol</strong> asignado, <strong>organización</strong> de pertenencia, <strong>código</strong> de identificación y <strong>permisos asociados</strong>. Los cambios aplican de inmediato al guardar.',
            },
            {
                'order': 5, 'step_key': 'usrlab-desactivar', 'step_type': 'MODAL',
                'title': 'Desactivar un usuario',
                'content': 'Cuando un usuario ya no requiere acceso al laboratorio, cambie su estado a <strong>Inactivo</strong> en lugar de eliminarlo. Esto preserva el historial completo de sus acciones (trazabilidad) y cumple con requisitos de auditoría. El usuario desactivado no puede iniciar sesión ni operar en el sistema.',
            },
        ],
    },

    # Gap 3: Estadísticas de Reactivos
    {
        'title': 'Estadísticas de Reactivos',
        'slug': 'estadisticas-reactivos',
        'description': 'Consultar estadísticas de consumo e inventario de reactivos por período',
        'url_name': 'laboratory:shel_objects_reactives',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 42,
        'roles': [1, 6, 10, 5, 15, 13, 14],
        'steps': [
            {
                'order': 1, 'step_key': 'stat-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son las Estadísticas de Reactivos?',
                'content': 'El módulo de <strong>Estadísticas de Reactivos</strong> permite consultar métricas del inventario durante un período determinado. Es especialmente útil para <strong>cierres anuales</strong>, <strong>auditorías internas</strong>, <strong>análisis de consumo</strong> y <strong>toma de decisiones</strong> sobre reordenamiento y presupuesto.',
            },
            {
                'order': 2, 'step_key': 'stat-periodo', 'step_type': 'MODAL',
                'title': 'Seleccionar período de análisis',
                'content': 'Defina el rango de fechas sobre el cual desea analizar el comportamiento del inventario. Puede consultar períodos mensuales, trimestrales o anuales. El sistema filtrará todos los movimientos de reactivos comprendidos en ese rango para generar las estadísticas.',
            },
            {
                'order': 3, 'step_key': 'stat-consumo', 'step_type': 'MODAL',
                'title': 'Análisis de consumo',
                'content': 'Las estadísticas muestran cuánto se ha consumido de cada reactivo en el período seleccionado. Con esta información puede identificar los reactivos de <strong>mayor rotación</strong>, ajustar los <strong>límites de reorden</strong> y optimizar las compras para evitar desabastecimiento o acumulación innecesaria.',
            },
            {
                'order': 4, 'step_key': 'stat-cierre', 'step_type': 'MODAL',
                'title': 'Cierre anual de inventario',
                'content': 'Al cierre de año, use este módulo para obtener un <strong>reporte de inventario inicial vs. final</strong>. Esto permite comparar el stock al inicio del período contra el stock actual, identificar diferencias y generar evidencia para auditorías. Los datos pueden exportarse para incluirse en informes institucionales.',
            },
        ],
    },

    # Gap 4: Reportes Específicos del Laboratorio
    {
        'title': 'Reportes Específicos del Laboratorio',
        'slug': 'reportes-especificos',
        'description': 'Guía detallada de cada tipo de reporte disponible y sus campos requeridos',
        'url_name': 'laboratory:reports',
        'chapter': 'GENERAL',
        'auto_start': False,
        'order': 43,
        'roles': [11, 1, 7, 6, 10, 5],
        'steps': [
            {
                'order': 1, 'step_key': 'rptdet-infregencial', 'step_type': 'MODAL',
                'title': 'Informe regencial',
                'content': 'El <strong>Informe regencial</strong> es utilizado por el regente del laboratorio. Genera un resumen en formato <strong>XLS u ODS</strong> con la información del inventario bajo su responsabilidad. Campos requeridos: <em>elemento</em> (laboratorio u organización) y <em>período</em> de consulta.',
            },
            {
                'order': 2, 'step_key': 'rptdet-saludlaboral', 'step_type': 'MODAL',
                'title': 'Reporte de salud laboral',
                'content': 'Genera reportes asociados al personal del laboratorio. Se selecciona el <strong>usuario o registro</strong> deseado y el sistema descarga automáticamente el informe. Es útil para auditorías de salud ocupacional y seguimiento del personal expuesto a sustancias peligrosas.',
            },
            {
                'order': 3, 'step_key': 'rptdet-muebles', 'step_type': 'MODAL',
                'title': 'Reporte de muebles y objetos en límite',
                'content': 'El <strong>Reporte de muebles</strong> genera información sobre muebles y su contenido por sala. El <strong>Reporte de objetos en límite</strong> muestra reactivos u objetos cercanos al límite mínimo o máximo configurado. Ambos requieren: laboratorio y sala como filtros principales.',
            },
            {
                'order': 4, 'step_key': 'rptdet-movimientos', 'step_type': 'MODAL',
                'title': 'Reporte de movimientos y precursores',
                'content': 'El <strong>Reporte de movimientos de objetos</strong> consulta todas las entradas, salidas y transferencias de reactivos en un período. El <strong>Reporte de precursores</strong> y <strong>Objetos reactivos precursores</strong> generan el listado de sustancias con control regulatorio especial. Campos: laboratorio, período e indicador de precursor.',
            },
            {
                'order': 5, 'step_key': 'rptdet-desechos', 'step_type': 'MODAL',
                'title': 'Reporte de desechos y reactivos',
                'content': 'El <strong>Reporte de desechos</strong> descarga información sobre sustancias u objetos desechados en un período. El <strong>Reporte de reactivos</strong> genera el inventario general de reactivos del laboratorio. El <strong>Reporte general por laboratorio</strong> consolida todo: inventario, movimientos, usuarios, reactivos, materiales, equipos y estado general.',
            },
            {
                'order': 6, 'step_key': 'rptdet-sga', 'step_type': 'MODAL',
                'title': 'Reportes SGA y compatibilidad',
                'content': 'El <strong>Reporte de compatibilidad SGA</strong> y el <strong>Informe de laboratorio por compatibilidad</strong> generan información sobre la compatibilidad de almacenamiento según el Sistema Globalmente Armonizado. El <strong>Reporte de zonas de riesgo</strong> requiere laboratorio, zona de riesgo y edificio como filtros. El <strong>Informe de donaciones</strong> lista los objetos o sustancias ingresados por donación.',
            },
        ],
    },

    # Gap 5: Tipos de Zona de Riesgo
    {
        'title': 'Tipos de Zona de Riesgo',
        'slug': 'tipos-zona-riesgo',
        'description': 'Clasificación y gestión de los tipos de zona de riesgo del laboratorio',
        'url_name': 'riskmanagement:riskzone_list',
        'chapter': 'GENERAL',
        'auto_start': False,
        'order': 44,
        'roles': [11, 1, 6, 10, 7],
        'steps': [
            {
                'order': 1, 'step_key': 'zonetype-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son los Tipos de Zona?',
                'content': 'El <strong>Tipo de Zona</strong> clasifica cada zona de riesgo según la naturaleza del peligro que representa. Esta clasificación determina los protocolos de seguridad, el equipo de protección personal requerido y las restricciones de acceso aplicables a cada área del laboratorio.',
            },
            {
                'order': 2, 'step_key': 'zonetype-tipos', 'step_type': 'MODAL',
                'title': 'Tipos de zona disponibles',
                'content': 'Los tipos de zona de riesgo disponibles son: <strong>Química</strong> (manejo de sustancias químicas peligrosas), <strong>Biológica</strong> (agentes biológicos o patógenos), <strong>Inflamable</strong> (materiales o vapores inflamables), <strong>Almacenamiento</strong> (depósito de sustancias o materiales), <strong>Residuos</strong> (área de acopio de desechos) y <strong>Alto Tránsito</strong> (zonas con alta circulación de personas).',
            },
            {
                'order': 3, 'step_key': 'zonetype-asignar', 'step_type': 'MODAL',
                'title': 'Asignar tipo al crear una zona',
                'content': 'Al registrar una nueva zona de riesgo, seleccione el <strong>tipo de zona</strong> que mejor describe el área. Esta clasificación aparece en los listados, reportes y mapas de riesgo, permitiendo identificar rápidamente la naturaleza del peligro de cada zona y aplicar las medidas de seguridad correspondientes.',
            },
            {
                'order': 4, 'step_key': 'zonetype-impacto', 'step_type': 'MODAL',
                'title': 'Impacto en reportes y gestión',
                'content': 'El tipo de zona afecta directamente los <strong>reportes de zonas de riesgo</strong> y la <strong>compatibilidad SGA</strong> del área. Las zonas químicas e inflamables están sujetas a evaluación del Decreto 44741 de Costa Rica. Mantener el tipo correcto garantiza que los cálculos de riesgo y los reportes regulatorios sean precisos.',
            },
        ],
    },

    # Gap 6: MSDS Gestión Detallada
    {
        'title': 'Gestión Detallada de MSDS',
        'slug': 'msds-gestion-detallada',
        'description': 'Búsqueda con filtros, visualización completa, descarga y carga de nuevas hojas de seguridad',
        'url_name': 'msds:index_msds',
        'chapter': 'SUSTANCIAS',
        'auto_start': False,
        'order': 45,
        'roles': [1, 6, 10, 5, 13, 7],
        'steps': [
            {
                'order': 1, 'step_key': 'msdsdet-busqueda', 'step_type': 'MODAL',
                'title': 'Búsqueda con filtros avanzados',
                'content': 'La vista principal de MSDS permite filtrar hojas de seguridad por: <strong>nombre de la sustancia</strong>, <strong>código CAS</strong>, <strong>fuente</strong> (proveedor o institución de origen), <strong>fecha de revisión</strong> y <strong>última actualización</strong>. Ingrese el criterio, presione <strong>Buscar</strong> y seleccione el registro deseado.',
            },
            {
                'order': 2, 'step_key': 'msdsdet-visualizar', 'step_type': 'MODAL',
                'title': 'Visualización completa de una MSDS',
                'content': 'Al seleccionar una hoja registrada, el sistema muestra su información general: <strong>nombre de la sustancia</strong>, <strong>código CAS</strong>, <strong>proveedor o fuente</strong>, <strong>fecha de emisión</strong>, <strong>fecha de revisión</strong>, <strong>versión</strong> y el <strong>archivo PDF</strong> adjunto disponible para descarga inmediata.',
            },
            {
                'order': 3, 'step_key': 'msdsdet-descarga', 'step_type': 'MODAL',
                'title': 'Descargar una hoja de seguridad',
                'content': 'Para descargar una MSDS: seleccione el registro en la lista, presione el botón <strong>Descargar</strong> y el archivo se descargará automáticamente en formato <strong>PDF</strong>. Las hojas de seguridad son documentos legalmente requeridos que deben estar disponibles físicamente en el laboratorio para cualquier sustancia peligrosa.',
            },
            {
                'order': 4, 'step_key': 'msdsdet-carga', 'step_type': 'MODAL',
                'title': 'Cargar una nueva hoja de seguridad',
                'content': 'Para registrar una nueva MSDS: seleccione <strong>Crear nuevo archivo SDS</strong>, presione <strong>Examinar</strong> para seleccionar el archivo PDF desde su equipo, complete los datos de la sustancia (nombre, CAS, fuente, fechas) y presione <strong>Guardar</strong>. La hoja quedará disponible para consulta de todos los usuarios con acceso al módulo.',
            },
            {
                'order': 5, 'step_key': 'msdsdet-vencimiento', 'step_type': 'MODAL',
                'title': 'Control de versiones y vigencia',
                'content': 'Registre la <strong>fecha de revisión</strong> de cada MSDS para mantener el control de vigencia. Las hojas de seguridad deben actualizarse cuando el fabricante lanza una nueva versión o cuando cambian las propiedades o clasificación de la sustancia. El campo <strong>última actualización</strong> permite identificar rápidamente las hojas que requieren revisión.',
            },
        ],
    },

    # Gap 7: SGA Etiquetas y Aplicación Física
    {
        'title': 'Etiquetas SGA y Aplicación Física',
        'slug': 'sga-etiquetas-aplicacion',
        'description': 'Crear etiquetas SGA paso a paso y aplicarlas correctamente en el laboratorio',
        'url_name': 'sga:step_one',
        'chapter': 'SUSTANCIAS',
        'auto_start': False,
        'order': 46,
        'roles': [16, 1, 6, 10, 5, 14, 13],
        'steps': [
            {
                'order': 1, 'step_key': 'sgaetq-crear', 'step_type': 'MODAL',
                'title': 'Crear una nueva etiqueta SGA',
                'content': 'Para crear una etiqueta: seleccione <strong>Crear nueva etiqueta</strong>, ingrese el <strong>nombre</strong> de la sustancia o producto químico (ej: Ácido clorhídrico, Acetona) y seleccione la <strong>plantilla</strong> gráfica correspondiente. La plantilla define el formato visual de la etiqueta con su estructura de pictogramas y frases.',
            },
            {
                'order': 2, 'step_key': 'sgaetq-plantilla', 'step_type': 'MODAL',
                'title': 'Seleccionar la plantilla correcta',
                'content': 'La <strong>plantilla</strong> determina qué elementos aparecerán en la etiqueta: <strong>pictogramas SGA</strong> (llama, calavera, signo de exclamación, etc.), <strong>palabra de advertencia</strong> (Peligro o Atención), <strong>frases H</strong> de peligro y <strong>frases P</strong> de prudencia. Seleccione la plantilla que corresponda a la clasificación de la sustancia.',
            },
            {
                'order': 3, 'step_key': 'sgaetq-visualizar', 'step_type': 'MODAL',
                'title': 'Visualizar etiquetas registradas',
                'content': 'La lista principal muestra todas las etiquetas SGA registradas con su nombre, plantilla asignada, fecha de creación, estado y tipo de riesgo. Puede consultar el detalle de cada etiqueta para verificar que todos los elementos estén correctamente configurados antes de imprimirla y aplicarla.',
            },
            {
                'order': 4, 'step_key': 'sgaetq-uso', 'step_type': 'MODAL',
                'title': 'Usos de las etiquetas SGA',
                'content': 'Las etiquetas generadas se utilizan para: <strong>identificación de reactivos</strong> en el inventario, <strong>etiquetado de contenedores</strong> de almacenamiento, <strong>señalización de zonas de riesgo</strong>, <strong>reportes de compatibilidad</strong> y cumplimiento del Decreto 44741. Una sustancia peligrosa sin etiqueta SGA es un incumplimiento regulatorio.',
            },
            {
                'order': 5, 'step_key': 'sgaetq-aplicacion', 'step_type': 'MODAL',
                'title': 'Aplicación física en el laboratorio',
                'content': 'Las etiquetas SGA deben colocarse físicamente en: <strong>frascos y envases</strong> de reactivos, <strong>contenedores</strong> de almacenamiento, <strong>estantes</strong> donde se ubican sustancias peligrosas, <strong>zonas de almacenamiento</strong> de riesgo y <strong>recipientes de residuos</strong>. Imprima la etiqueta desde el sistema y péguela de forma visible y duradera.',
            },
        ],
    },

    # Gap 8: Clasificación y Consulta de Desechos
    {
        'title': 'Clasificación y Consulta de Desechos',
        'slug': 'desechos-clasificacion-consulta',
        'description': 'Tipos de clasificación de desechos, consulta por laboratorio y ubicación física del residuo',
        'url_name': 'laboratory:disposal_substance',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 47,
        'roles': [13, 14, 1, 6, 10, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'desclass-tipos', 'step_type': 'MODAL',
                'title': 'Clasificación del desecho',
                'content': 'Cada desecho debe clasificarse según su naturaleza. Los tipos disponibles son: <strong>Reactivos vencidos</strong> (sustancias fuera de fecha de caducidad), <strong>Materiales contaminados</strong> (utensilios o equipos con residuos), <strong>Residuos químicos</strong> (sobrantes de reacciones o procesos), <strong>Sustancias precursoras</strong> (con control regulatorio especial) y <strong>Residuos peligrosos</strong> (con riesgo para la salud o el ambiente).',
            },
            {
                'order': 2, 'step_key': 'desclass-lista', 'step_type': 'MODAL',
                'title': 'Vista principal de desechos',
                'content': 'La pantalla principal muestra la <strong>lista de sustancias desechadas</strong> con: laboratorio, sustancia o reactivo, cantidad restante, ubicación (sala/estante/contenedor), estado y fecha de registro. Desde aquí puede consultar el detalle de cada desecho y filtrar por laboratorio para ver solo los residuos de un área específica.',
            },
            {
                'order': 3, 'step_key': 'desclass-ubicacion', 'step_type': 'MODAL',
                'title': 'Ubicación física del desecho',
                'content': 'El sistema registra la <strong>ubicación exacta</strong> de cada residuo: laboratorio → sala → mueble → estante → contenedor. Esta información es clave para los procesos de <strong>recolección</strong> y <strong>disposición final</strong>. La empresa gestora de residuos puede usar esta información para identificar y retirar los materiales de forma eficiente.',
            },
            {
                'order': 4, 'step_key': 'desclass-consulta', 'step_type': 'MODAL',
                'title': 'Consulta por laboratorio',
                'content': 'La información de desechos se organiza <strong>por laboratorio</strong>, lo que permite: <strong>control por unidad</strong> académica o de investigación, <strong>auditoría interna</strong> de residuos generados, <strong>gestión ambiental por sede</strong> y <strong>control de residuos acumulados</strong>. Use los filtros para ver solo el laboratorio de interés.',
            },
            {
                'order': 5, 'step_key': 'desclass-integracion', 'step_type': 'MODAL',
                'title': 'Integración con otros módulos',
                'content': 'El módulo de Desechos se integra directamente con: <strong>Reactivos</strong> (origen del desecho), <strong>SGA</strong> (clasificación de peligrosidad), <strong>MSDS</strong> (procedimientos de disposición segura), <strong>Zonas de Riesgo</strong> (área donde se genera el residuo), <strong>Reportes</strong> (informe de desechos) y <strong>Movimientos de Objetos</strong> (trazabilidad del traslado al área de descarte).',
            },
        ],
    },

    # Gap 9: Operaciones Avanzadas de Inventario
    {
        'title': 'Operaciones Avanzadas de Inventario',
        'slug': 'operaciones-avanzadas-inventario',
        'description': 'Bitácora del reactivo, administración de contenedor, mover estante, descarga de información y sustracción',
        'url_name': 'laboratory:rooms_list',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 48,
        'roles': [1, 6, 10, 5, 15, 13, 14, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'opinv-bitacora', 'step_type': 'MODAL',
                'title': 'Bitácora del reactivo',
                'content': 'Cada reactivo en estante tiene una <strong>bitácora completa</strong> que registra el historial de todos sus movimientos y cambios. La bitácora incluye: <strong>acción realizada</strong> (ingreso, consumo, transferencia, etc.), <strong>descripción</strong>, <strong>fecha</strong> del evento, <strong>usuario responsable</strong> y <strong>estado actualizado</strong>. Es la fuente de trazabilidad completa del reactivo.',
            },
            {
                'order': 2, 'step_key': 'opinv-contenedor', 'step_type': 'MODAL',
                'title': 'Administración de contenedor',
                'content': 'La opción <strong>Administrar contenedor</strong> permite gestionar el envase físico donde está el reactivo. Las acciones disponibles son: <strong>usar el contenedor actual</strong> (ya registrado), <strong>crear un nuevo contenedor</strong> (registrar un envase nuevo) o <strong>asociar un contenedor existente</strong> al reactivo. Esto permite rastrear en qué frasco o recipiente físico está almacenada la sustancia.',
            },
            {
                'order': 3, 'step_key': 'opinv-mover', 'step_type': 'MODAL',
                'title': 'Mover a otro estante',
                'content': 'La opción <strong>Mover</strong> permite reubicar un reactivo dentro del mismo laboratorio sin crear una transferencia. Seleccione la nueva <strong>sala</strong>, el <strong>mueble</strong>, el <strong>estante</strong> y el <strong>contenedor</strong> destino. El movimiento queda registrado en la bitácora con el usuario y la fecha para mantener la trazabilidad de la ubicación física.',
            },
            {
                'order': 4, 'step_key': 'opinv-descarga', 'step_type': 'MODAL',
                'title': 'Descarga de información del reactivo',
                'content': 'La opción <strong>Descargar</strong> genera un reporte detallado del reactivo con: nombre, cantidad, <strong>estado físico</strong>, <strong>fecha de caducidad</strong>, contenedor, <strong>fórmula molecular</strong>, <strong>código CAS</strong>, biocumulable, <strong>tipo de almacenamiento</strong>, si es precursor y descripción general. Útil para inventarios físicos y auditorías.',
            },
            {
                'order': 5, 'step_key': 'opinv-sustraer', 'step_type': 'MODAL',
                'title': 'Sustracción de reactivos',
                'content': 'La opción <strong>Sustraer</strong> descuenta una cantidad del stock actual del reactivo. Campos requeridos: <strong>cantidad</strong> a descontar, <strong>descripción</strong> del motivo de la sustracción (uso, derrame, vencimiento, etc.) y <strong>unidad de medida</strong>. El stock se actualiza automáticamente y el movimiento queda registrado en la bitácora con el usuario responsable.',
            },
        ],
    },

    # Gap 11: Tutoriales y Documentación del Sistema
    {
        'title': 'Tutoriales y Documentación del Sistema',
        'slug': 'tutoriales-documentacion-sistema',
        'description': 'Módulo de consulta de tutoriales, manuales, reglamentos y documentación institucional',
        'url_name': 'laboratory:labindex',
        'chapter': 'GENERAL',
        'auto_start': False,
        'order': 49,
        'roles': [11, 1, 6, 10, 4, 5, 13, 14, 15, 7, 8, 16],
        'steps': [
            {
                'order': 1, 'step_key': 'tutdoc-concepto', 'step_type': 'MODAL',
                'title': 'Módulo de Tutoriales y Documentación',
                'content': 'El módulo <strong>Tutoriales y Documentación</strong> centraliza los recursos de apoyo del sistema. Desde aquí puede acceder a <strong>tutoriales de uso</strong> por módulo (guías paso a paso), <strong>guías rápidas</strong> de consulta, <strong>documentación formal</strong> cargada por la organización, <strong>reglamentos</strong> institucionales y <strong>manuales internos</strong>.',
            },
            {
                'order': 2, 'step_key': 'tutdoc-tutoriales', 'step_type': 'MODAL',
                'title': 'Sección de Tutoriales',
                'content': 'La opción <strong>Tutoriales</strong> muestra guías interactivas sobre el uso de los diferentes módulos del sistema. Cada tutorial explica <strong>dónde se encuentra el módulo</strong>, <strong>qué funciones posee</strong> y <strong>qué acciones se pueden realizar</strong>. Se recomienda consultar esta sección cuando necesite aprender a usar una función nueva o validar el flujo de un proceso.',
            },
            {
                'order': 3, 'step_key': 'tutdoc-documentacion', 'step_type': 'MODAL',
                'title': 'Sección de Documentación',
                'content': 'La opción <strong>Documentación</strong> permite consultar toda la información formal cargada en el sistema. Esta sección puede incluir: <strong>manuales de usuario</strong>, <strong>procedimientos internos</strong>, <strong>instructivos</strong>, <strong>normativas institucionales</strong> y <strong>documentos de respaldo</strong>. Los documentos pueden visualizarse y descargarse según los permisos asignados.',
            },
            {
                'order': 4, 'step_key': 'tutdoc-reglamentos', 'step_type': 'MODAL',
                'title': 'Reglamentos institucionales',
                'content': 'Dentro de Documentación puede consultar los <strong>reglamentos institucionales</strong> relacionados con: <strong>seguridad en el laboratorio</strong>, <strong>uso de instalaciones</strong>, <strong>manejo de sustancias</strong>, <strong>gestión de residuos</strong>, <strong>acceso de usuarios</strong> y <strong>normas operativas</strong>. Mantener estos reglamentos actualizados en el sistema garantiza que todo el personal los tenga disponibles.',
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
        ('presentation', '0010_fix_salas_muebles_url'),
        ('auth_and_perms', '0026_remove_unused_roles'),
    ]

    operations = [
        migrations.RunPython(load_tutorials, remove_tutorials),
    ]
