from openpyxl import Workbook
from io import BytesIO, StringIO
from pyexcel_io.manager import get_io
from pyexcel_io import save_data
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from django.utils.translation import gettext as _


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
