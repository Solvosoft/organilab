"""
Vistas de ``laboratory/api/views.py`` y serializers de ``laboratory/api/serializers.py``
que quedaban sin ejercitar: reservas por pk, comentarios de informes, bitácora,
equipos, reactivos, materiales, incremento/decremento de reactivos y solicitudes
de laboratorio u organización.
"""

from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory
from django.urls import reverse

from laboratory.api import serializers as api_serializers
from laboratory.models import (
    Object,
    ShelfObject,
    Catalog,
    CommentInform,
    Inform,
    EquipmentType,
    EquipmentCharacteristics,
    ReactiveLimit,
    MaterialCapacity,
    LabOrOrgRequest,
    Laboratory,
    OrganizationStructure,
    OrganizationStructureRelations,
)
from laboratory.tests.test_cov_api_base import CovApiBase, UNIDADES, MILILITROS, LITROS
from reservations_management.models import ReservedProducts
from sga.models import SubstanceCharacteristics


class ReservasPorPkApiTest(CovApiBase):
    """``ApiReservedProductsCRUD``: lectura, cambio y borrado de un producto reservado."""

    def setUp(self):
        super().setUp()
        for codename in ("view_reservedproducts", "change_reservedproducts", "delete_reservedproducts"):
            self.user.user_permissions.add(Permission.objects.get(codename=codename))
        self.url_pk = reverse("laboratory:api_reservation_update", kwargs={"pk": 1})

    def test_lee_el_producto_reservado(self):
        response = self.client.get(self.url_pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["shelf_object"], 1)

    def test_cambio_invalido(self):
        response = self.client.put(self.url_pk, data={"status": "x"}, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.json())

    def test_producto_reservado_inexistente_da_404(self):
        response = self.client.get(reverse("laboratory:api_reservation_update", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, 404)

    def test_borra_el_producto_reservado(self):
        response = self.client.delete(reverse("laboratory:api_reservation_delete", kwargs={"pk": 2}))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ReservedProducts.objects.filter(pk=2).exists())

    def test_sin_permisos_responde_403(self):
        self.client.force_login(User.objects.get(username="tuwp"))
        # HandleErrorMiddleware convierte el 403 sin JSON en redirección.
        self.assertIn(self.client.get(self.url_pk).status_code, (302, 403))
        self.assertIn(self.client.put(self.url_pk, data={}, content_type="application/json").status_code, (302, 403))
        self.assertIn(self.client.delete(self.url_pk).status_code, (302, 403))
        self.assertTrue(ReservedProducts.objects.filter(pk=1).exists())

    def test_reservacion_invalida(self):
        self.user.user_permissions.add(Permission.objects.get(codename="add_reservations"))
        response = self.client.post(
            reverse("laboratory:api_individual_reservation_create"), data={"status": "x"}
        )
        self.assertEqual(response.status_code, 400)


