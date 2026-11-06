"""
Validaciones de ``laboratory/shelfobject/serializers.py`` y utilidades de
``laboratory/shelfobject/utils.py`` probadas directamente: son ramas de error que
las vistas solo alcanzan con datos muy concretos, y cada una protege un caso
(laboratorio ajeno, unidades incompatibles, cajas, límites) que conviene fijar.
"""

from django.test import RequestFactory
from django.urls import reverse

from laboratory.models import (
    ShelfObject,
    Shelf,
    Object,
    Catalog,
    Furniture,
    LaboratoryRoom,
    Laboratory,
    ShelfObjectLimits,
    ShelfObjectObservation,
    ShelfObjectEquipmentCharacteristics,
    MaterialCapacity,
    TranferObject,
    OrganizationStructure,
)
from laboratory.models import REQUESTED
from laboratory.shelfobject import serializers as so_serializers
from laboratory.shelfobject import utils as so_utils
from laboratory.shelfobject.forms import TransferOutShelfObjectForm
from laboratory.tests.test_cov_api_base import (
    CovApiBase,
    UNIDADES,
    MILILITROS,
    LITROS,
    METROS,
    ESTADO_EXCELENTE,
)
from reservations_management.models import ReservedProducts, BORROWED


def errores(serializer):
    serializer.is_valid()
    return serializer.errors


