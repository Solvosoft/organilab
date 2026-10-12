"""Lookups select2 de ``laboratory/gtselects.py``.

Cada lookup se ejercita por su ruta (``<basename>-list``) con el cliente de
pruebas: la respuesta válida, la petición mal formada (400) y, en los que reciben
la organización por query string, el rechazo a quien no pertenece a ella.
"""

import json

from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse

from auth_and_perms.models import Rol
from laboratory.models import (
    Catalog,
    EquipmentCharacteristics,
    EquipmentType,
    Laboratory,
    MaterialCapacity,
    Object,
    OrganizationStructure,
    Provider,
    Shelf,
)
from laboratory.tests.gtapi.base import TestCaseBase
from risk_management.models import Buildings, Regent
from sga.models import Pictogram


def otorgar(user, *perms):
    """Asigna permisos directos ``app_label.codename`` al usuario."""
    for perm in perms:
        app_label, codename = perm.split(".")
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
        )


class GTSelectsBase(TestCaseBase):

    def setUp(self):
        super().setUp()
        otorgar(
            self.user1,
            "laboratory.view_object",
            "laboratory.view_catalog",
            "laboratory.view_provider",
            "laboratory.view_equipmenttype",
            "laboratory.view_laboratory",
            "risk_management.view_regent",
            "risk_management.view_buildings",
            "risk_management.view_structure",
            "auth.view_user",
        )
        # user4 tiene los mismos permisos pero no pertenece a ninguna organización.
        otorgar(
            self.user4,
            "laboratory.view_provider",
            "laboratory.view_laboratory",
            "risk_management.view_regent",
            "auth.view_user",
        )

    def consultar(self, basename, data, client=None):
        client = client or self.client1
        response = client.get(
            reverse(f"{basename}-list"), data=data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        return response

    def resultados(self, response):
        self.assertEqual(response.status_code, 200, response.content)
        return json.loads(response.content)["results"]

    def textos(self, response):
        return [item["text"] for item in self.resultados(response)]

    def ids(self, response):
        return [item["id"] for item in self.resultados(response)]


class OrganizationRolsLookupTest(GTSelectsBase):

    def setUp(self):
        super().setUp()
        self.rol = Rol.objects.create(name="Rol de la organización", color="#000")
        Rol.objects.create(name="Rol de otra organización", color="#000")
        self.org1.rol.add(self.rol)

    def test_lista_solo_los_roles_de_la_raiz_de_la_organizacion(self):
        for basename in ("organization_rols", "organization_roles"):
            with self.subTest(basename=basename):
                response = self.consultar(basename, {"organization": self.org1.pk})
                self.assertEqual(self.textos(response), ["Rol de la organización"])

    def test_sin_organizacion_responde_400(self):
        for basename in ("organization_rols", "organization_roles"):
            with self.subTest(basename=basename):
                response = self.consultar(basename, {})
                self.assertEqual(response.status_code, 400)
                self.assertIn("organization", json.loads(response.content)["errors"])

    def test_usuario_ajeno_a_la_organizacion_recibe_403(self):
        for basename in ("organization_rols", "organization_roles"):
            with self.subTest(basename=basename):
                response = self.consultar(
                    basename, {"organization": self.org1.pk}, client=self.client4
                )
                self.assertEqual(response.status_code, 403)

    def test_superusuario_consulta_cualquier_organizacion(self):
        self.user4.is_superuser = True
        self.user4.save()
        response = self.consultar(
            "organization_roles", {"organization": self.org1.pk}, client=self.client4
        )
        self.assertEqual(self.textos(response), ["Rol de la organización"])

    def test_queryset_vacio_sin_organizacion(self):
        """Sin organización validada el lookup no lista nada (rama defensiva)."""
        from djgentelella.groute import routes

        for prefix, viewset, basename in routes.registry:
            if basename in ("organization_rols", "organization_roles"):
                vista = viewset()
                vista.org = None
                self.assertFalse(vista.get_queryset().exists())


class ObjectOrgSearchLookupTest(GTSelectsBase):

    def test_estante_limitado_devuelve_solo_los_objetos_permitidos(self):
        self.shelf.limit_only_objects = True
        self.shelf.save()
        permitido = Object.objects.get(pk=3)
        self.shelf.available_objects_when_limit.add(permitido)
        data = dict(self.data, objecttype=Object.MATERIAL)
        response = self.consultar("objectorgsearch", data)
        self.assertEqual(self.ids(response), [permitido.pk])

    def test_estante_sin_limite_devuelve_los_objetos_del_tipo_en_la_organizacion(self):
        data = dict(self.data, objecttype=Object.MATERIAL)
        response = self.consultar("objectorgsearch", data)
        self.assertEqual(
            sorted(self.ids(response)),
            sorted(
                Object.objects.filter(organization=self.org, type=Object.MATERIAL).values_list("pk", flat=True)
            ),
        )

    def test_peticion_sin_tipo_responde_400(self):
        response = self.consultar("objectorgsearch", self.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("objecttype", json.loads(response.content)["errors"])

    def test_queryset_vacio_sin_organizacion(self):
        from djgentelella.groute import routes

        vista = dict((b, v) for p, v, b in routes.registry)["objectorgsearch"]()
        self.assertFalse(vista.get_queryset().exists())


class CatalogUnitLookupTest(GTSelectsBase):

    def test_unidad_con_base_lista_las_convertibles(self):
        from laboratory.models import BaseUnitValues

        base = BaseUnitValues.objects.filter(measurement_unit=self.shelf.measurement_unit).first()
        if base is None:
            base = BaseUnitValues.objects.create(
                measurement_unit=self.shelf.measurement_unit,
                measurement_unit_base=self.shelf.measurement_unit,
                si_value=1,
            )
        esperado = BaseUnitValues.objects.filter(
            measurement_unit_base=base.measurement_unit_base
        ).values_list("measurement_unit__pk", flat=True)
        for basename in ("catalogunit", "catalogunitIncDec"):
            with self.subTest(basename=basename):
                response = self.consultar(basename, self.data)
                self.assertEqual(
                    json.loads(response.content)["total_count"],
                    Catalog.objects.filter(key="units", pk__in=list(esperado)).count(),
                )

    def test_estante_sin_unidad_lista_todas_las_unidades(self):
        Shelf.objects.filter(pk=self.shelf.pk).update(measurement_unit=None)
        response = self.consultar("catalogunit", self.data)
        self.assertEqual(
            json.loads(response.content)["total_count"],
            Catalog.objects.filter(key="units").count(),
        )

    def test_unidad_sin_base_registrada_no_lista_nada(self):
        unidad = Catalog.objects.create(key="units", description="Unidad sin base")
        Shelf.objects.filter(pk=self.shelf.pk).update(measurement_unit=unidad)
        response = self.consultar("catalogunit", self.data)
        self.assertEqual(self.resultados(response), [])

    def test_sin_estante_responde_400(self):
        data = dict(self.data)
        data.pop("shelf")
        response = self.consultar("catalogunit", data)
        self.assertEqual(response.status_code, 400)

    def test_queryset_vacio_sin_estante(self):
        from djgentelella.groute import routes

        vista = dict((b, v) for p, v, b in routes.registry)["catalogunit"]()
        self.assertFalse(vista.get_queryset().exists())


class CatalogUnitIncreaseDecreaseTest(GTSelectsBase):

    def test_unidad_del_objeto_sin_base_no_lista_nada(self):
        unidad = Catalog.objects.create(key="units", description="Unidad sin base")
        self.shelfobject.measurement_unit = unidad
        self.shelfobject.save()
        response = self.consultar("catalogunitIncDec", self.data)
        self.assertEqual(self.resultados(response), [])

    def test_sin_objeto_lista_todas_las_unidades(self):
        data = dict(self.data, shelfobject="")
        response = self.consultar("catalogunitIncDec", data)
        self.assertEqual(
            json.loads(response.content)["total_count"],
            Catalog.objects.filter(key="units").count(),
        )

    def test_objeto_de_otro_estante_responde_400(self):
        data = dict(self.data, shelf=2)
        response = self.consultar("catalogunitIncDec", data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("shelfobject", json.loads(response.content)["errors"])

    def test_queryset_vacio_sin_estante(self):
        from djgentelella.groute import routes

        vista = dict((b, v) for p, v, b in routes.registry)["catalogunitIncDec"]()
        self.assertFalse(vista.get_queryset().exists())


class ContainerLookupsTest(GTSelectsBase):

    def setUp(self):
        super().setUp()
        otorgar(self.user1, "laboratory.view_shelfobject")
        self.contenedor = Object.objects.get(pk=3)
        self.contenedor.is_container = True
        self.contenedor.save()
        self.unidad = Catalog.objects.get(pk=64)
        MaterialCapacity.objects.create(
            object=self.contenedor, capacity=500, capacity_measurement_unit=self.unidad
        )
        self.data.pop("shelfobject")

    def test_contenedores_disponibles_muestran_la_capacidad(self):
        response = self.consultar("available-container-search", self.data)
        textos = self.textos(response)
        self.assertTrue(textos)
        self.assertIn(f"500.0 {self.unidad.description}", textos[0])
        self.assertIn(self.contenedor.code, textos[0])

    def test_contenedores_disponibles_lab_ajeno_responde_400(self):
        data = dict(self.data, laboratory=self.lab2_org2.pk)
        response = self.consultar("available-container-search", data)
        self.assertEqual(response.status_code, 400)

    def test_contenedores_disponibles_sin_estante_no_lista_nada(self):
        """shelf es opcional en el serializer: antes su ausencia daba KeyError (500)."""
        self.data.pop("shelf")
        response = self.consultar("available-container-search", self.data)
        self.assertEqual(self.resultados(response), [])

    def test_contenedores_para_clonar_muestran_la_capacidad(self):
        response = self.consultar("container-for-cloning-search", self.data)
        self.assertEqual(
            self.textos(response),
            [
                f"{self.contenedor.code} {self.contenedor.name} - 500.0 {self.unidad.description}"
            ],
        )

    def test_contenedores_para_clonar_sin_estante_no_lista_nada(self):
        """shelf es opcional en el serializer: antes su ausencia daba KeyError (500)."""
        self.data.pop("shelf")
        response = self.consultar("container-for-cloning-search", self.data)
        self.assertEqual(self.resultados(response), [])

    def test_contenedores_para_clonar_lab_ajeno_responde_400(self):
        data = dict(self.data, laboratory=self.lab2_org2.pk)
        response = self.consultar("container-for-cloning-search", data)
        self.assertEqual(response.status_code, 400)


class LabScopedLookupsTest(GTSelectsBase):
    """Lookups validados con ``ValidateUserAccessOrgLabSerializer``."""

    def setUp(self):
        super().setUp()
        self.data = {"laboratory": self.lab.pk, "organization": self.org.pk}
        self.data_ajena = {"laboratory": self.lab2_org2.pk, "organization": self.org.pk}

    def test_estados_de_shelfobject(self):
        Catalog.objects.create(key="shelfobject_status", description="En revisión")
        response = self.consultar("shelfobject_status_search", self.data)
        self.assertIn("En revisión", self.textos(response))
        response = self.consultar("shelfobject_status_search", self.data_ajena)
        self.assertEqual(response.status_code, 400)

    def test_proveedores_del_laboratorio(self):
        Provider.objects.create(name="Proveedor propio", laboratory=self.lab)
        Provider.objects.create(name="Proveedor ajeno", laboratory=self.lab2_org2)
        response = self.consultar("provider", self.data)
        self.assertEqual(self.textos(response), ["Proveedor propio"])
        response = self.consultar("provider", self.data_ajena)
        self.assertEqual(response.status_code, 400)

    def test_queryset_vacio_sin_laboratorio(self):
        from djgentelella.groute import routes

        vistas = dict((b, v) for p, v, b in routes.registry)
        for basename in ("provider", "objectorgavailable"):
            with self.subTest(basename=basename):
                self.assertFalse(vistas[basename]().get_queryset().exists())

    def test_objetos_disponibles_de_la_organizacion(self):
        response = self.consultar("objectorgavailable", self.data)
        ids = self.ids(response)
        self.assertEqual(
            sorted(ids),
            sorted(Object.objects.filter(organization=self.org).values_list("pk", flat=True)),
        )
        response = self.consultar("objectorgavailable", self.data_ajena)
        self.assertEqual(response.status_code, 400)

    def test_familia_instrumental(self):
        Catalog.objects.create(key="instrumental_family", description="Ópticos")
        response = self.consultar("instrumentalfamily", self.data)
        self.assertEqual(self.textos(response), ["Ópticos"])
        response = self.consultar("instrumentalfamily", self.data_ajena)
        self.assertEqual(response.status_code, 400)

    def test_tipos_de_equipo(self):
        EquipmentType.objects.create(name="Centrífuga", description="")
        response = self.consultar("equipmenttype", self.data)
        self.assertIn("Centrífuga", self.textos(response))
        response = self.consultar("equipmenttype", self.data_ajena)
        self.assertEqual(response.status_code, 400)


class ObjectProvidersLookupTest(GTSelectsBase):

    def setUp(self):
        super().setUp()
        self.equipo = Object.objects.create(
            code="EQ1", name="Microscopio", type=Object.EQUIPMENT, organization=self.org
        )
        self.proveedor = Provider.objects.create(name="Proveedor equipo", laboratory=self.lab)
        Provider.objects.create(name="Otro proveedor", laboratory=self.lab)
        caracteristicas = EquipmentCharacteristics.objects.create(object=self.equipo)
        caracteristicas.providers.add(self.proveedor)
        self.data = {
            "laboratory": self.lab.pk,
            "organization": self.org.pk,
        }

    def test_lista_los_proveedores_del_equipo(self):
        response = self.consultar(
            "object_providers", dict(self.data, object=self.equipo.pk)
        )
        self.assertEqual(self.textos(response), ["Proveedor equipo"])

    def test_objeto_sin_caracteristicas_de_equipo_no_lista_nada(self):
        response = self.consultar("object_providers", dict(self.data, object=3))
        self.assertEqual(self.resultados(response), [])

    def test_sin_objeto_responde_400(self):
        response = self.consultar("object_providers", self.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("object", json.loads(response.content)["errors"])


class OrganizationPeopleLookupsTest(GTSelectsBase):
    """Perfiles, proveedores y usuarios de una organización (``ValidateOrganizationSerializer``)."""

    def setUp(self):
        super().setUp()
        # laboratory.view_profile y laboratory.view_user no existen como permisos:
        # solo un superusuario pasa la verificación de estos lookups.
        self.user1.is_superuser = True
        self.user1.save()
        self.user2.first_name = ""
        self.user2.last_name = ""
        self.user2.save()

    def test_perfiles_de_la_organizacion_usan_el_username_sin_nombre(self):
        response = self.consultar("org_profiles", {"organization": self.org1.pk})
        textos = self.textos(response)
        self.assertIn("User 1", textos)
        self.assertIn("user2", textos)
        self.assertNotIn("user4", textos)

    def test_perfiles_sin_organizacion_responde_400(self):
        response = self.consultar("org_profiles", {})
        self.assertEqual(response.status_code, 400)

    def test_perfiles_de_referencia_son_todos_los_activos(self):
        self.user3.is_active = False
        self.user3.save()
        response = self.consultar("profiles_ref", {})
        textos = self.textos(response)
        self.assertIn("user2", textos)
        self.assertIn("User 4", textos)
        self.assertNotIn("User 3", textos)

    def test_proveedores_de_la_organizacion(self):
        Provider.objects.create(name="Proveedor org 1", laboratory=self.lab1_org1)
        Provider.objects.create(name="Proveedor org 2", laboratory=self.lab2_org2)
        response = self.consultar("org_providers", {"organization": self.org1.pk})
        self.assertEqual(self.textos(response), ["Proveedor org 1"])
        response = self.consultar("org_providers", {})
        self.assertEqual(response.status_code, 400)

    def test_usuarios_de_la_organizacion(self):
        response = self.consultar("userorg", {"organization": self.org1.pk})
        self.assertEqual(sorted(self.textos(response)), ["User 1", "user2"])
        response = self.consultar("userorg", {})
        self.assertEqual(response.status_code, 400)

    def test_proveedores_y_usuarios_rechazan_a_quien_no_es_de_la_organizacion(self):
        for basename in ("org_providers", "org_profiles", "userorg"):
            with self.subTest(basename=basename):
                response = self.consultar(
                    basename, {"organization": self.org1.pk}, client=self.client4
                )
                self.assertEqual(response.status_code, 403)

    def test_querysets_vacios_sin_organizacion(self):
        from djgentelella.groute import routes

        vistas = dict((b, v) for p, v, b in routes.registry)
        for basename in ("org_profiles", "org_providers", "userorg"):
            with self.subTest(basename=basename):
                self.assertFalse(vistas[basename]().get_queryset().exists())


class RiskLookupsTest(GTSelectsBase):

    def setUp(self):
        super().setUp()
        self.org3 = OrganizationStructure.objects.create(name="Organización 3")
        self.regente = Regent.objects.create(user=self.user2, organization=self.org1)
        self.edificio = Buildings.objects.create(
            name="Edificio A", phone="2222-2222", organization=self.org1
        )

    def test_usuarios_de_riesgo(self):
        response = self.consultar("risk_users", {"org_pk": self.org1.pk})
        self.assertEqual(sorted(self.ids(response)), [self.user1.pk, self.user2.pk])

    def test_usuarios_de_riesgo_sin_organizacion_no_lista_nada(self):
        response = self.consultar("risk_users", {})
        self.assertEqual(self.resultados(response), [])

    def test_usuarios_de_riesgo_exige_autenticacion_y_pertenencia(self):
        response = self.consultar("risk_users", {"org_pk": self.org1.pk}, client=Client())
        self.assertEqual(response.status_code, 403)
        response = self.consultar(
            "risk_users", {"org_pk": self.org1.pk}, client=self.client4
        )
        self.assertEqual(response.status_code, 403)

    def test_regentes(self):
        response = self.consultar("risk_regents", {"org_pk": self.org1.pk})
        self.assertEqual(self.ids(response), [self.regente.pk])
        response = self.consultar("risk_regents", {})
        self.assertEqual(self.resultados(response), [])
        response = self.consultar(
            "risk_regents", {"org_pk": self.org1.pk}, client=self.client4
        )
        self.assertEqual(response.status_code, 403)

    def test_edificios(self):
        response = self.consultar("risk_building", {"org_pk": self.org1.pk})
        self.assertEqual(self.textos(response), ["Edificio A"])
        response = self.consultar("risk_building", {})
        self.assertEqual(self.resultados(response), [])

    def test_laboratorios_de_riesgo(self):
        response = self.consultar("risk_laboratory", {"org_pk": self.org1.pk})
        self.assertEqual(sorted(self.ids(response)), [self.lab1_org1.pk])
        response = self.consultar("risk_laboratory", {})
        self.assertEqual(self.resultados(response), [])
        response = self.consultar(
            "risk_laboratory", {"org_pk": self.org1.pk}, client=self.client4
        )
        self.assertEqual(response.status_code, 403)

    def test_estructuras(self):
        Catalog.objects.create(key="structure_type", description="Concreto")
        response = self.consultar("risk_structure", {"org_pk": self.org1.pk})
        self.assertIn("Concreto", self.textos(response))
        response = self.consultar("risk_structure", {})
        self.assertEqual(self.resultados(response), [])

    def test_usuarios_de_la_organizacion_raiz(self):
        self.user2.first_name = ""
        self.user2.last_name = ""
        self.user2.save()
        response = self.consultar("user_organization", {"org_pk": self.org1.pk})
        self.assertEqual(sorted(self.textos(response)), ["User 1", "user2"])
        response = self.consultar("user_organization", {})
        self.assertEqual(response.status_code, 400)
        response = self.consultar(
            "user_organization", {"org_pk": self.org1.pk}, client=self.client4
        )
        self.assertEqual(response.status_code, 403)

    def test_querysets_vacios_sin_organizacion(self):
        from djgentelella.groute import routes

        vistas = dict((b, v) for p, v, b in routes.registry)
        for basename in ("user_organization", "get_laboratories_by_organization"):
            with self.subTest(basename=basename):
                self.assertFalse(vistas[basename]().get_queryset().exists())


class MiscLookupsTest(GTSelectsBase):

    def test_pictogramas_devuelven_la_url_de_la_imagen(self):
        Pictogram.objects.create(name="ZZ prueba", pictogram="sga/zz_prueba.svg")
        response = self.consultar("imagebasename", {"term": "ZZ prueba"})
        resultados = self.resultados(response)
        self.assertEqual(len(resultados), 1)
        self.assertTrue(resultados[0]["url"].endswith("sga/zz_prueba.svg"))

    def test_laboratorios_por_organizacion(self):
        response = self.consultar(
            "get_laboratories_by_organization", {"organization": self.org1.pk}
        )
        self.assertEqual(
            sorted(self.ids(response)),
            sorted(Laboratory.objects.filter(pk__in=self.org1.get_my_laboratories).values_list("pk", flat=True)),
        )
        response = self.consultar("get_laboratories_by_organization", {})
        self.assertEqual(response.status_code, 400)
        response = self.consultar(
            "get_laboratories_by_organization",
            {"organization": self.org1.pk},
            client=self.client4,
        )
        self.assertEqual(response.status_code, 403)
