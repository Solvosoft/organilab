import io

import ezodf
from lxml import etree

from laboratory.models import Object, ShelfObject
from risk_management.models import RiskZone
from sga.models import DangerIndication

NS_STYLE = 'urn:oasis:names:tc:opendocument:xmlns:style:1.0'
NS_FO = 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0'
NS_TABLE = 'urn:oasis:names:tc:opendocument:xmlns:table:1.0'

ODS_STYLES = {
    'green_bg': '#00B050',
    'yellow_bg': '#FFD700',
    'red_bg': '#FF0000',
    'gray_bg': '#D9D9D9',
    'header_bg': '#4472C4',
    'alert_bg': '#FFC7CE',
}

COMPAT_TO_STYLE = {
    'V': 'green_bg',
    'A': 'yellow_bg',
    'R': 'red_bg',
    '-': 'gray_bg',
}

COMPAT_LABELS = {
    'V': 'Compatible',
    'A': 'Precaución',
    'R': 'Incompatible',
    '-': '-',
}

COMPAT_LABEL_COLORS = {
    COMPAT_LABELS[code]: ODS_STYLES[COMPAT_TO_STYLE[code]]
    for code in COMPAT_TO_STYLE
}

# H-code -> hazard class mapping (based on SGA Annex 3, Rev.6)
H_CODE_TO_CLASS = {
    # Physical Hazards (Part 2)
    'H200': 'explosivos', 'H201': 'explosivos', 'H202': 'explosivos',
    'H203': 'explosivos', 'H204': 'explosivos', 'H205': 'explosivos',
    'H206': 'explosivos_insensibilizados', 'H207': 'explosivos_insensibilizados',
    'H208': 'explosivos_insensibilizados',
    'H220': 'gases_inflamables', 'H221': 'gases_inflamables',
    'H222': 'aerosoles_inflamables', 'H223': 'aerosoles_inflamables',
    'H224': 'liquidos_inflamables', 'H225': 'liquidos_inflamables',
    'H226': 'liquidos_inflamables', 'H227': 'liquidos_inflamables',
    'H228': 'solidos_inflamables',
    'H229': 'aerosoles_presion',
    'H230': 'gases_inflamables', 'H231': 'gases_inflamables',
    'H232': 'gases_inflamables',
    'H240': 'autorreactivas', 'H241': 'autorreactivas', 'H242': 'autorreactivas',
    'H250': 'piroforicos',
    'H251': 'calentamiento_espontaneo', 'H252': 'calentamiento_espontaneo',
    'H260': 'reactivos_agua', 'H261': 'reactivos_agua',
    'H270': 'gases_comburentes',
    'H271': 'comburentes_liq_sol', 'H272': 'comburentes_liq_sol',
    'H280': 'gases_presion', 'H281': 'gases_presion',
    'H290': 'corrosivos_metales',
    # Health Hazards (Part 3)
    'H300': 'toxicidad_aguda', 'H301': 'toxicidad_aguda', 'H302': 'toxicidad_aguda',
    'H303': 'toxicidad_aguda', 'H304': 'peligro_aspiracion', 'H305': 'peligro_aspiracion',
    'H310': 'toxicidad_aguda', 'H311': 'toxicidad_aguda', 'H312': 'toxicidad_aguda',
    'H313': 'toxicidad_aguda',
    'H314': 'corrosion_cutanea', 'H315': 'irritacion_cutanea', 'H316': 'irritacion_cutanea',
    'H317': 'sensibilizacion_cutanea',
    'H318': 'lesiones_oculares', 'H319': 'irritacion_ocular', 'H320': 'irritacion_ocular',
    'H330': 'toxicidad_aguda', 'H331': 'toxicidad_aguda', 'H332': 'toxicidad_aguda',
    'H333': 'toxicidad_aguda',
    'H334': 'sensibilizacion_respiratoria',
    'H335': 'toxicidad_organos_diana', 'H336': 'toxicidad_organos_diana',
    'H340': 'mutagenicidad', 'H341': 'mutagenicidad',
    'H350': 'carcinogenicidad', 'H351': 'carcinogenicidad',
    'H360': 'toxicidad_reproduccion', 'H361': 'toxicidad_reproduccion',
    'H362': 'toxicidad_reproduccion',
    'H370': 'toxicidad_organos_diana', 'H371': 'toxicidad_organos_diana',
    'H372': 'toxicidad_organos_diana', 'H373': 'toxicidad_organos_diana',
    # Environmental Hazards (Part 4)
    'H400': 'medio_ambiente_acuatico', 'H401': 'medio_ambiente_acuatico',
    'H402': 'medio_ambiente_acuatico',
    'H410': 'medio_ambiente_acuatico', 'H411': 'medio_ambiente_acuatico',
    'H412': 'medio_ambiente_acuatico', 'H413': 'medio_ambiente_acuatico',
    'H420': 'capa_ozono',
}

