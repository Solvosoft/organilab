from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from sga.models import Substance


class SustanceCreateFormTest(TestCase):
    """El paso 1 del asistente de sustancias tiene que poder enviarse.

    `organization` es obligatorio y va en un HiddenInput. La vista no le pasaba
    `initial`, así que se renderizaba vacío y el formulario nunca validaba: no
    se podía crear una sustancia desde la pantalla. El único test que tocaba
    esta página (`capacitacion/test_cap3_sustancias.py`) pulsaba Guardar sin
    comprobar nada, así que pasaba igualmente.
    """

    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)
        self.url = reverse("sga:create_sustance", kwargs={"org_pk": 1})

    def test_el_formulario_trae_la_organizacion(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["objform"]["organization"].value(), 1)

    def test_alta_valida_y_redirige_al_paso_cuatro(self):
        from laboratory.models import ObjectFeatures

        feature = ObjectFeatures.objects.first()
        response = self.client.post(
            self.url,
            data={
                "comercial_name": "Acetona de prueba",
                "brand": "Marca",
                "organization": 1,
                "features": [feature.pk],
                "density": "0.79",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("step_four", response.url)
        self.assertTrue(
            Substance.objects.filter(comercial_name="Acetona de prueba").exists()
        )
