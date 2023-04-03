from openpyxl import Workbook
from io import BytesIO

class ExcelGraphBuilder:

    def __init__(self):
        self.wb = Workbook()
        self.ws = self.wb.active
        self.x = 1
        self.y = 1
        self.row_max=0

    def add_table(self, data, title):
        start_x = self.x
        self.ws.append([title])
        self.row_max += 1

        for row in data:
            self.ws.append(row)
            self.row_max += 1
        col_count= len(data[0])
        cell = self.ws.cell(self.x, self.y)
        mcel = self.ws.cell(self.x, self.y + col_count)
        scell = cell.column_letter + str(cell.row)
        self.ws.merge_cells('%s:%s' % (
            scell,
            mcel.column_letter + str(mcel.row)
        ))

    def save(self, output=None):
        if output is None:
            output = BytesIO()
        self.wb.save(output)
        return output