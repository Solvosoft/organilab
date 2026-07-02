"""
Valores por defecto y constantes de la metodología INTE T55 (IPER).

Las *listas* (categorías de peligro, probabilidad, consecuencia y niveles de
riesgo) se guardan como entradas del modelo ``laboratory.Catalog`` (global), y se
eligen en ``IPERHazard`` con ``GTForeignKey`` filtrando por ``key``. La *matriz*
Probabilidad x Consecuencia -> Nivel se guarda en ``IPERRiskMatrix``.

Este módulo concentra:
  * los ``key`` de cada catálogo,
  * los textos por defecto que siembra la migración,
  * los atributos fijos del estándar (emoji/color por categoría, prioridad/color/
    acción por nivel, ejemplos de ayuda) que ``Catalog`` no puede almacenar.

Los textos sembrados (``description``) son la **clave estable** con la que se
indexan los metadatos de abajo; no deben renombrarse sin actualizar este módulo.
"""
from django.utils.translation import gettext_lazy as _

# --- keys de Catalog -------------------------------------------------------
KEY_HAZARD_CATEGORY = "iper_hazard_category"
KEY_PROBABILITY = "iper_probability"
KEY_CONSEQUENCE = "iper_consequence"
KEY_RISK_LEVEL = "iper_risk_level"

# --- categorías de peligro -------------------------------------------------
# description (clave) -> emoji, color (clase Tailwind/bootstrap), ejemplos
HAZARD_CATEGORIES = {
    "Seguridad": {
        "emoji": "⚠️",
        "color": "orange",
        "description": _("Condiciones físicas que pueden causar accidentes"),
        "examples": [
            _("Pisos mojados, resbaladizos o en mal estado"),
            _("Maquinaria sin guardas de protección"),
            _("Instalaciones eléctricas deficientes o sin protección"),
            _("Trabajo en alturas sin equipo de seguridad"),
            _("Almacenamiento inadecuado de materiales pesados"),
            _("Herramientas en mal estado o uso incorrecto"),
            _("Señalización de seguridad deficiente o ausente"),
            _("Materiales inflamables mal almacenados"),
            _("Riesgo de explosión por gases o presión"),
            _("Falta de orden y limpieza en el área"),
        ],
    },
    "Físico": {
        "emoji": "🔊",
        "color": "blue",
        "description": _("Energía en el ambiente que puede dañar la salud"),
        "examples": [
            _("Exposición a ruido elevado por maquinaria o equipos"),
            _("Iluminación insuficiente en el área de trabajo"),
            _("Exposición a temperaturas extremas, calor o frío"),
            _("Vibraciones generadas por herramientas o equipos"),
            _("Radiación no ionizante por equipos, lámparas o fuentes UV"),
            _("Ventilación deficiente en espacios cerrados"),
            _("Cambios bruscos de temperatura en el ambiente"),
            _("Exposición prolongada a humedad"),
            _("Presencia de polvo suspendido en el ambiente"),
            _("Presión atmosférica anormal en trabajos especiales"),
        ],
    },
    "Químico": {
        "emoji": "🧪",
        "color": "purple",
        "description": _("Sustancias que pueden ser tóxicas, corrosivas o peligrosas"),
        "examples": [
            _("Manipulación de sustancias tóxicas sin protección adecuada"),
            _("Exposición a vapores, gases o aerosoles químicos"),
            _("Almacenamiento incorrecto de productos químicos"),
            _("Mezcla de sustancias incompatibles"),
            _("Derrames de productos químicos en el área de trabajo"),
            _("Uso de solventes, ácidos o bases corrosivas"),
            _("Falta de rotulación en envases químicos"),
            _("Inhalación de polvo químico o partículas peligrosas"),
            _("Contacto directo con sustancias irritantes para la piel"),
            _("Ausencia o desconocimiento de hojas de datos de seguridad"),
        ],
    },
    "Biológico": {
        "emoji": "🦠",
        "color": "green",
        "description": _("Agentes vivos que pueden causar enfermedades o infecciones"),
        "examples": [
            _("Contacto con sangre, fluidos corporales o material contaminado"),
            _("Exposición a bacterias, virus, hongos o parásitos"),
            _("Manipulación de muestras biológicas sin protección"),
            _("Presencia de residuos biológicos mal gestionados"),
            _("Uso inadecuado de contenedores para material punzocortante"),
            _("Limpieza deficiente de superficies contaminadas"),
            _("Exposición a animales, insectos o vectores"),
            _("Falta de protocolos para manejo de material infeccioso"),
            _("Riesgo de contaminación cruzada entre áreas"),
            _("Ausencia de lavado de manos o higiene adecuada"),
        ],
    },
    "Ergonómico": {
        "emoji": "🏋️",
        "color": "yellow",
        "description": _("Condiciones que generan lesiones musculoesqueléticas"),
        "examples": [
            _("Posturas forzadas durante la ejecución de tareas"),
            _("Levantamiento manual de cargas pesadas"),
            _("Movimientos repetitivos de manos, brazos o espalda"),
            _("Trabajo prolongado de pie o sentado sin pausas"),
            _("Altura inadecuada de mesas, sillas o estaciones de trabajo"),
            _("Uso de herramientas que obligan a posiciones incómodas"),
            _("Esfuerzo físico excesivo durante la tarea"),
            _("Alcances frecuentes por encima del hombro"),
            _("Manipulación de cargas sin ayuda mecánica"),
            _("Diseño inadecuado del puesto de trabajo"),
        ],
    },
    "Psicosocial": {
        "emoji": "🧠",
        "color": "red",
        "description": _("Factores que afectan el bienestar mental y emocional"),
        "examples": [
            _("Sobrecarga de trabajo o presión excesiva por tiempos de entrega"),
            _("Jornadas prolongadas sin pausas adecuadas"),
            _("Falta de claridad en funciones o responsabilidades"),
            _("Conflictos laborales o mala comunicación en el equipo"),
            _("Acoso laboral, trato irrespetuoso o intimidación"),
            _("Falta de apoyo por parte de jefaturas o compañeros"),
            _("Trabajo monótono o con bajo control sobre la tarea"),
            _("Exposición a usuarios agresivos o situaciones de tensión"),
            _("Cambios organizacionales sin comunicación adecuada"),
            _("Desequilibrio entre carga laboral y recursos disponibles"),
        ],
    },
}

