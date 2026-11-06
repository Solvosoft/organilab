"""
Segunda pasada de cobertura sobre ``laboratory/api/views.py``,
``laboratory/api/serializers.py``, ``laboratory/utils.py`` y los listados de
``laboratory/api/labview/viewsets.py``.

Casi todo lo que quedaba eran ramas defensivas (sin ``lab_pk``/``org_pk`` en la
URL, relaciones opcionales vacías) que por HTTP no se alcanzan porque el
permiso o el router lo impiden antes: se prueban llamando al método, que es lo
que protegen. Lo demás son defectos corregidos, cada uno con su prueba.
"""

from types import SimpleNamespace

from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework.exceptions import ValidationError

from auth_and_perms.models import Profile
from laboratory import utils as lab_utils
from laboratory.api import serializers as api_serializers
from laboratory.api import views as api_views
from laboratory.models import (
    Furniture,
    LaboratoryRoom,
    Object,
    UserOrganization,
)
from laboratory.shelfobject import serializers as so_serializers
from laboratory.tests.test_cov_api_base import CovApiBase
from sga.models import SubstanceCharacteristics


class RamasSinParametrosDeUrlTest(CovApiBase):
    """Los viewsets se registran siempre con ``lab_pk``/``org_pk``; sin ellos
    deben devolver nada o negarse, no filtrar por ``None``."""

    def vista(self, clase, **kwargs):
        vista = clase()
        vista.kwargs = kwargs
        return vista

    def test_listados_sin_laboratorio_quedan_vacios(self):
        for clase in (
            api_views.LaboratoryProcessViewset,
            api_views.ShelfObjectHcodeViewset,
            api_views.ShelObjectReactiveViewset,
        ):
            with self.subTest(clase=clase.__name__):
                self.assertFalse(self.vista(clase).get_queryset().exists())

    def test_alta_sin_laboratorio_se_niega(self):
        for clase in (api_views.ProviderViewSet, api_views.ObjectFeatureViewSet):
            with self.subTest(clase=clase.__name__):
                with self.assertRaises(ValidationError) as error:
                    self.vista(clase).get_lab_pk_or_error()
                self.assertIn("lab_pk", error.exception.detail)
        self.assertEqual(
            self.vista(api_views.ProviderViewSet, lab_pk=self.lab.pk).get_lab_pk_or_error(),
            self.lab.pk,
        )

    def test_alta_de_material_sin_organizacion_se_niega(self):
        with self.assertRaises(ValidationError) as error:
            self.vista(api_views.ObjectViewSet).get_org_pk_or_error()
        self.assertIn("org_pk", error.exception.detail)


