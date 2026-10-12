import datetime
import json
from types import SimpleNamespace

from django.contrib import admin as django_admin
from django.contrib.contenttypes.models import ContentType
from django.test import SimpleTestCase, TestCase

from laboratory import admin as lab_admin
from laboratory import models
from presentation.models import QRModel


class _BaseConRelacionados:
    valor = False

    def get_list_select_related(self, request):
        return self.valor


class _InfoOrg(lab_admin.OrganizationInfoAdminMixin, _BaseConRelacionados):
    pass


class _AccionOrg(lab_admin.OrganizationWhereActionAdminMixin, _BaseConRelacionados):
    pass


class _Dual(lab_admin.DualOrganizationAdminMixin, _BaseConRelacionados):
    pass


class _SinPadre(lab_admin.OrganizationInfoAdminMixin):
    list_select_related = ("user",)


class MixinsDeOrganizacionTest(SimpleTestCase):
    """Los tres mixins añaden su campo de organización al select_related del listado."""

    def casos(self, clase, extra):
        admin = clase()
        for valor, esperado in [
            (True, True),
            (False, tuple(extra)),
            ("user", ("user",) + tuple(extra)),
            (["user"] + list(extra[:1]), ("user",) + tuple(extra)),
        ]:
            with self.subTest(clase=clase.__name__, valor=valor):
                admin.valor = valor
                self.assertEqual(admin.get_list_select_related(None), esperado)

    def test_select_related(self):
        self.casos(_InfoOrg, ["organization"])
        self.casos(_AccionOrg, ["organization_where_action_taken"])
        self.casos(_Dual, ["organization_creator", "organization_register"])
        self.assertEqual(_SinPadre().get_list_select_related(None), ("user", "organization"))

    def test_columnas_de_organizacion(self):
        org = SimpleNamespace(id=7, name="Org")
        for clase, campo in [(_InfoOrg, "organization"), (_AccionOrg, "organization_where_action_taken")]:
            admin = clase()
            self.assertEqual(admin.organization_id_display(SimpleNamespace(**{campo: org})), 7)
            self.assertEqual(admin.organization_name_display(SimpleNamespace(**{campo: org})), "Org")
            self.assertEqual(admin.organization_id_display(SimpleNamespace(**{campo: None})), "-")
            self.assertEqual(admin.organization_name_display(SimpleNamespace(**{campo: None})), "-")
        dual = _Dual()
        con = SimpleNamespace(organization_creator=org, organization_register=org)
        sin = SimpleNamespace(organization_creator=None, organization_register=None)
        self.assertEqual(
            [dual.organization_creator_id_display(con), dual.organization_creator_name_display(con),
             dual.organization_register_id_display(con), dual.organization_register_name_display(con)],
            [7, "Org", 7, "Org"],
        )
        self.assertEqual(
            {dual.organization_creator_id_display(sin), dual.organization_creator_name_display(sin),
             dual.organization_register_id_display(sin), dual.organization_register_name_display(sin)},
            {"-"},
        )


class AccionesYColumnasDelAdminTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.lab = models.Laboratory.objects.get(pk=1)
        self.org = models.OrganizationStructure.objects.get(pk=1)

    def registro(self, modelo):
        return django_admin.site._registry[modelo]

    def test_exportar_laboratorio_serializa_su_inventario(self):
        respuesta = lab_admin.export_laboratory(None, None, models.Laboratory.objects.filter(pk=self.lab.pk))
        self.assertEqual(respuesta["Content-Disposition"], 'attachment; filename="laboratory.json"')
        exportados = {(o["model"], o["pk"]) for o in json.loads(respuesta.content)}
        self.assertIn(("laboratory.laboratoryroom", 1), exportados)
        self.assertIn(("laboratory.furniture", 1), exportados)
        self.assertIn(("laboratory.shelf", 1), exportados)
        self.assertIn(("laboratory.shelfobject", 1), exportados)
        self.assertNotIn(("laboratory.laboratoryroom", 3), exportados)

    def test_regenerar_qr_crea_el_codigo(self):
        models.ShelfObject.objects.filter(pk=1).update(shelf_object_url="https://example.org/so/1")
        lab_admin.regenerate_qr_codes(None, None, models.ShelfObject.objects.filter(pk=1))
        ct = ContentType.objects.get_for_model(models.ShelfObject)
        qr = QRModel.objects.get(content_type=ct, object_id=1, organization=self.org)
        self.assertEqual(qr.qr_url, "https://example.org/so/1")

    def test_ejecutar_informes_programados(self):
        hoy = datetime.datetime.today().date()
        models.InformScheduler.objects.filter(pk=1).update(start_application_date=hoy, close_application_date=hoy)
        models.InformsPeriod.objects.filter(scheduler_id=1).delete()
        accion = self.registro(models.InformScheduler).actions[0]
        accion(None, None, models.InformScheduler.objects.filter(pk=1))
        self.assertEqual(models.InformsPeriod.objects.filter(scheduler_id=1, start_application_date=hoy).count(), 1)

    def test_columnas_de_listados(self):
        relaciones = self.registro(models.OrganizationStructureRelations)
        relacion = models.OrganizationStructureRelations.objects.get(pk=1)
        self.assertEqual(relaciones.content_object_display(relacion), str(self.lab))
        relacion.object_id = 99999
        self.assertEqual(relaciones.content_object_display(relacion), "-")

        bitacora = self.registro(models.ObjectLogChange)
        log = models.ObjectLogChange.objects.get(pk=1)
        self.assertEqual(bitacora.user_display(log), str(log.user))
        log.deleted_user_info = "Usuario eliminado"
        self.assertEqual(bitacora.user_display(log), "%s (Usuario eliminado)" % log.user)

        inventario = self.registro(models.ShelfObject)
        con_lab = models.ShelfObject.objects.get(pk=1)
        sin_lab = models.ShelfObject.objects.get(pk=4)
        self.assertEqual(
            [inventario.laboratory_name_display(con_lab), inventario.organization_id_display(con_lab),
             inventario.organization_name_display(con_lab)],
            ["Vick Lab", self.org.pk, self.org.name],
        )
        self.assertEqual(
            {inventario.laboratory_name_display(sin_lab), inventario.organization_id_display(sin_lab),
             inventario.organization_name_display(sin_lab)},
            {"-"},
        )

        arbol = self.registro(models.OrganizationStructure)
        hija = models.OrganizationStructure.objects.create(name="Hija", parent=self.org)
        hija.level = 2
        self.assertEqual(arbol.indented_name(hija), "—— Hija")
        hija.level = 0
        self.assertEqual(arbol.indented_name(hija), "Hija")
