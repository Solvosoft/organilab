"""``build_substance_code`` sin alguno de sus tres ingredientes.

La aprobación de una sustancia puede llegar sin laboratorio (sustancia de la
organización) y entonces el código no se forma: se devuelve None en vez de
reventar al leer ``laboratory.code``.
"""
from django.test import SimpleTestCase

from laboratory.models import Laboratory, OrganizationStructure
from sga.models import Substance
from sga.substance_codes import build_substance_code


class CodigoSinDatosTest(SimpleTestCase):

    def test_falta_laboratorio_organizacion_o_sustancia(self):
        lab = Laboratory(name="Lab", code="LQG")
        org = OrganizationStructure(name="Org", code="UCR")
        sustancia = Substance(comercial_name="Etanol")
        self.assertIsNone(build_substance_code(None, org, sustancia))
        self.assertIsNone(build_substance_code(lab, None, sustancia))
        self.assertIsNone(build_substance_code(lab, org, None))
