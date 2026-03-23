import re
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

PDF_EXTRACT_TIMEOUT = 30


UNICODE_SUBSCRIPT_MAP = {
    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
    '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
}


def _normalize_subscripts(text):
    for uni, digit in UNICODE_SUBSCRIPT_MAP.items():
        text = text.replace(uni, digit)
    return text


def _detect_language(text):
    """Detect SDS language from section headers and keywords. Returns 'es' or 'en'."""
    header = text[:2000].upper()
    if 'SECCI' in header:
        return 'es'
    # Older Merck Spanish SDS don't use SECCIÓN headers
    es_indicators = ['FECHA DE', 'DENOMINACI', 'FICHA DE DATOS', 'HOJA DE DATOS',
                     'IDENTIFICACI', 'SUSTANCIA PELIGROSA']
    if sum(1 for kw in es_indicators if kw in header) >= 2:
        return 'es'
    return 'en'


def _section_pattern(n, lang):
    """Return a regex pattern matching section N header for the given language."""
    if lang == 'es':
        return r'SECCI[ÓO]N\s*' + str(n)
    return r'Section\s*' + str(n)


def _extract_product_name(text, lang='es'):
    sec2 = re.search(_section_pattern(2, lang), text, re.IGNORECASE)
    section1_text = text[:sec2.start()] if sec2 else text[:2000]

    if lang == 'es':
        patterns = [
            r'Nombre\s+del\s+producto\s*:?\s*(.+)',
            r'Nombre\s+comercial\s*:?\s*(.+)',
            r'Denominaci[óo]n\s*:?\s*(.+)',
            r'Nombre\s+de\s+la\s+sustancia\s*:?\s*(.+)',
        ]
    else:
        patterns = [
            r'Product\s+[Nn]ame\s*:?\s*(.+)',
            r'Trade\s+[Nn]ame\s*:?\s*(.+)',
            r'Substance\s+[Nn]ame\s*:?\s*(.+)',
        ]
    for pattern in patterns:
        match = re.search(pattern, section1_text)
        if match:
            name = match.group(1).strip().lstrip('·').strip().rstrip('.')
            if name and len(name) >= 2:
                return name
    return None


def _extract_cas_number(text, lang='es'):
    patterns = [
        r'CAS[-\s]*No\.?\s*[:\.]?\s*(\d{1,7}-\d{2}-\d)',
        r'CAS\s*Number\s*:?\s*\n?\s*(\d{1,7}-\d{2}-\d)',
        r'N\.º\s*CAS\s*:?\s*(\d{1,7}-\d{2}-\d)',
        r'N[ºúu](?:mero)?\s*CAS\s*\[?\s*(\d{1,7}-\d{2}-\d)',
        r'\bCAS\s+(\d{1,7}-\d{2}-\d)',
    ]

    sec2 = re.search(_section_pattern(2, lang), text, re.IGNORECASE)
    section1_text = text[:sec2.start()] if sec2 else text
    for pattern in patterns:
        match = re.search(pattern, section1_text)
        if match:
            return match.group(1)

    # Try section 3 with formal section header
    sec3 = re.search(_section_pattern(3, lang), text, re.IGNORECASE)
    sec4 = re.search(_section_pattern(4, lang), text, re.IGNORECASE)
    if sec3:
        sec3_text = text[sec3.start():sec4.start() if sec4 else len(text)]
        for pattern in patterns:
            match = re.search(pattern, sec3_text)
            if match:
                return match.group(1)
        # Fallback: any CAS-formatted number in section 3
        match = re.search(r'(\d{1,7}-\d{2}-\d)', sec3_text)
        if match:
            return match.group(1)

    # Fallback for SDS without standard section headers (e.g. Cayman)
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return None