# Flammable classes (all types)
INFLAMABLES = {
    'gases_inflamables', 'aerosoles_inflamables', 'liquidos_inflamables',
    'solidos_inflamables', 'aerosoles_presion',
}

# Oxidizer/comburent classes
COMBURENTES = {'gases_comburentes', 'comburentes_liq_sol'}

# Corrosive classes
CORROSIVOS = {'corrosivos_metales'}

# Health hazard classes
SALUD = {
    'toxicidad_aguda', 'peligro_aspiracion', 'corrosion_cutanea',
    'irritacion_cutanea', 'sensibilizacion_cutanea', 'lesiones_oculares',
    'irritacion_ocular', 'sensibilizacion_respiratoria',
    'toxicidad_organos_diana', 'mutagenicidad', 'carcinogenicidad',
    'toxicidad_reproduccion',
}

# Environmental classes
MEDIO_AMBIENTE = {'medio_ambiente_acuatico', 'capa_ozono'}


def get_compatibility(class_a, class_b):
    """Determine compatibility between two hazard classes.

    Returns: 'V' (green/compatible), 'A' (yellow/caution), 'R' (red/incompatible)
    Based on SGA ST/SG/AC.10/30/Rev.6, Annexes 1 and 3,
    and Reglamento 44741-S-MAG Cuadro 4.
    """
    if class_a == class_b:
        return 'V'

    pair = frozenset({class_a, class_b})

    if 'explosivos' in pair:
        return 'R'

    if 'explosivos_insensibilizados' in pair:
        return 'R'

    if 'autorreactivas' in pair:
        return 'R'

    if 'piroforicos' in pair:
        # Pirofóricos se inflaman espontáneamente al aire (SGA A1.9/A1.10, Cuadro 4 P7)
        # Requieren almacenamiento aislado
        return 'R'

    if (class_a in INFLAMABLES and class_b in COMBURENTES) or \
       (class_b in INFLAMABLES and class_a in COMBURENTES):
        return 'R'

    if (class_a in INFLAMABLES and class_b == 'reactivos_agua') or \
       (class_b in INFLAMABLES and class_a == 'reactivos_agua'):
        return 'R'

    if (class_a == 'calentamiento_espontaneo' and class_b in COMBURENTES) or \
       (class_b == 'calentamiento_espontaneo' and class_a in COMBURENTES):
        return 'R'

    if (class_a == 'reactivos_agua' and class_b in COMBURENTES) or \
       (class_b == 'reactivos_agua' and class_a in COMBURENTES):
        return 'R'

    if (class_a in COMBURENTES and class_b in CORROSIVOS) or \
       (class_b in COMBURENTES and class_a in CORROSIVOS):
        return 'R'

    if (class_a in CORROSIVOS and class_b in SALUD) or \
       (class_b in CORROSIVOS and class_a in SALUD):
        return 'R'

    if (class_a == 'reactivos_agua' and class_b in CORROSIVOS) or \
       (class_b == 'reactivos_agua' and class_a in CORROSIVOS):
        return 'A'

    if (class_a == 'calentamiento_espontaneo' and class_b in INFLAMABLES) or \
       (class_b == 'calentamiento_espontaneo' and class_a in INFLAMABLES):
        return 'A'

    if class_a in INFLAMABLES and class_b in INFLAMABLES:
        return 'V'

    if class_a in SALUD and class_b in SALUD:
        return 'A'

    if class_a in MEDIO_AMBIENTE or class_b in MEDIO_AMBIENTE:
        return 'A'

    return 'A'


