"""Vistas IPER: el ciclo de una evaluación (crear, editar, completar, versionar,
duplicar, borrar), sus peligros y observaciones, el historial y el catálogo.

Complementa `test_iper.py`; todo se hace desde la organización propia y se
comprueba que un pk de otra organización no se cuele.
"""
import datetime
import io

import openpyxl
from django.urls import reverse

from laboratory.models import Catalog, Object, OrganizationStructure
from pending_tasks.models import PendingTask
from risk_management.iper_defaults import (
    KEY_CONSEQUENCE,
    KEY_HAZARD_CATEGORY,
    KEY_PROBABILITY,
    KEY_RISK_LEVEL,
)
from risk_management.models import (
    IPERAssessment,
    IPERConfig,
    IPERHazard,
    IPERObservation,
)
from risk_management.tests.base import RiskTestCase, crear_usuario
from risk_management.tests.test_vistas_zonas import AJAX, MiembroSinRolMixin

HOY = datetime.date.today()


def url(name, **kwargs):
    return reverse("riskmanagement:" + name, kwargs=kwargs)


class IPERBase(RiskTestCase):

    def setUp(self):
        super().setUp()
        self.org_pk = self.organization.pk
        self.quimico = Catalog.objects.get(key=KEY_HAZARD_CATEGORY, description="Químico")
        self.fisico = Catalog.objects.filter(key=KEY_HAZARD_CATEGORY).exclude(pk=self.quimico.pk).first()
        self.alta = Catalog.objects.get(key=KEY_PROBABILITY, description="Alta")
        self.baja = Catalog.objects.get(key=KEY_PROBABILITY, description="Baja")
        self.extremo = Catalog.objects.get(key=KEY_CONSEQUENCE, description="Extremadamente Dañino")
        self.ligero = Catalog.objects.get(key=KEY_CONSEQUENCE, description="Ligeramente Dañino")

    def evaluacion(self, **kwargs):
        datos = dict(
            organization=self.organization, laboratory=self.lab, assessment_date=HOY,
            responsible=self.user, created_by=self.user,
        )
        datos.update(kwargs)
        return IPERAssessment.objects.create(**datos)

    def peligro(self, evaluacion, **kwargs):
        datos = dict(
            assessment=evaluacion, category=self.quimico, description="Vapores",
            probability=self.alta, consequence=self.extremo,
        )
        datos.update(kwargs)
        return IPERHazard.objects.create(**datos)

    def detalle(self, evaluacion):
        return url("iper_detail", org_pk=self.org_pk, pk=evaluacion.pk)