# --- probabilidad ----------------------------------------------------------
# description (clave) -> etiqueta corta, ayuda
PROBABILITY_LEVELS = {
    "Baja": {
        "short": "B",
        "help": _("El daño puede ocurrir rara vez o únicamente bajo condiciones excepcionales."),
    },
    "Media": {
        "short": "M",
        "help": _("El daño puede ocurrir algunas veces, especialmente durante ciertas tareas o condiciones específicas."),
    },
    "Alta": {
        "short": "A",
        "help": _("El daño puede ocurrir con frecuencia, diariamente o casi siempre que se realiza la actividad."),
    },
}

# --- consecuencia ----------------------------------------------------------
CONSEQUENCE_LEVELS = {
    "Ligeramente Dañino": {
        "short": "LD",
        "help": _("Daños leves que requieren primeros auxilios o atención básica, sin incapacidad importante."),
    },
    "Dañino": {
        "short": "D",
        "help": _("Daños moderados que pueden generar incapacidad temporal o enfermedades reversibles."),
    },
    "Extremadamente Dañino": {
        "short": "ED",
        "help": _("Daños graves, irreversibles, incapacitantes o que pueden causar la muerte."),
    },
}

# --- niveles de riesgo -----------------------------------------------------
# description (clave) -> prioridad (1-5), color, acción recomendada
RISK_LEVELS = {
    "Trivial": {
        "priority": 1,
        "color": "green",
        "action": _("No se requiere acción específica. Mantener las condiciones actuales."),
    },
    "Tolerable": {
        "priority": 2,
        "color": "lime",
        "action": _(
            "No se necesitan controles adicionales. Verificar periódicamente los "
            "controles existentes."
        ),
    },
    "Moderado": {
        "priority": 3,
        "color": "yellow",
        "action": _(
            "Se deben hacer esfuerzos para reducir el riesgo. Establezca mejoras en un "
            "plazo determinado."
        ),
    },
    "Importante": {
        "priority": 4,
        "color": "orange",
        "action": _(
            "No debe comenzarse el trabajo hasta reducir el riesgo. Se requiere acción "
            "urgente."
        ),
    },
    "Intolerable": {
        "priority": 5,
        "color": "red",
        "action": _(
            "No debe comenzar ni continuar el trabajo. Prohibir la actividad hasta "
            "eliminar el riesgo."
        ),
    },
}

