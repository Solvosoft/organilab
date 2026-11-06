"""Informes de laboratorio (``views/informs.py``), agendador de informes
(``views/inform_period.py``) y la portada del laboratorio (``views/__init__.py``)."""

from django.test import RequestFactory
from django.urls import reverse

from derb.models import CustomForm
from laboratory.models import Inform, InformScheduler, Laboratory, OrganizationStructure
from laboratory.tests.utils import BaseLaboratorySetUpTest
from laboratory.views.informs import get_components_url, update_inform_data


class InformViewsTest(BaseLaboratorySetUpTest):

    def url(self, name, **kwargs):
        kwargs.update({"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        return reverse(f"laboratory:{name}", kwargs=kwargs)

    def test_eliminar_informe_inexistente_redirige_sin_borrar(self):
        total = Inform.objects.count()
        response = self.client.post(self.url("remove_inform", pk=999999))
        self.assertRedirects(response, self.url("get_informs"))
        self.assertEqual(Inform.objects.count(), total)

    def test_crear_informe_invalido_vuelve_a_mostrar_la_pagina(self):
        url = self.url("add_informs", content_type="laboratory", model="laboratory")
        total = Inform.objects.count()
        response = self.client.post(url, data={"name": "Sin plantilla"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "laboratory/inform.html")
        self.assertEqual(Inform.objects.count(), total)

    def test_crear_informe_reescribe_la_url_de_los_select_personalizados(self):
        plantilla = CustomForm.objects.create(
            name="Plantilla con selects",
            status="admin",
            organization=self.org,
            schema={
                "components": [
                    {
                        "type": "custom_select",
                        "key": "lab",
                        "data": {"api": "api_laboratory_by_org", "url": "/x/?lab=1"},
                    },
                    {
                        "type": "custom_select",
                        "key": "obj",
                        "data": {"api": "api_objects", "url": "/x/"},
                    },
                    {"type": "textfield", "key": "texto"},
                ]
            },
        )
        url = self.url("add_informs", content_type="laboratory", model="laboratory")
        response = self.client.post(
            url, data={"name": "Informe con selects", "custom_form": plantilla.pk}
        )
        self.assertRedirects(response, self.url("get_informs"))
        inform = Inform.objects.get(name="Informe con selects")
        componentes = inform.schema["components"]
        ruta_lab = reverse("derb:api_laboratory_by_org", kwargs={"org_pk": self.org.pk})
        ruta_obj = reverse("derb:api_objects", kwargs={"org_pk": self.org.pk})
        self.assertEqual(
            componentes[0]["data"]["url"], f"http://testserver{ruta_lab}?lab={self.lab.pk}"
        )
        self.assertEqual(componentes[1]["data"]["url"], f"http://testserver{ruta_obj}")

    def test_completar_informe_guarda_selects_casillas_y_filas(self):
        inform = Inform.objects.get(pk=1)
        inform.schema = {
            "components": [
                {"key": "texto", "type": "textfield", "defaultValue": ""},
                {"key": "uno", "type": "select", "defaultValue": ""},
                {"key": "varios", "type": "selectboxes", "defaultValue": {}},
                {
                    "key": "tabla",
                    "type": "table",
                    "rows": [[{"key": "celda", "type": "textfield", "defaultValue": ""}]],
                },
            ]
        }
        inform.save()
        response = self.client.post(
            self.url("complete_inform", pk=inform.pk),
            data={
                "csrfmiddlewaretoken": "x",
                "status": "Finalized",
                "data[texto]": "Hola",
                "data[uno]": ["a", "b"],
                "data[varios]": ["x", "y"],
                "data[celda]": "Valor",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["url"], self.url("get_informs"))
        inform.refresh_from_db()
        componentes = inform.schema["components"]
        self.assertEqual(inform.status, "Finalized")
        self.assertEqual(componentes[0]["defaultValue"], "Hola")
        self.assertEqual(componentes[1]["defaultValue"], ["a", "b"])
        self.assertEqual(componentes[2]["defaultValue"], {"x": True, "y": True})
        self.assertEqual(componentes[3]["rows"][0][0]["defaultValue"], "Valor")


class InformHelpersTest(BaseLaboratorySetUpTest):

    def test_update_inform_data_recorre_componentes_anidados(self):
        schema = {
            "components": [
                {
                    "key": "panel",
                    "components": [{"key": "dentro", "type": "custom_select", "defaultValue": None}],
                }
            ]
        }
        update_inform_data(schema, {"dentro": ["1", "2"]})
        self.assertEqual(schema["components"][0]["components"][0]["defaultValue"], ["1", "2"])

    def test_get_components_url_usa_https_si_la_peticion_es_segura(self):
        request = RequestFactory().get("/", secure=True)
        schema = {
            "components": [
                {"type": "custom_select", "data": {"api": "api_objects", "url": ""}}
            ]
        }
        get_components_url(request, schema, self.org.pk, self.lab.pk)
        self.assertTrue(schema["components"][0]["data"]["url"].startswith("https://testserver/"))


class InformSchedulerViewsTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()

    def datos(self, **extra):
        data = {
            "organization": self.org.pk,
            "name": "Agenda trimestral",
            "start_application_date": "2026-01-01",
            "close_application_date": "2026-01-31",
            "period_on_days": 90,
            "inform_template": 1,
            "laboratories": [self.lab.pk],
            "active": True,
        }
        data.update(extra)
        return data

    def test_crear_agendador_redirige_al_indice(self):
        response = self.client.post(
            reverse("laboratory:add_period_scheduler", kwargs={"org_pk": self.org.pk}),
            data=self.datos(),
        )
        self.assertRedirects(
            response, reverse("laboratory:inform_index", args=[self.org.pk])
        )
        scheduler = InformScheduler.objects.get(name="Agenda trimestral")
        self.assertEqual(scheduler.period_on_days, 90)
        self.assertEqual(list(scheduler.laboratories.all()), [self.lab])

    def test_editar_agendador_redirige_al_indice(self):
        scheduler = InformScheduler.objects.get(pk=1)
        data = self.datos(name="Agenda editada", period_on_days=30)
        response = self.client.post(
            reverse(
                "laboratory:edit_period_scheduler",
                kwargs={"org_pk": self.org.pk, "pk": scheduler.pk},
            ),
            data=data,
        )
        self.assertRedirects(
            response, reverse("laboratory:inform_index", args=[self.org.pk])
        )
        scheduler.refresh_from_db()
        self.assertEqual(scheduler.name, "Agenda editada")
        self.assertEqual(scheduler.period_on_days, 30)


class LabIndexTest(BaseLaboratorySetUpTest):

    def test_laboratorio_de_otra_organizacion_responde_404(self):
        # El laboratorio 3 del fixture no está relacionado con ninguna organización (el 1
        # sí lo está con varias, incluida «Organization Testing»).
        response = self.client.get(
            reverse("laboratory:labindex", kwargs={"org_pk": self.org.pk, "lab_pk": 3})
        )
        self.assertNegado(response, 404)

    def test_laboratorio_de_la_organizacion_renderiza_el_indice(self):
        lab = Laboratory.objects.get(pk=self.lab.pk)
        response = self.client.get(
            reverse("laboratory:labindex", kwargs={"org_pk": self.org.pk, "lab_pk": lab.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["laboratory"], lab.pk)