class EvaluacionTest(MiembroSinRolMixin, IPERBase):

    def test_listado_sin_acceso_a_la_organizacion_es_404(self):
        self.client.force_login(self.miembro_sin_rol())
        response = self.client.get(url("iper_list", org_pk=self.org_pk), **AJAX)
        self.assertEqual(response.status_code, 404)

    def test_crear_calcula_el_vencimiento(self):
        IPERConfig.objects.create(organization=self.organization, period_months=6)
        self.lab.responsible = self.sin_permisos
        self.lab.save()
        response = self.client.post(
            url("iper_create", org_pk=self.org_pk),
            {"laboratory": self.lab.pk, "assessment_date": "2026-01-31"},
        )
        evaluacion = IPERAssessment.objects.get()
        self.assertRedirects(response, self.detalle(evaluacion), fetch_redirect_response=False)
        self.assertEqual(evaluacion.organization, self.organization)
        self.assertEqual(evaluacion.responsible, self.sin_permisos)
        self.assertEqual(evaluacion.due_date, datetime.date(2026, 7, 31))
        self.assertEqual(evaluacion.source, IPERAssessment.ON_DEMAND)

    def test_crear_sin_configuracion_no_vence(self):
        self.client.post(
            url("iper_create", org_pk=self.org_pk),
            {"laboratory": self.lab.pk, "assessment_date": "2026-01-31"},
        )
        evaluacion = IPERAssessment.objects.get()
        self.assertIsNone(evaluacion.due_date)
        self.assertEqual(evaluacion.responsible, self.user)

    def test_editar(self):
        evaluacion = self.evaluacion()
        response = self.client.post(
            url("iper_update", org_pk=self.org_pk, pk=evaluacion.pk),
            {"laboratory": self.lab.pk, "assessment_date": "2026-02-01"},
        )
        self.assertRedirects(response, self.detalle(evaluacion), fetch_redirect_response=False)
        evaluacion.refresh_from_db()
        self.assertEqual(evaluacion.assessment_date, datetime.date(2026, 2, 1))

    def test_evaluacion_de_otra_organizacion_es_404(self):
        ajena = self.evaluacion(organization=self.other, laboratory=self.other_lab)
        for name in ("iper_update", "iper_detail", "iper_toggle_anonymous",
                     "iper_toggle_status", "iper_clone", "iper_observation_add"):
            with self.subTest(name=name):
                response = self.client.get(url(name, org_pk=self.org_pk, pk=ajena.pk), **AJAX)
                self.assertEqual(response.status_code, 404)

    def test_anonimato(self):
        evaluacion = self.evaluacion(is_anonymous=True)
        response = self.client.get(url("iper_toggle_anonymous", org_pk=self.org_pk, pk=evaluacion.pk))
        self.assertRedirects(response, self.detalle(evaluacion), fetch_redirect_response=False)
        evaluacion.refresh_from_db()
        self.assertFalse(evaluacion.is_anonymous)

    def test_completar_reabrir_y_obsoleta(self):
        evaluacion = self.evaluacion()
        cambiar = url("iper_toggle_status", org_pk=self.org_pk, pk=evaluacion.pk)
        self.client.get(cambiar)
        evaluacion.refresh_from_db()
        self.assertEqual(evaluacion.status, IPERAssessment.COMPLETED)
        self.client.get(cambiar)
        evaluacion.refresh_from_db()
        self.assertEqual(evaluacion.status, IPERAssessment.DRAFT)
        IPERAssessment.objects.filter(pk=evaluacion.pk).update(status=IPERAssessment.OBSOLETE)
        response = self.client.get(cambiar)
        self.assertRedirects(response, self.detalle(evaluacion), fetch_redirect_response=False)
        evaluacion.refresh_from_db()
        self.assertEqual(evaluacion.status, IPERAssessment.OBSOLETE)


class PeligrosTest(IPERBase):

    def datos(self, **extra):
        datos = {
            "category": self.quimico.pk, "description": "Mezcla", "location": "Mesa",
            "probability": self.baja.pk, "consequence": self.ligero.pk,
            "controls": "", "recommended_controls": "",
        }
        datos.update(extra)
        return datos

    def test_editar_un_peligro_recalcula_el_nivel(self):
        evaluacion = self.evaluacion()
        peligro = self.peligro(evaluacion)
        response = self.client.post(
            url("iper_hazard_update", org_pk=self.org_pk, assessment_pk=evaluacion.pk, pk=peligro.pk),
            self.datos(),
        )
        self.assertRedirects(response, self.detalle(evaluacion), fetch_redirect_response=False)
        peligro.refresh_from_db()
        self.assertEqual(peligro.description, "Mezcla")
        self.assertEqual(peligro.risk_level.description, "Trivial")

    def test_formulario_invalido_no_guarda(self):
        evaluacion = self.evaluacion()
        self.client.post(
            url("iper_hazard_create", org_pk=self.org_pk, assessment_pk=evaluacion.pk),
            self.datos(description=""),
        )
        self.assertFalse(evaluacion.hazards.exists())

    def test_peligro_de_otra_evaluacion_es_404(self):
        evaluacion = self.evaluacion()
        otro = self.peligro(self.evaluacion())
        for name in ("iper_hazard_update", "iper_hazard_delete"):
            with self.subTest(name=name):
                response = self.client.post(
                    url(name, org_pk=self.org_pk, assessment_pk=evaluacion.pk, pk=otro.pk), self.datos(), **AJAX
                )
                self.assertEqual(response.status_code, 404)
        self.assertTrue(IPERHazard.objects.filter(pk=otro.pk).exists())

    def test_borrar(self):
        evaluacion = self.evaluacion()
        peligro = self.peligro(evaluacion)
        response = self.client.post(
            url("iper_hazard_delete", org_pk=self.org_pk, assessment_pk=evaluacion.pk, pk=peligro.pk)
        )
        self.assertRedirects(response, self.detalle(evaluacion), fetch_redirect_response=False)
        self.assertFalse(IPERHazard.objects.filter(pk=peligro.pk).exists())

    def test_evaluacion_completada_no_se_modifica(self):
        evaluacion = self.evaluacion(status=IPERAssessment.COMPLETED)
        peligro = self.peligro(evaluacion)
        self.client.post(
            url("iper_hazard_create", org_pk=self.org_pk, assessment_pk=evaluacion.pk), self.datos()
        )
        response = self.client.post(
            url("iper_hazard_delete", org_pk=self.org_pk, assessment_pk=evaluacion.pk, pk=peligro.pk)
        )
        self.assertRedirects(response, self.detalle(evaluacion), fetch_redirect_response=False)
        self.assertEqual(list(evaluacion.hazards.all()), [peligro])


