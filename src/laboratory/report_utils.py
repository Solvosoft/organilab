import re
from io import BytesIO, StringIO

import ezodf
import xlwt
from django.utils.translation import gettext as _
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, NamedStyle, PatternFill, Side
from openpyxl.utils import get_column_letter
from pyexcel_io import save_data
from pyexcel_io.manager import get_io


class ExcelGraphBuilder:
    def __init__(self):
        self.wb = Workbook()
        self.ws = self.wb.active
        self.x = 1
        self.y = 1
        self.row_max = 0

    def add_table(self, data, title):

        self.ws.append([title])
        self.ws[f"A1"].alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )

        self.row_max += 1

        for row in data:
            self.ws.append(row)
            self.row_max += 1
        col_count = len(data[0])
        cell = self.ws.cell(self.x, self.y)
        mcel = self.ws.cell(self.x, self.y + col_count)
        scell = cell.column_letter + str(cell.row)
        self.ws.merge_cells("%s:%s" % (scell, mcel.column_letter + str(mcel.row)))

    def save(self, output=None):
        if output is None:
            output = BytesIO()
        self.wb.save(output)
        return output

    def save_ods(self, data, format_type="ods"):
        """Hoja de cálculo de un reporte (XLS, XLSX u ODS) a partir de sus filas.

        Las filas se escriben tal cual (mismos valores, mismo orden) y se les
        da estilo según su rol, que se deduce de su forma: ver
        :func:`infer_spreadsheet_roles`.
        """
        if format_type in SPREADSHEET_WRITERS and isinstance(data, list):
            rows = infer_spreadsheet_roles(data)
            headers = [i for i, (role, _cells) in enumerate(rows) if role == "header"]
            options = {"freeze_row": headers[0] + 1 if len(headers) == 1 else None}
            title = rows[0][1][0] if rows and rows[0][0] == "title" else ""
            return write_spreadsheet([(sheet_name(title), rows, options)], format_type)
        io = get_io(format_type)
        save_data(io, data, format_type)
        return io

    def safe_bool(self, value):
        if value in (True, 1, "1", "True", "true"):
            return _("Yes")
        return _("No")

    def autosize_columns(self, max_width=60):
        for col in range(1, self.ws.max_column + 1):
            max_len = 0
            col_letter = get_column_letter(col)
            for row in range(1, self.ws.max_row + 1):
                val = self.ws.cell(row=row, column=col).value
                if val is None:
                    continue
                max_len = max(max_len, len(str(val)))
            self.ws.column_dimensions[col_letter].width = min(max_len + 2, max_width)

    def style_header(self):
        header_font = Font(bold=True)
        for cell in self.ws[1]:
            cell.font = header_font
            cell.alignment = Alignment(vertical="center")
        self.ws.auto_filter.ref = self.ws.dimensions

    def format_border_cell(self, max_row, col_index):

        for row in range(1, max_row):
            for col in range(1, col_index + 1):
                self.ws.cell(row, col).border = Border(
                    top=Side(border_style="thin", color="FF000000"),
                    right=Side(border_style="thin", color="FF000000"),
                    bottom=Side(border_style="thin", color="FF000000"),
                    left=Side(border_style="thin", color="FF000000"),
                )


# --- Estilo común de las hojas de cálculo de los reportes -------------------
#
# Cada hoja es ``(nombre, filas, opciones)`` y cada fila ``(rol, celdas)``. El
# rol dice cómo se dibuja; XLSX (openpyxl), XLS (xlwt) y ODS (ezodf) lo
# traducen a su librería con los mismos colores, así los tres formatos se ven
# igual. Opciones: ``freeze_row`` (filas fijas arriba, con autofiltro en XLSX)
# y ``max_width`` (ancho máximo de columna en caracteres).

BRAND = "1F4E79"
BORDER_COLOR = "BFBFBF"
RISK_COLORS = {"risk_high": ("FFC7CE", "9C0006"), "risk_low": ("C6EFCE", "006100")}


def _as_cells(row):
    if row is None:
        return []
    if isinstance(row, (list, tuple)):
        return list(row)
    return [row]


def _is_empty(value):
    return value is None or value == ""


def infer_spreadsheet_roles(data):
    """Rol de cada fila de un reporte plano, deducido de su forma.

    Los reportes arman sus filas como ``[[nombre], [encabezados], filas...]``,
    a veces en secciones (``[laboratorio]``, encabezados, filas) y con filas
    de dato/valor antes de la tabla. Así:

    - fila vacía: ``blank``;
    - una sola celda: ``title`` si es la primera, si no ``section``;
    - en cada tramo de filas de varias celdas, las más cortas que la más ancha
      al principio son ``label`` (dato: valor), la primera de ancho completo es
      ``header`` y el resto ``cell``.

    Solo decide el estilo: las celdas no cambian.
    """
    rows = [_as_cells(row) for row in data]
    roles = [None] * len(rows)
    i = 0
    while i < len(rows):
        cells = rows[i]
        if all(_is_empty(c) for c in cells):
            roles[i] = "blank"
            i += 1
            continue
        if len(cells) == 1:
            roles[i] = "title" if i == 0 else "section"
            i += 1
            continue
        end = i
        while end < len(rows) and len(rows[end]) > 1 and not all(_is_empty(c) for c in rows[end]):
            end += 1
        width = max(len(rows[j]) for j in range(i, end))
        j = i
        while j < end and len(rows[j]) < width:
            roles[j] = "label"
            j += 1
        if j < end:
            roles[j] = "header"
            for k in range(j + 1, end):
                roles[k] = "cell"
        i = end
    return list(zip(roles, rows))


