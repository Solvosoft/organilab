"""Etiquetas y filtros de ``laboratory/templatetags``.

Se prueban como funciones con un contexto armado a mano (``RequestFactory`` y un
``resolver_match`` con los kwargs de la URL), que es como las invoca el motor de
plantillas.
"""

from django.contrib.auth.models import AnonymousUser, User
from django.template import Context, Template
from django.test import RequestFactory
from django.urls import resolve, reverse

from academic.models import Procedure, ProcedureRequiredObject, ProcedureStep
from laboratory.models import Catalog, Object, Shelf, ShelfObject
from laboratory.templatetags import humanformat, shelf_objects, shelf_position
from laboratory.templatetags import laboratory as labtags
from laboratory.tests.utils import BaseLaboratorySetUpTest


class LaboratoryTagsTest(BaseLaboratorySetUpTest):

    def contexto(self, user, url_name="laboratory:rooms_list", **kwargs):
        if not kwargs:
            kwargs = {"org_pk": self.org.pk, "lab_pk": self.lab.pk}
        url = reverse(url_name, kwargs=kwargs)
        request = RequestFactory().get(url)
        request.user = user
        request.resolver_match = resolve(url)
        return {"request": request}

    def test_has_perms_sin_request_es_falso(self):
        self.assertFalse(labtags.has_perms({}, "laboratory.view_laboratory"))

    def test_has_perms_con_permiso_directo(self):
        context = self.contexto(self.user)
        self.assertTrue(labtags.has_perms(context, "laboratory.change_object"))

    def test_has_perms_sin_lab_en_la_url_es_falso(self):
        sin_permisos = User.objects.get(username="tuwp")
        context = self.contexto(
            sin_permisos, "laboratory:mylabs", org_pk=self.org.pk
        )
        self.assertFalse(labtags.has_perms(context, "laboratory.view_laboratory"))

    def test_has_perms_usuario_ajeno_al_laboratorio_es_falso(self):
        """Con lab_pk en la URL se consulta el laboratorio; sin organización común ni
        permiso, la respuesta es falsa."""
        sin_permisos = User.objects.get(username="tuwp")
        context = self.contexto(sin_permisos)
        self.assertFalse(labtags.has_perms(context, "laboratory.view_laboratory"))

    def test_index_permissions_combina_los_permisos(self):
        sin_permisos = User.objects.get(username="tuwp")
        dev = labtags.index_permissions(
            self.contexto(sin_permisos, "laboratory:mylabs", org_pk=self.org.pk)
        )
        self.assertFalse(dev["show_labview"])
        self.assertFalse(dev["admin_lab"])
        self.assertFalse(dev["show_reports"])

        sin_permisos.is_superuser = True
        dev = labtags.index_permissions(
            self.contexto(sin_permisos, "laboratory:mylabs", org_pk=self.org.pk)
        )
        self.assertTrue(dev["show_labview"])
        self.assertTrue(dev["admin_lab"])
        self.assertTrue(dev["show_reports"])

    def test_check_perms(self):
        self.assertTrue(labtags.check_perms(user=self.user, perm="laboratory.change_object"))
        self.assertFalse(labtags.check_perms(user=AnonymousUser(), perm="laboratory.change_object"))

    def test_get_user_labs(self):
        self.assertEqual(labtags.get_user_labs({}), [])
        labs = labtags.get_user_labs(self.contexto(self.user))
        self.assertIn(self.lab, labs)

    def test_show_laboratory_name(self):
        self.assertEqual(labtags.show_laboratory_name({"laboratory": self.lab.pk}), str(self.lab))
        self.assertEqual(labtags.show_laboratory_name({"laboratory": 999999}), "")
        self.assertEqual(labtags.show_laboratory_name({}), "")

    def test_filtros_to_int_y_get_lab_pk(self):
        self.assertEqual(labtags.to_int("7"), 7)
        self.assertEqual(labtags.get_lab_pk(""), 0)
        self.assertEqual(labtags.get_lab_pk("3"), "3")
        self.assertEqual(labtags.get_lab_pk(4), 4)
        self.assertIsNone(labtags.get_lab_pk(None))

    def test_show_reserve_button(self):
        procedimiento = Procedure.objects.create(title="Titulación", description="")
        paso = ProcedureStep.objects.create(procedure=procedimiento, title="Paso 1")
        self.assertFalse(labtags.show_reserve_button(procedimiento))
        ProcedureRequiredObject.objects.create(
            step=paso,
            object=Object.objects.first(),
            quantity=1,
            measurement_unit=Catalog.objects.filter(key="units").first(),
        )
        self.assertTrue(labtags.show_reserve_button(procedimiento))

    def test_get_laboratory_view_url_incluye_el_shelfobject(self):
        shelfobject = ShelfObject.objects.filter(in_where_laboratory=self.lab).first()
        context = self.contexto(self.user)
        context.update({"laboratory": self.lab.pk, "org_pk": self.org.pk})
        url = labtags.get_laboratory_view_url(context, shelfobject.shelf, shelfobject)
        self.assertTrue(
            url.endswith(f"?shelf={shelfobject.shelf.pk}&shelfobject={shelfobject.pk}")
        )
        self.assertIn(
            reverse("laboratory:rooms_list", kwargs={"lab_pk": self.lab.pk, "org_pk": self.org.pk}),
            url,
        )


