import re
import logging
import signal

logger = logging.getLogger(__name__)

PDF_EXTRACT_TIMEOUT = 30


class _PdfTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise _PdfTimeout()


UNICODE_SUBSCRIPT_MAP = {
    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
    '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
}


def _normalize_subscripts(text):
    for uni, digit in UNICODE_SUBSCRIPT_MAP.items():
        text = text.replace(uni, digit)
    return text


def _extract_cas_number(text):
    # Only search section 1 (before section 2) to avoid matching CAS numbers
    # from composition tables in section 3.
    section1_match = re.search(
        r'(?:SECCI[ÓO]N\s*2|Section\s*2)\b', text, re.IGNORECASE
    )
    section1_text = text[:section1_match.start()] if section1_match else text

    patterns = [
        r'CAS[-\s]*No\.?\s*[:\.]?\s*(\d{1,7}-\d{2}-\d)',
        r'N[ºúu](?:mero)?\s*CAS\s*\[?\s*(\d{1,7}-\d{2}-\d)',
        r'\bCAS\s+(\d{1,7}-\d{2}-\d)',
    ]
    for pattern in patterns:
        match = re.search(pattern, section1_text)
        if match:
            return match.group(1)
    return None


def _extract_molecular_formula(text):
    normalized = _normalize_subscripts(text)

    # Merck/Sigma-Aldrich format: "Formula CH3COCH3 C3H6O (Hill)"
    # Extract the Hill notation (last formula token before "(Hill)")
    hill_match = re.search(
        r'([A-Z][A-Za-z0-9]+)\s*\(Hill\)', normalized
    )
    if hill_match:
        formula = hill_match.group(1)
        if re.match(r'^[A-Z][A-Za-z0-9]*$', formula) and len(formula) >= 2:
            # For hydrates like "C12H8N2 · H2O  H2O (Hill)", the Hill match
            # picks up the water of crystallization. Extract the real formula.
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

    # Other formats: "Fórmula molecular Cd O4 S" or "Molecular Formula C3 H8 O"
    patterns = [
        r'[Ff][óo]rmula\s+molecular\s+([A-Za-z0-9\s]+?)(?:\n|$|\(|\.[\s\n])',
        r'(?:Molecular\s+)?[Ff]ormula\s+([A-Za-z0-9\s]+?)(?:\n|$|\(|\.[\s\n])',
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


def _extract_density(text):
    patterns = [
        r'[Dd]ensidad\s+relativa\s+([\d]+[.,][\d]+)',
        r'[Rr]elative\s+density\s+([\d]+[.,][\d]+)',
        r'[Ss]pecific\s+[Gg]ravity\s+([\d]+[.,][\d]+)',
        r'[Dd]ensidad\s+([\d]+[.,][\d]+)',
        r'[Dd]ensity\s+([\d]+[.,][\d]+)',
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


def _extract_bioaccumulable(text):
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


def _extract_seveso(text):
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


def _extract_precursor(text):
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

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    try:
        signal.alarm(PDF_EXTRACT_TIMEOUT)
        with pdfplumber.open(pdf_path) as pdf:
            text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
        signal.alarm(0)
    except _PdfTimeout:
        logger.warning("Timeout reading PDF: %s", pdf_path)
        return None
    except Exception:
        logger.exception("Failed to read PDF: %s", pdf_path)
        return None
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    if not text.strip():
        return None

    return {
        'cas_id_number': _extract_cas_number(text),
        'molecular_formula': _extract_molecular_formula(text),
        'h_codes': _extract_h_codes(text),
        'density': _extract_density(text),
        'bioaccumulable': _extract_bioaccumulable(text),
        'seveso_list': _extract_seveso(text),
        'is_precursor': _extract_precursor(text),
        '_text': text,
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


def _extract_iarc(text, entries):
    """Extract IARC group from PDF text. Returns a single PK or None."""
    # Build map from group identifier to PK: {"1": pk, "2A": pk, ...}
    group_to_pk = {}
    for pk, desc in entries:
        m = re.search(r'Grupo\s+(\d[AB]?)', desc)
        if m:
            group_to_pk[m.group(1)] = pk

    if not group_to_pk:
        return None

    # Search near IARC keyword
    iarc_context = re.search(r'IARC.{0,300}', text, re.DOTALL | re.IGNORECASE)
    if not iarc_context:
        return None

    context = iarc_context.group(0)
    m = re.search(r'(?:Group|Grupo)\s*(1|2A|2B|3|4)', context, re.IGNORECASE)
    if m:
        group = m.group(1).upper()
        return group_to_pk.get(group)

    return None


def _extract_imdg(text, entries):
    """Extract IMDG class from section 14. Returns a single PK or None."""
    # Entries in PK order correspond to IMDG classes 1-9
    class_to_pk = {}
    for idx, (pk, desc) in enumerate(entries, start=1):
        class_to_pk[idx] = pk

    # Search section 14 for class number
    m = re.search(r'14\.3\s+Clas[es]*\s+(\d)', text)
    if m:
        cls = int(m.group(1))
        return class_to_pk.get(cls)

    # Also try English format
    m = re.search(r'14\.3\s+(?:Transport\s+hazard\s+)?[Cc]lass\s+(\d)', text)
    if m:
        cls = int(m.group(1))
        return class_to_pk.get(cls)

    return None


def _extract_white_organ(text, entries):
    """Extract target organs (M2M). Returns list of PKs."""
    # Find section 11 context for target organs
    section11 = re.search(
        r'(?:SECCI[ÓO]N\s*11|Section\s*11|11\.\s*Informaci[óo]n\s+toxicol[óo]gica'
        r'|11\.\s*Toxicological\s+information)'
        r'(.+?)(?:SECCI[ÓO]N\s*12|Section\s*12|12\.\s)',
        text, re.DOTALL | re.IGNORECASE
    )
    search_text = section11.group(1) if section11 else text

    matched_pks = []
    for pk, desc in entries:
        desc_lower = desc.lower().strip()
        # Search for the description directly (case-insensitive)
        if re.search(re.escape(desc_lower), search_text, re.IGNORECASE):
            matched_pks.append(pk)
            continue
        # Try English translation
        en_name = _ORGAN_ES_EN.get(desc_lower)
        if en_name and re.search(re.escape(en_name), search_text, re.IGNORECASE):
            matched_pks.append(pk)

    return matched_pks


def _extract_ue_code(text, entries):
    """Extract EU hazard statement codes (M2M). Returns list of PKs."""
    # Build map from EUH code number to PK
    code_to_pk = {}
    for pk, desc in entries:
        m = re.search(r'EUH\s*(\d{3}[A-Z]?)', desc)
        if m:
            code_to_pk[m.group(1)] = pk

    if not code_to_pk:
        return []

    # Find all EUH codes in PDF text
    found_codes = set(re.findall(r'EUH\s*(\d{3}[A-Z]?)', text))
    matched_pks = []
    for code in found_codes:
        if code in code_to_pk:
            matched_pks.append(code_to_pk[code])

    return sorted(matched_pks)


def _extract_nfpa(text, entries):
    """Extract NFPA flammable liquid classification (M2M). Returns list of PKs."""
    # Build map from class label to PK
    class_to_pk = {}
    for pk, desc in entries:
        m = re.search(r'clase\s+(I{1,3}[AB]?)', desc, re.IGNORECASE)
        if m:
            class_to_pk[m.group(1).upper()] = pk

    if not class_to_pk:
        return []

    # Extract flash point from section 9
    fp = None
    fp_patterns = [
        r'(?:Punto\s+de\s+inflamaci[óo]n|Flash\s+point)\s*[:\s]*(-?[\d]+[.,]?[\d]*)\s*[°ºo]?\s*C',
    ]
    for pat in fp_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            fp = float(m.group(1).replace(',', '.'))
            break

    if fp is None:
        return []

    # Extract boiling point from section 9
    bp = None
    bp_patterns = [
        r'(?:Punto\s+de\s+ebullici[óo]n|Boiling\s+point)\s*[:\s]*(-?[\d]+[.,]?[\d]*)\s*[°ºo]?\s*C',
    ]
    for pat in bp_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            bp = float(m.group(1).replace(',', '.'))
            break

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


def _extract_storage_class(text, entries):
    """Extract storage class (M2M). Returns list of PKs."""
    # Build map from normalized code to PK
    code_to_pk = {}
    for pk, desc in entries:
        m = re.match(r'^([\d.]+\s*[A-C]?)', desc.strip())
        if m:
            code = re.sub(r'\s+', '', m.group(1)).strip()
            code_to_pk[code] = pk

    if not code_to_pk:
        return []

    # Search PDF for storage class
    m = re.search(
        r'(?:Clase\s+de\s+almacenamiento|Storage\s+class)\s+([\d.]+\s*[A-C]?)',
        text, re.IGNORECASE
    )
    if not m:
        return []

    found_code = re.sub(r'\s+', '', m.group(1)).strip()

    # Exact match first
    if found_code in code_to_pk:
        return [code_to_pk[found_code]]

    # If no exact match, try without trailing letter (e.g., "3" matches "3A" or "3B")
    # But only if the found code is a bare number
    if re.match(r'^\d+$', found_code):
        matched = []
        for code, pk in code_to_pk.items():
            if code.rstrip('ABC') == found_code:
                matched.append(pk)
        return sorted(matched)

    return []


def _extract_precursor_type(text, entries):
    """Extract precursor type (FK). Returns a single PK or None."""
    # Build map from list number to PK
    list_to_pk = {}
    for pk, desc in entries:
        m = re.search(r'Lista\s+(\d)', desc)
        if m:
            list_to_pk[m.group(1)] = pk

    if not list_to_pk:
        return None

    # Search near "precursor" context
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


def extract_catalog_fields(text, catalogs):
    """Extract catalog-linked fields from PDF text.

    Args:
        text: Full extracted PDF text.
        catalogs: dict mapping catalog keys to lists of (pk, description) tuples.
            Expected keys: 'IARC', 'IDMG', 'white_organ', 'ue_code', 'nfpa',
            'storage_class', 'Precursor'.

    Returns:
        dict with keys: iarc, imdg, white_organ, ue_code, nfpa, storage_class,
        precursor_type. FK fields are single PK or None; M2M fields are lists of PKs.
    """
    return {
        'iarc': _extract_iarc(text, catalogs.get('IARC', [])),
        'imdg': _extract_imdg(text, catalogs.get('IDMG', [])),
        'white_organ': _extract_white_organ(text, catalogs.get('white_organ', [])),
        'ue_code': _extract_ue_code(text, catalogs.get('ue_code', [])),
        'nfpa': _extract_nfpa(text, catalogs.get('nfpa', [])),
        'storage_class': _extract_storage_class(text, catalogs.get('storage_class', [])),
        'precursor_type': _extract_precursor_type(text, catalogs.get('Precursor', [])),
    }
