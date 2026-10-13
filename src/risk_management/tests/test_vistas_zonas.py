"""Vistas de zonas de riesgo, edificios, estructuras e incidentes, sus selects y
su API: lo que cada vista hace y que un pk de otra organización no se cuele."""
import datetime
import io

import openpyxl
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from auth_and_perms.models import Profile
from laboratory.models import Catalog, UserOrganization
from risk_management.models import (
    EstablishmentLogs,
    IncidentReport,
    IPERAssessment,
    Regent,
    RiskZone,
    Structure,
    Workday,
)
from risk_management.tests.base import RiskTestCase, crear_usuario


def url(name, **kwargs):
    return reverse("riskmanagement:" + name, kwargs=kwargs)


# Sin esta cabecera los 403/404 de las páginas se convierten en una redirección
# a la página de error; con ella se ve el código real.
AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


class MiembroSinRolMixin:
    """Superusuario miembro de la organización pero sin rol en ella: pasa
    `user_is_allowed_on_organization` y falla `check_user_access_kwargs_org_lab`."""

    def miembro_sin_rol(self):
        user = User.objects.create_superuser("sin_rol", "sin_rol@example.com", "pass")
        Profile.objects.create(user=user)
        UserOrganization.objects.create(
            user=user, organization=self.organization, type_in_organization=1, status=True
        )
        return user


class ListZoneTest(RiskTestCase):

    def log(self, zone, **campos):
        return EstablishmentLogs.objects.create(
            content_type=ContentType.objects.get_for_model(RiskZone), object_id=zone.pk, **campos
        )

    def listar(self, **params):
        response = self.client.get(url("riskzone_list", org_pk=self.organization.pk), params)
        self.assertEqual(response.status_code, 200)
        return response

    def test_busqueda_por_nombre_o_laboratorio(self):
        RiskZone.objects.create(
            name="Bodega", organization=self.organization, num_workers=1, zone_type=self.zone_type
        )
        response = self.listar(q="Química")
        self.assertEqual([z.name for z in response.context["object_list"]], ["Zona propia"])
        self.assertEqual(response.context["pgparams"], "?q=Química&")
        self.assertTrue(response.context["eslochart"].endswith("?org_pk=%d&q=Química" % self.organization.pk))
        self.assertEqual(
            [z.name for z in self.listar(q="bodega").context["object_list"]], ["Bodega"]
        )

    def test_estado_segun_la_ultima_bitacora(self):
        self.log(self.zone, establishment_status="Riesgo mayor", physical=1.2,
                 date=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc))
        self.log(self.zone, establishment_status="Riesgo menor", physical=0.3,
                 xls_content="establishment/zona.xlsx")
        zona = self.listar().context["object_list"][0]
        self.assertEqual(zona.status, "Riesgo menor")
        self.assertTrue(zona.xls_url.endswith("establishment/zona.xlsx"))

    def test_bitacora_en_ceros_es_desconocido(self):
        self.log(self.zone, establishment_status="Riesgo menor", physical=0.0,
                 health=0.0, environmental=0.0)
        zona = self.listar().context["object_list"][0]
        self.assertEqual(zona.status, "Desconocido")
        self.assertIsNone(zona.xls_url)

    def test_solo_lista_las_zonas_de_la_organizacion(self):
        nombres = [z.name for z in self.listar().context["object_list"]]
        self.assertEqual(nombres, ["Zona propia"])


