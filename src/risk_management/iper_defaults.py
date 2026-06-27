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
            _("Ruido excesivo de centrífugas, agitadores o equipos"),
            _("Vibraciones de maquinaria de laboratorio"),
            _("Iluminación insuficiente en zonas de trabajo"),
            _("Calor excesivo cerca de hornos, autoclaves o reactores"),
            _("Frío extremo en cuartos de refrigeración o congelamiento"),
            _("Radiación ultravioleta de lámparas germicidas (UV)"),
            _("Radiación ionizante (rayos X, materiales radiactivos)"),
            _("Presiones anormales en equipos presurizados"),
            _("Ventilación inadecuada o corrientes de aire"),
        ],
    },
    "Químico": {
        "emoji": "🧪",
        "color": "purple",
        "description": _("Sustancias que pueden ser tóxicas, corrosivas o peligrosas"),
        "examples": [
            _("Vapores de solventes orgánicos (acetona, metanol, hexano)"),
            _("Gases tóxicos generados en reacciones químicas"),
            _("Ácidos corrosivos (HCl, H₂SO₄, HNO₃)"),
            _("Bases corrosivas (NaOH, KOH)"),
            _("Polvo de reactivos o muestras sólidas"),
            _("Aerosoles de soluciones químicas"),
            _("Reactivos cancerígenos o mutagénicos"),
            _("Formaldehído, glutaraldehído u otros preservantes"),
            _("Derrames de sustancias peligrosas"),
            _("Mezcla accidental de químicos incompatibles"),
        ],
    },
    "Biológico": {
        "emoji": "🦠",
        "color": "green",
        "description": _("Agentes vivos que pueden causar enfermedades o infecciones"),
        "examples": [
            _("Bacterias patógenas en muestras clínicas"),
            _("Virus presentes en muestras de sangre o fluidos corporales"),
            _("Hongos y esporas en cultivos microbiológicos"),
            _("Parásitos en muestras fecales u otras muestras"),
            _("Pinchazos accidentales con agujas contaminadas"),
            _("Contacto directo con sangre u otros fluidos"),
            _("Aerosoles de muestras infecciosas al centrifugar"),
            _("Residuos biológicos mal clasificados o gestionados"),
            _("Cultivos de microorganismos patógenos"),
        ],
    },
    "Ergonómico": {
        "emoji": "🏋️",
        "color": "yellow",
        "description": _("Condiciones que generan lesiones musculoesqueléticas"),
        "examples": [
            _("Postura forzada al usar microscopio u otros equipos"),
            _("Pipeteo manual continuo (movimientos repetitivos de mano)"),
            _("Carga manual de objetos pesados (tanques, cajas, equipos)"),
            _("Trabajo prolongado de pie sin pausas activas"),
            _("Silla, mesa o equipo no ajustable ergonómicamente"),
            _("Espacio de trabajo insuficiente o mal distribuido"),
            _("Tensión visual por trabajo de precisión prolongado"),
            _("Inclinación frecuente sobre superficies de trabajo"),
        ],
    },
    "Psicosocial": {
        "emoji": "🧠",
        "color": "red",
        "description": _("Factores que afectan el bienestar mental y emocional"),
        "examples": [
            _("Exceso de carga de trabajo o plazos muy ajustados"),
            _("Alta responsabilidad o trabajo bajo presión constante"),
            _("Funciones y responsabilidades poco claras"),
            _("Trabajo monótono y repetitivo sin variación"),
            _("Falta de comunicación o apoyo del equipo de trabajo"),
            _("Jornadas laborales prolongadas o trabajo nocturno"),
            _("Acoso laboral o conflictos interpersonales frecuentes"),
            _("Falta de reconocimiento o posibilidades de desarrollo"),
        ],
    },
}

# --- probabilidad ----------------------------------------------------------
# description (clave) -> etiqueta corta, ayuda
PROBABILITY_LEVELS = {
    "Baja": {
        "short": "B",
        "help": _("El daño ocurrirá raramente"),
    },
    "Media": {
        "short": "M",
        "help": _("El daño ocurrirá algunas veces"),
    },
    "Alta": {
        "short": "A",
        "help": _("El daño ocurrirá siempre o casi siempre"),
    },
}

# --- consecuencia ----------------------------------------------------------
CONSEQUENCE_LEVELS = {
    "Ligeramente Dañino": {
        "short": "LD",
        "help": _("Lesiones superficiales o irritación leve"),
    },
    "Dañino": {
        "short": "D",
        "help": _("Lesiones con incapacidad temporal"),
    },
    "Extremadamente Dañino": {
        "short": "ED",
        "help": _("Lesiones graves, irreversibles o muerte"),
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
