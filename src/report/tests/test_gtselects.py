from django.urls import reverse

from laboratory.models import Furniture, LaboratoryRoom
from report.tests.utils import XHR, ReportTestBase


class ReportLookupsTest(ReportTestBase):
    """Autocompletados (select2) de los formularios de reporte."""

    def ids(self, urlname, params, status=200):
        response = self.client.get(reverse(urlname), params, **XHR)
        self.assertEqual(response.status_code, status, response.content)
        if status != 200:
            return response
        return {int(r["id"]) for r in response.json()["results"]}

    def test_salas_de_todos_mis_laboratorios(self):
        """`all_labs_org` respondía 500: filtraba una lista como si fuera queryset."""
        ids = self.ids(
            "lab_room-list",
            {"organization": self.org.pk, "laboratory": self.lab.pk, "all_labs_org": True},
        )
        self.assertEqual(
            ids, set(LaboratoryRoom.objects.filter(laboratory=self.lab).values_list("pk", flat=True))
        )

    def test_salas_seleccionadas_quedan_marcadas(self):
        response = self.client.get(
            reverse("lab_room-list"),
            {"organization": self.org.pk, "laboratory": self.lab.pk, "lab_room": [2]},
            **XHR,
        )
        self.assertEqual(response.status_code, 200)
        marcadas = [r for r in response.json()["results"] if r.get("selected")]
        self.assertEqual([int(r["id"]) for r in marcadas], [2])

    def test_laboratorios_por_organizacion(self):
        ids = self.ids("labs_by_org-list", {"organization": self.org.pk})
        self.assertIn(self.lab.pk, ids)
        # Sin organización el serializador rechaza la búsqueda.
        errores = self.ids("labs_by_org-list", {}, status=400)
        self.assertIn("organization", errores.json()["errors"])

    def test_salas_por_laboratorio_u_organizacion(self):
        self.assertEqual(self.ids("lab_room_ref-list", {"laboratory": [3]}), set())
        self.assertEqual(
            self.ids("lab_room_ref-list", {"laboratory[]": [self.lab.pk]}),
            set(LaboratoryRoom.objects.filter(laboratory=self.lab).values_list("pk", flat=True)),
        )
        # Sin laboratorios se usan los del perfil en la organización.
        self.assertEqual(
            self.ids("lab_room_ref-list", {"organization": self.org.pk}),
            set(LaboratoryRoom.objects.filter(laboratory=self.lab).values_list("pk", flat=True)),
        )
        self.ids("lab_room_ref-list", {"organization": 999999}, status=404)

    def test_salas_sin_laboratorios_disponibles(self):
        vacia = self.foreign_org
        self.assertEqual(self.ids("lab_room_ref-list", {"organization": vacia.pk}), set())

    def test_muebles_por_laboratorio_u_organizacion(self):
        del_lab = set(
            Furniture.objects.filter(labroom__laboratory=self.lab).values_list("pk", flat=True)
        )
        # `relfield` son las salas elegidas en el select del que depende; djgentelella las
        # recibe en un solo parámetro separado por comas.
        salas = "1,2,3"
        self.assertEqual(
            self.ids("furniture_ref-list", {"laboratory": [self.lab.pk], "relfield": salas}), del_lab
        )
        self.assertEqual(
            self.ids("furniture_ref-list", {"organization": self.org.pk, "relfield": salas}), del_lab
        )
        self.assertEqual(self.ids("furniture_ref-list", {"laboratory": [self.lab.pk]}), set())
        self.ids("furniture_ref-list", {"organization": 999999}, status=404)
