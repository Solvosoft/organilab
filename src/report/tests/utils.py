"""Utilidades compartidas por las pruebas unitarias de la app `report`.

No contiene pruebas: solo la base con el usuario, la organización y el
laboratorio del fixture, y atajos para crear un `TaskReport` y leer el fichero
que un reporte deja escrito.
"""

import openpyxl
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from laboratory.models import Catalog, Laboratory, OrganizationStructure, Shelf, ShelfObject
from report.models import TaskReport

# Cabecera que hace que HandleErrorMiddleware deje pasar el 403/404 real en vez
# de redirigir a la pantalla de error.
XHR = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


@override_settings(MEDIA_ROOT="/tmp/organilab-test-media")
class ReportTestBase(TestCase):
    """Base con el fixture de laboratorio y un usuario con acceso a la org 1.

    `admin` pertenece a las organizaciones 1, 3 y 4 y su perfil tiene roles a
    nivel de perfil, así que `laboratory.do_report` le llega por el Rol. La
    organización 2 es la ajena: el usuario no es miembro.
    """

    fixtures = ["laboratory_data.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(username="admin")
        self.org = OrganizationStructure.objects.get(pk=1)
        self.foreign_org = OrganizationStructure.objects.get(pk=2)
        self.lab = Laboratory.objects.get(pk=1)
        self.client.force_login(self.user)

    def make_report(self, type_report, file_type="xlsx", **data):
        payload = {
            "name": "reporte-prueba",
            "title": "Reporte de prueba",
            "organization": self.org.pk,
            "org_pk": self.org.pk,
            "laboratory": [self.lab.pk],
        }
        payload.update(data)
        return TaskReport.objects.create(
            created_by=self.user,
            type_report=type_report,
            file_type=file_type,
            data=payload,
            language="es",
        )

    def unit(self, description="Mililitros"):
        return Catalog.objects.filter(key="units", description=description).first()

    def make_shelfobject(self, obj, shelf=None, quantity=5, **extra):
        """Unidad de inventario en el laboratorio de la prueba (estante 1 por defecto)."""
        values = {
            "shelf": shelf or Shelf.objects.get(pk=1),
            "object": obj,
            "quantity": quantity,
            "measurement_unit": self.unit(),
            "in_where_laboratory": self.lab,
        }
        values.update(extra)
        return ShelfObject.objects.create(**values)

    def read_xlsx(self, report):
        """Filas (listas de valores) de la primera hoja del fichero generado."""
        report.refresh_from_db()
        with report.file.open("rb") as fh:
            wb = openpyxl.load_workbook(fh)
        return [list(row) for row in wb.worksheets[0].iter_rows(values_only=True)]