class ComentariosInformeApiTest(CovApiBase):
    """``CommentAPI``: errores de validación y comentarios ajenos."""

    def setUp(self):
        super().setUp()
        self.inform = Inform.objects.first()
        self.comentario = CommentInform.objects.create(
            created_by=User.objects.get(username="renatafg"), comment="Ajeno", inform=self.inform
        )

    def ruta(self, pk=None):
        if pk is None:
            return reverse("laboratory:api-inform-list", kwargs={"org_pk": self.org.pk})
        return reverse("laboratory:api-inform-detail", kwargs={"org_pk": self.org.pk, "pk": pk})

    def test_crear_con_informe_inexistente(self):
        response = self.client.post(self.ruta(), data={"inform": 99999, "comment": "x"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("inform", response.json())

    def test_actualizar_con_informe_inexistente(self):
        response = self.client.put(
            self.ruta(self.comentario.pk), data={"inform": 99999, "comment": "x"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("inform", response.json())

    def test_no_actualiza_comentario_ajeno(self):
        response = self.client.put(
            self.ruta(self.comentario.pk),
            data={"comment": "Cambiado", "inform": self.inform.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.comentario.refresh_from_db()
        self.assertEqual(self.comentario.comment, "Ajeno")

    def test_crear_sin_texto_no_falla(self):
        response = self.client.post(self.ruta(), data={"inform": self.inform.pk})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(CommentInform.objects.filter(inform=self.inform, comment="", created_by=self.user).exists())

    def test_borrar_comentario_inexistente_da_404(self):
        response = self.client.delete(self.ruta(99999))
        self.assertEqual(response.status_code, 404)

    def test_no_borra_comentario_ajeno(self):
        response = self.client.delete(self.ruta(self.comentario.pk))
        self.assertEqual(response.status_code, 400)
        self.assertTrue(CommentInform.objects.filter(pk=self.comentario.pk).exists())


class BitacoraYListadosApiTest(CovApiBase):
    """Ramas de los listados: bitácora, protocolos, informes y serializers de bitácora."""

    def test_bitacora_filtra_por_usuario(self):
        LogEntry.objects.create(
            user=self.user,
            content_type=ContentType.objects.get_for_model(Laboratory),
            object_id=str(self.lab.pk),
            object_repr="Vick Lab",
            action_flag=2,
        )
        response = self.client.get(
            reverse("laboratory:api-logentry-list"), {"org_pk": self.org.pk, "user": "zzz-nadie"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], [])

    def test_bitacora_qr_no_numerico_no_devuelve_nada(self):
        response = self.client.get(reverse("laboratory:api-logentry-list"), {"qr_obj": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], [])

    def test_protocolos_sin_laboratorio(self):
        response = self.client.get(reverse("laboratory:api-protocol-list"), {"org_pk": self.org.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], [])

    def test_informes_sin_periodo(self):
        response = self.client.get(reverse("laboratory:api-informs-detail", kwargs={"pk": self.org.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], [])

    def test_serializers_de_bitacora(self):
        sin_nombre = User.objects.create_user(username="sinnombre")
        entrada = LogEntry(user=sin_nombre, action_flag=3, object_repr="x")
        self.assertEqual(api_serializers.LogEntryUserSerializer().get_user(entrada), "sinnombre")
        self.assertEqual(api_serializers.LogEntryUserSerializer().get_action_flag(entrada), "")
        self.assertEqual(api_serializers.LogEntrySerializer().get_user(entrada), "sinnombre")

    def test_accion_de_informe_sin_permiso(self):
        request = RequestFactory().get("/")
        request.user = User.objects.get(username="tuwp")
        serializer = api_serializers.InformSerializer(context={"request": request})
        self.assertEqual(serializer.get_action(self.lab), "")

    def test_accion_de_objeto_con_creador(self):
        objeto = ShelfObject.objects.get(pk=4)
        objeto.created_by = self.user
        serializer = api_serializers.ShelfObjectSerialize(context={"org_pk": self.org.pk})
        self.assertIn("/%d/" % self.user.pk, serializer.get_action(objeto))

    def test_registro_qr_sin_creador(self):
        from laboratory.models import RegisterUserQR

        self.assertEqual(api_serializers.RegisterUserQRSerializer().get_created_by(RegisterUserQR()), "")

    def test_accion_de_objeto_sin_creador(self):
        objeto = ShelfObject.objects.get(pk=4)
        objeto.created_by = None
        serializer = api_serializers.ShelfObjectSerialize(context={"org_pk": self.org.pk})
        self.assertEqual(serializer.get_action(objeto), "")


class ObjetosPorEstanteApiTest(CovApiBase):
    """``ShelfObjectAPI`` y ``ShelfObjectGraphicAPI`` (pantalla de desecho)."""

    def test_lista_objetos_del_estante(self):
        response = self.client.get(
            reverse("laboratory:api_shelfobject", kwargs={"org_pk": self.org.pk}), {"shelf": 15}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), ShelfObject.objects.filter(shelf=15).count())

    def test_grafico_del_estante(self):
        response = self.client.get(reverse("laboratory:api_shelfobject_graphic"), {"shelf": 1})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["labels"]), ShelfObject.objects.filter(shelf=1).count())
        self.assertEqual(len(data["labels"]), len(data["data"]))

    def test_grafico_de_estante_vacio(self):
        response = self.client.get(reverse("laboratory:api_shelfobject_graphic"), {"shelf": 999})
        self.assertEqual(response.json(), {"labels": [], "data": []})

    def test_anonimo_no_ve_objetos_ni_grafico(self):
        self.client.logout()
        response = self.client.get(
            reverse("laboratory:api_shelfobject", kwargs={"org_pk": self.org.pk}), {"shelf": 15}
        )
        self.assertIn(response.status_code, (401, 403))
        response = self.client.get(reverse("laboratory:api_shelfobject_graphic"), {"shelf": 1})
        self.assertIn(response.status_code, (401, 403))

    def test_usuario_de_otra_organizacion_no_ve_objetos(self):
        ajeno, org_ajena = self.crear_usuario_ajeno()
        self.client.force_login(ajeno)
        response = self.client.get(
            reverse("laboratory:api_shelfobject", kwargs={"org_pk": org_ajena.pk}), {"shelf": 15}
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.get(
            reverse("laboratory:api_shelfobject", kwargs={"org_pk": self.org.pk}), {"shelf": 15}
        )
        self.assertEqual(response.status_code, 403)


class EquiposApiTest(CovApiBase):
    """``EquipmentManagementViewset`` y ``EquipmentTypeManagementViewset``."""

    def setUp(self):
        super().setUp()
        self.tipo = EquipmentType.objects.get(pk=2)
        self.familia = Catalog.objects.create(key="instrumental_family", description="Óptica")
        self.equipo = Object.objects.get(pk=9)  # Microscopio
        self.caracteristicas = EquipmentCharacteristics.objects.create(
            object=self.equipo, equipment_type=self.tipo, instrumental_family=self.familia
        )
        self.caracteristicas.providers.add(1)

    def ruta(self, pk=None):
        kwargs = {"org_pk": self.org.pk, "lab_pk": self.lab.pk}
        if pk is None:
            return reverse("laboratory:api-equipment-list", kwargs=kwargs)
        kwargs["pk"] = pk
        return reverse("laboratory:api-equipment-detail", kwargs=kwargs)

    def datos(self, **extra):
        data = {
            "code": "MIC-1",
            "name": "Microscopio",
            "type": "2",
            "is_public": True,
            "features": [1],
            "providers": [1],
            "calibration_required": False,
            "operation_voltage": "",
            "operation_amperage": "",
            "generate_pathological_waste": False,
            "clean_period_according_to_provider": 3,
            "instrumental_family": None,
            "equipment_type": 2,
            "created_by": self.user.pk,
            "organization": self.org.pk,
            "model": "M-1",
            "serie": "S-1",
            "plaque": "P-1",
        }
        data.update(extra)
        return data

    def test_detalle_con_caracteristicas(self):
        response = self.client.get(self.ruta(self.equipo.pk))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["organization_name"], self.org.name)
        caracteristicas = data["equipment_characteristics"]
        self.assertEqual(caracteristicas["equipment_type"]["id"], self.tipo.pk)
        self.assertEqual(caracteristicas["instrumental_family"]["description"], "Óptica")
        self.assertEqual(caracteristicas["providers"][0]["id"], 1)
        self.assertIsNone(caracteristicas["use_manual"])

    def test_detalle_con_caracteristicas_incompletas(self):
        from laboratory.models import EquipmentCharacteristics as EC

        EC.objects.create(object_id=10, use_manual="manual.pdf")
        data = api_serializers.EquipmentDetailSerializer(Object.objects.get(pk=10)).data
        caracteristicas = data["equipment_characteristics"]
        self.assertIsNone(caracteristicas["equipment_type"])
        self.assertIsNone(caracteristicas["instrumental_family"])
        self.assertIn("use_manual", caracteristicas)

    def test_objetos_sin_organizacion(self):
        sin_org = Object(name="Huérfano")
        self.assertIsNone(api_serializers.EquipmentDetailSerializer().get_organization_name(sin_org))
        self.assertIsNone(api_serializers.ReactiveDetailSerializer().get_organization_name(sin_org))
        self.assertIsNone(api_serializers.ObjectMaterialDetailSerializer().get_organization_name(sin_org))

    def test_detalle_sin_caracteristicas(self):
        response = self.client.get(self.ruta(10))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["equipment_characteristics"])

    def test_listado_incluye_familia_y_tipo(self):
        response = self.client.get(self.ruta(), {"search": "Microscopio"})
        self.assertEqual(response.status_code, 200)
        fila = [r for r in response.json()["data"] if r["id"] == self.equipo.pk][0]
        self.assertEqual(fila["instrumental_family"]["id"], self.familia.pk)
        self.assertEqual(fila["equipment_type"]["id"], self.tipo.pk)

    def test_actualiza_equipo_con_caracteristicas(self):
        response = self.client.put(
            self.ruta(self.equipo.pk), data=self.datos(name="Microscopio óptico"), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.equipo.refresh_from_db()
        self.assertEqual(self.equipo.name, "Microscopio óptico")

    def test_proveedor_de_otro_laboratorio_se_rechaza(self):
        response = self.client.put(
            self.ruta(self.equipo.pk), data=self.datos(providers=[3]), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("providers", response.json())

    def test_actualizacion_con_ambos_serializers_invalidos(self):
        response = self.client.put(
            self.ruta(self.equipo.pk),
            data=self.datos(name="", clean_period_according_to_provider=-1),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())
        self.assertIn("clean_period_according_to_provider", response.json())

    def test_alta_con_caracteristicas_invalidas(self):
        response = self.client.post(
            self.ruta(), data=self.datos(code="NEW", providers=[3]), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("providers", response.json())
        self.assertFalse(Object.objects.filter(code="NEW").exists())

    def test_alta_con_ambos_serializers_invalidos(self):
        response = self.client.post(
            self.ruta(), data=self.datos(name="", clean_period_according_to_provider=-1), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())
        self.assertIn("clean_period_according_to_provider", response.json())

    def test_borra_equipo_con_caracteristicas(self):
        response = self.client.delete(self.ruta(self.equipo.pk))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Object.objects.filter(pk=self.equipo.pk).exists())
        self.assertFalse(EquipmentCharacteristics.objects.filter(pk=self.caracteristicas.pk).exists())

    def test_borrar_tipo_registra_equipos_y_objetos_en_estante(self):
        ShelfObject.objects.create(
            shelf_id=15, object=self.equipo, quantity=1, measurement_unit_id=UNIDADES,
            in_where_laboratory=self.lab, created_by=self.user,
        )
        response = self.client.delete(
            reverse(
                "laboratory:api-equipmenttype-detail",
                kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": self.tipo.pk},
            )
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(EquipmentType.objects.filter(pk=self.tipo.pk).exists())
        mensajes = list(LogEntry.objects.values_list("change_message", flat=True))
        self.assertTrue(any("Microscopio" in str(m) for m in mensajes))

    def test_mensaje_de_borrado_en_ingles(self):
        self.user.profile.language = "en"
        self.user.profile.save()
        request = RequestFactory().get("/")
        request.user = self.user
        serializer = api_serializers.EquipmentTypeSerializer(context={"request": request})
        mensaje = serializer.get_delete_msg(EquipmentType(name="Bomba"))
        # En inglés el nombre va justo después del verbo, antes de "equipment type".
        self.assertEqual(mensaje.split(" ")[1], "<b>Bomba</b>")


class ReactivosApiTest(CovApiBase):
    """``ReactiveManagementViewset``: detalle, límites y actualización."""

    def setUp(self):
        super().setUp()
        self.reactivo = Object.objects.get(pk=3)  # RA 100 gr, sin características
        self.rutas = {"org_pk": self.org.pk, "lab_pk": self.lab.pk}

    def ruta(self, name, **kwargs):
        kwargs.update(self.rutas)
        return reverse("laboratory:%s" % name, kwargs=kwargs)

    def caracteristicas_completas(self, objeto):
        catalogo = {
            key: Catalog.objects.create(key=key, description="%s 1" % key)
            for key in ("IARC", "IDMG", "white_organ", "Precursor", "ue_code", "nfpa", "storage_class")
        }
        sga = SubstanceCharacteristics.objects.create(
            object_related=objeto,
            iarc=catalogo["IARC"],
            imdg=catalogo["IDMG"],
            precursor_type=catalogo["Precursor"],
            bioaccumulable=True,
            security_sheet="hoja.pdf",
            img_representation="imagen.png",
        )
        sga.white_organ.add(catalogo["white_organ"])
        sga.ue_code.add(catalogo["ue_code"])
        sga.nfpa.add(catalogo["nfpa"])
        sga.storage_class.add(catalogo["storage_class"])
        return sga

    def test_detalle_con_caracteristicas(self):
        self.caracteristicas_completas(self.reactivo)
        response = self.client.get(self.ruta("api-reactive-detail", pk=self.reactivo.pk))
        self.assertEqual(response.status_code, 200)
        sga = response.json()["sustance_characteristics"]
        self.assertEqual(sga["iarc"]["description"], "IARC 1")
        self.assertEqual(sga["imdg"]["description"], "IDMG 1")
        self.assertEqual(sga["precursor_type"]["description"], "Precursor 1")
        self.assertEqual(len(sga["white_organ"]), 1)
        self.assertEqual(len(sga["ue_code"]), 1)
        self.assertEqual(len(sga["nfpa"]), 1)
        self.assertEqual(len(sga["storage_class"]), 1)
        self.assertIn("security_sheet", sga)
        self.assertIn("img_representation", sga)
        self.assertEqual(response.json()["organization_name"], self.org.name)

    def test_detalle_sin_caracteristicas(self):
        response = self.client.get(self.ruta("api-reactive-detail", pk=self.reactivo.pk))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["sustance_characteristics"])

    def test_detalle_de_caracteristicas_vacias(self):
        sga = SubstanceCharacteristics.objects.create(object_related=self.reactivo)
        data = api_serializers.SustanceCharacteristicsDetailSerializer(sga).data
        self.assertIsNone(data["iarc"])
        self.assertIsNone(data["imdg"])
        self.assertIsNone(data["precursor_type"])
        self.assertIsNone(data["security_sheet"])
        self.assertIsNone(data["img_representation"])

    def test_listado_con_limites_y_caracteristicas(self):
        self.caracteristicas_completas(self.reactivo)
        ReactiveLimit.objects.create(
            object=self.reactivo, laboratory=self.lab, measurement_unit_id=MILILITROS,
            minimum_limit=1, maximum_limit=9,
        )
        response = self.client.get(self.ruta("api-reactive-list"), {"search": "RA 100"})
        self.assertEqual(response.status_code, 200)
        fila = [r for r in response.json()["data"] if r["id"] == self.reactivo.pk][0]
        self.assertEqual(fila["maximum_limit"], 9)
        self.assertEqual(fila["minimum_limit"], 1)
        self.assertEqual(fila["measurement_unit"], MILILITROS)
        self.assertEqual(fila["maximum_limit_table"], 9)
        self.assertEqual(fila["minimum_limit_table"], 1)
        self.assertEqual(fila["measurement_unit_table"], "Mililitros")
        self.assertEqual(fila["iarc"]["text"], "IARC 1")
        self.assertEqual(fila["imdg"]["text"], "IDMG 1")
        self.assertEqual(fila["precursor_type"]["text"], "Precursor 1")
        self.assertEqual(len(fila["white_organ"]), 1)
        self.assertEqual(len(fila["ue_code"]), 1)
        self.assertEqual(len(fila["nfpa"]), 1)
        self.assertEqual(len(fila["storage_class"]), 1)
        self.assertIn("security_sheet", fila)
        self.assertIn("img_representation", fila)
        self.assertIn("fa-leaf", fila["combined_booleans"])

    def test_limites_del_reactivo(self):
        ReactiveLimit.objects.create(
            object=self.reactivo, laboratory=self.lab, measurement_unit_id=MILILITROS,
            minimum_limit=2, maximum_limit=7,
        )
        response = self.client.get(self.ruta("api-reactive-get-reactive-limits", pk=self.reactivo.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["maximum_limit"], 7)

    def limites(self, **extra):
        data = {
            "object": self.reactivo.pk,
            "laboratory": self.lab.pk,
            "measurement_unit": MILILITROS,
            "minimum_limit": 1,
            "maximum_limit": 5,
        }
        data.update(extra)
        return data

    def test_agrega_y_actualiza_limites(self):
        response = self.client.post(self.ruta("api-reactive-add-limits"), data=self.limites(), content_type="application/json")
        self.assertEqual(response.status_code, 201, response.content)
        response = self.client.post(
            self.ruta("api-reactive-add-limits") + "?reactive=%d" % self.reactivo.pk,
            data=self.limites(maximum_limit=8),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        limite = ReactiveLimit.objects.get(object=self.reactivo, laboratory=self.lab)
        self.assertEqual(limite.maximum_limit, 8)

    def test_limite_maximo_menor_que_minimo(self):
        response = self.client.post(
            self.ruta("api-reactive-add-limits"), data=self.limites(minimum_limit=9), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("maximum_limit", response.json())

    def test_limites_no_se_guardan_en_otro_laboratorio(self):
        response = self.client.post(
            self.ruta("api-reactive-add-limits"), data=self.limites(laboratory=2), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertFalse(ReactiveLimit.objects.filter(laboratory_id=2).exists())
        self.assertTrue(ReactiveLimit.objects.filter(laboratory=self.lab, object=self.reactivo).exists())

    def datos_reactivo(self, **extra):
        data = {
            "name": "RA 100 gr",
            "features": [1],
            "code": "RA43",
            "type": "0",
            "is_public": True,
            "created_by": self.user.pk,
            "molecular_formula": "C10H8",
            "organization": self.org.pk,
            "density": 1.0,
            "ue_code": [88],
            "white_organ": [5],
            "precursor_type": 85,
            "storage_class": [135],
        }
        data.update(extra)
        return data

    def test_actualiza_reactivo_sin_caracteristicas_las_crea(self):
        response = self.client.put(
            self.ruta("api-reactive-detail", pk=self.reactivo.pk),
            data=self.datos_reactivo(name="RA renombrado"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(self.reactivo.substancharacteristics_object.exists())

    def test_actualizacion_con_tipo_invalido(self):
        response = self.client.put(
            self.ruta("api-reactive-detail", pk=self.reactivo.pk),
            data=self.datos_reactivo(type="2"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("type", response.json())

    def test_actualizacion_con_organizacion_relacionada(self):
        # La organización 3 está relacionada con la 1 (fixture): el reactivo puede pasar a ella.
        response = self.client.put(
            self.ruta("api-reactive-detail", pk=self.reactivo.pk),
            data=self.datos_reactivo(organization=3),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.reactivo.refresh_from_db()
        self.assertEqual(self.reactivo.organization_id, 3)

    def test_actualizacion_con_organizacion_ajena(self):
        response = self.client.put(
            self.ruta("api-reactive-detail", pk=self.reactivo.pk),
            data=self.datos_reactivo(organization=2),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("organization", response.json())

    def test_actualizacion_con_caracteristicas_invalidas(self):
        response = self.client.put(
            self.ruta("api-reactive-detail", pk=self.reactivo.pk),
            data=self.datos_reactivo(density="densa"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("density", response.json())

    def test_actualizacion_con_ambos_serializers_invalidos(self):
        response = self.client.put(
            self.ruta("api-reactive-detail", pk=self.reactivo.pk),
            data=self.datos_reactivo(name="", density="densa"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())
        self.assertIn("density", response.json())

    def test_alta_con_caracteristicas_invalidas(self):
        response = self.client.post(
            self.ruta("api-reactive-list"),
            data=self.datos_reactivo(code="NUEVO", density="densa"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Object.objects.filter(code="NUEVO").exists())

    def test_serializer_de_limites_por_anio(self):
        serializer = api_serializers.ReactiveLimitsSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("years", serializer.errors)


class MaterialesApiTest(CovApiBase):
    """``ObjectValidateSerializer`` y el detalle de materiales."""

    def setUp(self):
        super().setUp()
        self.contenedor = Object.objects.get(pk=4)  # contenedor usado por el objeto 14

    def test_detalle_de_material_con_capacidad(self):
        MaterialCapacity.objects.create(object=self.contenedor, capacity=10, capacity_measurement_unit_id=LITROS)
        response = self.client.get(
            reverse("laboratory:api-object-detail", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": self.contenedor.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["material_capacity"]["capacity"], 10)
        self.assertEqual(data["material_capacity"]["capacity_measurement_unit"]["id"], LITROS)
        self.assertEqual(data["organization_name"], self.org.name)

    def test_detalle_de_material_sin_capacidad(self):
        data = api_serializers.ObjectMaterialDetailSerializer(Object.objects.get(pk=5)).data
        self.assertIsNone(data["material_capacity"])

    def validar(self, data, instance=None):
        base = {"code": "M-1", "name": "Probeta", "features": [1]}
        base.update(data)
        serializer = api_serializers.ObjectValidateSerializer(instance=instance, data=base)
        serializer.is_valid()
        return serializer

    def test_contenedor_requiere_capacidad(self):
        self.assertIn("capacity", self.validar({"is_container": True}).errors)

    def test_capacidad_negativa(self):
        self.assertIn("capacity", self.validar({"is_container": True, "capacity": -1}).errors)

    def test_crea_contenedor_con_capacidad(self):
        serializer = self.validar({"is_container": True, "capacity": 5, "capacity_measurement_unit": LITROS})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        objeto = serializer.save(organization=self.org, created_by=self.user)
        self.assertEqual(objeto.type, Object.MATERIAL)
        self.assertEqual(objeto.materialcapacity.capacity, 5)

    def test_contenedor_usado_no_deja_de_serlo(self):
        serializer = self.validar({"is_container": False}, instance=self.contenedor)
        self.assertIn("is_container", serializer.errors)

    def test_contenedor_usado_sin_capacidad_registrada(self):
        serializer = self.validar(
            {"is_container": True, "capacity": 5, "capacity_measurement_unit": LITROS}, instance=self.contenedor
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.contenedor.refresh_from_db()
        self.assertEqual(self.contenedor.materialcapacity.capacity, 5)

    def test_contenedor_usado_no_cambia_de_unidad(self):
        MaterialCapacity.objects.create(object=self.contenedor, capacity=10, capacity_measurement_unit_id=LITROS)
        serializer = self.validar(
            {"is_container": True, "capacity": 5, "capacity_measurement_unit": MILILITROS}, instance=self.contenedor
        )
        self.assertIn("capacity_measurement_unit", serializer.errors)

    def test_contenedor_sin_uso_actualiza_capacidad_y_unidad(self):
        libre = Object.objects.create(name="Probeta libre", code="PL", type=Object.MATERIAL, organization=self.org)
        serializer = self.validar(
            {"is_container": True, "capacity": 3, "capacity_measurement_unit": MILILITROS}, instance=libre
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        libre.refresh_from_db()
        self.assertEqual(libre.materialcapacity.capacity_measurement_unit_id, MILILITROS)

    def test_serializer_de_listado_y_hcode(self):
        request = RequestFactory().get("/")
        request.user = self.user
        MaterialCapacity.objects.create(object=self.contenedor, capacity=10, capacity_measurement_unit_id=LITROS)
        data = api_serializers.ObjectSerializer(self.contenedor, context={"request": request}).data
        self.assertEqual(data["capacity_measurement_unit"]["id"], LITROS)
        self.assertIsNone(api_serializers.ShelfObjectHcodeSerializer().get_h_code(ShelfObject.objects.get(pk=6)))


class ArchivoDeCargaSerializerTest(CovApiBase):

    def test_solo_acepta_xlsm(self):
        serializer = api_serializers.LoadArchiveSerializer()
        self.assertFalse(serializer.fields["lab_room"].required)

        class Archivo:
            name = "carga.xlsx"

        from rest_framework.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            serializer.validate_file(Archivo())
        Archivo.name = "carga.XLSM"
        self.assertIsInstance(serializer.validate_file(Archivo()), Archivo)


class IncrementoDecrementoReactivoApiTest(CovApiBase):
    """``ShelObjectReactiveViewset.increase``/``decrease`` y sus serializers."""

    def setUp(self):
        super().setUp()
        self.reactivo = ShelfObject.objects.get(pk=2)  # Cal 100 gr, 23 ml, estante 1 en ml

    def ruta(self, accion):
        return reverse(
            "laboratory:api-shelobjectsreactives-%s" % accion,
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )

    def test_incrementa_usando_la_unidad_del_objeto(self):
        response = self.client.post(
            self.ruta("increase"), data={"shelfobject": self.reactivo.pk, "amount": 2, "description": "Compra"}
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.reactivo.refresh_from_db()
        self.assertEqual(self.reactivo.quantity, 25)

    def test_incremento_invalido(self):
        response = self.client.post(self.ruta("increase"), data={"shelf_object": self.reactivo.pk, "amount": -2})
        self.assertEqual(response.status_code, 400)
        self.assertIn("amount", response.json()["errors"])

    def test_decrementa_con_motivo(self):
        response = self.client.post(
            self.ruta("decrease"), data={"shelfobject": self.reactivo.pk, "amount": 3, "measurement_unit": MILILITROS, "reason": "Práctica 4"}
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.reactivo.refresh_from_db()
        self.assertEqual(self.reactivo.quantity, 20)

    def test_miembro_sin_permiso_de_cambio_no_incrementa(self):
        from auth_and_perms.models import Profile, Rol

        miembro = User.objects.create_user(username="miembro")
        Profile.objects.create(user=miembro)
        self.org.users.add(miembro)
        solo_ver = Rol.objects.create(name="Solo ver", color="#FFF")
        solo_ver.permissions.add(Permission.objects.get(codename="view_shelfobject"))
        self.dar_rol(miembro, self.org, rol=solo_ver)
        self.client.force_login(miembro)
        response = self.client.post(
            self.ruta("increase"), data={"shelf_object": self.reactivo.pk, "amount": 2, "description": "x"}
        )
        self.assertEqual(response.status_code, 403)
        self.reactivo.refresh_from_db()
        self.assertEqual(self.reactivo.quantity, 23)

    def test_decremento_invalido(self):
        response = self.client.post(self.ruta("decrease"), data={"shelf_object": self.reactivo.pk, "amount": 3})
        self.assertEqual(response.status_code, 400)
        self.assertIn("measurement_unit", response.json()["errors"])


class SolicitudesLabOrgApiTest(CovApiBase):
    """``LabOrOrgRequestViewSet`` (solicitante) y ``LabOrOrgRequestReviewViewSet`` (revisor)."""

    def ruta(self, base, pk=None, accion=None, org=None):
        kwargs = {"org_pk": (org or self.org).pk}
        if pk is None:
            return reverse("laboratory:%s-list" % base, kwargs=kwargs)
        kwargs["pk"] = pk
        return reverse("laboratory:%s-%s" % (base, accion or "detail"), kwargs=kwargs)

    def solicitud(self, **extra):
        data = {
            "entity_type": LabOrOrgRequest.TYPE_LABORATORY,
            "name": "Lab nuevo",
            "organization": self.org,
            "requested_by": self.user,
        }
        data.update(extra)
        return LabOrOrgRequest.objects.create(**data)

    def test_crea_solicitud_de_laboratorio(self):
        response = self.client.post(
            self.ruta("api-labororgrequest"),
            data={"name": "Lab de suelos", "organization": self.org.pk, "is_org": False},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        solicitud = LabOrOrgRequest.objects.get(name="Lab de suelos")
        self.assertEqual(solicitud.entity_type, LabOrOrgRequest.TYPE_LABORATORY)
        self.assertEqual(solicitud.status, LabOrOrgRequest.STATUS_PENDING)
        self.assertEqual(solicitud.requested_by, self.user)

    def test_solicitud_no_se_crea_en_otra_organizacion(self):
        response = self.client.post(
            self.ruta("api-labororgrequest"),
            data={"name": "Lab infiltrado", "organization": 2, "is_org": False},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(LabOrOrgRequest.objects.get(name="Lab infiltrado").organization, self.org)

    def test_solicitud_de_laboratorio_requiere_organizacion(self):
        response = self.client.post(
            self.ruta("api-labororgrequest"), data={"name": "Sin org"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("organization", response.json())

    def test_solicitud_de_organizacion_requiere_padre(self):
        response = self.client.post(
            self.ruta("api-labororgrequest"), data={"name": "Sub", "is_org": True}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("parent_org", response.json())

    def test_crea_solicitud_de_organizacion(self):
        response = self.client.post(
            self.ruta("api-labororgrequest"),
            data={"name": "Sub org", "is_org": True, "parent_org": self.org.pk, "phone_number": "1"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        solicitud = LabOrOrgRequest.objects.get(name="Sub org")
        self.assertEqual(solicitud.entity_type, LabOrOrgRequest.TYPE_ORGANIZATION)
        self.assertEqual(solicitud.phone_number, "")

    def test_lista_y_actualiza_la_propia(self):
        solicitud = self.solicitud()
        response = self.client.get(self.ruta("api-labororgrequest"))
        self.assertEqual(response.status_code, 200)
        fila = response.json()["data"][0]
        self.assertFalse(fila["is_org"])
        self.assertEqual(fila["actions"], {"update": True, "destroy": True})
        response = self.client.patch(
            self.ruta("api-labororgrequest", pk=solicitud.pk),
            data={"name": "Lab renombrado", "is_org": True},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.name, "Lab renombrado")
        self.assertEqual(solicitud.entity_type, LabOrOrgRequest.TYPE_LABORATORY)

    def test_actualiza_solicitud_de_organizacion(self):
        solicitud = self.solicitud(entity_type=LabOrOrgRequest.TYPE_ORGANIZATION, parent_org=self.org)
        response = self.client.patch(
            self.ruta("api-labororgrequest", pk=solicitud.pk), data={"name": "Org renombrada"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200, response.content)

    def test_borra_la_propia(self):
        solicitud = self.solicitud()
        response = self.client.delete(self.ruta("api-labororgrequest", pk=solicitud.pk))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(LabOrOrgRequest.objects.filter(pk=solicitud.pk).exists())

    def test_no_borra_la_ajena(self):
        from laboratory.api.views import LabOrOrgRequestViewSet
        from rest_framework.exceptions import PermissionDenied

        solicitud = self.solicitud(requested_by=User.objects.get(username="renatafg"))
        vista = LabOrOrgRequestViewSet()
        vista.request = type("R", (), {"user": self.user})()
        with self.assertRaises(PermissionDenied):
            vista.perform_destroy(solicitud)
        self.assertTrue(LabOrOrgRequest.objects.filter(pk=solicitud.pk).exists())

    def test_revisor_lista_y_aprueba_laboratorio(self):
        solicitud = self.solicitud(organization=OrganizationStructure.objects.get(pk=1))
        solicitud.workplace.add(self.org)
        response = self.client.get(self.ruta("api-labororgrequest-review"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["data"][0]["actions"]["approve"])
        response = self.client.post(self.ruta("api-labororgrequest-review", pk=solicitud.pk, accion="approve"))
        self.assertEqual(response.status_code, 200, response.content)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.status, LabOrOrgRequest.STATUS_APPROVED)
        lab = Laboratory.objects.get(name="Lab nuevo")
        self.assertEqual(list(lab.workplace.all()), [self.org])
        self.assertTrue(
            OrganizationStructureRelations.objects.filter(
                organization=self.org, object_id=lab.pk,
                content_type=ContentType.objects.get_for_model(Laboratory),
            ).exists()
        )

    def test_revisor_aprueba_organizacion(self):
        solicitud = self.solicitud(entity_type=LabOrOrgRequest.TYPE_ORGANIZATION, name="Org hija", parent_org=self.org)
        response = self.client.post(self.ruta("api-labororgrequest-review", pk=solicitud.pk, accion="approve"))
        self.assertEqual(response.status_code, 200, response.content)
        hija = OrganizationStructure.objects.get(name="Org hija")
        self.assertEqual(hija.parent, self.org)

    def test_revisor_rechaza(self):
        solicitud = self.solicitud()
        response = self.client.post(self.ruta("api-labororgrequest-review", pk=solicitud.pk, accion="reject"))
        self.assertEqual(response.status_code, 200)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.status, LabOrOrgRequest.STATUS_REJECTED)