class ObservacionesTest(IPERBase):

    def observar(self, evaluacion, texto="Revisar campana"):
        return self.client.post(url("iper_observation_add", org_pk=self.org_pk, pk=evaluacion.pk), {"text": texto})

    def test_guarda_la_observacion(self):
        evaluacion = self.evaluacion(responsible=self.sin_permisos)
        response = self.observar(evaluacion)
        self.assertRedirects(response, self.detalle(evaluacion), fetch_redirect_response=False)
        observacion = IPERObservation.objects.get()
        self.assertEqual((observacion.author, observacion.text), (self.user, "Revisar campana"))

    def test_sin_notificar_al_autor(self):
        evaluacion = self.evaluacion(responsible=self.user)
        self.observar(evaluacion)
        self.assertEqual(IPERObservation.objects.count(), 1)

    def test_texto_vacio_no_guarda(self):
        self.observar(self.evaluacion(), texto="")
        self.assertFalse(IPERObservation.objects.exists())


class VersionadoTest(IPERBase):

    def test_completada_no_se_clona(self):
        evaluacion = self.evaluacion(status=IPERAssessment.COMPLETED)
        response = self.client.get(url("iper_clone", org_pk=self.org_pk, pk=evaluacion.pk))
        self.assertRedirects(response, self.detalle(evaluacion), fetch_redirect_response=False)
        self.assertEqual(IPERAssessment.objects.count(), 1)

    def test_clon_con_configuracion_e_inventario(self):
        IPERConfig.objects.create(organization=self.organization, period_months=12)
        evaluacion = self.evaluacion()
        peligro = self.peligro(evaluacion)
        reactivo = Object.objects.create(code="R1", name="Reactivo", type=Object.REACTIVE, organization=self.organization)
        estante = self._estante()
        from laboratory.models import ShelfObject
        objeto = ShelfObject.objects.create(
            object=reactivo, shelf=estante, quantity=1,
            measurement_unit=Catalog.objects.create(key="units", description="u"),
            in_where_laboratory=self.lab, created_by=self.user,
        )
        peligro.related_shelfobjects.add(objeto)
        self.client.get(url("iper_clone", org_pk=self.org_pk, pk=evaluacion.pk))
        nueva = IPERAssessment.objects.get(version=2)
        self.assertEqual(nueva.due_date, add_months_hoy(12))
        self.assertEqual(list(nueva.hazards.get().related_shelfobjects.all()), [objeto])

    def _estante(self):
        from laboratory.models import Furniture, LaboratoryRoom, Shelf

        room = LaboratoryRoom.objects.create(laboratory=self.lab, name="Sala")
        mueble = Furniture.objects.create(
            labroom=room, name="Mueble", dataconfig="",
            type=Catalog.objects.create(key="furniture_type", description="Estante"),
        )
        return Shelf.objects.create(
            furniture=mueble, name="E1", type=Catalog.objects.create(key="container_type", description="Caja")
        )


def add_months_hoy(meses):
    from risk_management.models_utils import add_months

    return add_months(HOY, meses)