def get_compatibility_reason(class_a, class_b):
    """Return a human-readable reason for an incompatibility."""
    pair = frozenset({class_a, class_b})

    if 'explosivos' in pair:
        return 'Explosivos son incompatibles con todas las clases'
    if 'explosivos_insensibilizados' in pair:
        return 'Explosivos insensibilizados requieren almacenamiento separado'
    if 'autorreactivas' in pair:
        return 'Sustancias autorreactivas son incompatibles con la mayoría de clases'
    if 'piroforicos' in pair:
        return 'Sustancias pirofóricas son altamente reactivas'

    if (class_a in INFLAMABLES and class_b in COMBURENTES) or \
       (class_b in INFLAMABLES and class_a in COMBURENTES):
        return 'Inflamables vs Comburentes: NO almacenar juntos'

    if (class_a in INFLAMABLES and class_b == 'reactivos_agua') or \
       (class_b in INFLAMABLES and class_a == 'reactivos_agua'):
        return 'Inflamables vs Reactivos con agua: NO almacenar juntos'

    if (class_a == 'calentamiento_espontaneo' and class_b in COMBURENTES) or \
       (class_b == 'calentamiento_espontaneo' and class_a in COMBURENTES):
        return 'Calentamiento espontáneo vs Comburentes: riesgo de combustión acelerada'

    if (class_a == 'reactivos_agua' and class_b in COMBURENTES) or \
       (class_b == 'reactivos_agua' and class_a in COMBURENTES):
        return 'Reactivos con agua vs Comburentes: doble riesgo de reacción'

    if (class_a in COMBURENTES and class_b in CORROSIVOS) or \
       (class_b in COMBURENTES and class_a in CORROSIVOS):
        return 'Comburentes vs Corrosivos: NO almacenar juntos'

    if (class_a in CORROSIVOS and class_b in SALUD) or \
       (class_b in CORROSIVOS and class_a in SALUD):
        return 'Corrosivos vs Tóxicos: pueden generar gases tóxicos'

    return 'Clases de peligro incompatibles'


def get_h_code_compatibility(code_a, code_b):
    """Determine compatibility between two H-codes using their hazard classes."""
    class_a = H_CODE_TO_CLASS.get(code_a)
    class_b = H_CODE_TO_CLASS.get(code_b)
    if not class_a or not class_b:
        return 'A'
    return get_compatibility(class_a, class_b)


def get_zone_substances(zone):
    """Get substances with their H-codes for all laboratories in a risk zone.

    Returns a dict: {lab: [(object_name, [h_codes])]}
    """
    lab_substances = {}
    for lab in zone.laboratories.all():
        substances = []
        shelf_objects = ShelfObject.objects.filter(
            in_where_laboratory=lab,
            object__type=Object.REACTIVE
        ).select_related(
            'object'
        ).prefetch_related(
            'object__sustancecharacteristics__h_code'
        )
        for so in shelf_objects:
            obj = so.object
            if hasattr(obj, 'sustancecharacteristics') and obj.sustancecharacteristics:
                h_codes = list(
                    obj.sustancecharacteristics.h_code.values_list('code', flat=True)
                )
                if h_codes:
                    substances.append((obj.name, sorted(h_codes)))
        if substances:
            lab_substances[lab] = substances
    return lab_substances


def collect_h_codes(lab_substances):
    """Collect all unique H-codes from lab substances."""
    all_codes = set()
    for substances in lab_substances.values():
        for _, h_codes in substances:
            all_codes.update(h_codes)
    return sorted(all_codes)


def build_compatibility_matrix(h_codes):
    """Build NxN compatibility matrix for the given H-codes."""
    matrix = {}
    for code_a in h_codes:
        matrix[code_a] = {}
        for code_b in h_codes:
            if code_a == code_b:
                matrix[code_a][code_b] = '-'
            else:
                matrix[code_a][code_b] = get_h_code_compatibility(code_a, code_b)
    return matrix