# --- matriz Probabilidad x Consecuencia -> Nivel ---------------------------
# (probabilidad, consecuencia) -> nivel de riesgo (claves = description sembradas)
RISK_MATRIX = {
    ("Baja", "Ligeramente Dañino"): "Trivial",
    ("Baja", "Dañino"): "Tolerable",
    ("Baja", "Extremadamente Dañino"): "Moderado",
    ("Media", "Ligeramente Dañino"): "Tolerable",
    ("Media", "Dañino"): "Moderado",
    ("Media", "Extremadamente Dañino"): "Importante",
    ("Alta", "Ligeramente Dañino"): "Moderado",
    ("Alta", "Dañino"): "Importante",
    ("Alta", "Extremadamente Dañino"): "Intolerable",
}

# Mapeo description -> prioridad, usado para desnormalizar IPERHazard.risk_priority
RISK_LEVEL_PRIORITY = {desc: data["priority"] for desc, data in RISK_LEVELS.items()}

# Mapeo description -> clase de color Bootstrap (badges en templates)
RISK_LEVEL_BOOTSTRAP = {
    "Trivial": "success",
    "Tolerable": "info",
    "Moderado": "warning",
    "Importante": "danger",
    "Intolerable": "dark",
}

# Período por defecto (meses) para solicitar actualización del IPER.
DEFAULT_PERIOD_MONTHS = 12
DEFAULT_REMINDER_DAYS_BEFORE = 30


def get_catalog_seed():
    """Devuelve la lista de tuplas ``(key, description)`` a sembrar en Catalog."""
    seed = []
    for desc in HAZARD_CATEGORIES:
        seed.append((KEY_HAZARD_CATEGORY, desc))
    for desc in PROBABILITY_LEVELS:
        seed.append((KEY_PROBABILITY, desc))
    for desc in CONSEQUENCE_LEVELS:
        seed.append((KEY_CONSEQUENCE, desc))
    for desc in RISK_LEVELS:
        seed.append((KEY_RISK_LEVEL, desc))
    return seed


def seed_iper(Catalog, IPERRiskMatrix, IPERConfig, OrganizationStructure):
    """Siembra idempotente de catálogos IPER, matriz de riesgo y configuración.

    Recibe las clases de modelo (reales o históricas en una migración) para poder
    invocarse tanto desde ``migrations.RunPython`` como desde un management command.

    1. Crea las entradas ``Catalog`` de los 4 ``key`` si no existen.
    2. Crea las 9 filas de ``IPERRiskMatrix``.
    3. Crea una ``IPERConfig`` por defecto para cada organización raíz (``parent=Null``).
    """
    # 1. Catálogos (Catalog es global)
    for key, description in get_catalog_seed():
        Catalog.objects.get_or_create(key=key, description=description)

    def _cat(key, description):
        return Catalog.objects.filter(key=key, description=description).first()

    # 2. Matriz Probabilidad x Consecuencia -> Nivel
    for (probability, consequence), risk_level in RISK_MATRIX.items():
        prob = _cat(KEY_PROBABILITY, probability)
        cons = _cat(KEY_CONSEQUENCE, consequence)
        level = _cat(KEY_RISK_LEVEL, risk_level)
        if prob and cons and level:
            IPERRiskMatrix.objects.get_or_create(
                probability=prob,
                consequence=cons,
                defaults={"risk_level": level},
            )

    # 3. IPERConfig por cada organización raíz (parent=Null)
    for org in OrganizationStructure.objects.filter(parent__isnull=True):
        IPERConfig.objects.get_or_create(
            organization=org,
            laboratory=None,
            defaults={
                "period_months": DEFAULT_PERIOD_MONTHS,
                "reminder_days_before": DEFAULT_REMINDER_DAYS_BEFORE,
                "is_active": True,
            },
        )