class ZonaDeOtraOrganizacionTest(RiskTestCase):
    """Detalle, edición y borrado de una zona solo desde su organización."""

    def test_zona_ajena_es_404(self):
        for name in ("riskzone_detail", "riskzone_update", "riskzone_delete"):
            with self.subTest(name=name):
                propia = self.client.get(url(name, org_pk=self.organization.pk, pk=self.zone.pk))
                self.assertEqual(propia.status_code, 200)
                ajena = self.client.get(url(name, org_pk=self.organization.pk, pk=self.other_zone.pk), **AJAX)
                self.assertEqual(ajena.status_code, 404)

    def test_no_se_borra_una_zona_ajena(self):
        response = self.client.post(
            url("riskzone_delete", org_pk=self.organization.pk, pk=self.other_zone.pk), **AJAX
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(RiskZone.objects.filter(pk=self.other_zone.pk).exists())

    def test_jornadas_de_una_zona_ajena_es_404(self):
        propia = self.client.get(url("workday_list", org_pk=self.organization.pk, risk_zone=self.zone.pk))
        self.assertEqual(propia.status_code, 200)
        self.assertEqual(propia.context["risk"], self.zone)
        ajena = self.client.get(url("workday_list", org_pk=self.organization.pk, risk_zone=self.other_zone.pk), **AJAX)
        self.assertEqual(ajena.status_code, 404)


class TipoDeZonaTest(MiembroSinRolMixin, RiskTestCase):

    def test_formulario_y_errores(self):
        destino = url("zone_type_add", org_pk=self.organization.pk)
        vacio = self.client.get(destino, {"tipo": "a b"}).json()
        self.assertTrue(vacio["ok"])
        self.assertIn("form", vacio["message"])
        invalido = self.client.post(destino, {"name": ""}).json()
        self.assertFalse(invalido["ok"])

    def test_sin_acceso_a_la_organizacion_es_404(self):
        self.client.force_login(self.miembro_sin_rol())
        response = self.client.get(url("zone_type_add", org_pk=self.organization.pk))
        self.assertEqual(response.status_code, 404)


class EdificiosTest(RiskTestCase):

    def test_editar_sin_permiso_de_cambio_es_403(self):
        user = crear_usuario("solo_crea_edificios", self.organization, permisos=["risk_management.add_buildings"])
        self.client.force_login(user)
        crear = self.client.get(url("buildings_create", org_pk=self.organization.pk))
        self.assertEqual(crear.status_code, 200)
        editar = self.client.get(url("buildings_update", org_pk=self.organization.pk, pk=self.building.pk), **AJAX)
        self.assertEqual(editar.status_code, 403)


class EstructurasTest(RiskTestCase):

    def datos(self, **extra):
        datos = {
            "name": "Tanque de agua",
            "type_structure": Catalog.objects.create(key="structure_type", description="Tanque").pk,
            "buildings": [self.building.pk],
            "area": "12.5",
            "measuerement_unit": Catalog.objects.create(key="distance_unit", description="m2").pk,
            "geolocation": "9.895804362670006,-84.1552734375",
            "manager": self.user.pk,
        }
        datos.update(extra)
        return datos

    def test_crear(self):
        response = self.client.post(url("structures_create", org_pk=self.organization.pk), self.datos())
        self.assertRedirects(response, url("structures_list", org_pk=self.organization.pk))
        estructura = Structure.objects.get(name="Tanque de agua")
        self.assertEqual(estructura.organization, self.organization)
        self.assertEqual(estructura.created_by, self.user)
        self.assertEqual(list(estructura.buildings.all()), [self.building])

    def test_formulario_invalido_no_crea(self):
        response = self.client.post(url("structures_create", org_pk=self.organization.pk), self.datos(name=""))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Structure.objects.exists())

    def test_estructura_ajena_es_404(self):
        datos = self.datos()
        ajena = Structure.objects.create(
            name="Ajena", organization=self.other, area=1,
            type_structure_id=datos["type_structure"], measuerement_unit_id=datos["measuerement_unit"],
        )
        response = self.client.get(url("structures_update", org_pk=self.organization.pk, pk=ajena.pk), **AJAX)
        self.assertEqual(response.status_code, 404)
        response = self.client.post(url("structures_update", org_pk=self.organization.pk, pk=ajena.pk), datos, **AJAX)
        self.assertEqual(response.status_code, 404)
        ajena.refresh_from_db()
        self.assertEqual((ajena.name, ajena.organization), ("Ajena", self.other))