class DuplicadoTest(IPERBase):

    def duplicar(self, evaluacion, metodo="post", **datos):
        destino = url("iper_duplicate", org_pk=self.org_pk, pk=evaluacion.pk)
        return getattr(self.client, metodo)(destino, datos)

    def test_solo_completadas_y_por_post(self):
        borrador = self.evaluacion()
        self.assertEqual(self.duplicar(borrador).status_code, 400)
        completada = self.evaluacion(status=IPERAssessment.COMPLETED)
        self.assertEqual(self.duplicar(completada, metodo="get").status_code, 405)
        invalido = self.duplicar(completada, laboratory="", assessment_date="")
        self.assertEqual(invalido.status_code, 400)
        self.assertIn("laboratory", invalido.json()["errors"])

    def test_duplica_peligros_y_observaciones(self):
        original = self.evaluacion(status=IPERAssessment.COMPLETED, is_anonymous=False)
        self.peligro(original)
        IPERObservation.objects.create(assessment=original, text="Nota", author=self.sin_permisos)
        response = self.duplicar(original, laboratory=self.lab.pk, assessment_date="2026-03-01")
        self.assertEqual(response.status_code, 200)
        nueva = IPERAssessment.objects.exclude(pk=original.pk).get()
        self.assertEqual(response.json()["redirect_url"], self.detalle(nueva))
        self.assertEqual((nueva.version, nueva.status, nueva.is_anonymous), (1, IPERAssessment.DRAFT, False))
        self.assertEqual(nueva.hazards.count(), 1)
        self.assertEqual(nueva.observations.get().author, self.user)
        self.assertEqual(original.hazards.count(), 1)
        # Sin configuración previa se crea una para el laboratorio (12 meses).
        self.assertEqual(nueva.due_date, datetime.date(2027, 3, 1))
        self.assertTrue(IPERConfig.objects.filter(laboratory=self.lab, period_months=12).exists())

    def test_usa_la_configuracion_existente(self):
        IPERConfig.objects.create(organization=self.organization, period_months=3)
        original = self.evaluacion(status=IPERAssessment.COMPLETED)
        self.duplicar(original, laboratory=self.lab.pk, assessment_date="2026-03-01")
        nueva = IPERAssessment.objects.exclude(pk=original.pk).get()
        self.assertEqual(nueva.due_date, datetime.date(2026, 6, 1))
        self.assertEqual(IPERConfig.objects.count(), 1)


class SolicitudPorZonaTest(IPERBase):

    def test_crea_tareas_a_los_responsables_con_perfil(self):
        self.lab.responsible = self.sin_permisos
        self.lab.save()
        sin_responsable = self.crear_laboratorio("Sin responsable", self.organization)
        from django.contrib.auth.models import User
        sin_perfil = self.crear_laboratorio("Responsable sin perfil", self.organization)
        sin_perfil.responsible = User.objects.create_user("sin_perfil", password="x")
        sin_perfil.save()
        self.zone.laboratories.add(sin_responsable, sin_perfil)
        antes = PendingTask.objects.count()
        response = self.client.get(url("iper_request_zone", org_pk=self.org_pk, risk_pk=self.zone.pk))
        self.assertRedirects(
            response, url("riskzone_detail", org_pk=self.org_pk, pk=self.zone.pk), fetch_redirect_response=False
        )
        self.assertEqual(PendingTask.objects.count(), antes + 1)

    def test_zona_ajena_es_404(self):
        response = self.client.get(url("iper_request_zone", org_pk=self.org_pk, risk_pk=self.other_zone.pk), **AJAX)
        self.assertEqual(response.status_code, 404)


