from django.db import migrations


TUTORIALS = [
    {
        'title': 'Mis Procedimientos',
        'slug': 'mis-procedimientos',
        'description': 'Crear y ejecutar instancias de procedimientos de laboratorio',
        'url_name': 'academic:get_my_procedures',
        'chapter': 'PROCEDIMIENTOS',
        'auto_start': False,
        'order': 17,
        'roles': [1, 6, 10, 5, 15, 14, 13],
        'steps': [
            {
                'order': 1, 'step_key': 'misproc-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son Mis Procedimientos?',
                'content': '<strong>Mis Procedimientos</strong> es el módulo donde se gestionan las instancias de ejecución de procedimientos de laboratorio. A diferencia de los procedimientos (plantillas reutilizables), aquí cada registro representa una ejecución concreta realizada por un usuario en un laboratorio específico.',
            },
            {
                'order': 2, 'step_key': 'misproc-crear', 'step_type': 'MODAL',
                'title': 'Crear una instancia',
                'content': 'Haga clic en <strong>Crear procedimiento</strong> para iniciar una nueva instancia. Seleccione el procedimiento base (plantilla) que desea ejecutar y asígnele un nombre. La instancia quedará en estado <strong>Borrador</strong> hasta que comience su ejecución.',
            },
            {
                'order': 3, 'step_key': 'misproc-estados', 'step_type': 'MODAL',
                'title': 'Estados de ejecución',
                'content': 'Cada instancia atraviesa los siguientes estados: <strong>Borrador</strong> (en preparación), <strong>En Revisión</strong> (pendiente de aprobación) y <strong>Finalizado</strong> (completado). En cada paso puede registrar observaciones y completar formularios asociados.',
            },
            {
                'order': 4, 'step_key': 'misproc-reservacion', 'step_type': 'MODAL',
                'title': 'Generar reservación',
                'content': 'Una vez creada la instancia, puede generar una <strong>reservación automática</strong> de los materiales, reactivos y equipos requeridos por el procedimiento. El sistema verifica que el laboratorio tenga stock suficiente antes de confirmar la reservación.',
            },
            {
                'order': 5, 'step_key': 'misproc-lista', 'step_type': 'MODAL',
                'title': 'Lista de procedimientos',
                'content': 'La tabla muestra todas las instancias del laboratorio: nombre, procedimiento base, estado y acciones disponibles (completar, generar reservación, eliminar). Use los filtros y la búsqueda para localizar instancias rápidamente.',
            },
        ],
    },
    {
        'title': 'Procesos del Laboratorio',
        'slug': 'procesos-laboratorio',
        'description': 'Documentar y gestionar procesos internos del laboratorio',
        'url_name': 'laboratory:laboratory_process_list',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 18,
        'roles': [1, 6, 10, 5, 15, 14, 13],
        'steps': [
            {
                'order': 1, 'step_key': 'labproc-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son los Procesos del Laboratorio?',
                'content': 'Los <strong>Procesos del Laboratorio</strong> permiten documentar y centralizar los protocolos, normativas e instrucciones operativas internas de su laboratorio. Cada proceso tiene una descripción detallada en formato de texto que queda registrada y disponible para el personal.',
            },
            {
                'order': 2, 'step_key': 'labproc-crear', 'step_type': 'MODAL',
                'title': 'Crear un proceso',
                'content': 'Haga clic en <strong>Crear proceso</strong> para registrar un nuevo proceso. Redacte la descripción usando el editor de texto, donde puede incluir formato, listas y tablas para estructurar la información de forma clara.',
            },
            {
                'order': 3, 'step_key': 'labproc-editar', 'step_type': 'MODAL',
                'title': 'Editar y eliminar procesos',
                'content': 'Desde la lista puede <strong>editar</strong> cualquier proceso existente para actualizar su descripción, o <strong>eliminarlo</strong> si ya no aplica. Mantenga los procesos actualizados para garantizar que el personal trabaje con información vigente.',
            },
            {
                'order': 4, 'step_key': 'labproc-lista', 'step_type': 'MODAL',
                'title': 'Lista de procesos',
                'content': 'La tabla muestra todos los procesos documentados del laboratorio. Cada proceso incluye su descripción y las acciones disponibles. Use la búsqueda para localizar procesos específicos rápidamente.',
            },
        ],
    },
    {
        'title': 'Crear Paso de Procedimiento',
        'slug': 'crear-paso-procedimiento',
        'description': 'Crear pasos, formularios dinámicos, objetos y observaciones en un procedimiento',
        'url_name': 'academic:procedure_step',
        'chapter': 'PROCEDIMIENTOS',
        'auto_start': False,
        'order': 19,
        'roles': [11, 1, 6, 10],
        'steps': [
            {
                'order': 1, 'step_key': 'paso-concepto', 'step_type': 'MODAL',
                'title': '¿Qué es un paso de procedimiento?',
                'content': 'Cada procedimiento se compone de <strong>pasos secuenciales</strong>. Un paso define una acción concreta que el usuario debe realizar: incluye un título, una descripción detallada, un formulario de captura de datos, los objetos (reactivos/materiales/equipos) necesarios y observaciones de seguridad o contexto.',
            },
            {
                'order': 2, 'step_key': 'paso-titulo-desc', 'step_type': 'MODAL',
                'title': 'Título y descripción del paso',
                'content': 'Complete el <strong>título</strong> del paso con una acción clara (ej: "Preparar solución buffer") y en la <strong>descripción</strong> detalle las instrucciones de ejecución. Estos campos son la base del paso y son visibles para el usuario al ejecutar el procedimiento.',
            },
            {
                'order': 3, 'step_key': 'paso-formulario', 'step_type': 'MODAL',
                'title': 'Constructor de formulario dinámico',
                'content': 'La sección <strong>Form</strong> permite diseñar un formulario personalizado que el usuario completará al ejecutar este paso. Arrastre y suelte campos desde la paleta: texto, número, selección, fecha, hora o área de texto. Este formulario queda vinculado al paso y captura datos durante la ejecución.',
            },
            {
                'order': 4, 'step_key': 'paso-objetos', 'step_type': 'MODAL',
                'title': 'Agregar objetos requeridos',
                'content': 'En la sección <strong>Lista de Objetos</strong> registre los reactivos, materiales o equipos que se necesitan para este paso. Haga clic en <strong>Crear Objeto</strong>, seleccione el objeto del inventario, indique la cantidad y la unidad de medida. Al ejecutar el procedimiento el sistema verificará el stock disponible.',
            },
            {
                'order': 5, 'step_key': 'paso-observaciones', 'step_type': 'MODAL',
                'title': 'Agregar observaciones',
                'content': 'En la sección <strong>Observaciones</strong> documente advertencias de seguridad, notas técnicas o cualquier información complementaria del paso. Haga clic en <strong>Crear Observación</strong> e ingrese la descripción. Puede agregar tantas observaciones como sean necesarias.',
            },
            {
                'order': 6, 'step_key': 'paso-guardar', 'step_type': 'MODAL',
                'title': 'Guardar el paso',
                'content': 'Al hacer clic en <strong>Guardar</strong>, el sistema registra el paso junto con el formulario dinámico diseñado. Puede agregar múltiples pasos al mismo procedimiento. El orden en que se crean define la secuencia de ejecución para el usuario.',
            },
        ],
    },
    {
        'title': 'Plantillas de Informes',
        'slug': 'plantillas-informes',
        'description': 'Crear y gestionar plantillas de informes personalizados',
        'url_name': 'derb:form_list',
        'chapter': 'GENERAL',
        'auto_start': False,
        'order': 20,
        'roles': [11, 1, 6, 10],
        'steps': [
            {
                'order': 1, 'step_key': 'inform-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son las Plantillas de Informes?',
                'content': 'Las <strong>Plantillas de Informes</strong> permiten diseñar formularios personalizados que se usan para capturar datos estructurados en la organización. Cada plantilla define los campos que el usuario debe completar al generar un informe, y puede vincularse a pasos de procedimientos.',
            },
            {
                'order': 2, 'step_key': 'inform-estados', 'step_type': 'MODAL',
                'title': 'Estados de una plantilla',
                'content': 'Cada plantilla tiene un estado que indica su fase: <strong>Creando formulario</strong> (en diseño, solo administradores pueden editarla), <strong>Llenando formulario</strong> (disponible para que los usuarios completen datos) y <strong>Resultados</strong> (formulario cerrado, datos consolidados para consulta).',
            },
            {
                'order': 3, 'step_key': 'inform-crear', 'step_type': 'MODAL',
                'title': 'Crear una plantilla',
                'content': 'Haga clic en <strong>Crear Plantilla de Informe</strong> e ingrese el nombre. La plantilla se creará en estado <strong>Creando formulario</strong> y será redirigido al editor para agregar los campos necesarios.',
            },
            {
                'order': 4, 'step_key': 'inform-editar', 'step_type': 'MODAL',
                'title': 'Editar la plantilla',
                'content': 'Use el botón de <strong>edición</strong> para abrir el editor de la plantilla. Desde el editor puede agregar, reordenar y configurar los campos del formulario usando el constructor visual. Al guardar, los cambios quedan disponibles de inmediato.',
            },
            {
                'order': 5, 'step_key': 'inform-preview', 'step_type': 'MODAL',
                'title': 'Previsualizar la plantilla',
                'content': 'El botón de <strong>previsualización</strong> muestra cómo verá el usuario final el formulario antes de publicarlo. Úselo para verificar que los campos, etiquetas y estructura sean correctos antes de cambiar el estado a <strong>Llenando formulario</strong>.',
            },
            {
                'order': 6, 'step_key': 'inform-eliminar', 'step_type': 'MODAL',
                'title': 'Eliminar una plantilla',
                'content': 'El botón de <strong>eliminación</strong> borra la plantilla de forma permanente. Esta acción no puede deshacerse. Asegúrese de que la plantilla no tenga respuestas registradas antes de eliminarla.',
            },
        ],
    },
    {
        'title': 'Edificios',
        'slug': 'edificios',
        'description': 'Registrar y consultar edificios de la organización para gestión de riesgo',
        'url_name': 'riskmanagement:buildings_list',
        'chapter': 'GENERAL',
        'auto_start': False,
        'order': 21,
        'roles': [11, 1, 6, 10],
        'steps': [
            {
                'order': 1, 'step_key': 'edif-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son los Edificios?',
                'content': 'El módulo de <strong>Edificios</strong> permite registrar las instalaciones físicas de la organización que albergan laboratorios. Cada edificio centraliza información operativa y de riesgo: laboratorios que contiene, edificios cercanos, responsable, regentes químicos y geolocalización.',
            },
            {
                'order': 2, 'step_key': 'edif-crear', 'step_type': 'MODAL',
                'title': 'Registrar un edificio',
                'content': 'Haga clic en <strong>Crear Edificio</strong> e ingrese los datos del edificio: nombre, teléfono de contacto, responsable y regentes asociados. Puede vincular los <strong>laboratorios</strong> que operan dentro del edificio y marcar si tiene edificios cercanos que puedan verse afectados en caso de incidente.',
            },
            {
                'order': 3, 'step_key': 'edif-geolocalizacion', 'step_type': 'MODAL',
                'title': 'Geolocalización',
                'content': 'Cada edificio tiene una <strong>ubicación geográfica</strong> configurada en el mapa. Esto es fundamental para la gestión de riesgo, ya que permite identificar la proximidad a recursos hídricos, otras instalaciones y rutas de evacuación.',
            },
            {
                'order': 4, 'step_key': 'edif-lista', 'step_type': 'MODAL',
                'title': 'Lista de edificios',
                'content': 'La tabla muestra todos los edificios registrados en la organización con su nombre y laboratorios vinculados. Desde aquí puede consultar el detalle de cada edificio para revisar su información de riesgo asociada.',
            },
        ],
    },
    {
        'title': 'Estructuras',
        'slug': 'estructuras',
        'description': 'Registrar estructuras físicas dentro de los edificios de la organización',
        'url_name': 'riskmanagement:structures_list',
        'chapter': 'GENERAL',
        'auto_start': False,
        'order': 22,
        'roles': [11, 1, 6, 10],
        'steps': [
            {
                'order': 1, 'step_key': 'struct-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son las Estructuras?',
                'content': 'Las <strong>Estructuras</strong> representan las divisiones físicas internas de los edificios de la organización: alas, pisos, módulos, bodegas u otras subdivisiones relevantes para la gestión de riesgo. Cada estructura se vincula a uno o más edificios y cuenta con responsable, tipo, área y geolocalización.',
            },
            {
                'order': 2, 'step_key': 'struct-crear', 'step_type': 'MODAL',
                'title': 'Registrar una estructura',
                'content': 'Haga clic en <strong>Crear Estructura</strong> e ingrese el nombre, el <strong>tipo de estructura</strong> (según el catálogo), el <strong>área</strong> con su unidad de medida y el <strong>responsable</strong>. Vincule la estructura a los edificios correspondientes para mantener la trazabilidad física de la organización.',
            },
            {
                'order': 3, 'step_key': 'struct-geolocalizacion', 'step_type': 'MODAL',
                'title': 'Geolocalización',
                'content': 'Al igual que los edificios, cada estructura tiene una <strong>ubicación geográfica</strong> en el mapa. Esto permite identificar con precisión dónde se encuentra la estructura dentro del campus o instalaciones, lo cual es clave para la planificación de respuesta ante emergencias.',
            },
            {
                'order': 4, 'step_key': 'struct-lista', 'step_type': 'MODAL',
                'title': 'Lista de estructuras',
                'content': 'La tabla muestra todas las estructuras registradas en la organización con su nombre, tipo y edificios asociados. Desde aquí puede consultar el detalle de cada estructura para revisar su información de riesgo.',
            },
        ],
    },
    {
        'title': 'Regentes',
        'slug': 'regentes',
        'description': 'Registrar regentes químicos y vincularlos a laboratorios',
        'url_name': 'riskmanagement:regents',
        'chapter': 'GENERAL',
        'auto_start': False,
        'order': 23,
        'roles': [11, 1, 6, 10],
        'steps': [
            {
                'order': 1, 'step_key': 'regent-concepto', 'step_type': 'MODAL',
                'title': '¿Qué es un Regente?',
                'content': 'Un <strong>Regente</strong> es el profesional legalmente responsable del manejo de sustancias químicas en uno o más laboratorios. El sistema admite tres tipos: <strong>Regente Químico</strong>, <strong>Ingeniero Químico</strong> y <strong>Veterinario</strong>. Su registro es obligatorio para el cumplimiento regulatorio en Costa Rica.',
            },
            {
                'order': 2, 'step_key': 'regent-registrar', 'step_type': 'MODAL',
                'title': 'Registrar un regente',
                'content': 'Haga clic en <strong>Registrar Regente</strong>, seleccione el usuario de la organización que ejercerá como regente, elija el <strong>tipo de regente</strong> y asigne los <strong>laboratorios</strong> bajo su responsabilidad. Un mismo usuario puede ser regente de múltiples laboratorios.',
            },
            {
                'order': 3, 'step_key': 'regent-vinculo', 'step_type': 'MODAL',
                'title': 'Vínculo con edificios',
                'content': 'Los regentes registrados quedan disponibles para asociarse a los <strong>Edificios</strong> de la organización. Esto permite que en la ficha de cada edificio se identifique quién es el responsable técnico de las sustancias químicas que se manejan en sus laboratorios.',
            },
        ],
    },
    {
        'title': 'Palabras de Advertencia',
        'slug': 'palabras-advertencia',
        'description': 'Gestionar las palabras de advertencia SGA de la organización',
        'url_name': 'sga:warning_words',
        'chapter': 'SUSTANCIAS',
        'auto_start': False,
        'order': 24,
        'roles': [16],
        'steps': [
            {
                'order': 1, 'step_key': 'warn-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son las Palabras de Advertencia?',
                'content': 'Las <strong>Palabras de Advertencia</strong> son términos normalizados del Sistema Global Armonizado (SGA) que indican el nivel de gravedad de un peligro químico. Los dos valores estándar son <strong>Peligro</strong> (para los peligros más graves) y <strong>Atención</strong> (para los peligros menos severos). Aparecen obligatoriamente en las etiquetas de sustancias peligrosas.',
            },
            {
                'order': 2, 'step_key': 'warn-peso', 'step_type': 'MODAL',
                'title': 'Peso de la palabra de advertencia',
                'content': 'Cada palabra de advertencia tiene un <strong>peso numérico</strong> que determina su jerarquía cuando una sustancia presenta múltiples clasificaciones de peligro. El sistema utiliza este peso para seleccionar automáticamente la palabra de advertencia de mayor gravedad al generar una etiqueta SGA.',
            },
            {
                'order': 3, 'step_key': 'warn-agregar', 'step_type': 'MODAL',
                'title': 'Agregar una palabra de advertencia',
                'content': 'Haga clic en <strong>Agregar</strong> para registrar una nueva palabra de advertencia. Ingrese el nombre y asigne el peso correspondiente. Estas palabras quedan disponibles para su uso en la clasificación y etiquetado de sustancias químicas de la organización.',
            },
        ],
    },
    {
        'title': 'Indicaciones de Peligro',
        'slug': 'indicaciones-peligro',
        'description': 'Consultar y gestionar las indicaciones de peligro H del estándar SGA',
        'url_name': 'sga:danger_indications',
        'chapter': 'SUSTANCIAS',
        'auto_start': False,
        'order': 25,
        'roles': [16],
        'steps': [
            {
                'order': 1, 'step_key': 'danger-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son las Indicaciones de Peligro?',
                'content': 'Las <strong>Indicaciones de Peligro</strong> (códigos H) son frases normalizadas del SGA que describen la naturaleza y gravedad del peligro de una sustancia química. Ejemplos: <strong>H301</strong> - Tóxico en caso de ingestión, <strong>H314</strong> - Provoca quemaduras graves en la piel. Son obligatorias en las etiquetas y fichas de seguridad.',
            },
            {
                'order': 2, 'step_key': 'danger-estructura', 'step_type': 'MODAL',
                'title': 'Estructura de una indicación',
                'content': 'Cada indicación de peligro está compuesta por: un <strong>código H</strong> (identificador único), una <strong>descripción</strong> del peligro, la <strong>palabra de advertencia</strong> asociada (Peligro o Atención), la <strong>clase y categoría de peligro</strong> y los <strong>consejos de prudencia P</strong> recomendados.',
            },
            {
                'order': 3, 'step_key': 'danger-uso', 'step_type': 'MODAL',
                'title': 'Uso en la clasificación SGA',
                'content': 'Al clasificar una sustancia en el módulo SGA, se asignan las indicaciones H que correspondan a su perfil de peligrosidad. El sistema utiliza estas indicaciones para generar automáticamente la <strong>etiqueta SGA</strong> con los pictogramas, palabra de advertencia y consejos de prudencia correctos.',
            },
            {
                'order': 4, 'step_key': 'danger-agregar', 'step_type': 'MODAL',
                'title': 'Agregar una indicación de peligro',
                'content': 'Si necesita registrar una indicación no incluida por defecto, haga clic en <strong>Agregar</strong>. Ingrese el código H, la descripción, la palabra de advertencia correspondiente, las clases y categorías de peligro y los consejos de prudencia asociados.',
            },
        ],
    },
    {
        'title': 'Consejos de Prudencia',
        'slug': 'consejos-prudencia',
        'description': 'Consultar y gestionar los consejos de prudencia P del estándar SGA',
        'url_name': 'sga:prudence_advices',
        'chapter': 'SUSTANCIAS',
        'auto_start': False,
        'order': 26,
        'roles': [16],
        'steps': [
            {
                'order': 1, 'step_key': 'prud-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son los Consejos de Prudencia?',
                'content': 'Los <strong>Consejos de Prudencia</strong> (códigos P) son frases normalizadas del SGA que describen las medidas recomendadas para minimizar o prevenir los efectos adversos de una sustancia peligrosa. Ejemplos: <strong>P260</strong> - No respirar el polvo/humo/gas, <strong>P280</strong> - Usar equipo de protección individual. Son obligatorios en las etiquetas SGA.',
            },
            {
                'order': 2, 'step_key': 'prud-estructura', 'step_type': 'MODAL',
                'title': 'Estructura de un consejo de prudencia',
                'content': 'Cada consejo de prudencia contiene un <strong>código P</strong> (identificador único), un <strong>nombre</strong> con la instrucción preventiva y un <strong>texto de ayuda</strong> opcional con información adicional sobre su aplicación. Los consejos se asocian a las indicaciones de peligro H para conformar la clasificación SGA completa.',
            },
            {
                'order': 3, 'step_key': 'prud-agregar', 'step_type': 'MODAL',
                'title': 'Agregar un consejo de prudencia',
                'content': 'Si necesita registrar un consejo no incluido por defecto, haga clic en <strong>Agregar</strong>. Ingrese el código P, el nombre con la instrucción preventiva y, opcionalmente, el texto de ayuda. Una vez registrado queda disponible para vincularse a indicaciones de peligro y usarse en la generación de etiquetas SGA.',
            },
        ],
    },
    {
        'title': 'Sustancias Peligrosas',
        'slug': 'sustancias-peligrosas',
        'description': 'Registrar sustancias peligrosas con códigos H y criterios de identificación',
        'url_name': 'sga:danger_substance',
        'chapter': 'SUSTANCIAS',
        'auto_start': False,
        'order': 27,
        'roles': [16],
        'steps': [
            {
                'order': 1, 'step_key': 'dansub-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son las Sustancias Peligrosas?',
                'content': 'El módulo de <strong>Sustancias Peligrosas</strong> mantiene un catálogo de sustancias con perfil de peligrosidad definido. Cada registro vincula la sustancia a sus <strong>códigos H</strong> correspondientes, lo que permite que el sistema identifique automáticamente el nivel de peligro al clasificar productos químicos del inventario.',
            },
            {
                'order': 2, 'step_key': 'dansub-identificacion', 'step_type': 'MODAL',
                'title': 'Criterios de identificación',
                'content': 'Una sustancia peligrosa puede identificarse por tres criterios: <strong>Código CAS</strong> (número único internacional), <strong>Tipo de coincidencia</strong> (clasificación por tipo de sustancia) o <strong>Nombre patrón</strong> (coincidencia por nombre). Esto permite una identificación flexible según la información disponible.',
            },
            {
                'order': 3, 'step_key': 'dansub-umbral', 'step_type': 'MODAL',
                'title': 'Umbral y condición especial',
                'content': 'El campo <strong>Umbral</strong> define la cantidad mínima a partir de la cual la sustancia se considera peligrosa en el contexto regulatorio. El campo <strong>Condición especial</strong> permite registrar restricciones o requisitos particulares de manejo que apliquen a esa sustancia.',
            },
            {
                'order': 4, 'step_key': 'dansub-registrar', 'step_type': 'MODAL',
                'title': 'Registrar una sustancia peligrosa',
                'content': 'Haga clic en <strong>Registrar Sustancia Peligrosa</strong>, ingrese el nombre, el código CAS si lo conoce, seleccione el tipo de coincidencia, asigne los <strong>códigos H</strong> que la describen y defina el umbral. Una vez registrada, el sistema podrá reconocerla automáticamente al ingresarla al inventario.',
            },
        ],
    },
    {
        'title': 'Categorías de Sustancias Peligrosas',
        'slug': 'categorias-sustancias-peligrosas',
        'description': 'Definir categorías de peligro vinculadas a códigos H para clasificación SGA',
        'url_name': 'sga:danger_substance_category',
        'chapter': 'SUSTANCIAS',
        'auto_start': False,
        'order': 28,
        'roles': [16],
        'steps': [
            {
                'order': 1, 'step_key': 'dansubcat-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son las Categorías de Sustancias Peligrosas?',
                'content': 'Las <strong>Categorías de Sustancias Peligrosas</strong> permiten clasificar cada código H dentro de una categoría de peligro específica. Existen tres categorías: <strong>Salud</strong> (efectos sobre el organismo humano), <strong>Física</strong> (propiedades físico-químicas como inflamabilidad o explosividad) y <strong>Ambiental</strong> (toxicidad acuática u otros impactos al entorno).',
            },
            {
                'order': 2, 'step_key': 'dansubcat-estructura', 'step_type': 'MODAL',
                'title': 'Estructura de una categoría',
                'content': 'Cada registro vincula un <strong>código H</strong> con su <strong>categoría</strong> (salud, física o ambiental) y una <strong>sección</strong> que identifica el apartado regulatorio al que pertenece. Esto permite organizar los peligros de forma estructurada y facilita la generación automática de etiquetas y fichas SGA.',
            },
            {
                'order': 3, 'step_key': 'dansubcat-registrar', 'step_type': 'MODAL',
                'title': 'Registrar una categoría',
                'content': 'Haga clic en <strong>Registrar</strong>, seleccione el <strong>código H</strong> al que desea asignar la categoría, elija la <strong>categoría</strong> correspondiente e ingrese la <strong>sección</strong> regulatoria. Una vez registrada, esta clasificación queda disponible para el proceso de etiquetado SGA de sustancias en la organización.',
            },
        ],
    },
    {
        'title': 'Protocolos del Laboratorio',
        'slug': 'protocolos-laboratorio',
        'description': 'Subir, consultar y descargar protocolos PDF del laboratorio',
        'url_name': 'laboratory:protocol_list',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 29,
        'roles': [1, 6, 10, 5, 15, 13, 14, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'proto-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son los Protocolos?',
                'content': 'Los <strong>Protocolos</strong> son documentos PDF oficiales del laboratorio que describen procedimientos, normas de seguridad, instrucciones de operación u otros lineamientos técnicos. Centralizar estos documentos en Organilab garantiza que todo el personal tenga acceso a las versiones vigentes desde cualquier lugar.',
            },
            {
                'order': 2, 'step_key': 'proto-subir', 'step_type': 'MODAL',
                'title': 'Subir un protocolo',
                'content': 'Haga clic en <strong>Subir Protocolo</strong> y complete el nombre, una breve descripción y seleccione el archivo <strong>PDF</strong> correspondiente. Solo se permiten archivos en formato PDF. El sistema registra automáticamente el usuario que lo subió y la fecha de carga.',
            },
            {
                'order': 3, 'step_key': 'proto-descargar', 'step_type': 'MODAL',
                'title': 'Consultar y descargar',
                'content': 'La lista muestra todos los protocolos del laboratorio con su nombre y descripción. Use el botón de <strong>Descarga</strong> para obtener el archivo PDF. Puede buscar protocolos por nombre o descripción usando el campo de búsqueda de la tabla.',
            },
        ],
    },
    {
        'title': 'Registro de Usuarios por QR',
        'slug': 'registro-usuarios-qr',
        'description': 'Generar códigos QR para que nuevos usuarios se registren en el laboratorio',
        'url_name': 'laboratory:list_register_user_qr',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 30,
        'roles': [11, 1, 6, 10],
        'steps': [
            {
                'order': 1, 'step_key': 'qrreg-concepto', 'step_type': 'MODAL',
                'title': '¿Qué es el Registro por QR?',
                'content': 'El módulo de <strong>Registro de Usuarios por QR</strong> permite generar códigos QR que facilitan el ingreso de nuevos usuarios al laboratorio sin intervención manual del administrador. El usuario escanea el QR, completa su registro y queda asociado automáticamente al laboratorio con el rol preconfigurado en el código.',
            },
            {
                'order': 2, 'step_key': 'qrreg-crear', 'step_type': 'MODAL',
                'title': 'Crear un código QR de registro',
                'content': 'Haga clic en <strong>Crear Registro QR</strong>. Defina el <strong>rol</strong> que se asignará automáticamente al usuario que se registre con ese código, la <strong>organización</strong> a la que pertenecerá y si el usuario quedará <strong>activo</strong> de inmediato. Cada QR generado queda registrado con el usuario que lo creó y la fecha.',
            },
            {
                'order': 3, 'step_key': 'qrreg-descargar', 'step_type': 'MODAL',
                'title': 'Descargar el QR en PDF',
                'content': 'Use el botón de <strong>Descarga</strong> para obtener el código QR en formato PDF listo para imprimir o compartir. El PDF incluye instrucciones para el usuario y el QR con el enlace de registro. Puede generar múltiples QR con diferentes roles para distintos perfiles de usuarios.',
            },
            {
                'order': 4, 'step_key': 'qrreg-historial', 'step_type': 'MODAL',
                'title': 'Historial y auditoría',
                'content': 'Cada código QR tiene un <strong>historial</strong> donde puede consultar qué usuarios se registraron usando ese enlace, la fecha de registro y la organización. Esto permite un control completo de los accesos generados mediante este mecanismo.',
            },
        ],
    },
    {
        'title': 'Gestión de Reactivos',
        'slug': 'gestion-reactivos',
        'description': 'Crear, consultar y gestionar el catálogo de reactivos del laboratorio',
        'url_name': 'laboratory:sustance_list',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 31,
        'roles': [1, 6, 10, 5, 15, 13, 14, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'react-concepto', 'step_type': 'MODAL',
                'title': '¿Qué es la Gestión de Reactivos?',
                'content': 'Este módulo centraliza el <strong>catálogo de reactivos</strong> del laboratorio. Cada reactivo registrado incluye código, nombre, sinónimos, estado de peligrosidad, hoja de seguridad y límites de stock. Desde aquí se administran los reactivos que pueden luego ubicarse en los estantes del inventario.',
            },
            {
                'order': 2, 'step_key': 'react-crear', 'step_type': 'MODAL',
                'title': 'Crear un reactivo',
                'content': 'Haga clic en <strong>Crear Reactivo</strong> e ingrese el nombre, código, sinónimos y clasifíquelo según sus propiedades: si es <strong>puro</strong>, si tiene <strong>umbral de peligrosidad</strong> y si está marcado como <strong>peligroso</strong>. También puede adjuntar la <strong>hoja de seguridad</strong> (PDF) del reactivo.',
            },
            {
                'order': 3, 'step_key': 'react-limites', 'step_type': 'MODAL',
                'title': 'Configurar límites de stock',
                'content': 'Use el botón de <strong>Límites</strong> para establecer el <strong>límite máximo</strong> y el <strong>límite mínimo</strong> de cantidad permitida del reactivo en el laboratorio. El sistema generará alertas automáticas cuando el stock baje del mínimo o supere el máximo configurado.',
            },
            {
                'order': 4, 'step_key': 'react-hoja', 'step_type': 'MODAL',
                'title': 'Descargar hoja de seguridad',
                'content': 'Si el reactivo tiene una <strong>hoja de seguridad</strong> adjunta, use el botón de <strong>Descarga</strong> para obtenerla. Las hojas de seguridad son documentos obligatorios para sustancias peligrosas y deben estar disponibles para todo el personal del laboratorio.',
            },
        ],
    },
    {
        'title': 'Gestión de Materiales',
        'slug': 'gestion-materiales',
        'description': 'Crear y gestionar el catálogo de materiales del laboratorio',
        'url_name': 'laboratory:object_view',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 32,
        'roles': [1, 6, 10, 5, 15, 13, 14, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'mat-concepto', 'step_type': 'MODAL',
                'title': '¿Qué es la Gestión de Materiales?',
                'content': 'Este módulo administra el <strong>catálogo de materiales</strong> del laboratorio: consumibles, utensilios y cualquier objeto que no sea reactivo ni equipo. Los materiales registrados aquí pueden ubicarse en estantes del inventario y solicitarse mediante reservaciones.',
            },
            {
                'order': 2, 'step_key': 'mat-crear', 'step_type': 'MODAL',
                'title': 'Registrar un material',
                'content': 'Haga clic en <strong>Registrar Objeto</strong> e ingrese el código, nombre, sinónimos y descripción del material. Indique si el material es <strong>público</strong> (visible en otros laboratorios de la organización) y si actúa como <strong>contenedor</strong> de reactivos.',
            },
            {
                'order': 3, 'step_key': 'mat-contenedor', 'step_type': 'MODAL',
                'title': 'Material como contenedor',
                'content': 'Si el material puede usarse como <strong>contenedor</strong> (por ejemplo: un frasco o un balón volumétrico), active la opción <strong>¿Es contenedor?</strong>. Deberá especificar la <strong>capacidad</strong> y su unidad de medida. Esto permite vincular reactivos almacenados dentro de ese contenedor en el inventario.',
            },
        ],
    },
    {
        'title': 'Gestión de Equipos',
        'slug': 'gestion-equipos',
        'description': 'Crear y gestionar el catálogo de equipos del laboratorio',
        'url_name': 'laboratory:equipment_list',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 33,
        'roles': [1, 6, 10, 5, 15, 13, 14, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'equip-concepto', 'step_type': 'MODAL',
                'title': '¿Qué es la Gestión de Equipos?',
                'content': 'Este módulo administra el <strong>catálogo de equipos</strong> del laboratorio: instrumentos, aparatos y dispositivos como balanzas, espectrofotómetros, centrífugas, etc. Los equipos registrados pueden ubicarse en estantes del inventario, vincularse a proveedores y solicitarse mediante reservaciones.',
            },
            {
                'order': 2, 'step_key': 'equip-crear', 'step_type': 'MODAL',
                'title': 'Registrar un equipo',
                'content': 'Haga clic en <strong>Crear Equipo</strong> e ingrese el código, nombre, tipo de equipo, modelo, serie y placa. Puede adjuntar el <strong>manual de uso</strong> (PDF), indicar si requiere <strong>calibración</strong> y especificar el voltaje y amperaje de operación. También puede asociar <strong>proveedores</strong> al equipo.',
            },
            {
                'order': 3, 'step_key': 'equip-tipo', 'step_type': 'MODAL',
                'title': 'Tipo y familia instrumental',
                'content': 'Cada equipo se clasifica por su <strong>tipo de equipo</strong> y puede vincularse a una <strong>familia instrumental</strong>. Estas clasificaciones permiten filtrar y agrupar los equipos por categoría, facilitando la gestión de mantenimiento y la trazabilidad de calibraciones.',
            },
            {
                'order': 4, 'step_key': 'equip-complementos', 'step_type': 'MODAL',
                'title': 'Proveedores y características',
                'content': 'Desde los botones superiores puede gestionar los módulos complementarios: <strong>Proveedores</strong> (empresas que suministran los equipos), <strong>Características de objetos</strong> (atributos personalizados) y <strong>Familia Instrumental</strong> (agrupaciones por tipo de instrumento).',
            },
        ],
    },
    {
        'title': 'Características de Objetos',
        'slug': 'caracteristicas-objetos',
        'description': 'Gestionar atributos personalizados para clasificar objetos del laboratorio',
        'url_name': 'laboratory:objectfeatures_view',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 34,
        'roles': [1, 6, 10, 5, 15, 13, 14, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'objfeat-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son las Características de Objetos?',
                'content': 'Las <strong>Características de Objetos</strong> son atributos personalizados que se pueden asignar a los reactivos, materiales y equipos del laboratorio. Permiten agregar etiquetas descriptivas como "inflamable", "corrosivo", "frágil" u otras propiedades específicas que faciliten la búsqueda y clasificación del inventario.',
            },
            {
                'order': 2, 'step_key': 'objfeat-crear', 'step_type': 'MODAL',
                'title': 'Registrar una característica',
                'content': 'Haga clic en <strong>Registrar Característica</strong> e ingrese el <strong>nombre</strong> de la característica (debe ser único) y una <strong>descripción</strong> que explique su significado. Una vez creada, quedará disponible para asignarse a cualquier objeto del catálogo del laboratorio.',
            },
            {
                'order': 3, 'step_key': 'objfeat-uso', 'step_type': 'MODAL',
                'title': 'Uso en objetos del inventario',
                'content': 'Al crear o editar un reactivo, material o equipo, encontrará un campo de <strong>Características</strong> donde puede asignar una o varias de las características registradas. Esto permite filtrar el inventario por características específicas y agrupar objetos con propiedades comunes.',
            },
        ],
    },
    {
        'title': 'Familia Instrumental',
        'slug': 'familia-instrumental',
        'description': 'Gestionar las agrupaciones de familias instrumentales para clasificar equipos',
        'url_name': 'laboratory:instrumentalfamily_list',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 35,
        'roles': [1, 6, 10, 5, 15, 13, 14, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'instfam-concepto', 'step_type': 'MODAL',
                'title': '¿Qué es la Familia Instrumental?',
                'content': 'Las <strong>Familias Instrumentales</strong> son agrupaciones que clasifican los equipos del laboratorio según su naturaleza o función. Ejemplos: "Espectroscopia", "Cromatografía", "Equipos de pesaje". Esta clasificación facilita la organización, búsqueda y filtrado de equipos en el catálogo del laboratorio.',
            },
            {
                'order': 2, 'step_key': 'instfam-crear', 'step_type': 'MODAL',
                'title': 'Registrar una familia instrumental',
                'content': 'Haga clic en <strong>Crear registro de familia instrumental</strong> e ingrese la <strong>descripción</strong> de la familia. Sea descriptivo y use nombres que reflejen claramente el grupo de instrumentos que representa. Una vez creada, estará disponible para asignarse a equipos en el catálogo.',
            },
            {
                'order': 3, 'step_key': 'instfam-uso', 'step_type': 'MODAL',
                'title': 'Uso en la gestión de equipos',
                'content': 'Al registrar o editar un equipo en el módulo de <strong>Gestión de Equipos</strong>, puede asignarle la familia instrumental correspondiente. Esto permite agrupar equipos de la misma naturaleza y facilita la búsqueda por tipo de instrumento en el inventario.',
            },
        ],
    },
    {
        'title': 'Tipos de Equipo',
        'slug': 'tipos-equipo',
        'description': 'Gestionar los tipos de equipo para clasificar el catálogo de equipos',
        'url_name': 'laboratory:equipmenttype_list',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 36,
        'roles': [1, 6, 10, 5, 15, 13, 14, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'eqtype-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son los Tipos de Equipo?',
                'content': 'Los <strong>Tipos de Equipo</strong> permiten clasificar los equipos del laboratorio por su categoría funcional. Ejemplos: "Balanza analítica", "Agitador magnético", "Centrífuga", "Horno de secado". Esta clasificación es más específica que la familia instrumental y se usa directamente al registrar o filtrar equipos.',
            },
            {
                'order': 2, 'step_key': 'eqtype-crear', 'step_type': 'MODAL',
                'title': 'Registrar un tipo de equipo',
                'content': 'Haga clic en <strong>Crear registro de tipo de equipo</strong> e ingrese el <strong>nombre</strong> del tipo y una <strong>descripción</strong> que lo defina claramente. Una vez creado, estará disponible para asignarse a cualquier equipo al momento de registrarlo en el catálogo del laboratorio.',
            },
            {
                'order': 3, 'step_key': 'eqtype-uso', 'step_type': 'MODAL',
                'title': 'Uso en la gestión de equipos',
                'content': 'Al registrar un equipo en el módulo de <strong>Gestión de Equipos</strong>, seleccione el tipo correspondiente. La tabla de equipos muestra el tipo asignado y permite filtrar por él, facilitando la localización rápida de instrumentos específicos dentro del inventario del laboratorio.',
            },
        ],
    },
    {
        'title': 'Consumo y Reorden de Reactivos',
        'slug': 'consumo-reorden-reactivos',
        'description': 'Registrar aumentos y disminuciones de cantidad en objetos del inventario',
        'url_name': 'laboratory:shel_objects_reactives',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 37,
        'roles': [1, 6, 10, 5, 15, 13, 14, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'consreact-concepto', 'step_type': 'MODAL',
                'title': '¿Qué es el Consumo y Reorden?',
                'content': 'El módulo de <strong>Consumo y Reorden</strong> permite registrar movimientos de cantidad sobre los objetos ubicados en los estantes del laboratorio. Desde aquí puede registrar un <strong>aumento</strong> (ingreso de nuevo stock) o una <strong>disminución</strong> (consumo o retiro) de cualquier reactivo, material o equipo del inventario.',
            },
            {
                'order': 2, 'step_key': 'consreact-aumentar', 'step_type': 'MODAL',
                'title': 'Registrar un aumento',
                'content': 'Use el botón <strong>Agregar</strong> para registrar una entrada de stock. Seleccione el objeto en estante, ingrese la <strong>cantidad</strong> con su unidad de medida y describa el <strong>motivo</strong> del ingreso (compra, devolución, donación, etc.). El inventario se actualiza automáticamente al confirmar.',
            },
            {
                'order': 3, 'step_key': 'consreact-disminuir', 'step_type': 'MODAL',
                'title': 'Registrar una disminución',
                'content': 'Use el botón <strong>Disminuir</strong> para registrar un consumo o retiro de stock. Ingrese la <strong>cantidad</strong> consumida y el <strong>motivo</strong> del retiro. El sistema descuenta la cantidad del inventario y registra el movimiento con el usuario y la fecha para trazabilidad completa.',
            },
            {
                'order': 4, 'step_key': 'consreact-trazabilidad', 'step_type': 'MODAL',
                'title': 'Trazabilidad de movimientos',
                'content': 'Cada aumento o disminución queda registrado en el historial del objeto en estante. Esto permite auditar quién consumió qué cantidad, cuándo y por qué motivo, facilitando el control de inventario y el cumplimiento de normativas de trazabilidad en el laboratorio.',
            },
        ],
    },
    {
        'title': 'Condición de Proceso de Reactivos',
        'slug': 'condicion-proceso-reactivos',
        'description': 'Gestionar la condición de proceso de reactivos inflamables en el inventario',
        'url_name': 'laboratory:shelf_object_hcode',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 38,
        'roles': [1, 6, 10, 5, 15, 13, 14, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'hcode-concepto', 'step_type': 'MODAL',
                'title': '¿Qué es la Condición de Proceso?',
                'content': 'Este módulo lista los <strong>reactivos inflamables</strong> presentes en el inventario del laboratorio, identificados por sus códigos H de inflamabilidad (H220–H226 y similares). Para cada reactivo en estante se puede registrar la <strong>condición de proceso</strong>: el estado operativo bajo el cual se maneja la sustancia (temperatura ambiente, refrigeración, presión controlada, etc.).',
            },
            {
                'order': 2, 'step_key': 'hcode-actualizar', 'step_type': 'MODAL',
                'title': 'Actualizar la condición de proceso',
                'content': 'Haga clic en el botón de edición del reactivo correspondiente. Se abrirá un modal donde podrá seleccionar la <strong>condición de proceso</strong> adecuada del catálogo. Esta información es relevante para la gestión de riesgo y el cumplimiento de normas de almacenamiento de sustancias inflamables.',
            },
            {
                'order': 3, 'step_key': 'hcode-importancia', 'step_type': 'MODAL',
                'title': 'Importancia regulatoria',
                'content': 'Registrar correctamente la condición de proceso de los reactivos inflamables es un requisito de seguridad. Esta información se usa en los <strong>reportes de gestión de riesgo</strong> y en la evaluación de compatibilidad de almacenamiento según el estándar SGA, ayudando a prevenir incidentes en el laboratorio.',
            },
        ],
    },
    {
        'title': 'Proveedores',
        'slug': 'proveedores',
        'description': 'Registrar y gestionar los proveedores de equipos y materiales del laboratorio',
        'url_name': 'laboratory:provider_view',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 39,
        'roles': [1, 6, 10, 5, 15, 13, 14, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'prov-concepto', 'step_type': 'MODAL',
                'title': '¿Qué son los Proveedores?',
                'content': 'Los <strong>Proveedores</strong> son las empresas o personas que suministran equipos, reactivos y materiales al laboratorio. Registrarlos en el sistema permite vincularlos directamente a los equipos del catálogo, facilitando la trazabilidad de compras, garantías y contactos de soporte técnico.',
            },
            {
                'order': 2, 'step_key': 'prov-registrar', 'step_type': 'MODAL',
                'title': 'Registrar un proveedor',
                'content': 'Haga clic en <strong>Registrar Proveedor</strong> e ingrese el <strong>nombre</strong> de la empresa o persona, el <strong>teléfono</strong> de contacto, el <strong>correo electrónico</strong> y la <strong>identidad legal</strong> (número de cédula jurídica o identificación). Estos datos quedan disponibles para vincularse a equipos del catálogo.',
            },
            {
                'order': 3, 'step_key': 'prov-vinculo', 'step_type': 'MODAL',
                'title': 'Vínculo con equipos',
                'content': 'Una vez registrado el proveedor, podrá asociarlo a uno o varios <strong>equipos</strong> desde el módulo de Gestión de Equipos. Esto permite saber rápidamente a quién contactar para mantenimiento, garantía o reposición de un instrumento específico del laboratorio.',
            },
        ],
    },
    {
        'title': 'Carga Masiva de Inventario',
        'slug': 'carga-masiva-inventario',
        'description': 'Importar reactivos al inventario desde un archivo XLSM',
        'url_name': 'laboratory:load_archive',
        'chapter': 'LABORATORIOS',
        'auto_start': False,
        'order': 40,
        'roles': [1, 6, 10, 5, 15, 13, 14, 8],
        'steps': [
            {
                'order': 1, 'step_key': 'loadarch-concepto', 'step_type': 'MODAL',
                'title': '¿Qué es la Carga Masiva de Inventario?',
                'content': 'La <strong>Carga Masiva de Inventario</strong> permite importar un listado de reactivos al inventario del laboratorio desde un archivo <strong>XLSM</strong> (Excel con macros). Esto es útil cuando se recibe un inventario inicial, se migra desde otro sistema o se necesita registrar muchos reactivos de una sola vez.',
            },
            {
                'order': 2, 'step_key': 'loadarch-archivo', 'step_type': 'MODAL',
                'title': 'Formato del archivo XLSM',
                'content': 'El archivo debe contener la hoja <strong>"Formato de Iventario"</strong> con datos a partir de la fila 8. Las columnas esperadas son: nombre del producto, número CAS, fórmula química, estado físico, cantidad, unidades, capacidad del envase, unidades de capacidad, número de envases, material del contenedor, cantidad máxima anual, unidades de cantidad máxima y fecha de caducidad.',
            },
            {
                'order': 3, 'step_key': 'loadarch-destino', 'step_type': 'MODAL',
                'title': 'Seleccionar destino en el inventario',
                'content': 'Puede indicar un <strong>destino específico</strong> seleccionando la sala, el mueble y el estante donde se almacenarán los reactivos importados. Si no selecciona un destino, el sistema creará automáticamente una sala <strong>"Reactivos Cargados"</strong> con su mueble y estante correspondientes.',
            },
            {
                'order': 4, 'step_key': 'loadarch-unidad', 'step_type': 'MODAL',
                'title': 'Compatibilidad de unidades',
                'content': 'Si el estante destino tiene una <strong>unidad de medida definida</strong>, todas las filas del archivo deben usar esa misma unidad. Si algún reactivo tiene una unidad diferente, el sistema rechazará la carga y mostrará un mensaje indicando la unidad esperada.',
            },
            {
                'order': 5, 'step_key': 'loadarch-revision', 'step_type': 'MODAL',
                'title': 'Revisión y confirmación',
                'content': 'Tras cargar el archivo, el sistema muestra un <strong>formulario de revisión</strong> con todos los reactivos detectados. Puede corregir los campos antes de confirmar la importación. Una vez confirmado, los reactivos se crean en el inventario con toda la información del archivo.',
            },
            {
                'order': 6, 'step_key': 'loadarch-envases', 'step_type': 'MODAL',
                'title': 'Número de envases',
                'content': 'La columna <strong>número de envases</strong> indica cuántas unidades del mismo reactivo se importan. Si una fila tiene número de envases = 3, el sistema creará 3 objetos en estante con los mismos datos, representando cada envase individual en el inventario.',
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
        ('presentation', '0008_load_initial_tutorials'),
        ('auth_and_perms', '0026_remove_unused_roles'),
    ]

    operations = [
        migrations.RunPython(load_tutorials, remove_tutorials),
    ]