class BitacoraDeActualizacionDeReactivoTest(CovApiBase):
    """``ReactiveManagementViewset.update`` registraba siempre «Updated»: la
    existencia de las características se miraba después de guardarlas."""

    def test_caracteristicas_nuevas_se_registran_como_alta(self):
        reactivo = Object.objects.get(pk=3)  # sin características SGA
        self.assertFalse(reactivo.substancharacteristics_object.exists())
        response = self.client.put(
            reverse(
                "laboratory:api-reactive-detail",
                kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": reactivo.pk},
            ),
            data={
                "name": "RA 100 gr",
                "features": [1],
                "code": "RA43",
                "type": "0",
                "is_public": True,
                "created_by": self.user.pk,
                "organization": self.org.pk,
                "molecular_formula": "C10H8",
                "density": 1.0,
                "ue_code": [88],
                "white_organ": [5],
                "precursor_type": 85,
                "storage_class": [135],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        sga = reactivo.substancharacteristics_object.get()
        entrada = LogEntry.objects.get(
            content_type=ContentType.objects.get_for_model(SubstanceCharacteristics),
            object_id=str(sga.pk),
        )
        self.assertEqual(entrada.action_flag, ADDITION)


class PermisoDeLaboratorioPorGrupoTest(CovApiBase):
    """``check_lab_group_has_perm`` (lo usa la etiqueta ``has_perms``)."""

    def setUp(self):
        super().setUp()
        self.miembro = User.objects.create_user(username="miembro_sin_permisos", password="x")
        Profile.objects.create(user=self.miembro)
        self.org.users.add(self.miembro)
        UserOrganization.objects.create(
            organization=self.org, user=self.miembro, type_in_organization=1
        )

    def test_sin_usuario_o_sin_laboratorio(self):
        self.assertFalse(lab_utils.check_lab_group_has_perm(None, self.lab, "laboratory.view_shelf"))
        self.assertFalse(lab_utils.check_lab_group_has_perm(self.user, None, "laboratory.view_shelf"))

    def test_superusuario_y_anonimo(self):
        superusuario = User.objects.create_superuser("super_cov2", "s@x.com", "x")
        self.assertTrue(lab_utils.check_lab_group_has_perm(superusuario, self.lab, "laboratory.view_shelf"))
        self.assertFalse(lab_utils.check_lab_group_has_perm(AnonymousUser(), self.lab, "laboratory.view_shelf"))

    def test_miembro_de_la_organizacion_sin_permiso(self):
        # Antes: ``lab_org in user_org`` llevaba a ``get_ancestors``/``org.group``
        # (restos de MPTT) y la etiqueta reventaba con AttributeError.
        self.assertEqual(self.lab.organization, self.org)
        self.assertFalse(
            lab_utils.check_lab_group_has_perm(self.miembro, self.lab, "laboratory.view_shelf")
        )

    def test_usuario_sin_organizaciones(self):
        ajeno = User.objects.create_user(username="sin_organizacion_cov2", password="x")
        Profile.objects.create(user=ajeno)
        self.assertFalse(
            lab_utils.check_lab_group_has_perm(ajeno, self.lab, "laboratory.view_shelf")
        )

    def test_listados_auxiliares(self):
        self.assertIn(self.lab, lab_utils.filter_laboratorist_profile(self.miembro))
        self.assertIn(self.org, lab_utils.get_organizations_by_user(self.miembro))


class SerializersConRelacionesVaciasTest(CovApiBase):
    """Métodos de serializer ante objetos o relaciones opcionales vacías."""

    def test_protocolo_sin_objeto(self):
        self.assertEqual(api_serializers.ProtocolSerializer().get_file(None)["url"], "#")

    def test_bitacora_sin_usuario(self):
        for clase in (api_serializers.LogEntryUserSerializer, api_serializers.LogEntrySerializer):
            with self.subTest(clase=clase.__name__):
                self.assertEqual(str(clase().get_user(None)), "No user found")
                self.assertEqual(str(clase().get_user(SimpleNamespace(user=None))), "No user found")

    def test_accion_de_objeto_vacio(self):
        serializer = api_serializers.ShelfObjectSerialize(context={"org_pk": self.org.pk})
        self.assertEqual(serializer.get_action(None), "")

    def test_objeto_en_estante_sin_contenedor(self):
        serializer = api_serializers.ShelfObjectLaboratoryViewSerializer()
        self.assertEqual(serializer.get_container(SimpleNamespace(container=None)), "")

    def test_capacidad_sin_unidad(self):
        serializer = api_serializers.MaterialCapacityDetailSerializer()
        self.assertIsNone(
            serializer.get_capacity_measurement_unit(SimpleNamespace(capacity_measurement_unit=None))
        )

    def test_ubicacion_sin_estante(self):
        sin_estante = SimpleNamespace(shelf=None)
        for clase in (api_serializers.ShelfObjectHcodeSerializer, so_serializers.ShelObjectReactiveSerializer):
            with self.subTest(clase=clase.__name__):
                serializer = clase()
                self.assertIsNone(serializer.get_labroom(sin_estante))
                self.assertIsNone(serializer.get_furniture(sin_estante))
        self.assertIsNone(api_serializers.ShelfObjectHcodeSerializer().get_shelf(sin_estante))


class ListadosDelLabviewTest(CovApiBase):
    """Los listados de muebles y de estantes se acotan al padre de la URL."""

    def setUp(self):
        super().setUp()
        self.kwargs = {"org_pk": self.org.pk, "lab_pk": self.lab.pk}
        self.mueble = Furniture.objects.get(pk=1)

    def listar(self, nombre, parametro, valor):
        url = reverse("laboratory:%s" % nombre, kwargs=self.kwargs) + "?%s=%d" % (parametro, valor)
        return self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def test_salas_del_laboratorio(self):
        response = self.client.get(
            reverse("laboratory:api-labview-labroom-list", kwargs=self.kwargs),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200, response.content)
        pks = {fila["id"] for fila in response.json()["data"]}
        self.assertEqual(pks, set(self.lab.laboratoryroom_set.values_list("pk", flat=True)))

    def test_muebles_de_una_sala(self):
        sala = self.mueble.labroom
        response = self.listar("api-labview-furniture-list", "labroom", sala.pk)
        self.assertEqual(response.status_code, 200, response.content)
        pks = {fila["id"] for fila in response.json()["data"]}
        self.assertEqual(pks, set(Furniture.objects.filter(labroom=sala).values_list("pk", flat=True)))

    def test_estantes_de_un_mueble(self):
        response = self.listar("api-labview-shelf-list", "furniture", self.mueble.pk)
        self.assertEqual(response.status_code, 200, response.content)
        pks = {fila["id"] for fila in response.json()["data"]}
        self.assertEqual(pks, set(self.mueble.shelf_set.values_list("pk", flat=True)))

    def test_sala_de_otro_laboratorio_da_404(self):
        ajena = LaboratoryRoom.objects.exclude(laboratory=self.lab).first()
        response = self.listar("api-labview-furniture-list", "labroom", ajena.pk)
        self.assertEqual(response.status_code, 404)