class PanelDeZonasTest(RiskTestCase):

    def test_filtros_viajan_a_los_graficos(self):
        response = self.client.get(
            url("zone_dashboard", org_pk=self.organization.pk), {"risk_zone": [self.zone.pk, 99]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.context["nfpachart"].endswith(
                "?org_pk=%d&risk_zone=%d&risk_zone=99" % (self.organization.pk, self.zone.pk)
            )
        )


class IncidentesTest(RiskTestCase):

    def setUp(self):
        super().setUp()
        self.incidente = self.crear_incidente("Derrame de ácido")

    def crear_incidente(self, descripcion, zona=None):
        incidente = IncidentReport.objects.create(
            short_description=descripcion, incident_date=datetime.date(2026, 5, 1),
            causes="<p>Fuga</p>", infraestructure_impact="Piso", people_impact="Ninguno",
            environment_impact="<b>Vapores</b>", result_of_plans="Plan", mitigation_actions="Neutralizar",
            recomendations="Revisar", organization=self.organization, risk_zone=zona or self.zone,
        )
        incidente.laboratories.add(self.lab)
        incidente.buildings.add(self.building)
        return incidente

    def datos(self, **extra):
        datos = {
            "short_description": "Incendio",
            "incident_date": "2026-05-02",
            "laboratories": [self.lab.pk],
            "buildings": [self.building.pk],
            "causes": "Corto",
            "infraestructure_impact": "Pared",
            "people_impact": "Ninguno",
            "environment_impact": "Humo",
            "result_of_plans": "Evacuación",
            "mitigation_actions": "Extintor",
            "recomendations": "Revisar cableado",
            # El widget de carga por partes espera JSON aunque no se adjunte nada.
            "notification_copy": "{}",
        }
        datos.update(extra)
        return datos

    def kwargs(self, **extra):
        return dict(org_pk=self.organization.pk, building_pk=self.building.pk, **extra)

    def test_listado_con_busqueda(self):
        self.crear_incidente("Fuga de gas")
        response = self.client.get(url("incident_list", **self.kwargs()), {"q": "ácido"})
        self.assertEqual([i.short_description for i in response.context["object_list"]], ["Derrame de ácido"])
        self.assertEqual(response.context["pgparams"], "?q=ácido&")
        todos = self.client.get(url("incident_list", **self.kwargs()))
        self.assertEqual(todos.context["pgparams"], "?")
        self.assertEqual(len(todos.context["object_list"]), 2)

    def test_crear(self):
        response = self.client.post(url("incident_create", **self.kwargs()), self.datos())
        self.assertRedirects(response, url("riskzone_list", org_pk=self.organization.pk))
        incidente = IncidentReport.objects.get(short_description="Incendio")
        self.assertEqual(incidente.organization, self.organization)
        self.assertEqual(incidente.created_by, self.user)

    def test_editar(self):
        response = self.client.post(
            url("incident_update", **self.kwargs(pk=self.incidente.pk)), self.datos(short_description="Corregido")
        )
        self.assertRedirects(response, url("riskzone_list", org_pk=self.organization.pk))
        self.incidente.refresh_from_db()
        self.assertEqual(self.incidente.short_description, "Corregido")

    def test_detalle_y_borrado(self):
        detalle = self.client.get(url("incident_detail", **self.kwargs(pk=self.incidente.pk)))
        self.assertEqual(detalle.status_code, 200)
        self.assertEqual(detalle.context["object"], self.incidente)
        response = self.client.post(url("incident_delete", **self.kwargs(pk=self.incidente.pk)))
        self.assertRedirects(response, url("riskzone_list", org_pk=self.organization.pk))
        self.assertFalse(IncidentReport.objects.filter(pk=self.incidente.pk).exists())

    def reporte(self, risk_pk=None, pk=0, formato="xlsx"):
        return self.client.get(
            url("incident_report", org_pk=self.organization.pk, risk_pk=risk_pk or self.zone.pk, pk=pk),
            {"format": formato}, **AJAX,
        )

    def filas(self, response):
        self.assertEqual(response.status_code, 200)
        libro = openpyxl.load_workbook(io.BytesIO(response.content))
        return [[c.value for c in fila] for fila in libro.active.iter_rows()]

    def test_reporte_en_hoja_de_calculo(self):
        filas = self.filas(self.reporte())
        self.assertEqual(len(filas), 2)
        encabezado, fila = filas
        self.assertEqual(len(fila), len(encabezado))
        self.assertEqual(fila[2], "Derrame de ácido")
        self.assertEqual(fila[4], "Fuga")
        # Cada valor bajo su encabezado: faltaba el impacto ambiental.
        self.assertEqual(fila[7], "Vapores")
        self.assertEqual(fila[8], "Plan")
        self.assertEqual(fila[11], self.lab.name)
        self.assertEqual(fila[12], self.building.name)

    def test_reporte_de_un_incidente_de_la_zona(self):
        self.crear_incidente("Otro")
        filas = self.filas(self.reporte(pk=self.incidente.pk))
        self.assertEqual([f[2] for f in filas[1:]], ["Derrame de ácido"])

    def test_reporte_no_exporta_incidentes_de_otra_zona(self):
        otra_zona = self.crear_zona("Otra zona", self.organization, self.lab, self.building)
        ajeno = self.crear_incidente("De otra zona", zona=otra_zona)
        filas = self.filas(self.reporte(pk=ajeno.pk))
        self.assertEqual(filas[1:], [])

    def test_reporte_de_zona_ajena_es_404(self):
        self.assertEqual(self.reporte(risk_pk=self.other_zone.pk).status_code, 404)


class SelectsTest(RiskTestCase):

    def opciones(self, name, **params):
        response = self.client.get(reverse(name), params)
        self.assertEqual(response.status_code, 200, response.content)
        return [r["text"] for r in response.json()["results"]]

    def test_laboratorios_de_la_zona(self):
        self.assertEqual(
            self.opciones("risk_laboratories-list", org_pk=self.organization.pk, risk=self.zone.pk),
            [self.lab.name],
        )
        self.assertEqual(self.opciones("risk_laboratories-list", org_pk=self.organization.pk), [])

    def test_edificios_de_la_zona(self):
        self.assertEqual(
            self.opciones("risk_buildings-list", org_pk=self.organization.pk, risk=self.zone.pk),
            [self.building.name],
        )
        self.assertEqual(self.opciones("risk_buildings-list", org_pk=self.organization.pk), [])
        ajena = self.client.get(
            reverse("risk_buildings-list"), {"org_pk": self.organization.pk, "risk": self.other_zone.pk}
        )
        self.assertEqual(ajena.status_code, 404)

    def test_laboratorios_para_regentes(self):
        self.assertEqual(
            self.opciones("regent_laboratories-list", org_pk=self.organization.pk), [self.lab.name]
        )

    def test_organizacion_ajena_es_403(self):
        for name in ("risk_laboratories-list", "risk_buildings-list", "regent_laboratories-list"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name), {"org_pk": self.other.pk, "risk": self.other_zone.pk})
                self.assertEqual(response.status_code, 403)

    def test_sin_organizacion_es_400(self):
        for name in ("risk_laboratories-list", "risk_buildings-list", "regent_laboratories-list"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["status"], "Bad request")