def _extract_molecular_formula(text, lang='es'):
    normalized = _normalize_subscripts(text)

    # Merck/Sigma-Aldrich format: "Formula CH3COCH3 C3H6O (Hill)"
    hill_match = re.search(
        r'([A-Z][A-Za-z0-9]+)\s*\(Hill\)', normalized
    )
    if hill_match:
        formula = hill_match.group(1)
        if re.match(r'^[A-Z][A-Za-z0-9]*$', formula) and len(formula) >= 2:
            if formula == 'H2O':
                pre_hill = normalized[:hill_match.start()]
                hydrate_match = re.search(
                    r'([A-Z][A-Za-z0-9]+)\s*[·•]\s*H2O', pre_hill
                )
                if hydrate_match:
                    real = hydrate_match.group(1)
                    if re.match(r'^[A-Z][A-Za-z0-9]*$', real) and len(real) >= 2:
                        return real
            return formula

    if lang == 'es':
        patterns = [
            r'[Ff][óo]rmula\s+molecular\s*:?\s*([A-Za-z0-9\s]+?)(?:\n|$|\(|\.[\s\n])',
        ]
    else:
        patterns = [
            r'Molecular\s+[Ff]ormula\s*:?\s*([A-Za-z0-9\s]+?)(?:\n|$|\(|\.[\s\n])',
            r'Structural\s+[Ff]ormula\s*:?\s*([A-Za-z0-9\s]+?)(?:\n|$|\(|\.[\s\n])',
            r'Formula\s*:?\s*([A-Za-z0-9\s]+?)(?:\n|$|\(|\.[\s\n])',
        ]
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            raw = match.group(1).strip()
            formula = re.sub(r'\s+', '', raw)
            if re.match(r'^[A-Z][A-Za-z0-9]*$', formula) and len(formula) >= 2:
                return formula
    return None


def _extract_h_codes(text):
    codes = set(re.findall(r'\bH\d{3}\b', text))
    return sorted(codes)


def _extract_density(text, lang='es'):
    if lang == 'es':
        patterns = [
            r'Densidad\s+relativa\s*:?\s*(?:aprox\.?\s*)?([\d]+[.,][\d]+)',
            r'Densidad\s+a\s+[\d.,]+\s*[°ºo]?\s*C[^:]*:\s*([\d]+[.,][\d]+)',
            r'Densidad\s*:?\s*(?:aprox\.?\s*)?([\d]+[.,][\d]+)',
        ]
    else:
        patterns = [
            r'Relative\s+density\s*:?\s*(?:approx\.?\s*)?([\d]+[.,][\d]+)',
            r'Specific\s+[Gg]ravity\s*:?\s*(?:approx\.?\s*)?([\d]+[.,][\d]+)',
            r'Density\s+at\s+[\d.,]+\s*[°ºo]?\s*C[^:]*:\s*([\d]+[.,][\d]+)',
            r'Density\s*:?\s*(?:approx\.?\s*)?([\d]+[.,][\d]+)',
        ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).replace(',', '.')
            try:
                return float(value)
            except ValueError:
                continue
    return None


def _extract_bioaccumulable(text, lang='es'):
    negative_patterns = [
        r'(?:bioaccumul|bioacumul)\w*\s+(?:es|is)\s+(?:improbable|unlikely|low)',
        r'no.{0,50}(?:bioaccumul|bioacumul)',
        r'(?:bioaccumul|bioacumul).{0,50}(?:no\s+(?:es|is)|improbable|unlikely)',
        r'not.{0,30}(?:bioaccumul|bioacumul)',
        r'no\s+components?\s+(?:are\s+)?considered.{0,50}(?:bioaccumul|bioacumul)',
    ]
    for pattern in negative_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False

    section12 = re.search(
        r'(?:12\.3|Potencial de bioacumulaci|Bioaccumulative potential)'
        r'(.{0,500}?)(?:12\.4|12\.5|Movilidad|Mobility)',
        text, re.DOTALL | re.IGNORECASE
    )
    if section12:
        context = section12.group(1)
        if re.search(r'(?:improbable|unlikely|low|no\s+data|no\s+hay)', context, re.IGNORECASE):
            return False
        if re.search(r'(?:high|significant|probable|likely)', context, re.IGNORECASE):
            return True

    return None


def _extract_seveso(text, lang='es'):
    if not re.search(r'[Ss]eveso', text):
        return False

    not_applicable_patterns = [
        r'[Ss]eveso.{0,500}(?:[Nn]o\s+(?:es\s+)?aplicable|[Nn]ot\s+applicable)',
        r'[Ss]eveso.{0,500}no\s+asignado',
        r'[Ss]eveso.{0,500}[Nn]ot\s+(?:subject|listed|regulated)',
    ]
    for pattern in not_applicable_patterns:
        if re.search(pattern, text, re.DOTALL):
            return False

    substance_patterns = [
        r'[Ss]eveso.{0,200}(?:[Cc]ategor|[Qq]ualifying|umbral|[Tt]hreshold).{0,200}\d',
        r'[Ss]eveso.{0,100}(?:listed|incluido|sujeto)',
    ]
    for pattern in substance_patterns:
        if re.search(pattern, text, re.DOTALL):
            return True

    return False