def get_incompatibility_alerts(h_codes):
    """Find all RED incompatibilities and return alert info."""
    alerts = []
    seen = set()
    h_code_descriptions = {}
    for code in h_codes:
        try:
            di = DangerIndication.objects.get(code=code)
            h_code_descriptions[code] = di.description
        except DangerIndication.DoesNotExist:
            h_code_descriptions[code] = 'Descripción no disponible'

    for code_a in h_codes:
        for code_b in h_codes:
            if code_a >= code_b:
                continue
            pair_key = (code_a, code_b)
            if pair_key in seen:
                continue
            seen.add(pair_key)
            compat = get_h_code_compatibility(code_a, code_b)
            if compat == 'R':
                class_a = H_CODE_TO_CLASS.get(code_a, 'desconocido')
                class_b = H_CODE_TO_CLASS.get(code_b, 'desconocido')
                reason = get_compatibility_reason(class_a, class_b)
                alerts.append({
                    'code_a': code_a,
                    'desc_a': h_code_descriptions.get(code_a, ''),
                    'code_b': code_b,
                    'desc_b': h_code_descriptions.get(code_b, ''),
                    'reason': reason,
                })
    return alerts


def add_ods_styles(doc):
    """Add cell color styles to the ODS document."""
    auto_styles = doc.content.automatic_styles
    for style_name, color in ODS_STYLES.items():
        style_el = etree.SubElement(
            auto_styles.xmlnode, '{%s}style' % NS_STYLE
        )
        style_el.set('{%s}name' % NS_STYLE, style_name)
        style_el.set('{%s}family' % NS_STYLE, 'table-cell')
        props = etree.SubElement(
            style_el, '{%s}table-cell-properties' % NS_STYLE
        )
        props.set('{%s}background-color' % NS_FO, color)
        text_props = etree.SubElement(
            style_el, '{%s}text-properties' % NS_STYLE
        )
        if style_name == 'header_bg':
            text_props.set('{%s}color' % NS_FO, '#FFFFFF')
            text_props.set('{%s}font-weight' % NS_FO, 'bold')
        elif style_name == 'red_bg':
            text_props.set('{%s}color' % NS_FO, '#FFFFFF')
            text_props.set('{%s}font-weight' % NS_FO, 'bold')
        else:
            text_props.set('{%s}font-weight' % NS_FO, 'bold')


def set_cell(sheet, row, col, value, style_name=None):
    """Set a cell value and optionally apply a style."""
    cell = sheet[row, col]
    cell.set_value(str(value), 'string')
    if style_name:
        cell.xmlnode.set('{%s}style-name' % NS_TABLE, style_name)