class ApiTest(MiembroSinRolMixin, RiskTestCase):

    def listar(self, name, org=None, **kwargs):
        return self.client.get(url(name, org_pk=(org or self.organization).pk, **kwargs))

    def test_regentes(self):
        Regent.objects.create(user=self.user, organization=self.other)
        self.assertEqual(self.listar("api-regent-list").json()["recordsTotal"], 0)
        response = self.client.post(
            url("api-regent-list", org_pk=self.organization.pk),
            {"user": self.sin_permisos.pk, "laboratories": [self.lab.pk], "type_regent": "veterinarian"},
        )
        self.assertEqual(response.status_code, 201, response.content)
        regente = Regent.objects.get(user=self.sin_permisos)
        self.assertEqual(regente.organization, self.organization)
        self.assertEqual(self.listar("api-regent-list").json()["recordsTotal"], 1)

    def test_organizacion_ajena_es_403(self):
        for name, kwargs in (
            ("api-regent-list", {}),
            ("api-structure-list", {}),
            ("api-incident-list", {"risk": self.other_zone.pk}),
            ("api-workday-list", {"risk": self.other_zone.pk}),
        ):
            with self.subTest(name=name):
                self.assertEqual(self.listar(name, org=self.other, **kwargs).status_code, 403)

    def test_sin_sesion_es_401(self):
        self.client.logout()
        response = self.client.post(
            url("api-regent-list", org_pk=self.organization.pk),
            {"user": self.user.pk, "laboratories": [self.lab.pk], "type_regent": "chemical"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertFalse(Regent.objects.exists())
        self.assertEqual(self.listar("api-structure-list").status_code, 401)

    def test_zona_ajena_bajo_la_organizacion_propia(self):
        IncidentReport.objects.create(
            short_description="Ajeno", incident_date=datetime.date.today(), risk_zone=self.other_zone,
            causes="", infraestructure_impact="", people_impact="", environment_impact="",
            result_of_plans="", mitigation_actions="", recomendations="",
        )
        Workday.objects.create(
            workday="day shift", num_workers=1, start_time="08:00", end_time="16:00",
            risk_zone=self.other_zone, organization=self.other,
        )
        for name in ("api-incident-list", "api-workday-list"):
            with self.subTest(name=name):
                response = self.listar(name, risk=self.other_zone.pk)
                self.assertEqual(response.json()["recordsTotal"], 0)
        response = self.client.post(
            url("api-workday-list", org_pk=self.organization.pk, risk=self.other_zone.pk),
            {"workday": "night shift", "num_workers": 2, "start_time": "22:00", "end_time": "06:00"},
        )
        self.assertEqual(response.status_code, 404)

    def test_jornadas(self):
        Workday.objects.create(
            workday="turno raro", num_workers=4, start_time="08:00", end_time="16:00",
            risk_zone=self.zone, organization=self.organization,
        )
        response = self.listar("api-workday-list", risk=self.zone.pk)
        fila = response.json()["data"][0]
        self.assertEqual(fila["workday"]["text"], "turno raro")
        self.assertEqual(
            fila["actions"], {"list": True, "create": True, "update": True, "destroy": True}
        )

    def test_iper_sin_acceso_a_la_organizacion_es_404(self):
        self.client.force_login(self.miembro_sin_rol())
        self.assertEqual(self.listar("api-iperassessment-list").status_code, 404)

    def test_iper_sin_ver_todo_solo_lista_sus_laboratorios(self):
        # Laboratorio fuera de las organizaciones del lector.
        IPERAssessment.objects.create(
            organization=self.organization, laboratory=self.other_lab, assessment_date=datetime.date.today()
        )
        self.assertEqual(self.listar("api-iperassessment-list").json()["recordsTotal"], 1)
        user = crear_usuario("iper_lector", self.organization, permisos=["risk_management.view_iperassessment"])
        self.client.force_login(user)
        self.assertEqual(self.listar("api-iperassessment-list").json()["recordsTotal"], 0)
