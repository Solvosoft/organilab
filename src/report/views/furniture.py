from laboratory.models import Furniture
from report.utils import update_table_report
from django.utils.translation import gettext as _

from report.views.base import get_furniture_queryset_by_filters


def furniture_html(report):
    furniture_list = get_furniture_queryset_by_filters(report)
    rows = ""
    col_list = [_("Code"), _("Object"), _("Type"), _("Quantity"), _("Laboratory"), _("Laboratory Room"), _("Furniture"), _("Shelf")]
    for furniture in furniture_list:
        for shelfobject in furniture.get_objects():
            shelf_unit = shelfobject.get_measurement_unit_display()
            furniture = shelfobject.shelf.furniture
            rows += f'<tr><td>{shelfobject.object.code}</td><td>{shelfobject.object.name}</td><td>{shelfobject.object.get_type_display()}</td>' \
                     f'<td>{shelfobject.quantity} {shelf_unit}</td><td>{shelfobject.in_where_laboratory.name}</td>' \
                     f'<td>{furniture.labroom.name}</td><td>{furniture.name}</td><td>{shelfobject.shelf.name}</td></tr>'
    update_table_report(report, col_list, rows)