def _extract_precursor(text, lang='es'):
    if not re.search(r'[Pp]recursor', text):
        return False

    not_applicable_patterns = [
        r'[Pp]recursor.{0,200}(?:[Nn]o\s+(?:es\s+)?aplicable|[Nn]ot\s+applicable)',
        r'[Pp]recursor.{0,200}(?:[Nn]o\s+(?:est[áa]|is)\s+(?:sujeto|subject|listed))',
    ]
    for pattern in not_applicable_patterns:
        if re.search(pattern, text, re.DOTALL):
            return False

    substance_patterns = [
        r'[Pp]recursor.{0,100}(?:sujeto|subject|restrict|listed|regulat)',
        r'(?:sujeto|subject|restrict).{0,100}[Pp]recursor',
    ]
    for pattern in substance_patterns:
        if re.search(pattern, text, re.DOTALL):
            return True

    return False


REVISION_DATE_PATTERNS_ES = [
    r'Fecha\s+de\s+[Rr]evisi[oó]n[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
    r'Fecha\s+de\s+[Rr]evisi[oó]n[:\s]*(\d{2,4}[.-]\d{1,2}[.-]\d{1,2})',
    r'Revisi[oó]n[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
    r'Fecha:\s*(\d{4}-\d{2}-\d{2})',
    r'Fecha\s+de\s+emisi[oó]n[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
]

REVISION_DATE_PATTERNS_EN = [
    r'Revision\s+Date[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
    r'Revision\s+Date[:\s]*(\d{2,4}[.-]\d{1,2}[.-]\d{1,2})',
    r'Date\s+of\s+Revision[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
    r'Revision.*?(\d{2}[./]\d{2}[./]\d{4})',
]

# Combined list for backward compatibility (used by identify_sds_sources.py)
REVISION_DATE_PATTERNS = REVISION_DATE_PATTERNS_ES + REVISION_DATE_PATTERNS_EN