class HistorialTest(IPERBase):

    def setUp(self):
        super().setUp()
        self.vieja = self.evaluacion(assessment_date=datetime.date(2025, 1, 10), is_anonymous=False)
        self.peligro(self.vieja, description="Viejo")
        self.nueva = self.evaluacion(assessment_date=datetime.date(2026, 1, 10))
        self.peligro(self.nueva, description="Nuevo", category=self.fisico,
                     probability=self.baja, consequence=self.ligero)

    def historial(self, **params):
        return self.client.get(url("iper_history", org_pk=self.org_pk), params)

    def descripciones(self, response):
        return [p.description for p in response.context["object_list"]]

    def test_filtros(self):
        trivial = Catalog.objects.get(key=KEY_RISK_LEVEL, description="Trivial")
        self.assertEqual(self.descripciones(self.historial(category=self.quimico.pk)), ["Viejo"])
        self.assertEqual(self.descripciones(self.historial(risk_level=trivial.pk)), ["Nuevo"])
        self.assertEqual(self.descripciones(self.historial(date_from="2025-06-01")), ["Nuevo"])
        self.assertEqual(self.descripciones(self.historial(date_to="2025-06-01")), ["Viejo"])
        resumen = {r["level"]: r["count"] for r in self.historial().context["risk_summary"]}
        self.assertEqual((resumen["Intolerable"], resumen["Trivial"]), (1, 1))

    def test_sin_ver_todo_solo_sus_laboratorios(self):
        self.evaluacion(laboratory=self.other_lab).hazards.create(
            category=self.quimico, description="Ajeno", probability=self.alta, consequence=self.extremo
        )
        self.assertEqual(len(self.descripciones(self.historial())), 3)
        lector = crear_usuario("historial_lector", self.organization,
                               permisos=["risk_management.view_iperassessment"])
        self.client.force_login(lector)
        self.assertEqual(sorted(self.descripciones(self.historial())), ["Nuevo", "Viejo"])

    def test_exportar_sin_estilos_enmascara_anonimas(self):
        for formato in ("xls", "ods"):
            with self.subTest(formato=formato):
                response = self.historial(format=formato)
                self.assertEqual(response.status_code, 200)
                self.assertIn("attachment", response["Content-Disposition"])

    def test_libro_enmascara_anonimas(self):
        from risk_management.iper_views import IPERHistory

        vista = IPERHistory()
        vista.kwargs = {"org_pk": self.org_pk}
        vista.request = self.client.get(url("iper_history", org_pk=self.org_pk)).wsgi_request
        filas = vista.get_book({})
        laboratorios = {fila[3]: fila[1] for fila in filas[1:]}
        self.assertEqual(laboratorios["Viejo"], self.lab.name)
        self.assertNotEqual(laboratorios["Nuevo"], self.lab.name)

    def test_xlsx_colorea_el_nivel(self):
        response = self.historial(format="xlsx")
        hoja = openpyxl.load_workbook(io.BytesIO(response.content)).active
        niveles = {hoja.cell(row=r, column=4).value: hoja.cell(row=r, column=8) for r in range(2, hoja.max_row + 1)}
        self.assertEqual(niveles["Viejo"].fill.fgColor.rgb[-6:], "FF0000")


class AyudaDelLaboratorioTest(IPERBase):

    def test_laboratorio_de_otra_organizacion_es_404(self):
        response = self.client.get(
            url("iper_lab_help", org_pk=self.org_pk, lab_pk=self.other_lab.pk), **AJAX
        )
        self.assertEqual(response.status_code, 404)


class CatalogoIPERTest(IPERBase):

    def destino(self, org=None):
        return url("iper_catalog_add", org_pk=(org or self.organization).pk)

    def test_formulario(self):
        response = self.client.get(self.destino(), {"key": KEY_HAZARD_CATEGORY})
        self.assertTrue(response.json()["ok"])
        self.assertIn("?key=%s" % KEY_HAZARD_CATEGORY, response.json()["message"])

    def test_clave_fuera_del_iper_es_404(self):
        self.assertEqual(self.client.get(self.destino(), {"key": "units"}, **AJAX).status_code, 404)

    def test_crear(self):
        response = self.client.post(
            self.destino() + "?key=%s" % KEY_HAZARD_CATEGORY, {"key": "units", "description": "Biomecánico"}
        )
        self.assertTrue(response.json()["ok"])
        nueva = Catalog.objects.get(pk=response.json()["id"])
        # La clave validada manda: no se cuela una entrada en otro catálogo.
        self.assertEqual((nueva.key, nueva.description), (KEY_HAZARD_CATEGORY, "Biomecánico"))

    def test_invalido(self):
        response = self.client.post(self.destino(), {"key": KEY_PROBABILITY, "description": ""})
        self.assertFalse(response.json()["ok"])

    def test_solo_la_organizacion_raiz(self):
        hija = OrganizationStructure.objects.create(name="Hija", parent=self.organization)
        from laboratory.models import UserOrganization

        UserOrganization.objects.create(user=self.user, organization=hija, type_in_organization=1)
        response = self.client.get(self.destino(hija), {"key": KEY_HAZARD_CATEGORY})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()["ok"])
