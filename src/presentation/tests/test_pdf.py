"""El helper único de PDF (xhtml2pdf)."""

import os
import tempfile
from io import BytesIO

from django.test import SimpleTestCase, override_settings

from presentation.pdf import PDFRenderError, html_to_pdf, link_callback_for
from report.utils import get_pdf_table_content


class HtmlToPdfTest(SimpleTestCase):

    def test_devuelve_un_pdf(self):
        pdf = html_to_pdf("<html><body><p>Hola</p></body></html>")
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_escribe_en_el_archivo_dado(self):
        buffer = BytesIO()
        self.assertIsNone(html_to_pdf("<p>Hola</p>", output=buffer))
        self.assertTrue(buffer.getvalue().startswith(b"%PDF"))

    def test_numeracion_y_frames_de_la_base_de_reportes(self):
        from django.template.loader import render_to_string

        html = render_to_string(
            "report/base_report_pdf.html",
            {"datalist": "<p>contenido</p>", "title": "Prueba", "size_sheet": "landscape"},
        )
        self.assertTrue(html_to_pdf(html).startswith(b"%PDF"))

    def test_un_error_de_xhtml2pdf_se_propaga(self):
        from unittest import mock

        fake = mock.Mock(err=1)
        with mock.patch("presentation.pdf.pisa.CreatePDF", return_value=fake):
            with self.assertRaises(PDFRenderError):
                html_to_pdf("<p>x</p>")


class LinkCallbackTest(SimpleTestCase):

    def test_media_absoluta_se_resuelve_a_disco(self):
        with tempfile.TemporaryDirectory() as media:
            path = os.path.join(media, "qr.svg")
            open(path, "w").close()
            with override_settings(MEDIA_ROOT=media, MEDIA_URL="/media/"):
                callback = link_callback_for("http://example.com/x/")
                self.assertEqual(callback("http://example.com/media/qr.svg"), path)
                self.assertEqual(callback("/media/qr.svg"), path)

    def test_data_uri_y_desconocidos_pasan_tal_cual(self):
        callback = link_callback_for()
        self.assertEqual(callback("data:image/png;base64,AA"), "data:image/png;base64,AA")
        self.assertEqual(callback("http://otro/sitio.png"), "http://otro/sitio.png")


class PdfTableContentTest(SimpleTestCase):

    def test_tablas_en_bloques_con_encabezado(self):
        table = {
            "columns": [{"title": "A"}],
            "dataset": [[n] for n in range(5)],
        }
        html = get_pdf_table_content(table, chunk_size=2)
        self.assertEqual(html.count("<table"), 3)
        self.assertEqual(html.count("<th>A</th>"), 3)
        self.assertIn("<td>5</td>", html)  # columna Item numerada desde 1
