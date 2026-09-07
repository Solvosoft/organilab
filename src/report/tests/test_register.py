from django.forms import Form
from django.test import TestCase
from django.utils.module_loading import import_string

from report import register

FORMATOS = ("html", "pdf", "xls", "xlsx", "ods")


class ReportRegisterTest(TestCase):
    """Recorre `report/register.py` en vez de enumerar reportes a mano.

    El registro declara 16 tipos de reporte, cada formato apuntando a un
    callable por ruta de importación. `check_import_obj` (`report/utils.py:180`)
    traga el ImportError y devuelve None, y entonces `build_report`
    (`report/views/base.py:45`) no hace nada: **una ruta mal escrita no falla en
    ningún sitio, el reporte simplemente no se genera nunca**. Sin recorrer el
    registro eso solo se descubre en producción.

    Recorrerlo también significa que un reporte nuevo queda cubierto por el
    mero hecho de registrarse.

    Ojo con una suposición que parece razonable y es falsa: NO todos los
    reportes ofrecen los cinco formatos. `compatibility_report` no genera xls ni
    xlsx y `hazard_map_report` solo hace html y pdf, y en ambos casos el
    formulario recorta sus opciones en consecuencia. Por eso lo que se comprueba
    no es "están los cinco", sino que el formulario y el registro digan lo mismo.
    """

    def formatos_declarados(self, entrada):
        return {clave for clave in FORMATOS if clave in entrada}

    def formatos_ofrecidos(self, entrada):
        form_cls = import_string(entrada["form"])
        campo = form_cls.base_fields.get("format")
        if campo is None:
            return None
        return {valor for valor, _etiqueta in campo.choices}

    def test_todas_las_rutas_importan(self):
        for nombre, entrada in register.REPORT_FORMS.items():
            for clave, ruta in entrada.items():
                with self.subTest(reporte=nombre, clave=clave):
                    self.assertIsNotNone(
                        import_string(ruta),
                        "%s[%s] = %r no importa" % (nombre, clave, ruta),
                    )

    def test_check_import_obj_no_devuelve_none(self):
        """El helper que usa build_report resuelve todas las rutas del registro.

        Es la comprobación que de verdad protege: si esto devolviera None para
        alguna ruta, ese reporte quedaría inerte sin un solo error en el log.
        """
        from report.utils import check_import_obj

        for nombre, entrada in register.REPORT_FORMS.items():
            for clave, ruta in entrada.items():
                with self.subTest(reporte=nombre, clave=clave):
                    self.assertIsNotNone(check_import_obj(ruta))

    def test_cada_reporte_declara_task_y_form(self):
        for nombre, entrada in register.REPORT_FORMS.items():
            with self.subTest(reporte=nombre):
                faltan = {"task", "form"} - set(entrada)
                self.assertFalse(
                    faltan, "a %s le faltan claves: %s" % (nombre, sorted(faltan))
                )

    def test_cada_reporte_declara_al_menos_un_formato(self):
        for nombre, entrada in register.REPORT_FORMS.items():
            with self.subTest(reporte=nombre):
                self.assertTrue(
                    self.formatos_declarados(entrada),
                    "%s no declara ningún formato" % nombre,
                )

    def test_el_formulario_no_ofrece_formatos_que_el_registro_no_sabe_generar(self):
        """El invariante que rompe la pantalla si se incumple.

        Si el formulario ofrece un formato que el registro no declara, el
        usuario lo elige, `build_report` no encuentra la clave y se queda sin
        hacer nada: el reporte nunca aparece y no hay error que mirar.
        """
        for nombre, entrada in register.REPORT_FORMS.items():
            ofrecidos = self.formatos_ofrecidos(entrada)
            if ofrecidos is None:
                continue
            with self.subTest(reporte=nombre):
                sobran = ofrecidos - self.formatos_declarados(entrada)
                self.assertFalse(
                    sobran,
                    "%s ofrece en pantalla formatos que el registro no genera: %s"
                    % (nombre, sorted(sobran)),
                )

    def test_cada_form_es_un_formulario(self):
        for nombre, entrada in register.REPORT_FORMS.items():
            with self.subTest(reporte=nombre):
                form_cls = import_string(entrada["form"])
                self.assertTrue(
                    issubclass(form_cls, Form),
                    "%s.form no es un Form: %r" % (nombre, form_cls),
                )

    def test_los_callables_son_invocables(self):
        for nombre, entrada in register.REPORT_FORMS.items():
            for clave in self.formatos_declarados(entrada) | {"task"}:
                with self.subTest(reporte=nombre, clave=clave):
                    self.assertTrue(callable(import_string(entrada[clave])))