def sheet_name(title, default="Reporte"):
    """Nombre válido de hoja: sin ``[]:*?/\\`` y con 31 caracteres como máximo."""
    name = re.sub(r"[\[\]:*?/\\]", " ", str(title or "")).strip()[:31].strip()
    return name or default


def spreadsheet_cell_style(role, col, value):
    """Estilo de una celda según el rol de su fila (y su columna)."""
    if role == "label":
        return "label" if col == 0 else "text"
    if role == "risk":
        if col:
            return "cell"
        return "risk_high" if "mayor" in str(value) else "risk_low"
    if role == "blank":
        return "text"
    return role


def spreadsheet_column_widths(rows, max_width=50, min_width=10):
    """Ancho de cada columna en caracteres; títulos y secciones no cuentan."""
    widths = {}
    for role, cells in rows:
        if role in ("title", "section"):
            continue
        for col, value in enumerate(cells):
            text = "" if value is None else str(value)
            widths[col] = max(widths.get(col, min_width), min(len(text) + 2, max_width))
    return widths


def _xlsx_styles():
    side = Side(border_style="thin", color=BORDER_COLOR)
    border = Border(top=side, bottom=side, left=side, right=side)
    wrap = Alignment(vertical="top", wrap_text=True)
    font = "Arial"
    styles = {
        "title": {"font": Font(name=font, bold=True, size=14, color=BRAND)},
        "section": {"font": Font(name=font, bold=True, size=11, color=BRAND)},
        "label": {"font": Font(name=font, bold=True)},
        "text": {"font": Font(name=font)},
        "header": {
            "font": Font(name=font, bold=True, color="FFFFFF"),
            "fill": PatternFill("solid", fgColor=BRAND),
            "alignment": Alignment(horizontal="center", vertical="center", wrap_text=True),
            "border": border,
        },
        "cell": {"font": Font(name=font), "alignment": wrap, "border": border},
    }
    for name, (fill, color) in RISK_COLORS.items():
        styles[name] = {
            "font": Font(name=font, bold=True, color=color),
            "fill": PatternFill("solid", fgColor=fill),
            "alignment": wrap,
            "border": border,
        }
    return styles


def write_xlsx(sheets):
    wb = Workbook()
    wb.remove(wb.active)
    # Estilos con nombre: se registran una vez y cada celda solo los referencia
    # (asignar fuente, borde y relleno celda por celda era 10 veces más lento).
    for name, attrs in _xlsx_styles().items():
        style = NamedStyle(name="report_" + name)
        for attr, value in attrs.items():
            setattr(style, attr, value)
        wb.add_named_style(style)
    for name, rows, options in sheets:
        ws = wb.create_sheet(name)
        for role, cells in rows:
            ws.append(cells)
            row = ws.max_row
            for col, value in enumerate(cells):
                ws.cell(row, col + 1).style = "report_" + spreadsheet_cell_style(role, col, value)
        for col, width in spreadsheet_column_widths(rows, options.get("max_width", 50)).items():
            ws.column_dimensions[get_column_letter(col + 1)].width = width
        freeze = options.get("freeze_row")
        if freeze and len(rows) > freeze:
            ws.freeze_panes = "A%d" % (freeze + 1)
            ws.auto_filter.ref = "A%d:%s%d" % (
                freeze, get_column_letter(len(rows[freeze - 1][1])), ws.max_row
            )
        # Al imprimir: horizontal y todas las columnas en el ancho de la página.
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
    output = BytesIO()
    wb.save(output)
    return output


def _xls_styles(wb):
    # xlwt solo dibuja colores de su paleta: se redefinen casillas libres.
    palette = {
        "brand": BRAND,
        "border": BORDER_COLOR,
        "risk_high_fill": RISK_COLORS["risk_high"][0],
        "risk_high_font": RISK_COLORS["risk_high"][1],
        "risk_low_fill": RISK_COLORS["risk_low"][0],
        "risk_low_font": RISK_COLORS["risk_low"][1],
    }
    for index, (name, rgb) in enumerate(palette.items(), start=0x21):
        xlwt.add_palette_colour("report_" + name, index)
        wb.set_colour_RGB(index, *bytes.fromhex(rgb))
    borders = (
        "borders: left thin, right thin, top thin, bottom thin, "
        "left_colour report_border, right_colour report_border, "
        "top_colour report_border, bottom_colour report_border;"
    )
    styles = {
        "title": xlwt.easyxf("font: bold on, height 280, colour report_brand;"),
        "section": xlwt.easyxf("font: bold on, height 220, colour report_brand;"),
        "label": xlwt.easyxf("font: bold on;"),
        "text": xlwt.easyxf(""),
        "header": xlwt.easyxf(
            "font: bold on, colour white; pattern: pattern solid, fore_colour report_brand;"
            "align: wrap on, vert centre, horiz centre; " + borders
        ),
        "cell": xlwt.easyxf("align: wrap on, vert top; " + borders),
    }
    for name in RISK_COLORS:
        styles[name] = xlwt.easyxf(
            "font: bold on, colour report_%s_font; "
            "pattern: pattern solid, fore_colour report_%s_fill; "
            "align: wrap on, vert top; %s" % (name, name, borders)
        )
    return styles


