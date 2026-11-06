"""
Acciones de ``ShelfObjectViewSet`` (``laboratory/api/shelfobject.py``) que no
cubren las pruebas por acción de ``laboratory/tests/shelfobject``: altas en
estantes de desecho, edición de reactivos y materiales, límites, tamaños de
recipiente, borrado con reservas activas, contenedores y la búsqueda del labview.
"""

from django.urls import reverse

from laboratory.models import (
    ShelfObject,
    Shelf,
    Object,
    Catalog,
    ShelfObjectLimits,
    ShelfObjectObservation,
    Laboratory,
    OrganizationStructure,
)
from laboratory.tests.test_cov_api_base import (
    CovApiBase,
    UNIDADES,
    MILILITROS,
    METROS,
    ESTADO_EXCELENTE,
)
from sga.models import Pictogram, RecipientSize


class CrearEnEstanteDeDesechoApiTest(CovApiBase):
    """``create_shelfobject`` con estantes de desecho y errores de los métodos de alta."""

    def setUp(self):
        super().setUp()
        self.shelf = Shelf.objects.get(pk=13)  # 40 metros, mueble del laboratorio 1
        self.url_crear = self.url("api-shelfobject-create-shelfobject")

    def crear(self, data):
        return self.client.post(self.url_crear, data=data, content_type="application/json")

    def test_reactivo_de_desecho(self):
        self.shelf.discard = True
        self.shelf.save()
        pictograma = Pictogram.objects.create(name="Inflamable")
        data = {
            "shelf": self.shelf.pk,
            "object": 2,
            "objecttype": 0,
            "status": ESTADO_EXCELENTE,
            "quantity": 5,
            "measurement_unit": METROS,
            "batch": "D-1",
            "physical_status": "liquid",
            "pictograms": [pictograma.pk],
            "description": "Residuo de práctica",
            "minimum_limit": 0,
            "maximum_limit": 10,
            "container_select_option": "clone",
            "container_for_cloning": 4,
            "available_container": "",
        }
        response = self.crear(data)
        self.assertEqual(response.status_code, 201, response.content)
        creado = ShelfObject.objects.filter(shelf=self.shelf, object_id=2).latest("pk")
        self.assertTrue(creado.marked_as_discard)
        self.assertEqual(creado.quantity, 5)
        self.assertIsNotNone(creado.container)
        self.assertTrue(
            ShelfObjectObservation.objects.filter(
                shelf_object=creado, description="Residuo de práctica"
            ).exists()
        )

    def test_reactivo_de_desecho_en_estante_sin_unidad(self):
        shelf = Shelf.objects.get(pk=5)  # desecho, sin unidad
        shelf.infinity_quantity = True
        shelf.save()
        pictograma = Pictogram.objects.create(name="Tóxico")
        data = {
            "shelf": shelf.pk,
            "object": 2,
            "objecttype": 0,
            "status": ESTADO_EXCELENTE,
            "quantity": 3,
            "measurement_unit": MILILITROS,
            "batch": "D-2",
            "physical_status": "liquid",
            "pictograms": [pictograma.pk],
            "description": "Sin unidad",
            "minimum_limit": 0,
            "maximum_limit": 10,
            "container_select_option": "clone",
            "container_for_cloning": 4,
            "available_container": "",
        }
        response = self.crear(data)
        self.assertEqual(response.status_code, 201, response.content)
        creado = ShelfObject.objects.filter(shelf=shelf).latest("pk")
        self.assertEqual(creado.measurement_unit_id, MILILITROS)

    def equipo(self, **extra):
        data = {
            "shelf": self.shelf.pk,
            "object": 8,
            "objecttype": 2,
            "status": ESTADO_EXCELENTE,
            "limit_quantity": 0,
            "quantity": 1,
            "description": "Balanza nueva",
            "minimum_limit": 0,
            "maximum_limit": 0,
            "equipment_price": 100,
            "have_guarantee": False,
            "available_to_use": True,
            "notes": "",
        }
        data.update(extra)
        return data

    def test_equipo_de_desecho(self):
        self.shelf.discard = True
        self.shelf.save()
        response = self.crear(self.equipo())
        self.assertEqual(response.status_code, 201, response.content)
        creado = ShelfObject.objects.filter(shelf=self.shelf, object_id=8).latest("pk")
        self.assertTrue(creado.marked_as_discard)
        self.assertEqual(creado.measurement_unit.description, "Unidades")
        self.assertTrue(hasattr(creado, "shelfobjectequipmentcharacteristics"))

    def test_caracteristicas_invalidas_de_equipo_no_dejan_objeto(self):
        antes = ShelfObject.objects.filter(shelf=self.shelf).count()
        response = self.crear(self.equipo(equipment_price="caro"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("equipment_price", response.json()["errors"])
        self.assertEqual(ShelfObject.objects.filter(shelf=self.shelf).count(), antes)

    def test_caracteristicas_invalidas_de_equipo_de_desecho(self):
        self.shelf.discard = True
        self.shelf.save()
        antes = ShelfObject.objects.filter(shelf=self.shelf).count()
        response = self.crear(self.equipo(first_date_use="ayer"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("first_date_use", response.json()["errors"])
        self.assertEqual(ShelfObject.objects.filter(shelf=self.shelf).count(), antes)

    def test_limites_invalidos_no_crean_el_objeto(self):
        antes = ShelfObject.objects.filter(shelf=self.shelf).count()
        response = self.crear(self.equipo(objecttype=1, object=4, measurement_unit=METROS, minimum_limit=-1, maximum_limit=10))
        self.assertEqual(response.status_code, 400)
        self.assertIn("minimum_limit", response.json()["errors"])
        self.assertEqual(ShelfObject.objects.filter(shelf=self.shelf).count(), antes)

    def test_material_en_otra_unidad_toma_la_del_estante(self):
        data = {
            "shelf": self.shelf.pk,
            "object": 4,
            "objecttype": 1,
            "status": ESTADO_EXCELENTE,
            "quantity": 2,
            "limit_quantity": 0,
            "measurement_unit": METROS,
            "description": "Tubos",
            "minimum_limit": 0,
            "maximum_limit": 10,
        }
        response = self.crear(data)
        self.assertEqual(response.status_code, 201, response.content)


class EditarReactivoApiTest(CovApiBase):
    """``get_reactive_edit_data``, ``edit_reactive_shelfobject`` y ``get_shelfobject_limits``."""

    def setUp(self):
        super().setUp()
        self.reactivo = ShelfObject.objects.get(pk=2)  # Cal 100 gr, 23 ml
        self.reactivo.limits = ShelfObjectLimits.objects.create(minimum_limit=1, maximum_limit=50)
        self.reactivo.save()
        self.data = {
            "status": ESTADO_EXCELENTE,
            "description": "Reetiquetado",
            "reactive_expiration_date": "31/12/2031",
            "physical_status": "solid",
            "batch": "L-9",
            "minimum_limit": 2,
            "maximum_limit": 40,
        }

    def test_datos_de_edicion_incluyen_limites(self):
        response = self.client.get(self.url("api-shelfobject-get-reactive-edit-data", pk=self.reactivo.pk))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["minimum_limit"], 1)
        self.assertEqual(data["maximum_limit"], 50)

    def test_limites_del_objeto(self):
        response = self.client.get(self.url("api-shelfobject-get-shelfobject-limits", pk=self.reactivo.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["maximum_limit"], 50)

    def test_edita_reactivo_y_limites(self):
        response = self.client.put(
            self.url("api-shelfobject-edit-reactive-shelfobject", pk=self.reactivo.pk),
            data=self.data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.reactivo.refresh_from_db()
        self.assertEqual(self.reactivo.description, "Reetiquetado")
        self.assertEqual(self.reactivo.batch, "L-9")
        self.assertEqual(self.reactivo.limits.maximum_limit, 40)
        self.assertEqual(str(self.reactivo.reactive_expiration_date), "2031-12-31")

    def test_reactivo_sin_limites_los_crea(self):
        ShelfObject.objects.filter(pk=self.reactivo.pk).update(limits=None)
        response = self.client.put(
            self.url("api-shelfobject-edit-reactive-shelfobject", pk=self.reactivo.pk),
            data=self.data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.reactivo.refresh_from_db()
        self.assertEqual(self.reactivo.limits.minimum_limit, 2)

    def test_limite_minimo_mayor_que_maximo(self):
        data = dict(self.data, minimum_limit=30, maximum_limit=10)
        response = self.client.put(
            self.url("api-shelfobject-edit-reactive-shelfobject", pk=self.reactivo.pk),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("minimum_limit", response.json()["errors"])

    def test_limite_minimo_mayor_que_la_existencia(self):
        data = dict(self.data, minimum_limit=30, maximum_limit=60)
        response = self.client.put(
            self.url("api-shelfobject-edit-reactive-shelfobject", pk=self.reactivo.pk),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("minimum_limit", response.json()["errors"])

    def test_datos_del_reactivo_invalidos(self):
        data = dict(self.data)
        del data["description"]
        response = self.client.put(
            self.url("api-shelfobject-edit-reactive-shelfobject", pk=self.reactivo.pk),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("description", response.json()["errors"])

    def test_organizacion_relacionada_que_no_es_la_duena_no_edita(self):
        # El laboratorio 1 está relacionado con la organización 3, pero su dueña es la 1.
        org3 = OrganizationStructure.objects.get(pk=3)
        self.dar_rol(self.user, org3)
        response = self.client.put(
            self.url("api-shelfobject-edit-reactive-shelfobject", org=org3, pk=self.reactivo.pk),
            data=self.data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("shelfobject", response.json()["errors"])
        self.reactivo.refresh_from_db()
        self.assertNotEqual(self.reactivo.description, "Reetiquetado")

    def test_reactivo_de_otro_laboratorio_da_404(self):
        ShelfObject.objects.filter(pk=self.reactivo.pk).update(in_where_laboratory_id=2)
        response = self.client.put(
            self.url("api-shelfobject-edit-reactive-shelfobject", pk=self.reactivo.pk),
            data=self.data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)


class EditarMaterialApiTest(CovApiBase):
    """``edit_material_shelfobject``."""

    def setUp(self):
        super().setUp()
        self.material = ShelfObject.objects.get(pk=11)
        self.material.limits = ShelfObjectLimits.objects.create(minimum_limit=0, maximum_limit=5)
        self.material.save()

    def editar(self, **data):
        return self.client.put(
            self.url("api-shelfobject-edit-material-shelfobject", pk=self.material.pk),
            data=data,
            content_type="application/json",
        )

    def test_edita_material_y_limites(self):
        response = self.editar(status=ESTADO_EXCELENTE, description="Tubos limpios", batch="M-1", minimum_limit=1, maximum_limit=8)
        self.assertEqual(response.status_code, 200, response.content)
        self.material.refresh_from_db()
        self.assertEqual(self.material.description, "Tubos limpios")
        self.assertEqual(self.material.limits.maximum_limit, 8)

    def test_limites_invalidos(self):
        response = self.editar(status=ESTADO_EXCELENTE, description="x", batch="M-1", minimum_limit=-1, maximum_limit=8)
        self.assertEqual(response.status_code, 400)
        self.assertIn("minimum_limit", response.json()["errors"])

    def test_datos_invalidos(self):
        response = self.editar(status=999999, minimum_limit=0, maximum_limit=8)
        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.json()["errors"])


class RecipientesApiTest(CovApiBase):
    """``recipient_list``, ``create_recipient`` y ``delete_recipient``."""

    def setUp(self):
        super().setUp()
        self.recipiente = RecipientSize.objects.create(
            name="Frasco 250", height=12, width=6, laboratory=self.lab
        )
        self.ajeno = RecipientSize.objects.create(
            name="Frasco ajeno", height=1, width=1, laboratory=Laboratory.objects.get(pk=2)
        )

    def test_lista_solo_recipientes_del_laboratorio(self):
        response = self.client.get(self.url("api-shelfobject-recipient-list", pk=0))
        self.assertEqual(response.status_code, 200)
        nombres = [r["name"] for r in response.json()["data"]]
        self.assertEqual(nombres, ["Frasco 250"])
        self.assertEqual(response.json()["recordsTotal"], 1)

    def test_crea_recipiente_en_centimetros(self):
        response = self.client.post(
            self.url("api-shelfobject-create-recipient", pk=0),
            data={"name": "Tubo", "height": 10, "width": 2},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        creado = RecipientSize.objects.get(name="Tubo")
        self.assertEqual(creado.laboratory, self.lab)
        self.assertEqual(creado.height_unit, "cm")

    def test_recipiente_invalido(self):
        response = self.client.post(
            self.url("api-shelfobject-create-recipient", pk=0),
            data={"name": "Tubo", "height": -1, "width": 2},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("height", response.json()["errors"])

    def test_elimina_recipiente(self):
        response = self.client.delete(self.url("api-shelfobject-delete-recipient", pk=self.recipiente.pk))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(RecipientSize.objects.filter(pk=self.recipiente.pk).exists())

    def test_no_elimina_recipiente_de_otro_laboratorio(self):
        response = self.client.delete(self.url("api-shelfobject-delete-recipient", pk=self.ajeno.pk))
        self.assertEqual(response.status_code, 400)
        self.assertIn("recipient_size", response.json()["errors"])
        self.assertTrue(RecipientSize.objects.filter(pk=self.ajeno.pk).exists())


class BorradoYEtiquetaApiTest(CovApiBase):

    def test_no_borra_objeto_con_reservas_activas(self):
        # El objeto 1 tiene dos reservas sin cerrar en el fixture.
        response = self.client.delete(
            self.url("api-shelfobject-delete"),
            data={"shelfobj": 1},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(ShelfObject.objects.filter(pk=1).exists())

    def test_etiqueta_rechaza_usuario_de_otra_organizacion(self):
        ajeno, _org = self.crear_usuario_ajeno()
        self.client.force_login(ajeno)
        response = self.client.post(self.url("api-shelfobject-tag"))
        self.assertEqual(response.status_code, 403)


class ContenedoresApiTest(CovApiBase):
    """``manage_shelfobject_container`` y el movimiento de reactivos con contenedor."""

    def test_contenedor_invalido_devuelve_errores(self):
        response = self.client.post(
            self.url("api-shelfobject-manage-shelfobject-container"),
            data={"shelf": 1, "shelf_object": 2, "container_select_option": "available", "available_container": 999999},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("available_container", response.json()["errors"])

    def test_no_cambia_el_contenedor_de_un_objeto_de_otro_laboratorio(self):
        ajeno = ShelfObject.objects.get(pk=2)
        ShelfObject.objects.filter(pk=ajeno.pk).update(in_where_laboratory_id=2)
        contenedor_previo = ajeno.container_id
        response = self.client.post(
            self.url("api-shelfobject-manage-shelfobject-container"),
            data={
                "shelf": 1,
                "shelf_object": ajeno.pk,
                "container_select_option": "clone",
                "container_for_cloning": 4,
                "available_container": None,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("shelf_object", response.json()["errors"])
        ajeno.refresh_from_db()
        self.assertEqual(ajeno.container_id, contenedor_previo)

    def test_mover_reactivo_con_opcion_de_contenedor_invalida(self):
        shelf = Shelf.objects.get(pk=13)
        shelf.infinity_quantity = True
        shelf.measurement_unit = None
        shelf.save()
        response = self.client.post(
            self.url("api-shelfobject-move-shelfobject-to-shelf"),
            data={
                "shelf": shelf.pk,
                "furniture": shelf.furniture.pk,
                "lab_room": shelf.furniture.labroom.pk,
                "shelf_object": 2,
                "container_select_option": "available",
                "available_container": 999999,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("available_container", response.json()["errors"])


class TablaYBusquedaApiTest(CovApiBase):
    """``ShelfObjectTableViewSet`` con búsqueda por pk y ``SearchLabView``."""

    def test_tabla_busca_por_pk_cuando_el_texto_no_coincide(self):
        response = self.client.get(
            self.url("api-shelfobjecttable-list"), {"shelf": 1, "search": "pk=2"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["pk"] for r in response.json()["data"]], [2])

    def test_tabla_con_estante_de_otro_laboratorio(self):
        from laboratory.models import Furniture

        mueble = Furniture.objects.create(labroom_id=3, name="Ajeno", type_id=75)
        estante = Shelf.objects.create(furniture=mueble, name="Ajeno", type_id=74)
        response = self.client.get(self.url("api-shelfobjecttable-list"), {"shelf": estante.pk})
        self.assertEqual(response.status_code, 400)

    def test_tabla_busqueda_invalida_no_devuelve_nada(self):
        response = self.client.get(
            self.url("api-shelfobjecttable-list"), {"shelf": 1, "search": "zzzzz"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], [])

    def test_tabla_busqueda_por_pk_sin_igual_no_falla(self):
        response = self.client.get(
            self.url("api-shelfobjecttable-list"), {"shelf": 1, "search": "p1234"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], [])

    def buscar(self, **params):
        return self.client.get(self.url("api-search-labview-get"), params)

    def test_busqueda_por_cada_nivel(self):
        response = self.buscar(labroom=[1], furniture=[1], shelf=[1], shelfobject=[2], object=[2])
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()["search_list"]
        self.assertEqual(data["labroom"], [1])
        self.assertEqual(data["furniture"], {"furniture": [1], "labroom": [1]})
        self.assertEqual(data["shelf"], {"shelf": [1], "furniture": [1], "labroom": [1]})
        self.assertEqual(data["shelfobject"]["shelfobject"], [2])
        self.assertEqual(data["shelfobject"]["shelf"], [1])
        self.assertIn("Cal 100 gr", data["object"]["object"])
        self.assertIn(1, data["object"]["shelf"]["shelf"])

    def test_busqueda_vacia(self):
        response = self.buscar()
        self.assertEqual(response.status_code, 200)
        data = response.json()["search_list"]
        self.assertEqual(data["labroom"], {})
        self.assertEqual(data["object"], {})

    def test_busqueda_con_sala_de_otro_laboratorio(self):
        response = self.buscar(labroom=[3])
        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.json()["errors"])

    def test_busqueda_rechaza_cada_nivel_ajeno(self):
        from laboratory.models import Furniture, LaboratoryRoom

        sala = LaboratoryRoom.objects.get(pk=3)  # laboratorio 2
        mueble = Furniture.objects.create(labroom=sala, name="Ajeno", type_id=75)
        estante = Shelf.objects.create(furniture=mueble, name="Ajeno", type_id=74)
        objeto = ShelfObject.objects.create(
            shelf=estante, object_id=2, quantity=1, measurement_unit_id=UNIDADES,
            in_where_laboratory_id=2, created_by=self.user,
        )
        for params in ({"furniture": [mueble.pk]}, {"shelf": [estante.pk]}, {"shelfobject": [objeto.pk]}, {"object": [11]}):
            with self.subTest(params=params):
                response = self.buscar(**params)
                self.assertEqual(response.status_code, 400)

    def test_busqueda_sin_permisos(self):
        from django.contrib.auth.models import User

        sin_permisos = User.objects.get(username="tuwp")
        self.client.force_login(sin_permisos)
        response = self.buscar(labroom=[1])
        self.assertEqual(response.status_code, 403)