class ShelfPositionTagsTest(BaseLaboratorySetUpTest):

    def test_print_position(self):
        self.assertEqual(shelf_position.print_position(0, 0, 0, 1), "A1")
        self.assertEqual(shelf_position.print_position(1, 2, 1, 3), "B3S2")
        self.assertEqual(shelf_position.print_position(26, 0, 0, 1), "AA1")

    def test_print_shelf(self):
        self.assertEqual(shelf_position.print_shelf("0", "1"), "A2")
        self.assertEqual(shelf_position.print_shelf(27, 0), "BB1")

    def test_get_laboratory_name(self):
        self.assertEqual(shelf_position.get_laboratory_name({"laboratory": self.lab.pk}), self.lab.name)
        self.assertEqual(shelf_position.get_laboratory_name({"laboratory": 999999}), "")
        self.assertEqual(shelf_position.get_laboratory_name({"laboratory": None}), "")
        self.assertEqual(shelf_position.get_laboratory_name({}), "")

    def test_plantilla_carga_las_etiquetas(self):
        html = Template(
            "{% load shelf_position %}{% print_position 2 0 0 1 %}|{% print_shelf 0 0 %}"
        ).render(Context({}))
        self.assertEqual(html, "C1|A1")


class HumanFormatFiltersTest(BaseLaboratorySetUpTest):

    def test_yesno(self):
        self.assertIn("fa-check-circle", humanformat.yesno(True))
        self.assertIn("fa-times-circle", humanformat.yesno(False))

    def test_yesnotext(self):
        self.assertEqual(humanformat.yesnotext(True), "Yes")
        self.assertEqual(humanformat.yesnotext(""), "No")


class ShelfObjectsTagsTest(BaseLaboratorySetUpTest):

    def test_porcentaje_del_laboratorio_con_desechos(self):
        shelfobject = ShelfObject.objects.filter(
            shelf__furniture__labroom__laboratory=self.lab
        ).first()
        shelf = shelfobject.shelf
        Shelf.objects.filter(pk=shelf.pk).update(quantity=100)
        ShelfObject.objects.filter(pk=shelfobject.pk).update(marked_as_discard=True)
        self.assertIn(shelf, shelf_objects.get_shelfs(self.lab))
        self.assertIn(shelfobject, shelf_objects.get_shelf_objects(shelf))
        estantes = Shelf.objects.filter(
            furniture__labroom__laboratory=self.lab, shelfobject__marked_as_discard=True
        ).distinct()
        con_cantidad = [s for s in estantes if s.quantity > 0]
        esperado = sum(s.get_refuse_porcentage() for s in estantes) / len(con_cantidad)
        self.assertAlmostEqual(shelf_objects.get_lab_porcentage(self.lab), esperado)

    def test_porcentaje_sin_desechos_es_cero(self):
        ShelfObject.objects.update(marked_as_discard=False)
        self.assertEqual(shelf_objects.get_lab_porcentage(self.lab), 0)
