import datetime

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from laboratory import models_utils
from laboratory.models import (
    BaseUnitValues,
    BlockedListNotification,
    Catalog,
    CLInventory,
    CommentInform,
    Furniture,
    Inform,
    LabOrOrgRequest,
    Laboratory,
    LaboratoryRoom,
    Object,
    ObjectLogChange,
    ObjectMaximumLimit,
    OrganizationStructure,
    PrecursorReport,
    ReactiveLimit,
    Shelf,
    ShelfObject,
    ShelfObjectCodeCounter,
    TranferObject,
    UserOrganization,
)


def asegurar_unidad(unidad_pk, base_pk, valor):
    if not BaseUnitValues.objects.filter(measurement_unit_id=unidad_pk).exists():
        BaseUnitValues.objects.create(measurement_unit_id=unidad_pk, measurement_unit_base_id=base_pk, si_value=valor)


class RepresentacionesSinBaseDeDatosTest(SimpleTestCase):

    def test_str_de_modelos_simples(self):
        self.assertEqual(str(CLInventory(name="Acetona")), "Acetona")
        self.assertEqual(str(LabOrOrgRequest(name="Lab nuevo")), "Lab nuevo")
        self.assertEqual(str(Inform(name="Informe anual")), "Informe anual")
        contador = ShelfObjectCodeCounter(substance_laboratory_id=5, year=2026, month=3, counter=7)
        self.assertEqual(str(contador), "5 2026-03: 7")

    def test_rango_de_fechas_del_reporte_de_precursores(self):
        reporte = PrecursorReport(month=5, month_belong=4, year=2026)
        self.assertEqual(reporte.get_date_range(), "1 of April of 2026 - 30 of April of 2026")

    def test_reporte_de_enero_pertenece_a_diciembre_del_anio_anterior(self):
        """El reporte que se genera en enero (month=1) describe diciembre (month_belong=12)
        del año anterior. Antes la condición estaba invertida y mostraba el año en curso."""
        reporte = PrecursorReport(month=1, month_belong=12, year=2026)
        self.assertEqual(reporte.get_date_range(), "1 of December of 2025 - 31 of December of 2025")

    def test_estante_sin_mueble_no_tiene_posicion(self):
        self.assertEqual(Shelf().positions(), (None, None))


class ModelosDeInventarioTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        asegurar_unidad(62, 62, 1)
        asegurar_unidad(63, 62, 1000)
        asegurar_unidad(64, 64, 1)
        self.lab = Laboratory.objects.get(pk=1)
        self.user = User.objects.get(username="admin")

    def test_propiedades_de_objeto_sin_caracteristicas_sga(self):
        material = Object.objects.get(pk=4)
        self.assertFalse(material.is_reactive)
        self.assertTrue(Object.objects.get(pk=1).is_reactive)
        self.assertEqual(material.cas_code, "")
        self.assertEqual(material.get_storage_class, "")

    def test_cajas_en_shelfobject(self):
        so = ShelfObject.objects.get(pk=1)
        so.is_box = True
        so.quantity = 2
        so.limit_quantity = 3
        so.quantity_units = [{"units": 2, "quantity": 1}, {"units": 5, "quantity": 4}]
        self.assertEqual(so.total_quantity, 14)
        self.assertTrue(so.limit_reached)
        self.assertEqual(so.get_box_code(), so.quantity_units)
        self.assertEqual([c["units"] for c in so.order_by_boxes(order=True)], [5, 2])
        so.is_box = False
        so.quantity = 4
        self.assertFalse(so.limit_reached)

    def test_conversion_entre_unidades(self):
        so = ShelfObject.objects.get(pk=1)  # mililitros
        litros = Catalog.objects.get(pk=62)
        unidades = Catalog.objects.get(pk=64)
        sin_equivalencia = Catalog.objects.create(key="units", description="Unidad sin equivalencia")
        casos = [
            (None, 500, 500),
            (litros, 500, 0.5),
            (sin_equivalencia, 500, None),
        ]
        for unidad, cantidad, esperado in casos:
            with self.subTest(unidad=unidad):
                self.assertEqual(so.get_shelfobject_conversion_from_two_units(unidad, cantidad), esperado)
                self.assertEqual(
                    models_utils.get_shelfobject_conversion_from_two_units(so.measurement_unit, unidad, cantidad),
                    esperado,
                )
        so.measurement_unit = litros
        self.assertEqual(so.get_shelfobject_conversion_from_two_units(Catalog.objects.get(pk=63), 2), 2000)
        self.assertEqual(models_utils.get_shelfobject_conversion_from_two_units(litros, Catalog.objects.get(pk=63), 2), 2000)
        so.measurement_unit = unidades
        self.assertEqual(so.get_shelfobject_conversion_from_two_units(litros, 3), 3)
        self.assertEqual(models_utils.get_shelfobject_conversion_from_two_units(unidades, litros, 3), 3)

    def test_conversion_segun_unidad_del_estante(self):
        so = ShelfObject.objects.get(pk=1)  # estante 1 en mililitros
        self.assertEqual(so.get_obj_conversion_from_two_units(), so.quantity)
        so.shelf.measurement_unit = None
        self.assertEqual(so.get_obj_conversion_from_two_units(), so.quantity)

    def test_estantes_y_muebles(self):
        estante = Shelf.objects.get(pk=1)
        self.assertEqual(estante.count_objects(), ShelfObject.objects.filter(shelf=estante).count())
        self.assertEqual(
            estante.get_shelf(),
            "%s %s %s %s" % (estante.furniture.labroom.name, estante.furniture.name, estante.type, estante.name),
        )
        mueble = Furniture.objects.get(pk=1)
        self.assertEqual(mueble.get_row_count(), 2)
        self.assertEqual(mueble.get_col_count(), 4)
        mueble.dataconfig = ""
        self.assertEqual(mueble.get_col_count(), 0)
        ShelfObject.objects.filter(pk=1).update(limit_quantity=50)
        self.assertIn(ShelfObject.objects.get(pk=1), Furniture.objects.get(pk=1).get_limited_shelf_objects())

    def test_laboratorio_y_salas(self):
        self.assertEqual(repr(self.lab), "Vick Lab")
        self.assertEqual(set(self.lab.get_rooms()), set(LaboratoryRoom.objects.filter(laboratory=self.lab)))

    def test_str_de_registros_relacionados(self):
        log = ObjectLogChange.objects.get(pk=1)
        self.assertEqual(str(log), log.object.name)
        bloqueo = BlockedListNotification(laboratory=self.lab, user=self.user, object=log.object)
        self.assertEqual(str(bloqueo), "%s: %s: %s" % (log.object, self.lab, self.user))
        maximo = ObjectMaximumLimit(laboratory=self.lab, object=log.object, measurement_unit_id=63)
        self.assertEqual(str(maximo), "Vick Lab %s - Mililitros" % log.object)
        limite = ReactiveLimit(laboratory=self.lab, object=log.object, measurement_unit_id=63)
        self.assertEqual(str(limite), "Vick Lab %s - Mililitros" % log.object)
        comentario = CommentInform.objects.first()
        self.assertEqual(str(comentario), "%s - %s" % (comentario.created_by, comentario.create_at))
        membresia = UserOrganization(user=self.user, organization=self.lab.organization, type_in_organization=1)
        self.assertEqual(str(membresia), "%s · %s (%s)" % (self.user, self.lab.organization, membresia.get_type_in_organization_display()))

    def test_traslado_en_cajas(self):
        traslado = TranferObject.objects.first()
        traslado.quantity_units = [{"units": 1}, {"units": 4}]
        so = traslado.object
        self.assertEqual(
            traslado.get_object_detail(),
            "%s %s %s" % (so.object.name, traslado.quantity, so.measurement_unit),
        )
        self.assertEqual(traslado.get_box_totals(), 5 * so.quantity)
        self.assertEqual([c["units"] for c in traslado.order_by_boxes()], [1, 4])


class ArbolDeOrganizacionesTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.org = OrganizationStructure.objects.get(pk=1)
        self.hija = OrganizationStructure.objects.create(name="Hija", parent=self.org, position=9)
        self.admin = User.objects.get(username="admin")
        self.sin_orgs = User.objects.get(username="tuwp")

    def test_arbol_de_organizacion_inexistente_es_vacio(self):
        self.assertFalse(OrganizationStructure.os_manager.organization_tree(99999).exists())

    def test_usuario_sin_organizaciones(self):
        self.assertFalse(OrganizationStructure.os_manager.filter_organization_by_user(self.sin_orgs).exists())
        self.assertFalse(OrganizationStructure.os_manager.filter_user_orgs(self.sin_orgs).exists())

    def test_organizaciones_del_usuario_por_membresia_directa(self):
        self.hija.users.add(self.admin)
        orgs = OrganizationStructure.os_manager.filter_user_orgs(self.admin)
        self.assertEqual(set(orgs.values_list("pk", flat=True)), {1, 3, 4, self.hija.pk})

    def test_hijos_incluyen_a_la_propia_organizacion(self):
        hijos = OrganizationStructure.os_manager.get_children(self.org.pk)
        self.assertEqual(set(o.pk for o in hijos), {self.org.pk, self.hija.pk})

    def test_nombres_de_laboratorios_y_posiciones(self):
        self.assertEqual(set(self.org.laboratories.split(" -- ")), {"Vick Lab", "Lab Ultra", "DS Cosme"})
        self.assertEqual(self.org.min_child_position, 9)
        self.assertEqual(self.hija.min_child_position, self.hija.position)
        self.assertEqual(self.hija.last_child_position, self.hija.position)

    def test_raiz_de_un_nodo_no_guardado(self):
        nodo = OrganizationStructure(name="Sin guardar", parent=self.org)
        self.assertIs(nodo.root, nodo)
        self.assertEqual(self.hija.root, self.org)
