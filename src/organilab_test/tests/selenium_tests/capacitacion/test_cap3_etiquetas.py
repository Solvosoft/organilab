from django.test import tag

from organilab_test.tests.selenium_tests.capacitacion.base import (
    CapacitacionSeleniumBase,
)

# La sustancia de la fixture de capacitación: "Acido Clorhidrico 37%",
# con características y tres indicaciones de peligro, que es lo que hace
# visible el etiquetado (pictogramas, palabra de advertencia y frases H).
ORG_PK = 4
SUBSTANCE_PK = 1


@tag("selenium")
class Cap3LabelGenerationTest(CapacitacionSeleniumBase):
    """Capitulo 3: Generacion de etiquetas SGA desde el catalogo de sustancias."""

    def test_generate_label_from_substance_detail(self):
        """Escenario 3.7: Generar la etiqueta GHS de una sustancia."""
        self.navigate_to_substance_detail(org_pk=ORG_PK, pk=SUBSTANCE_PK)

        path_list = [
            # El bloque de etiquetado vive al final del detalle de la sustancia.
            # Se ancla por id y no por el titulo, que es texto traducible.
            {
                "path": "//div[@id='label_preview']",
                "wait_ready": True,
                "scroll": "document.getElementById('btn_generate_label')"
                ".scrollIntoView({block:'center'});",
                "screenshot_name": "cap3_label_form",
                "extra_action": "script",
                "value": "",
            },
            # Ancho de la etiqueta, en milimetros
            {
                "path": "//input[@id='label_ancho']",
                "extra_action": "script",
                "value": "document.getElementById('label_ancho').value = 100;",
            },
            # Alto de la etiqueta, en milimetros
            {
                "path": "//input[@id='label_alto']",
                "extra_action": "script",
                "value": "document.getElementById('label_alto').value = 60;",
            },
            # Generar: con formato PNG la etiqueta se previsualiza en la pagina
            {
                "path": "//a[@id='btn_generate_label']",
                "sleep": 2,
            },
            # La etiqueta ya renderizada
            {
                "path": "//div[@id='label_preview']//img",
                "sleep": 2,
                "screenshot_name": "cap3_label_preview",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap3_generate_label", hover=False)

        preview = self.selenium.find_element("id", "label_preview")
        image = preview.find_elements("tag name", "img")
        self.assertTrue(image, "La previsualizacion no muestra la etiqueta generada")

    def test_label_endpoint_renders_png(self):
        """La vista de etiqueta devuelve una imagen, no una pagina de error."""
        self.navigate_to_generate_label(
            org_pk=ORG_PK, pk=SUBSTANCE_PK, ancho_mm=70, alto_mm=40, formato="png"
        )
        self.assert_no_server_error(context_msg="generate_label PNG")

        # El navegador muestra el PNG solo: el documento queda con una <img>.
        images = self.selenium.find_elements("tag name", "img")
        self.assertTrue(images, "La respuesta no es una imagen")
        self.assertTrue(
            self.selenium.execute_script(
                "var i = document.images[0];"
                "return i && i.naturalWidth > 0 && i.naturalHeight > 0;"
            ),
            "La etiqueta se sirvio pero no pudo decodificarse como imagen",
        )

    def test_label_too_small_is_reported_not_crashed(self):
        """Un tamano por debajo del minimo responde un aviso, no un error 500."""
        self.navigate_to_generate_label(
            org_pk=ORG_PK, pk=SUBSTANCE_PK, ancho_mm=20, alto_mm=12, formato="png"
        )
        self.assert_no_server_error(context_msg="generate_label con tamano invalido")
        self.assertIn("mm", self.selenium.page_source)
