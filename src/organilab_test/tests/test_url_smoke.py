# encoding: utf-8
"""Smoke de las vistas navegables, repartido por familia de fixture.

Una sola fixture no cubre las 172 páginas del proyecto, y forzarla produciría un
JSON gigante que nadie mantendría. Cada clase carga la fixture de su dominio y
recorre los namespaces que esa fixture puede sostener.

Cuando una ruta no se puede construir con los datos de la fixture, cuenta contra
`expected_skips`: el presupuesto es la señal. Subirlo sin motivo escrito es
tapar un hueco de cobertura.
"""

from django.test import TestCase

from organilab_test.tests.url_smoke import SkipRoute, UrlSmokeMixin


class LaboratoryUrlSmokeTest(UrlSmokeMixin, TestCase):
    fixtures = ["laboratory_data.json"]
    namespaces = ("laboratory",)

    # `show_shelf_container` redirige cuando el ShelfFilterForm no trae `shelf`
    # (shelfobject_container/views.py:25): en un GET pelado el 302 es correcto.
    redirect_ok = (
        "laboratory:shelf_containers",
        # `create_user_qr` genera el código y redirige a su gestión: el 302 es
        # el camino feliz, no un fallo.
        "laboratory:create_user_qr",
    )

    kwarg_models = {
        "labroom": "laboratory.LaboratoryRoom",
        "furniture_pk": "laboratory.Furniture",
        "shelf_pk": "laboratory.Shelf",
        "shelfobject": "laboratory.ShelfObject",
        "obj_pk": "laboratory.ShelfObject",
        "equipment_shelfobject_detail:pk": "laboratory.ShelfObject",
        "complete_inform:pk": "laboratory.Inform",
        "objectview_update:pk": "laboratory.Object",
        "objectview_delete:pk": "laboratory.Object",
        "profile_detail:pk": "auth_and_perms.Profile",
        "create_user_qr:pk": "auth.User",
    }

    # Registro por QR y carga de archivo: la fixture no trae ni códigos QR
    # emitidos ni una sesión de subida, y fabricarlos aquí sería montar el
    # escenario entero de otra prueba.
    expected_skips = 8

    def extra_kwarg(self, entry, name):
        if name in ("row", "col"):
            return 0
        return super().extra_kwarg(entry, name)


class ReportUrlSmokeTest(UrlSmokeMixin, TestCase):
    fixtures = ["laboratory_data.json"]
    namespaces = ("report",)
    kwarg_models = {
        "precusor_pk": "laboratory.PrecursorReportValues",
        "pk": "report.TaskReport",
    }
    expected_skips = 3


class SgaUrlSmokeTest(UrlSmokeMixin, TestCase):
    fixtures = ["laboratory_data.json", "substances.json", "sga_components_data.json"]
    namespaces = ("sga",)
    kwarg_models = {
        "substance": "sga.Substance",
        "detail_substance:pk": "sga.Substance",
        "update_substance:pk": "sga.Substance",
        "step_one:pk": "sga.Substance",
        "sgalabel_step_one:pk": "sga.Substance",
        "sgalabel_step_two:pk": "sga.Substance",
        "edit_company:pk": "sga.BuilderInformation",
        "edit_personal:pk": "sga.DisplayLabel",
        "update_danger_indication:pk": "sga.DangerIndication",
        "update_prudence_advice:pk": "sga.PrudenceAdvice",
        "update_warning_word:pk": "sga.WarningWord",
    }
    expected_skips = 4


class RiskUrlSmokeTest(UrlSmokeMixin, TestCase):
    # `riskmanagement_data.json` referencia objetos de inventario: sin
    # `object.json` delante, el loaddata rompe por clave foránea.
    fixtures = ["object.json", "riskmanagement_data.json"]
    namespaces = ("riskmanagement",)
    kwarg_models = {
        "building_pk": "risk_management.Buildings",
        "risk_zone": "risk_management.RiskZone",
        "buildings_update:pk": "risk_management.Buildings",
        "structures_update:pk": "risk_management.Structure",
    }
    # El módulo IPER es nuevo y ninguna fixture trae evaluaciones; tampoco hay
    # estructuras. Son huecos de fixture, no de cobertura de la vista.
    expected_skips = 4


class AcademicUrlSmokeTest(UrlSmokeMixin, TestCase):
    fixtures = ["object.json", "procedure.json", "my_procedure.json"]
    namespaces = ("academic",)
    kwarg_models = {
        "procedure_detail:pk": "academic.Procedure",
        "procedure_step:pk": "academic.Procedure",
        "complete_my_procedure:pk": "academic.MyProcedure",
    }
    # `add_my_procedures` recibe content_type y model como texto: construirlos
    # es montar el escenario de otra prueba.
    expected_skips = 1


class OrgUrlSmokeTest(UrlSmokeMixin, TestCase):
    fixtures = ["laboratory_data.json"]
    namespaces = ("auth_and_perms", "presentation", "pending_tasks", "msds", "derb",
                  "reservations_management")
    expected_skips = 4