def build_zone_ods_sheet(building, zone, doc, risk_zone_pks=None):
    """Generate an ODS sheet for a single building+zone combination.

    If risk_zone_pks is provided and the zone pk is not in that list, skip it.
    Returns True if a sheet was added, False otherwise.
    """
    if risk_zone_pks and zone.pk not in risk_zone_pks:
        return False

    lab_substances = get_zone_substances(zone)
    if not lab_substances:
        return False

    all_h_codes = collect_h_codes(lab_substances)
    if len(all_h_codes) < 2:
        return False

    matrix = build_compatibility_matrix(all_h_codes)
    alerts = get_incompatibility_alerts(all_h_codes)

    n = len(all_h_codes)
    num_substance_rows = sum(2 for _ in lab_substances)
    num_alert_rows = len(alerts) * 2 if alerts else 1
    total_rows = (
        2 + 1 + num_substance_rows + 1 + 1 + 1
        + 1 + n + 1 + 3 + 1 + 1 + num_alert_rows + 2
    )
    total_cols = max(n + 1, 6)

    sheet_name = '%s - %s' % (
        building.name[:15], zone.name[:15]
    )
    sheet = ezodf.Sheet(sheet_name, size=(total_rows, total_cols))
    doc.sheets += sheet

    row_idx = 0

    # Building header
    set_cell(
        sheet, row_idx, 0,
        'EDIFICIO: %s (ID: %d)' % (building.name, building.pk),
        'header_bg'
    )
    for c in range(1, total_cols):
        set_cell(sheet, row_idx, c, '', 'header_bg')
    row_idx += 1

    # Zone header
    set_cell(
        sheet, row_idx, 0,
        'Zona de Riesgo: %s (Prioridad: %d)' % (zone.name, zone.priority),
        'header_bg'
    )
    for c in range(1, total_cols):
        set_cell(sheet, row_idx, c, '', 'header_bg')
    row_idx += 2

    # Substances per lab
    for lab, substances in lab_substances.items():
        set_cell(sheet, row_idx, 0, 'Lab: %s' % lab.name)
        row_idx += 1
        substance_strs = []
        for name, h_codes in substances:
            substance_strs.append('%s (%s)' % (name, ', '.join(h_codes)))
        set_cell(
            sheet, row_idx, 0,
            '  Sustancias: %s' % ', '.join(substance_strs)
        )
        row_idx += 1

    row_idx += 1

    # H-codes present
    set_cell(
        sheet, row_idx, 0,
        'Codigos H presentes: %s' % ', '.join(all_h_codes)
    )
    row_idx += 2

    # Matrix header row
    set_cell(sheet, row_idx, 0, '', 'header_bg')
    for j, code in enumerate(all_h_codes):
        set_cell(sheet, row_idx, j + 1, code, 'header_bg')
    row_idx += 1

    # Matrix data rows
    for row_code in all_h_codes:
        set_cell(sheet, row_idx, 0, row_code, 'header_bg')
        for j, col_code in enumerate(all_h_codes):
            val = matrix[row_code][col_code]
            style = COMPAT_TO_STYLE.get(val, 'yellow_bg')
            label = COMPAT_LABELS.get(val, val)
            set_cell(sheet, row_idx, j + 1, label, style)
        row_idx += 1

    row_idx += 1

    # Legend
    set_cell(sheet, row_idx, 0, 'LEYENDA:')
    row_idx += 1
    set_cell(sheet, row_idx, 0, 'Compatible', 'green_bg')
    set_cell(sheet, row_idx, 1, 'Precaución', 'yellow_bg')
    set_cell(sheet, row_idx, 2, 'Incompatible', 'red_bg')
    set_cell(sheet, row_idx, 3, 'Diagonal', 'gray_bg')
    row_idx += 2

    # Alerts
    if alerts:
        set_cell(
            sheet, row_idx, 0,
            'ALERTAS DE INCOMPATIBILIDAD', 'alert_bg'
        )
        for c in range(1, total_cols):
            set_cell(sheet, row_idx, c, '', 'alert_bg')
        row_idx += 1

        for alert in alerts:
            set_cell(
                sheet, row_idx, 0,
                '[ROJO] %s (%s) <-> %s (%s)' % (
                    alert['code_a'], alert['desc_a'],
                    alert['code_b'], alert['desc_b'],
                ),
                'red_bg'
            )
            row_idx += 1
            set_cell(
                sheet, row_idx, 0,
                '  -> %s' % alert['reason']
            )
            row_idx += 1
    else:
        set_cell(
            sheet, row_idx, 0,
            'No se encontraron incompatibilidades (ROJO) en esta zona.',
            'green_bg'
        )

    return True


def generate_compatibility_ods(buildings_qs, filename=None, risk_zone_pks=None):
    """Generate a complete ODS file with compatibility matrices.

    Args:
        buildings_qs: QuerySet of Buildings to include.
        filename: Optional filename for ezodf (not used for BytesIO output).
        risk_zone_pks: Optional list of RiskZone PKs to filter zones.

    Returns:
        io.BytesIO with the ODS file content.
    """
    import logging
    logger = logging.getLogger("organilab.report")

    doc = ezodf.newdoc(doctype='ods', filename=filename or 'compatibility.ods')
    add_ods_styles(doc)

    if len(doc.sheets) > 0:
        del doc.sheets[0]

    sheets_added = 0
    for building in buildings_qs:
        zones = RiskZone.objects.filter(buildings=building)
        logger.info(
            "generate_ods: building=%s (pk=%d), zones_count=%d, risk_zone_pks=%s",
            building.name, building.pk, zones.count(), risk_zone_pks,
        )
        for zone in zones:
            added = build_zone_ods_sheet(building, zone, doc, risk_zone_pks=risk_zone_pks)
            if added:
                sheets_added += 1
            else:
                logger.info(
                    "generate_ods: zone=%s (pk=%d) skipped (no data or filtered)",
                    zone.name, zone.pk,
                )

    logger.info("generate_ods: total sheets_added=%d", sheets_added)

    file_io = io.BytesIO()
    doc.saveas(file_io)
    return file_io
