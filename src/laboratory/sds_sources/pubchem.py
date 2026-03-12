import json
import logging
import os
import re
import tempfile
from datetime import datetime

from .base import SDSSource

logger = logging.getLogger("organilab")

BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
VIEW_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view"

# PubChem rate limit: max 5 requests/second
# Callers should enforce delay between calls


class PubChemSource(SDSSource):
    """Download GHS safety data from PubChem and generate an SDS PDF.

    PubChem does not serve SDS PDFs directly, but provides comprehensive
    GHS classification data (H-codes, P-codes, signal words, pictograms).
    This source extracts that data and generates a basic SDS PDF.
    """

    name = "pubchem"
    timeout = 20

    def search(self, cas_number, substance_name="", pdf_path=None):
        if not cas_number:
            return None

        cid = self._get_cid(cas_number)
        if not cid and substance_name:
            cid = self._get_cid(substance_name)
        if not cid:
            return None

        ghs_data = self._get_ghs_data(cid)
        if not ghs_data:
            return None

        properties = self._get_properties(cid)

        return {
            'url': f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
            'cid': cid,
            'ghs': ghs_data,
            'properties': properties or {},
            'metadata': {
                'source': 'PubChem',
                'cid': cid,
                'cas': cas_number,
                'retrieved': datetime.now().strftime('%Y-%m-%d'),
            },
        }

    def download(self, search_result, dest_path):
        """Generate an SDS PDF from PubChem GHS data."""
        if not search_result or 'ghs' not in search_result:
            return False
        try:
            self._generate_sds_pdf(search_result, dest_path)
            return os.path.exists(dest_path) and os.path.getsize(dest_path) > 0
        except Exception as e:
            logger.warning("[pubchem] PDF generation error: %s", e)
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return False

    def _get_cid(self, identifier):
        url = f"{BASE_URL}/compound/name/{identifier}/cids/JSON"
        try:
            session = self._get_session()
            r = session.get(url, timeout=self.timeout)
            if r.status_code == 200:
                data = r.json()
                cids = data.get('IdentifierList', {}).get('CID', [])
                return cids[0] if cids else None
        except Exception as e:
            logger.debug("[pubchem] CID lookup failed for %s: %s", identifier, e)
        return None

    def _get_ghs_data(self, cid):
        url = f"{VIEW_URL}/data/compound/{cid}/JSON?heading=GHS+Classification"
        try:
            session = self._get_session()
            r = session.get(url, timeout=self.timeout)
            if r.status_code != 200:
                return None
            data = r.json()
            return self._parse_ghs(data)
        except Exception as e:
            logger.debug("[pubchem] GHS data failed for CID %s: %s", cid, e)
            return None

    def _get_properties(self, cid):
        url = (
            f"{BASE_URL}/compound/cid/{cid}/property/"
            "MolecularFormula,MolecularWeight,IUPACName/JSON"
        )
        try:
            session = self._get_session()
            r = session.get(url, timeout=self.timeout)
            if r.status_code == 200:
                props = r.json().get('PropertyTable', {}).get('Properties', [{}])
                return props[0] if props else {}
        except Exception:
            pass
        return {}

    def _parse_ghs(self, data):
        h_codes = set()
        p_codes = set()
        signal_word = None
        pictogram_urls = set()

        def _walk(obj):
            nonlocal signal_word
            if isinstance(obj, dict):
                if 'StringWithMarkup' in obj:
                    for swm in obj['StringWithMarkup']:
                        s = swm.get('String', '')
                        # H-codes: H225, H319, etc.
                        for m in re.finditer(r'\bH\d{3}[A-Za-z]?\b', s):
                            h_codes.add(m.group())
                        # P-codes: P210, P303+P361+P353, etc.
                        for m in re.finditer(r'\bP\d{3}(?:\+P\d{3})*\b', s):
                            p_codes.add(m.group())
                        if s in ('Danger', 'Warning'):
                            signal_word = s
                        if 'Markup' in swm:
                            for markup in swm['Markup']:
                                if markup.get('Type') == 'Icon' and 'URL' in markup:
                                    pictogram_urls.add(markup['URL'])
                for v in obj.values():
                    _walk(v)
            elif isinstance(obj, list):
                for item in obj:
                    _walk(item)

        _walk(data)
        if not h_codes and not signal_word:
            return None

        return {
            'signal_word': signal_word,
            'h_codes': sorted(h_codes),
            'p_codes': sorted(p_codes),
            'pictogram_urls': sorted(pictogram_urls),
        }

    def _generate_sds_pdf(self, search_result, dest_path):
        """Generate a basic SDS PDF from PubChem data using reportlab or fpdf.

        Falls back to a simple text-based PDF if reportlab is not available.
        """
        ghs = search_result['ghs']
        props = search_result.get('properties', {})
        meta = search_result.get('metadata', {})

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            self._generate_with_reportlab(dest_path, ghs, props, meta)
        except ImportError:
            self._generate_simple_pdf(dest_path, ghs, props, meta)

    def _generate_with_reportlab(self, dest_path, ghs, props, meta):
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(dest_path, pagesize=letter, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('SDSTitle', parent=styles['Title'], fontSize=14, spaceAfter=6)
        heading_style = ParagraphStyle('SDSHeading', parent=styles['Heading2'], fontSize=11, textColor=colors.darkblue, spaceBefore=10, spaceAfter=4)
        normal_style = styles['Normal']

        elements = []
        cas = meta.get('cas', 'N/A')
        name = props.get('IUPACName', cas)
        date = meta.get('retrieved', '')

        elements.append(Paragraph(f"Hoja de Datos de Seguridad (SDS)", title_style))
        elements.append(Paragraph(f"Fuente: PubChem (CID: {meta.get('cid', 'N/A')}) — Fecha: {date}", normal_style))
        elements.append(Spacer(1, 10))

        # Section 1: Identification
        elements.append(Paragraph("Sección 1: Identificación", heading_style))
        elements.append(Paragraph(f"<b>Nombre IUPAC:</b> {name}", normal_style))
        elements.append(Paragraph(f"<b>Número CAS:</b> {cas}", normal_style))
        if props.get('MolecularFormula'):
            elements.append(Paragraph(f"<b>Fórmula molecular:</b> {props['MolecularFormula']}", normal_style))
        if props.get('MolecularWeight'):
            elements.append(Paragraph(f"<b>Peso molecular:</b> {props['MolecularWeight']} g/mol", normal_style))

        # Section 2: Hazards Identification
        elements.append(Paragraph("Sección 2: Identificación de Peligros (GHS)", heading_style))
        if ghs.get('signal_word'):
            elements.append(Paragraph(f"<b>Palabra de advertencia:</b> {ghs['signal_word']}", normal_style))
        if ghs.get('h_codes'):
            elements.append(Paragraph(f"<b>Indicaciones de peligro:</b> {', '.join(ghs['h_codes'])}", normal_style))
        if ghs.get('p_codes'):
            elements.append(Paragraph(f"<b>Consejos de prudencia:</b> {', '.join(ghs['p_codes'])}", normal_style))

        # Disclaimer
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            "<i>Este documento fue generado automáticamente a partir de datos de PubChem "
            "(National Center for Biotechnology Information). No sustituye la hoja de seguridad "
            "del fabricante. Consulte la SDS del proveedor para información completa.</i>",
            ParagraphStyle('Disclaimer', parent=normal_style, fontSize=8, textColor=colors.gray)
        ))

        doc.build(elements)

    def _generate_simple_pdf(self, dest_path, ghs, props, meta):
        """Minimal PDF generation without external dependencies."""
        cas = meta.get('cas', 'N/A')
        name = props.get('IUPACName', cas)
        date = meta.get('retrieved', '')

        lines = [
            "HOJA DE DATOS DE SEGURIDAD (SDS)",
            f"Fuente: PubChem (CID: {meta.get('cid', 'N/A')}) - Fecha: {date}",
            "",
            "SECCION 1: IDENTIFICACION",
            f"Nombre IUPAC: {name}",
            f"Numero CAS: {cas}",
        ]
        if props.get('MolecularFormula'):
            lines.append(f"Formula molecular: {props['MolecularFormula']}")
        if props.get('MolecularWeight'):
            lines.append(f"Peso molecular: {props['MolecularWeight']} g/mol")
        lines.append("")
        lines.append("SECCION 2: IDENTIFICACION DE PELIGROS (GHS)")
        if ghs.get('signal_word'):
            lines.append(f"Palabra de advertencia: {ghs['signal_word']}")
        if ghs.get('h_codes'):
            lines.append(f"Indicaciones de peligro: {', '.join(ghs['h_codes'])}")
        if ghs.get('p_codes'):
            lines.append(f"Consejos de prudencia: {', '.join(ghs['p_codes'])}")
        lines.append("")
        lines.append("NOTA: Documento generado automaticamente desde PubChem.")
        lines.append("No sustituye la SDS del fabricante.")

        # Write a minimal valid PDF
        _write_text_pdf(dest_path, lines)


