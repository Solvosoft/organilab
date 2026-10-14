"""Gráficos del panel de zonas y del panel IPER (`gtcharts`).

Cada gráfico suma la cantidad de los reactivos en kilogramos, litros y libras;
lo que no tiene unidad base conocida se registra como error y no suma. Los
gráficos solo se ven desde una organización a la que el usuario pertenece.
"""
import datetime
import json

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from laboratory.models import (
    BaseUnitValues,
    Catalog,
    Furniture,
    LaboratoryRoom,
    Object,
    Shelf,
    ShelfObject,
)
from risk_management.iper_defaults import KEY_CONSEQUENCE, KEY_HAZARD_CATEGORY, KEY_PROBABILITY
from risk_management.models import EstablishmentLogs, IPERAssessment, IPERHazard, RiskZone
from risk_management.tests.base import RiskTestCase, indicacion
from sga.models import SubstanceCharacteristics

GRAFICOS_DE_INVENTARIO = (
    "dangerindicationchart",
    "whiteorganchart",
    "precursortypechart",
    "nfpachart",
    "uecodechart",
    "storageclasschart",
)


class GraficosDeInventarioTest(RiskTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        room = LaboratoryRoom.objects.create(laboratory=cls.lab, name="Sala 1")
        furniture = Furniture.objects.create(
            labroom=room, name="Mueble",
            type=Catalog.objects.create(key="furniture_type", description="Estante"),
            dataconfig="",
        )
        cls.shelf = Shelf.objects.create(
            furniture=furniture, name="Estante 1",
            type=Catalog.objects.create(key="container_type", description="Caja"),
        )
        cls.obj = Object.objects.create(
            code="ETA", name="Etanol", type=Object.REACTIVE, organization=cls.organization
        )
        caracteristicas = SubstanceCharacteristics.objects.create(
            object_related=cls.obj,
            precursor_type=Catalog.objects.create(key="Precursor", description="Precursor A"),
        )
        caracteristicas.h_code.add(indicacion("H225"))
        for key, description in (
            ("white_organ", "Hígado"), ("nfpa", "NFPA 3"),
            ("ue_code", "UE 1"), ("storage_class", "Clase 3"),
        ):
            getattr(caracteristicas, key).add(Catalog.objects.create(key=key, description=description))
        # Un reactivo en cada unidad: kilogramos, litros, libras y una sin base.
        for base in ("Kilogramos", "Litros", "Libra", None):
            unidad = Catalog.objects.create(key="units", description="Unidad %s" % base)
            if base:
                BaseUnitValues.objects.create(
                    measurement_unit=unidad, si_value=1,
                    measurement_unit_base=Catalog.objects.create(key="units", description=base),
                )
            ShelfObject.objects.create(
                object=cls.obj, shelf=cls.shelf, quantity=2, measurement_unit=unidad,
                in_where_laboratory=cls.lab, created_by=cls.user,
            )

    def grafico(self, basename, org=None, **params):
        return self.client.get(
            reverse(basename + "-detail", kwargs={"pk": (org or self.organization).pk}), params
        )

    def test_suma_por_unidad(self):
        etiquetas = {
            "dangerindicationchart": "H225",
            "whiteorganchart": "Hígado",
            "precursortypechart": "Precursor A",
            "nfpachart": "NFPA 3",
            "uecodechart": "UE 1",
            "storageclasschart": "Clase 3",
        }
        for basename in GRAFICOS_DE_INVENTARIO:
            with self.subTest(basename=basename):
                response = self.grafico(basename)
                self.assertEqual(response.status_code, 200)
                contenido = json.dumps(response.json(), ensure_ascii=False)
                self.assertIn(etiquetas[basename], contenido)
                # Litros, kilogramos y libras: 2.0 cada uno (la de libras
                # reventaba en el gráfico de indicaciones de peligro).
                self.assertEqual(contenido.count("[2.0]"), 3)

    def test_filtro_por_zona_o_edificio_sin_laboratorios(self):
        vacia = RiskZone.objects.create(
            name="Vacía", organization=self.organization, num_workers=1, zone_type=self.zone_type
        )
        for basename in GRAFICOS_DE_INVENTARIO:
            with self.subTest(basename=basename):
                contenido = json.dumps(self.grafico(basename, risk_zone=vacia.pk).json())
                self.assertNotIn("[2.0]", contenido)

    def test_filtro_por_zona_y_edificio(self):
        for basename in GRAFICOS_DE_INVENTARIO:
            with self.subTest(basename=basename):
                response = self.grafico(basename, risk_zone=self.zone.pk, buildings=self.building.pk)
                self.assertIn("[2.0]", json.dumps(response.json()))

    def test_organizacion_ajena_es_403(self):
        for basename in GRAFICOS_DE_INVENTARIO + ("substancetonschart", "eslochart"):
            with self.subTest(basename=basename):
                response = self.grafico(basename, org=self.other, zone=self.other_zone.pk)
                self.assertEqual(response.status_code, 403)

    def test_listado_no_existe(self):
        for basename in GRAFICOS_DE_INVENTARIO + ("substancetonschart", "eslochart", "iperrisklevelchart"):
            with self.subTest(basename=basename):
                self.assertEqual(self.client.get(reverse(basename + "-list")).status_code, 404)

    def test_toneladas_y_otras_unidades(self):
        base_unidades = Catalog.objects.create(key="units", description="Unidades")
        unidad = Catalog.objects.create(key="units", description="Unidad suelta")
        BaseUnitValues.objects.create(
            measurement_unit=unidad, measurement_unit_base=base_unidades, si_value=1
        )
        ShelfObject.objects.create(
            object=self.obj, shelf=self.shelf, quantity=7, quantity_base_unit=7,
            measurement_unit=unidad, in_where_laboratory=self.lab, created_by=self.user,
        )
        ShelfObject.objects.filter(measurement_unit=unidad).update(quantity_base_unit=7)
        response = self.grafico("substancetonschart")
        self.assertEqual(response.status_code, 200)
        contenido = json.dumps(response.json(), ensure_ascii=False)
        self.assertIn("Etanol", contenido)
        self.assertIn("Unidades", contenido)
        self.assertIn("7.0", contenido)

    def _reactivo(self, nombre, cantidad, unidad, base, si_value, densidad=None):
        """Un reactivo con una existencia en ``unidad`` (de la familia ``base``)."""
        obj = Object.objects.create(
            code=nombre[:3].upper(), name=nombre, type=Object.REACTIVE, organization=self.organization
        )
        if densidad is not None:
            SubstanceCharacteristics.objects.create(object_related=obj, density=densidad)
        base_catalog = Catalog.objects.filter(key="units", description=base).first() or \
            Catalog.objects.create(key="units", description=base)
        unit = Catalog.objects.create(key="units", description=unidad)
        BaseUnitValues.objects.create(
            measurement_unit=unit, measurement_unit_base=base_catalog, si_value=si_value
        )
        ShelfObject.objects.create(
            object=obj, shelf=self.shelf, quantity=cantidad, measurement_unit=unit,
            in_where_laboratory=self.lab, created_by=self.user,
        )

    def _serie(self, data, serie, nombre):
        """Valor de ``nombre`` en la serie ``serie`` (en español o en inglés)."""
        nombres = {"Toneladas (t)": ("Toneladas (t)",), "Metros (m)": ("Metros (m)", "Meters (m)")}[serie]
        datos = data["data"]
        etiquetas = datos["labels"]
        for dataset in datos["datasets"]:
            if dataset["label"] in nombres:
                return dataset["data"][etiquetas.index(nombre)]
        return None

    def test_toneladas_en_unidad_base_con_densidad(self):
        # 500 mL con densidad 1.84 kg/L -> 0.92 kg -> 0.00092 t
        self._reactivo("Sulfúrico", 500, "Mililitros", "Litros", 1000, densidad=1.84)
        # 500 mL sin densidad -> se asume 1 kg/L -> 0.0005 t
        self._reactivo("Acetona", 500, "Mililitros", "Litros", 1000, densidad=0)
        # 2000 g -> 2 kg -> 0.002 t
        self._reactivo("Cloruro", 2000, "Gramos", "Kilogramos", 1000)
        data = self.grafico("substancetonschart").json()
        self.assertAlmostEqual(self._serie(data, "Toneladas (t)", "Sulfúrico"), 0.0009, places=4)
        self.assertAlmostEqual(self._serie(data, "Toneladas (t)", "Acetona"), 0.0005, places=4)
        self.assertAlmostEqual(self._serie(data, "Toneladas (t)", "Cloruro"), 0.002, places=4)

    def test_metros_no_suman_toneladas(self):
        self._reactivo("Cinta", 150, "Centímetros", "Metros", 100)
        data = self.grafico("substancetonschart").json()
        self.assertEqual(self._serie(data, "Toneladas (t)", "Cinta"), 0)
        self.assertEqual(self._serie(data, "Metros (m)", "Cinta"), 1.5)


class GraficoDeBitacoraTest(RiskTestCase):

    def grafico(self, **params):
        return self.client.get(reverse("eslochart-detail", kwargs={"pk": self.organization.pk}), params)

    def test_ultima_bitacora_de_la_zona(self):
        EstablishmentLogs.objects.create(
            content_type=ContentType.objects.get_for_model(RiskZone), object_id=self.zone.pk,
            physical=0.4, health=0.7, environmental=0.1,
        )
        contenido = json.dumps(self.grafico(zone=self.zone.pk).json())
        for valor in ("[0.4]", "[0.7]", "[0.1]"):
            self.assertIn(valor, contenido)

    def test_zona_obligatoria_valida_y_propia(self):
        self.assertEqual(self.grafico().status_code, 404)
        self.assertEqual(self.grafico(zone="abc").status_code, 404)
        self.assertEqual(self.grafico(zone=self.other_zone.pk).status_code, 404)


class GraficosIPERTest(RiskTestCase):

    def test_peligros_y_cumplimiento(self):
        hoy = datetime.date.today()
        evaluacion = IPERAssessment.objects.create(
            organization=self.organization, laboratory=self.lab, assessment_date=hoy,
            due_date=hoy - datetime.timedelta(days=1),
        )
        IPERHazard.objects.create(
            assessment=evaluacion,
            category=Catalog.objects.get(key=KEY_HAZARD_CATEGORY, description="Químico"),
            probability=Catalog.objects.get(key=KEY_PROBABILITY, description="Alta"),
            consequence=Catalog.objects.get(key=KEY_CONSEQUENCE, description="Extremadamente Dañino"),
            description="Vapores",
        )
        al_dia = self.crear_laboratorio("Al día", self.organization)
        IPERAssessment.objects.create(
            organization=self.organization, laboratory=al_dia, assessment_date=hoy,
            due_date=hoy + datetime.timedelta(days=30),
        )
        self.crear_laboratorio("Sin IPER", self.organization)
        for basename, esperado in (
            ("iperrisklevelchart", "Intolerable"),
            ("iperhazardcategorychart", "Químico"),
            ("ipercompliancechart", "[1.0, 1.0, 1.0]"),
        ):
            with self.subTest(basename=basename):
                response = self.client.get(
                    reverse(basename + "-detail", kwargs={"pk": self.organization.pk})
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(esperado, json.dumps(response.json(), ensure_ascii=False))

    def test_organizacion_ajena_es_403(self):
        response = self.client.get(reverse("iperrisklevelchart-detail", kwargs={"pk": self.other.pk}))
        self.assertEqual(response.status_code, 403)