def write_xls(sheets):
    wb = xlwt.Workbook(encoding="utf-8")
    styles = _xls_styles(wb)
    for name, rows, options in sheets:
        ws = wb.add_sheet(name)
        for r, (role, cells) in enumerate(rows):
            for col, value in enumerate(cells):
                style = styles[spreadsheet_cell_style(role, col, value)]
                ws.write(r, col, "" if value is None else value, style)
        for col, width in spreadsheet_column_widths(rows, options.get("max_width", 50)).items():
            ws.col(col).width = 256 * width
        freeze = options.get("freeze_row")
        if freeze and len(rows) > freeze:
            ws.set_panes_frozen(True)
            ws.set_horz_split_pos(freeze)
            ws.set_remove_splits(True)
    output = BytesIO()
    wb.save(output)
    return output


ODS_STYLE = (
    '<style:style xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
    'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
    'style:name="report_%(name)s" style:family="table-cell" style:parent-style-name="Default">'
    '<style:table-cell-properties %(cell)s/>'
    '<style:paragraph-properties %(paragraph)s/>'
    '<style:text-properties %(text)s/>'
    '</style:style>'
)
ODS_COLUMN_STYLE = (
    '<style:style xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
    'style:name="report_col_%(width)s" style:family="table-column">'
    '<style:table-column-properties style:column-width="%(cm).2fcm"/>'
    '</style:style>'
)


def _ods_styles(doc):
    border = 'fo:border="0.06pt solid #%s"' % BORDER_COLOR
    wrap = 'fo:wrap-option="wrap" style:vertical-align="top" ' + border
    bold = 'fo:font-weight="bold" style:font-weight-asian="bold" style:font-weight-complex="bold"'
    styles = {
        "title": ("", "", '%s fo:font-size="14pt" fo:color="#%s"' % (bold, BRAND)),
        "section": ("", "", '%s fo:font-size="11pt" fo:color="#%s"' % (bold, BRAND)),
        "label": ("", "", bold),
        "text": ("", "", ""),
        "header": (
            'fo:background-color="#%s" fo:wrap-option="wrap" style:vertical-align="middle" %s' % (BRAND, border),
            'fo:text-align="center"',
            '%s fo:color="#FFFFFF"' % bold,
        ),
        "cell": (wrap, "", ""),
    }
    for name, (fill, color) in RISK_COLORS.items():
        styles[name] = ('fo:background-color="#%s" %s' % (fill, wrap), "", '%s fo:color="#%s"' % (bold, color))
    for name, (cell, paragraph, text) in styles.items():
        doc.inject_style(ODS_STYLE % {"name": name, "cell": cell, "paragraph": paragraph, "text": text})


def _ods_column_style(doc, width, injected):
    if width not in injected:
        node = ezodf.xmlns.fake_element(ODS_COLUMN_STYLE % {"width": width, "cm": width * 0.21})
        doc.content.automatic_styles.xmlnode.append(node.xmlnode)
        injected.add(width)
    return "report_col_%s" % width


def write_ods(sheets):
    doc = ezodf.newdoc(doctype="ods")
    _ods_styles(doc)
    injected = set()
    for name, rows, options in sheets:
        ncols = max([len(cells) for _role, cells in rows] + [1])
        sheet = ezodf.Sheet(name, size=(max(len(rows), 1), ncols))
        doc.sheets += sheet
        for r, (role, cells) in enumerate(rows):
            for col, value in enumerate(cells):
                cell = sheet[(r, col)]
                if not _is_empty(value):
                    cell.set_value(value)
                cell.style_name = "report_" + spreadsheet_cell_style(role, col, value)
        widths = spreadsheet_column_widths(rows, options.get("max_width", 50))
        for col, width in widths.items():
            sheet.column_info(col).style_name = _ods_column_style(doc, width, injected)
    return BytesIO(doc.tobytes())


SPREADSHEET_WRITERS = {"xlsx": write_xlsx, "xls": write_xls, "ods": write_ods}


def write_spreadsheet(sheets, format_type):
    """Libro con estilo en el formato pedido (``xlsx``, ``xls`` u ``ods``)."""
    return SPREADSHEET_WRITERS[format_type](sheets)