def _write_text_pdf(path, lines):
    """Write a minimal valid PDF with text content. No external deps required."""
    text_lines = []
    y = 750
    for line in lines:
        if not line:
            y -= 14
            continue
        safe = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        text_lines.append(f"BT /F1 10 Tf 50 {y} Td ({safe}) Tj ET")
        y -= 14
        if y < 50:
            break

    stream = "\n".join(text_lines)
    stream_bytes = stream.encode('latin-1', errors='replace')

    objects = []
    # Obj 1: Catalog
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    # Obj 2: Pages
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    # Obj 3: Page
    objects.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    # Obj 4: Stream
    objects.append(
        f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode()
        + stream_bytes
        + b"\nendstream\nendobj\n"
    )
    # Obj 5: Font
    objects.append(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    with open(path, 'wb') as f:
        f.write(b"%PDF-1.4\n")
        offsets = []
        for obj in objects:
            offsets.append(f.tell())
            f.write(obj)
        xref_pos = f.tell()
        f.write(b"xref\n")
        f.write(f"0 {len(objects) + 1}\n".encode())
        f.write(b"0000000000 65535 f \n")
        for offset in offsets:
            f.write(f"{offset:010d} 00000 n \n".encode())
        f.write(b"trailer\n")
        f.write(f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode())
        f.write(b"startxref\n")
        f.write(f"{xref_pos}\n".encode())
        f.write(b"%%EOF\n")