def _parse_revision_date(date_str):
    if not date_str:
        return None
    for fmt in ('%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d.%m.%y', '%d/%m/%y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def _extract_revision_date(text, lang='es'):
    patterns = REVISION_DATE_PATTERNS_ES if lang == 'es' else REVISION_DATE_PATTERNS_EN
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return _parse_revision_date(match.group(1).strip())
    return None


def extract_msds_data(pdf_path):
    """Extract MSDS/SDS data from a PDF file.

    Returns a dict with extracted fields, or None values for fields
    that could not be extracted.
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber is not installed. Run: pip install pdfplumber")
        return None

    result = {}

    def _read():
        try:
            with pdfplumber.open(pdf_path) as pdf:
                result['text'] = '\n'.join(
                    page.extract_text() or '' for page in pdf.pages
                )
        except Exception as exc:
            result['error'] = exc

    reader = threading.Thread(target=_read, daemon=True)
    reader.start()
    reader.join(timeout=PDF_EXTRACT_TIMEOUT)

    if reader.is_alive():
        logger.warning("Timeout reading PDF: %s", pdf_path)
        return None

    if 'error' in result:
        logger.exception(
            "Failed to read PDF: %s", pdf_path, exc_info=result['error']
        )
        return None

    text = result.get('text', '')

    if not text.strip():
        return None

    lang = _detect_language(text)

    return {
        'product_name': _extract_product_name(text, lang),
        'cas_id_number': _extract_cas_number(text, lang),
        'molecular_formula': _extract_molecular_formula(text, lang),
        'h_codes': _extract_h_codes(text),
        'density': _extract_density(text, lang),
        'bioaccumulable': _extract_bioaccumulable(text, lang),
        'seveso_list': _extract_seveso(text, lang),
        'is_precursor': _extract_precursor(text, lang),
        'revision_date': _extract_revision_date(text, lang),
        '_text': text,
        '_lang': lang,
    }


# --- Catalog field extraction ---

# Spanish-to-English organ name mapping for white_organ matching
_ORGAN_ES_EN = {
    'sistema nervioso central': 'central nervous system',
    'sistema nervioso': 'nervous system',
    'hígado': 'liver',
    'riñón': 'kidney',
    'riñones': 'kidneys',
    'pulmón': 'lung',
    'pulmones': 'lungs',
    'corazón': 'heart',
    'piel': 'skin',
    'ojos': 'eyes',
    'sangre': 'blood',
    'aparato digestivo': 'digestive system',
    'sistema digestivo': 'digestive system',
    'aparato respiratorio': 'respiratory system',
    'sistema respiratorio': 'respiratory system',
    'médula ósea': 'bone marrow',
    'tiroides': 'thyroid',
    'bazo': 'spleen',
    'sistema inmunitario': 'immune system',
    'sistema reproductor': 'reproductive system',
    'sistema cardiovascular': 'cardiovascular system',
    'huesos': 'bones',
    'dientes': 'teeth',
    'glándula suprarrenal': 'adrenal gland',
    'páncreas': 'pancreas',
    'vejiga': 'bladder',
    'tracto gastrointestinal': 'gastrointestinal tract',
    'sistema endocrino': 'endocrine system',
    'músculo': 'muscle',
    'músculos': 'muscles',
    'cerebro': 'brain',
}


def _extract_iarc(text, entries, lang='es'):
    """Extract IARC group from PDF text. Returns a single PK or None."""
    group_to_pk = {}
    for pk, desc in entries:
        m = re.search(r'Grupo\s+(\d[AB]?)', desc)
        if m:
            group_to_pk[m.group(1)] = pk

    if not group_to_pk:
        return None

    iarc_context = re.search(r'IARC.{0,300}', text, re.DOTALL | re.IGNORECASE)
    if not iarc_context:
        return None

    context = iarc_context.group(0)
    m = re.search(r'(?:Group|Grupo)\s*(1|2A|2B|3|4)', context, re.IGNORECASE)
    if m:
        group = m.group(1).upper()
        return group_to_pk.get(group)

    return None


def _extract_imdg(text, entries, lang='es'):
    """Extract IMDG class from section 14. Returns a single PK or None."""
    class_to_pk = {}
    for idx, (pk, desc) in enumerate(entries, start=1):
        class_to_pk[idx] = pk

    if lang == 'es':
        m = re.search(r'14\.3\s+Clas[es]*\s+(\d)', text)
    else:
        m = re.search(r'14\.3\s+(?:Transport\s+hazard\s+)?[Cc]lass\s+(\d)', text)
    if m:
        cls = int(m.group(1))
        return class_to_pk.get(cls)

    return None


def _extract_white_organ(text, entries, lang='es'):
    """Extract target organs (M2M). Returns list of PKs."""
    sec_pattern = _section_pattern(11, lang)
    sec_end_pattern = _section_pattern(12, lang)
    section11 = re.search(
        r'(?:' + sec_pattern + r'|11\.\s*Informaci[óo]n\s+toxicol[óo]gica'
        r'|11\.\s*Toxicological\s+information)'
        r'(.+?)(?:' + sec_end_pattern + r'|12\.\s)',
        text, re.DOTALL | re.IGNORECASE
    )
    search_text = section11.group(1) if section11 else text

    matched_pks = []
    for pk, desc in entries:
        desc_lower = desc.lower().strip()
        if re.search(re.escape(desc_lower), search_text, re.IGNORECASE):
            matched_pks.append(pk)
            continue
        en_name = _ORGAN_ES_EN.get(desc_lower)
        if en_name and re.search(re.escape(en_name), search_text, re.IGNORECASE):
            matched_pks.append(pk)

    return matched_pks


def _extract_ue_code(text, entries, lang='es'):
    """Extract EU hazard statement codes (M2M). Returns list of PKs."""
    code_to_pk = {}
    for pk, desc in entries:
        m = re.search(r'EUH\s*(\d{3}[A-Z]?)', desc)
        if m:
            code_to_pk[m.group(1)] = pk

    if not code_to_pk:
        return []

    found_codes = set(re.findall(r'EUH\s*(\d{3}[A-Z]?)', text))
    matched_pks = []
    for code in found_codes:
        if code in code_to_pk:
            matched_pks.append(code_to_pk[code])

    return sorted(matched_pks)


def _extract_nfpa(text, entries, lang='es'):
    """Extract NFPA flammable liquid classification (M2M). Returns list of PKs."""
    class_to_pk = {}
    for pk, desc in entries:
        m = re.search(r'clase\s+(I{1,3}[AB]?)', desc, re.IGNORECASE)
        if m:
            class_to_pk[m.group(1).upper()] = pk

    if not class_to_pk:
        return []

    fp = None
    if lang == 'es':
        fp_pattern = r'Punto\s+de\s+inflamaci[óo]n\s*[:\s]*(-?[\d]+[.,]?[\d]*)\s*[°ºo]?\s*C'
    else:
        fp_pattern = r'Flash\s+point\s*[:\s]*(-?[\d]+[.,]?[\d]*)\s*[°ºo]?\s*C'
    m = re.search(fp_pattern, text, re.IGNORECASE)
    if m:
        fp = float(m.group(1).replace(',', '.'))

    if fp is None:
        return []

    bp = None
    if lang == 'es':
        bp_pattern = r'Punto\s+de\s+ebullici[óo]n\s*[:\s]*(-?[\d]+[.,]?[\d]*)\s*[°ºo]?\s*C'
    else:
        bp_pattern = r'Boiling\s+point\s*[:\s]*(-?[\d]+[.,]?[\d]*)\s*[°ºo]?\s*C'
    m = re.search(bp_pattern, text, re.IGNORECASE)
    if m:
        bp = float(m.group(1).replace(',', '.'))

    # NFPA 30 classification
    nfpa_class = None
    if fp < 22.8:
        if bp is not None and bp < 37.8:
            nfpa_class = 'IA'
        else:
            nfpa_class = 'IB'
    elif fp < 37.8:
        nfpa_class = 'IC'
    elif fp < 60:
        nfpa_class = 'II'
    elif fp < 93.3:
        nfpa_class = 'IIIA'
    else:
        nfpa_class = 'IIIB'

    pk = class_to_pk.get(nfpa_class)
    return [pk] if pk else []


def _extract_storage_class(text, entries, lang='es'):
    """Extract storage class (M2M). Returns list of PKs."""
    code_to_pk = {}
    for pk, desc in entries:
        m = re.match(r'^([\d.]+\s*[A-C]?)', desc.strip())
        if m:
            code = re.sub(r'\s+', '', m.group(1)).strip()
            code_to_pk[code] = pk

    if not code_to_pk:
        return []

    if lang == 'es':
        sc_pattern = r'Clase\s+de\s+almacenamiento\s+([\d.]+\s*[A-C]?)'
    else:
        sc_pattern = r'Storage\s+class\s+([\d.]+\s*[A-C]?)'
    m = re.search(sc_pattern, text, re.IGNORECASE)
    if not m:
        return []

    found_code = re.sub(r'\s+', '', m.group(1)).strip()

    if found_code in code_to_pk:
        return [code_to_pk[found_code]]

    if re.match(r'^\d+$', found_code):
        matched = []
        for code, pk in code_to_pk.items():
            if code.rstrip('ABC') == found_code:
                matched.append(pk)
        return sorted(matched)

    return []


def _extract_precursor_type(text, entries, lang='es'):
    """Extract precursor type (FK). Returns a single PK or None."""
    list_to_pk = {}
    for pk, desc in entries:
        m = re.search(r'Lista\s+(\d)', desc)
        if m:
            list_to_pk[m.group(1)] = pk

    if not list_to_pk:
        return None

    precursor_context = re.search(
        r'[Pp]recursor.{0,500}', text, re.DOTALL
    )
    if not precursor_context:
        return None

    context = precursor_context.group(0)
    m = re.search(r'[Ll]ista\s+(\d)', context)
    if m:
        return list_to_pk.get(m.group(1))

    return None


def extract_catalog_fields(text, catalogs, lang='es'):
    """Extract catalog-linked fields from PDF text.

    Args:
        text: Full extracted PDF text.
        catalogs: dict mapping catalog keys to lists of (pk, description) tuples.
            Expected keys: 'IARC', 'IDMG', 'white_organ', 'ue_code', 'nfpa',
            'storage_class', 'Precursor'.
        lang: SDS language ('es' or 'en').

    Returns:
        dict with keys: iarc, imdg, white_organ, ue_code, nfpa, storage_class,
        precursor_type. FK fields are single PK or None; M2M fields are lists of PKs.
    """
    return {
        'iarc': _extract_iarc(text, catalogs.get('IARC', []), lang),
        'imdg': _extract_imdg(text, catalogs.get('IDMG', []), lang),
        'white_organ': _extract_white_organ(text, catalogs.get('white_organ', []), lang),
        'ue_code': _extract_ue_code(text, catalogs.get('ue_code', []), lang),
        'nfpa': _extract_nfpa(text, catalogs.get('nfpa', []), lang),
        'storage_class': _extract_storage_class(text, catalogs.get('storage_class', []), lang),
        'precursor_type': _extract_precursor_type(text, catalogs.get('Precursor', []), lang),
    }