class IncrementoDecrementoSerializerTest(CovApiBase):
    """``IncreaseShelfObjectSerializer`` y ``DecreaseShelfObjectSerializer``."""

    def setUp(self):
        super().setUp()
        self.reactivo = ShelfObject.objects.get(pk=2)  # 23 ml en estante de ml
        self.ctx = {"source_laboratory_id": self.lab.pk}

    def test_incremento_de_reactivo_en_estante_sin_unidad(self):
        ShelfObject.objects.filter(pk=self.reactivo.pk).update(shelf_id=2)
        serializer = so_serializers.IncreaseShelfObjectSerializer(
            data={"amount": 1, "shelf_object": self.reactivo.pk, "measurement_unit": LITROS}, context=self.ctx
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_incremento_que_excede_el_estante(self):
        shelf = self.reactivo.shelf
        shelf.quantity = 10
        shelf.infinity_quantity = False
        shelf.limit_only_objects = True
        shelf.save()
        data = {"amount": 50, "shelf_object": self.reactivo.pk, "measurement_unit": MILILITROS}
        errors = errores(so_serializers.IncreaseShelfObjectSerializer(data=data, context=self.ctx))
        self.assertIn("amount", errors)
        self.assertIn("shelf_object", errors)

    def test_incremento_con_error_ajeno_al_objeto(self):
        from unittest import mock

        with mock.patch.object(
            so_serializers, "validate_measurement_unit_and_quantity", return_value={"container": "x"}
        ):
            data = {"amount": 1, "shelf_object": self.reactivo.pk, "measurement_unit": MILILITROS}
            errors = errores(so_serializers.IncreaseShelfObjectSerializer(data=data, context=self.ctx))
        self.assertIn("container", errors)

    def decremento(self, **data):
        base = {"amount": 1, "shelf_object": self.reactivo.pk, "measurement_unit": MILILITROS}
        base.update(data)
        return so_serializers.DecreaseShelfObjectSerializer(data=base, context=self.ctx)

    def test_decremento_de_objeto_de_otro_laboratorio(self):
        ShelfObject.objects.filter(pk=self.reactivo.pk).update(in_where_laboratory_id=2)
        self.assertIn("shelf_object", errores(self.decremento()))

    def test_decremento_de_caja(self):
        caja = self.crear_caja(units_list=[10, 2])
        self.assertIn("box_index", errores(self.decremento(shelf_object=caja.pk)))
        self.assertIn("box_index", errores(self.decremento(shelf_object=caja.pk, box_index=5)))
        self.assertIn("amount", errores(self.decremento(shelf_object=caja.pk, box_index=1, amount=3)))
        self.assertTrue(self.decremento(shelf_object=caja.pk, box_index=0, amount=3).is_valid())

    def test_decremento_en_estante_sin_unidad(self):
        ShelfObject.objects.filter(pk=self.reactivo.pk).update(shelf_id=2)
        self.assertTrue(self.decremento().is_valid())

    def test_decremento_con_unidad_incompatible(self):
        self.assertIn("measurement_unit", errores(self.decremento(measurement_unit=METROS)))

    def test_decremento_mayor_a_la_existencia_y_objeto_no_permitido(self):
        shelf = self.reactivo.shelf
        shelf.limit_only_objects = True
        shelf.save()
        errors = errores(self.decremento(amount=500))
        self.assertIn("amount", errors)
        self.assertIn("shelf_object", errors)


class LimitesSerializerTest(CovApiBase):
    """``ShelfObjectLimitsSerializer`` y ``ShelfObjectMaterialLimitsSerializer``."""

    def limites(self, data, **context):
        return so_serializers.ShelfObjectLimitsSerializer(data=data, context=context)

    def test_maximo_mayor_que_la_existencia_del_objeto(self):
        errors = errores(self.limites({"minimum_limit": 0, "maximum_limit": 100}, shelfobject=2))
        self.assertIn("maximum_limit", errors)

    def test_reactivo_con_limites_invertidos_y_cantidad_fuera(self):
        errors = errores(self.limites({"minimum_limit": 9, "maximum_limit": 5}, type_id=Object.REACTIVE, quantity=7))
        self.assertIn("minimum_limit", errors)
        self.assertIn("quantity", errors)

    def test_reactivo_por_debajo_del_minimo(self):
        errors = errores(self.limites({"minimum_limit": 5, "maximum_limit": 9}, type_id=Object.REACTIVE, quantity=1))
        self.assertIn("quantity", errors)

    def test_limites_de_material_y_equipo(self):
        serializer = so_serializers.ShelfObjectMaterialLimitsSerializer(
            data={}, context={"type_id": Object.EQUIPMENT}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer = so_serializers.ShelfObjectMaterialLimitsSerializer(
            data={"minimum_limit": 5, "maximum_limit": 1}, context={"type_id": Object.MATERIAL}
        )
        self.assertIn("minimum_limit", errores(serializer))


class AltasSerializerTest(CovApiBase):
    """Errores de validación de las altas de reactivo de desecho, material y equipo."""

    ctx = {"organization_id": 1, "laboratory_id": 1}

    def test_reactivo_de_desecho_que_excede_el_estante(self):
        from sga.models import Pictogram

        pictograma = Pictogram.objects.create(name="Corrosivo")
        data = {
            "shelf": 13, "object": 2, "status": ESTADO_EXCELENTE, "quantity": 500,
            "measurement_unit": METROS, "batch": "1", "physical_status": "liquid",
            "pictograms": [pictograma.pk], "container_select_option": "clone",
            "container_for_cloning": 4, "available_container": None,
        }
        errors = errores(so_serializers.ReactiveRefuseShelfObjectSerializer(data=data, context=self.ctx))
        self.assertIn("quantity", errors)

    def test_equipo_que_excede_el_estante(self):
        data = {"shelf": 13, "object": 8, "status": ESTADO_EXCELENTE, "quantity": 500, "limit_quantity": 0}
        for clase in (so_serializers.EquipmentShelfObjectSerializer, so_serializers.EquipmentRefuseShelfObjectSerializer):
            with self.subTest(clase=clase.__name__):
                self.assertIn("quantity", errores(clase(data=data, context=self.ctx)))

    def test_equipo_de_desecho_valido(self):
        data = {"shelf": 13, "object": 8, "status": ESTADO_EXCELENTE, "quantity": 1, "limit_quantity": 0}
        serializer = so_serializers.EquipmentRefuseShelfObjectSerializer(data=data, context=self.ctx)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_caja_que_excede_el_estante(self):
        data = {
            "shelf": 13, "object": 6, "status": ESTADO_EXCELENTE, "quantity": 500,
            "measurement_unit": METROS, "units_per_box": 1,
        }
        self.assertIn("quantity", errores(so_serializers.BoxShelfObjectSerializer(data=data, context=self.ctx)))

    def test_caja_sin_cambios_de_cajas(self):
        caja = self.crear_caja()
        serializer = so_serializers.UpdateBoxShelfObjectSerializer(instance=caja, data={"batch": "B"}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class DetalleYEstanteSerializerTest(CovApiBase):
    """Getters de ``ShelfObjectDetailSerializer``, ``ShelfSerializer`` y observaciones."""

    def test_detalle_de_equipo_con_caracteristicas(self):
        equipo = ShelfObject.objects.get(pk=15)
        caracteristicas = ShelfObjectEquipmentCharacteristics.objects.get(shelfobject=equipo)
        caracteristicas.provider_id = 1
        caracteristicas.have_guarantee = True
        caracteristicas.available_to_use = True
        caracteristicas.contract_of_maintenance = "contrato.pdf"
        caracteristicas.save()
        equipo.type_budget = Catalog.objects.create(key="type_budget", description="Presupuesto A")
        equipo.save()
        response = self.client.get(self.url("api-shelfobject-details", pk=equipo.pk))
        self.assertEqual(response.status_code, 200)
        data = response.json()["object"]
        self.assertEqual(data["type_budget"], "Presupuesto A")
        caracteristicas = data["equipment_characteristics"]
        self.assertEqual(caracteristicas["provider"], "Karine Products")
        self.assertTrue(caracteristicas["contract_of_maintenance"].startswith("http://testserver"))
        self.assertTrue(caracteristicas["can_download_contract"])

    def test_detalle_de_caracteristicas_sin_datos(self):
        request = RequestFactory().get("/")
        request.user = type("U", (), {"has_perms": lambda self, perms: False})()
        caracteristicas = ShelfObjectEquipmentCharacteristics(have_guarantee=False, available_to_use=False)
        serializer = so_serializers.EquipmentShelfObjectCharacteristicsDetailSerializer(context={"request": request})
        self.assertTrue(str(serializer.get_provider(caracteristicas)))
        self.assertIsNone(serializer.get_contract_of_maintenance(caracteristicas))
        self.assertIsNone(serializer.get_can_download_contract(caracteristicas))
        self.assertNotEqual(serializer.get_have_guarantee(caracteristicas), "")
        self.assertNotEqual(serializer.get_available_to_use(caracteristicas), "")

    def test_estante_sin_unidad_desglosa_por_unidad(self):
        shelf = Shelf.objects.get(pk=15)  # sin unidad, objetos en ml y unidades
        serializer = so_serializers.ShelfSerializer()
        detalle = serializer.get_quantity_storage_status(shelf)
        self.assertIn("Mililitros", detalle)
        self.assertIn("Unidades", detalle)
        self.assertEqual(serializer.get_total(shelf), detalle)

    def test_creador_sin_nombre_completo(self):
        from django.contrib.auth.models import User

        sin_nombre = User.objects.create_user(username="anonimo")
        observacion = ShelfObjectObservation(created_by=sin_nombre, action_taken="x", description="y")
        self.assertEqual(
            so_serializers.ShelfObjectObservationSerializer().get_creator_name(observacion), "anonimo"
        )

    def test_reactivo_en_tabla_de_caja(self):
        caja = self.crear_caja(units_list=[3, 4], quantity=2)
        caja.container = ShelfObject.objects.get(pk=6)
        serializer = so_serializers.ShelObjectReactiveSerializer()
        self.assertEqual(serializer.get_quantity(caja), 14)
        self.assertEqual(serializer.get_container(caja), "Cal 100 gr")
        self.assertEqual(serializer.get_quantity_box(caja), 2)
        self.assertEqual(serializer.get_box_units(caja), caja.quantity_units)
        self.assertIn("Caja", str(serializer.get_object(caja)))

    def test_recipiente_en_centimetros(self):
        self.assertTrue(str(so_serializers.RecipientSizeSerializer().get_unit(None)))


class MovimientoSerializerTest(CovApiBase):
    """``MoveShelfObjectSerializer`` y ``MoveShelfObjectWithContainerSerializer``."""

    ctx = {"laboratory_id": 1, "organization_id": 1}

    def setUp(self):
        super().setUp()
        self.reactivo = ShelfObject.objects.get(pk=2)

    def datos(self, shelf, **extra):
        data = {
            "shelf": shelf.pk,
            "furniture": shelf.furniture_id,
            "lab_room": shelf.furniture.labroom_id,
            "shelf_object": self.reactivo.pk,
        }
        data.update(extra)
        return data

    def test_objeto_de_otro_laboratorio(self):
        ShelfObject.objects.filter(pk=self.reactivo.pk).update(in_where_laboratory_id=2)
        errors = errores(so_serializers.MoveShelfObjectSerializer(data=self.datos(Shelf.objects.get(pk=13)), context=self.ctx))
        self.assertIn("shelf_object", errors)

    def test_mismo_estante(self):
        errors = errores(so_serializers.MoveShelfObjectSerializer(data=self.datos(Shelf.objects.get(pk=1)), context=self.ctx))
        self.assertIn("shelf", errors)

    def test_destino_sin_unidades_compatibles(self):
        sala = LaboratoryRoom.objects.create(laboratory=self.lab, name="Sala de metros")
        mueble = Furniture.objects.create(labroom=sala, name="Mueble de metros", type_id=75)
        estante = Shelf.objects.create(furniture=mueble, name="Metros", type_id=74, measurement_unit_id=METROS, quantity=1)
        errors = errores(so_serializers.MoveShelfObjectSerializer(data=self.datos(estante), context=self.ctx))
        self.assertIn("lab_room", errors)
        self.assertIn("furniture", errors)
        self.assertIn("shelf", errors)
        self.assertIn("shelf_object", errors)

    def test_unidad_sin_conversion(self):
        unidad_a = Catalog.objects.create(key="units", description="Unidad sin base A")
        unidad_b = Catalog.objects.create(key="units", description="Unidad sin base B")
        ShelfObject.objects.filter(pk=self.reactivo.pk).update(measurement_unit=unidad_a)
        estante = Shelf.objects.get(pk=13)
        estante.measurement_unit = unidad_b
        estante.save()
        errors = errores(so_serializers.MoveShelfObjectSerializer(data=self.datos(estante), context=self.ctx))
        self.assertIn("shelf", errors)

    def test_opcion_de_contenedor_sin_contenedor_de_origen(self):
        ShelfObject.objects.filter(pk=self.reactivo.pk).update(container=None)
        estante = Shelf.objects.get(pk=13)
        estante.infinity_quantity = True
        # Misma unidad que el reactivo: así la validación llega hasta el contenedor.
        estante.measurement_unit_id = self.reactivo.measurement_unit_id
        estante.save()
        data = self.datos(
            estante, container_select_option="use_source", container_for_cloning=None, available_container=None
        )
        errors = errores(so_serializers.MoveShelfObjectWithContainerSerializer(data=data, context=self.ctx))
        self.assertIn("container_select_option", errors)


class ContenedorSerializerTest(CovApiBase):

    def test_contenedor_sin_capacidad_suficiente(self):
        MaterialCapacity.objects.create(object_id=4, capacity=1, capacity_measurement_unit_id=LITROS)
        data = {
            "shelf": 1, "shelf_object": 2, "container_select_option": "clone",
            "container_for_cloning": 4, "available_container": None,
        }
        serializer = so_serializers.ManageContainerSerializer(
            data=data, context={"organization_id": 1, "laboratory_id": 1}
        )
        errors = errores(serializer)
        self.assertIn("shelf_object", errors)


class TransferenciaSerializerTest(CovApiBase):
    """``TransferInShelfObjectSerializer`` y la variante con contenedor."""

    def setUp(self):
        super().setUp()
        self.lab2 = Laboratory.objects.get(pk=2)
        self.reactivo = ShelfObject.objects.get(pk=2)
        mueble = Furniture.objects.create(labroom_id=3, name="Destino", type_id=75)
        self.destino = Shelf.objects.create(furniture=mueble, name="Destino", type_id=74, infinity_quantity=True)
        self.ctx = {"laboratory_id": 2, "organization_id": 1, "validate_for_approval": True}

    def transferencia(self, **extra):
        data = {
            "object": self.reactivo, "quantity": 2, "laboratory_send": self.lab,
            "laboratory_received": self.lab2, "status": REQUESTED, "created_by": self.user,
        }
        data.update(extra)
        return TranferObject.objects.create(**data)

    def validar(self, transfer, clase=so_serializers.TransferInShelfObjectSerializer, **extra):
        data = {"transfer_object": transfer.pk, "shelf": self.destino.pk}
        data.update(extra)
        return errores(clase(data=data, context=self.ctx))

    def test_transferencia_enviada_a_otro_laboratorio(self):
        transfer = self.transferencia(laboratory_received=Laboratory.objects.get(pk=3))
        self.assertIn("transfer_object", self.validar(transfer))

    def test_objeto_que_ya_no_esta_en_el_laboratorio_que_envia(self):
        transfer = self.transferencia()
        ShelfObject.objects.filter(pk=self.reactivo.pk).update(in_where_laboratory_id=3)
        self.assertIn("transfer_object", self.validar(transfer))

    def test_cantidad_mayor_a_la_disponible(self):
        transfer = self.transferencia(quantity=500)
        self.assertIn("transfer_object", self.validar(transfer))

    def test_estante_sin_capacidad(self):
        self.destino.infinity_quantity = False
        self.destino.quantity = 1
        self.destino.save()
        transfer = self.transferencia(quantity=5)
        self.assertIn("transfer_object", self.validar(transfer))

    def test_con_contenedor_de_origen_inexistente(self):
        ShelfObject.objects.filter(pk=self.reactivo.pk).update(container=None)
        transfer = self.transferencia()
        errors = self.validar(
            transfer, so_serializers.TransferInShelfObjectApproveWithContainerSerializer,
            container_select_option="use_source", container_for_cloning=None, available_container=None,
        )
        self.assertIn("container_select_option", errors)

    def test_con_unidades_sin_conversion(self):
        unidad_a = Catalog.objects.create(key="units", description="Unidad sin base A")
        unidad_b = Catalog.objects.create(key="units", description="Unidad sin base B")
        ShelfObject.objects.filter(pk=self.reactivo.pk).update(measurement_unit=unidad_a)
        self.destino.measurement_unit = unidad_b
        self.destino.save()
        transfer = self.transferencia()
        errors = self.validar(
            transfer, so_serializers.TransferInShelfObjectApproveWithContainerSerializer,
            container_select_option="clone", container_for_cloning=4, available_container=None,
        )
        self.assertIn("transfer_object", errors)


class BusquedaSerializerTest(CovApiBase):
    """``SearchShelfObjectSerializer`` (búsqueda de un solo elemento por nivel)."""

    ctx = {"source_laboratory_id": 1}

    def validar(self, **data):
        return errores(so_serializers.SearchShelfObjectSerializer(data=data, context=self.ctx))

    def test_elementos_que_no_coinciden_entre_niveles(self):
        self.assertIn("non_field_errors", self.validar(labroom=3))
        self.assertIn("furniture", self.validar(labroom=2, furniture=1))
        self.assertIn("shelf", self.validar(furniture=2, shelf=1))
        self.assertIn("shelfobject", self.validar(labroom=2, shelf=1))
        self.assertIn("shelfobject", self.validar(shelf=15, shelfobject=2))
        self.assertIn("shelfobject", self.validar(furniture=2, shelfobject=2))
        self.assertIn("shelfobject", self.validar(labroom=2, shelfobject=2))

    def test_elementos_coherentes(self):
        self.assertEqual(self.validar(labroom=1, furniture=1, shelf=1, shelfobject=2), {})

    def test_busqueda_por_pk(self):
        serializer = so_serializers.ShelfObjectPk(data={"search": "p1234"})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["search"], "pk=1234")


class EquipoEdicionSerializerTest(CovApiBase):
    """``EditEquimentShelfobjectCharacteristicSerializer`` y ``EditEquipmentShelfObjectSerializer``."""

    def test_caracteristicas_de_objeto_que_no_es_equipo(self):
        reactivo = ShelfObject.objects.get(pk=2)
        serializer = so_serializers.EditEquimentShelfobjectCharacteristicSerializer(
            data={"shelfobject": reactivo.pk, "provider": None}, context={"organization": 1}
        )
        self.assertIn("shelfobject", errores(serializer))

    def test_proveedores_del_equipo_por_catalogo(self):
        from laboratory.models import EquipmentCharacteristics

        equipo = ShelfObject.objects.get(pk=15)
        caracteristicas = EquipmentCharacteristics.objects.create(object=equipo.object)
        caracteristicas.providers.add(2)
        serializer = so_serializers.EditEquimentShelfobjectCharacteristicSerializer(
            data={"shelfobject": equipo.pk, "provider": 1}, context={"organization": 1}
        )
        self.assertIn("provider", errores(serializer))
        serializer = so_serializers.EquimentShelfobjectCharacteristicSerializer(
            data={"shelfobject": equipo.pk, "provider": 1}, context={"organization": 1}
        )
        self.assertIn("provider", errores(serializer))

    def test_equipo_de_otro_laboratorio_u_organizacion(self):
        equipo = ShelfObject.objects.get(pk=15)
        data = {"status": ESTADO_EXCELENTE}
        serializer = so_serializers.EditEquipmentShelfObjectSerializer(
            instance=equipo, data=data, context={"lab_pk": 2, "org_pk": 1}
        )
        self.assertIn("shelfobject", errores(serializer))
        serializer = so_serializers.EditEquipmentShelfObjectSerializer(
            instance=equipo, data=data, context={"lab_pk": 1, "org_pk": 3}
        )
        self.assertIn("shelfobject", errores(serializer))

    def test_reactivo_de_otro_laboratorio(self):
        reactivo = ShelfObject.objects.get(pk=2)
        data = {
            "status": ESTADO_EXCELENTE, "description": "x", "reactive_expiration_date": "01/01/2030",
            "physical_status": "solid",
        }
        serializer = so_serializers.EditReactiveShelfObjectSerializer(
            instance=reactivo, data=data, context={"lab_pk": 2, "org_pk": 1}
        )
        self.assertIn("shelfobject", errores(serializer))

    def test_fecha_personalizada(self):
        import datetime

        campo = so_serializers.CustomDateInputFormat()
        self.assertEqual(campo.to_representation(datetime.date(2030, 1, 31)), "31/01/2030")
        self.assertIsNone(campo.to_internal_value(""))


class ReactivoIncrementoDecrementoSerializerTest(CovApiBase):
    """``IncreaseReactiveShelfObjectSerializer`` y ``DecreaseReactiveShelfObjectSerializer``."""

    def setUp(self):
        super().setUp()
        self.reactivo = ShelfObject.objects.get(pk=2)  # 23 ml
        self.ctx = {"source_laboratory_id": 1}

    def incremento(self, **extra):
        data = {"amount": 1, "description": "Compra", "shelf_object": self.reactivo.pk, "measurement_unit": MILILITROS}
        data.update(extra)
        return so_serializers.IncreaseReactiveShelfObjectSerializer(data=data, context=self.ctx)

    def decremento(self, **extra):
        data = {"amount": 1, "shelf_object": self.reactivo.pk, "measurement_unit": MILILITROS}
        data.update(extra)
        return so_serializers.DecreaseReactiveShelfObjectSerializer(data=data, context=self.ctx)

    def test_objeto_de_otro_laboratorio_o_que_no_es_reactivo(self):
        ShelfObject.objects.filter(pk=13).update(in_where_laboratory_id=1)
        self.assertIn("shelf_object", errores(self.incremento(shelf_object=13)))
        self.assertIn("shelf_object", errores(self.decremento(shelf_object=13)))
        ShelfObject.objects.filter(pk=self.reactivo.pk).update(in_where_laboratory_id=2)
        self.assertIn("shelf_object", errores(self.incremento()))
        self.assertIn("shelf_object", errores(self.decremento()))

    def test_decremento_sin_laboratorio_en_contexto(self):
        serializer = so_serializers.DecreaseReactiveShelfObjectSerializer(
            data={"amount": 1, "shelf_object": self.reactivo.pk}, context={}
        )
        self.assertIn("shelf_object", errores(serializer))

    def test_caja_salta_las_validaciones_de_unidad(self):
        caja = self.crear_caja(units_list=[5])
        Object.objects.filter(pk=6).update(type=Object.REACTIVE)
        self.assertTrue(self.incremento(shelf_object=caja.pk, measurement_unit=None).is_valid())
        self.assertIn("box_index", errores(self.decremento(shelf_object=caja.pk)))
        self.assertIn("box_index", errores(self.decremento(shelf_object=caja.pk, box_index=3)))
        self.assertIn("amount", errores(self.decremento(shelf_object=caja.pk, box_index=0, amount=9)))
        self.assertTrue(self.decremento(shelf_object=caja.pk, box_index=0, amount=2).is_valid())

    def test_unidad_requerida(self):
        self.assertIn("measurement_unit", errores(self.incremento(measurement_unit=None)))
        self.assertIn("measurement_unit", errores(self.decremento(measurement_unit=None)))

    def test_limites_del_objeto(self):
        self.reactivo.limits = ShelfObjectLimits.objects.create(minimum_limit=30, maximum_limit=40)
        self.reactivo.save()
        errors = errores(self.incremento(amount=1))
        self.assertIn("amount", errors)
        errors = errores(self.incremento(amount=100))
        self.assertIn("amount", errors)
        errors = errores(self.decremento(amount=1))
        self.assertIn("amount", errors)

    def test_unidad_incompatible(self):
        errors = errores(self.incremento(measurement_unit=METROS))
        self.assertIn("measurement_unit", errors)
        errors = errores(self.decremento(measurement_unit=METROS))
        self.assertIn("measurement_unit", errors)

    def test_errores_del_estante_se_agrupan(self):
        shelf = self.reactivo.shelf
        shelf.limit_only_objects = True
        shelf.quantity = 1
        shelf.infinity_quantity = False
        shelf.save()
        errors = errores(self.incremento(amount=5))
        self.assertIn("shelf_object", errors)
        self.assertIn("amount", errors)
        errors = errores(self.decremento(amount=500))
        self.assertIn("shelf_object", errors)
        self.assertIn("amount", errors)

    def test_error_de_estante_ajeno_al_objeto(self):
        from unittest import mock

        with mock.patch.object(
            so_serializers, "validate_measurement_unit_and_quantity", return_value={"container": "x"}
        ):
            self.assertIn("container", errores(self.incremento()))


class UtilidadesObjetoEnEstanteTest(CovApiBase):
    """Funciones de ``laboratory/shelfobject/utils.py``."""

    def request(self, **data):
        request = RequestFactory().get("/")
        request.user = self.user
        request.data = data
        return request

    def test_codigo_de_caja_evita_repetidos(self):
        codigo = so_utils.generate_box_code(7, existing_codes=["b7-AAAA"])
        self.assertTrue(codigo.startswith("b7-"))
        self.assertEqual(len(codigo), len("b7-AAAA"))

    def test_clonar_objeto_clona_tambien_los_limites(self):
        objeto = ShelfObject.objects.get(pk=2)
        objeto.limits = ShelfObjectLimits.objects.create(minimum_limit=1, maximum_limit=9)
        objeto.save()
        limites_originales = objeto.limits_id
        clon = so_utils.clone_shelfobject_to(objeto, 1, 1, Shelf.objects.get(pk=1), self.request(), quantity=2)
        self.assertNotEqual(clon.limits_id, limites_originales)
        self.assertEqual(clon.limits.maximum_limit, 9)

    def test_contenedores_en_estante_limitado(self):
        shelf = Shelf.objects.get(pk=15)
        shelf.limit_only_objects = True
        shelf.save()
        shelf.available_objects_when_limit.add(Object.objects.get(pk=5))
        disponibles = so_utils.get_available_containers_for_selection(1, shelf.pk)
        self.assertTrue(all(c.object_id == 5 for c in disponibles))
        clonables = so_utils.get_containers_for_cloning(1, shelf.pk)
        self.assertEqual(list(clonables), [])

    def test_validacion_de_unidad_y_cantidad(self):
        shelf = Shelf.objects.get(pk=1)  # ml
        objeto = Object.objects.get(pk=2)
        errors = so_utils.validate_measurement_unit_and_quantity(shelf, objeto, 0, measurement_unit=Catalog.objects.get(pk=METROS))
        self.assertIn("measurement_unit", errors)
        self.assertIn("quantity", errors)

    def test_capacidad_del_contenedor_en_estante(self):
        contenedor = ShelfObject.objects.get(pk=6)  # objeto 4, contenedor
        MaterialCapacity.objects.create(object=contenedor.object, capacity=5, capacity_measurement_unit_id=LITROS)
        shelf = Shelf.objects.get(pk=1)
        shelf.infinity_quantity = True
        shelf.save()
        objeto = ShelfObject.objects.get(pk=14)
        errors = so_utils.validate_measurement_unit_and_quantity(
            shelf, objeto.object, 10, measurement_unit=objeto.measurement_unit,
            container=contenedor, shelf_object=objeto, increase_unit=objeto.measurement_unit,
        )
        self.assertIn("quantity", errors)
        self.assertIn("measurement_unit", errors)

    def test_agrupa_errores_del_objeto(self):
        agrupados = so_utils.group_object_errors_for_serializer({"quantity": "q", "otro": "o"})
        self.assertEqual(agrupados, {"shelf_object": ["q"], "otro": "o"})

    def test_decremento_parcial_de_caja_sin_descripcion(self):
        caja = self.crear_caja(units_list=[10, 4])
        so_utils.save_increase_decrease_shelf_object(
            self.user, {"shelf_object": caja, "amount": 3, "box_index": 0}, self.lab, self.org
        )
        caja.refresh_from_db()
        self.assertEqual(caja.quantity_units[0]["units"], 7)
        observacion = ShelfObjectObservation.objects.filter(shelf_object=caja).latest("pk")
        self.assertIn("b-0", str(observacion.description))

    def test_incremento_de_caja_agrega_cajas(self):
        caja = self.crear_caja(units_list=[10])
        so_utils.save_increase_decrease_shelf_object(
            self.user, {"shelf_object": caja, "amount": 2}, self.lab, self.org, is_increase_process=True
        )
        caja.refresh_from_db()
        self.assertEqual(len(caja.quantity_units), 3)
        self.assertEqual(ShelfObjectObservation.objects.filter(shelf_object=caja).count(), 2)

    def test_incremento_de_caja_en_estante_con_unidad(self):
        caja = self.crear_caja(shelf_id=1, units_list=[10], unit=MILILITROS)
        so_utils.save_increase_decrease_shelf_object(
            self.user, {"shelf_object": caja, "amount": 1}, self.lab, self.org, is_increase_process=True
        )
        caja.refresh_from_db()
        self.assertEqual(len(caja.quantity_units), 2)

    def test_incremento_en_estante_sin_unidad(self):
        objeto = ShelfObject.objects.get(pk=8)  # estante 15 sin unidad, 2 ml
        so_utils.save_increase_decrease_shelf_object(
            self.user,
            {"shelf_object": objeto, "amount": 1, "measurement_unit": Catalog.objects.get(pk=LITROS)},
            self.lab, self.org, is_increase_process=True,
        )
        objeto.refresh_from_db()
        self.assertEqual(objeto.quantity, 1002)


class FormularioYLabviewTest(CovApiBase):
    """``TransferOutShelfObjectForm`` y las ramas del API del labview."""

    def test_formulario_de_transferencia_con_organizacion_inexistente(self):
        form = TransferOutShelfObjectForm(users=self.user, lab_send=1, org=99999)
        self.assertEqual(list(form.fields["laboratory"].queryset), [])

    def ruta(self, name, **extra):
        return reverse("laboratory:" + name, kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, **extra})

    def test_edita_muebles_y_estantes(self):
        response = self.client.patch(
            self.ruta("api-labview-furniture-detail", pk=1), data={"name": "Mueble renombrado"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(Furniture.objects.get(pk=1).name, "Mueble renombrado")

        response = self.client.patch(
            self.ruta("api-labview-shelf-detail", pk=3), data={"name": "Estante renombrado", "quantity": 5, "measurement_unit": MILILITROS},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(Shelf.objects.get(pk=3).name, "Estante renombrado")

    def test_crea_estante_limitado_a_objetos(self):
        response = self.client.post(
            self.ruta("api-labview-shelf-list") + "?furniture=1",
            data={
                "name": "Solo frascos", "type": 74, "quantity": 10, "measurement_unit": MILILITROS,
                "limit_only_objects": True, "available_objects_when_limit": [4, 5], "row": 0, "col": 0,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        estante = Shelf.objects.get(name="Solo frascos")
        self.assertEqual(set(estante.available_objects_when_limit.values_list("pk", flat=True)), {4, 5})

    def test_validaciones_del_estante(self):
        from laboratory.api.labview import serializers as labview_serializers

        def validar(**data):
            base = {"name": "E", "type": 74, "row": 0, "col": 0}
            base.update(data)
            return errores(labview_serializers.ValidateShelfSerializer(data=base))

        self.assertIn("measurement_unit", validar(quantity=0))
        self.assertIn("quantity", validar(quantity=0, measurement_unit=MILILITROS))
        self.assertIn("quantity", validar(quantity=-1, infinity_quantity=True))
        self.assertIn("measurement_unit", validar(quantity=5, discard=True))

    def test_porcentaje_de_ocupacion(self):
        from laboratory.api.labview import serializers as labview_serializers
        from laboratory.api.labview.tree_builder import TreeBuilder

        shelf = Shelf.objects.get(pk=1)
        shelf.quantity = 100
        shelf.infinity_quantity = False
        shelf.save()
        porcentaje = labview_serializers.ShelfAvailabilitySerializer().get_occupancy_percent(shelf)
        self.assertIsInstance(porcentaje, float)
        shelf.quantity = 0
        self.assertIsNone(TreeBuilder.occupancy_percent(None, shelf, {}))

    def test_quitar_fila_vacia_y_columna_ocupada(self):
        from laboratory import dataconfig

        mueble = Furniture.objects.get(pk=1)
        mueble.dataconfig = dataconfig.dump([[[1], [2]], [[3], [], [], []], [[], []]])
        mueble.save()
        response = self.client.post(
            self.ruta("api-labview-furniture-remove-row", pk=mueble.pk), data={"index": 2}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()["grid"]["cells"]), 2)
        response = self.client.post(
            self.ruta("api-labview-furniture-remove-col", pk=mueble.pk), data={"index": 0}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 409)

    def test_tabla_del_labview(self):
        response = self.client.get(self.ruta("api-labview-shelfobjecttable-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], [])
        response = self.client.get(self.ruta("api-labview-shelfobjecttable-list"), {"shelf": 1, "search": "pk=2"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["pk"] for r in response.json()["data"]], [2])


class FiltroSustanciasTest(CovApiBase):

    def test_busqueda_por_creador_o_nombre(self):
        from laboratory.api.filterset import SubstanceFilterSet
        from sga.models import Substance

        request = RequestFactory().get("/", {"search": "zzz-no-existe"})
        filtro = SubstanceFilterSet(data=request.GET, queryset=Substance.objects.all(), request=request)
        self.assertEqual(list(filtro.qs), [])
