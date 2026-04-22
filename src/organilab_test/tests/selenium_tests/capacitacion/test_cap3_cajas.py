from django.test import tag
from selenium import webdriver
from selenium.webdriver import ActionChains

from organilab_test.tests.selenium_tests.capacitacion.base import (
    CapacitacionSeleniumBase,
)


@tag("selenium")
class Cap3BoxesTest(CapacitacionSeleniumBase):
    """Capitulo 3: Gestion de cajas de materiales."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Recrear Chrome con --window-size para que el window manager
        # no limite el tamaño al de la pantalla fisica.
        cls.selenium.quit()
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        cls.selenium = webdriver.Chrome(options=options)
        cls.selenium.set_window_size(1920, 1080)
        cls.action = ActionChains(cls.selenium)
        cls.screenshot_size = "1920x1080"
        cls.folder = "%s/%s" % (cls.tmp, cls.screenshot_size)

    def test_create_box(self):
        """Escenario 3.7: Crear una caja de material desde la segunda ventana.

        Flujo:
        1. Navegar a rooms -> expandir sala -> expandir mueble -> seleccionar estante
        2. Clic en boton Crear Material (data-type=1)
        3. Clic en tab Crear caja (material_modal_tab2_btn)
        4. Rellenar formulario: objeto, estado, cantidad, unidad, vencimiento,
           numero de cajas, unidades por caja
        5. Guardar cambios

        GIF: docs/source/_static/gif/cap3_create_box.gif
        """
        self.navigate_to_rooms(org_pk=4, lab_pk=1)

        path_list = [
            # Expandir Sala de Almacenamiento (labroom pk=1)
            {
                "path": "//*[@id='labroom_1']",
                "sleep": 1,
            },
            # Expandir mueble Gabinete Principal (furniture pk=1)
            {
                "path": "//*[@id='furniture_1']",
                "sleep": 1,
            },
            # Seleccionar estante Estante Reactivos A (shelf pk=1)
            {
                "path": "//*[@id='shelf_1']",
                "scroll": "window.scrollTo(0, 250)",
                "sleep": 2,
            },
            # Clic en boton Crear Material (data-type="1", icono battery-quarter)
            {
                "path": "//button[contains(@class,'btn-success') and @data-type='1']",
                "sleep": 2,
            },
            # Clic en tab "Crear caja" (segunda pestana del modal)
            {
                "path": "//*[@id='material_modal_tab2_btn']",
                "sleep": 1,
            },
            # Establecer objeto Material via Select2 (Beaker 500ml, pk=2, objecttype=1)
            {
                "path": "//*[@id='material_modal']//form[@id='box_form']",
                "extra_action": "script",
                "value": (
                    "var opt = new Option('Butanona', '2', true, true);"
                    "$('#id_bf-object').append(opt).trigger('change');"
                    "$('#id_bf-objecttype').val('1');"
                ),
                "sleep": 1,
            },
            # Establecer estado (shelfobject_status pk=158, Ingresado)
            {
                "path": "//*[@id='material_modal']//form[@id='box_form']",
                "extra_action": "script",
                "value": (
                    "var optS = new Option('Ingresado', '158', true, true);"
                    "$('#id_bf-status').append(optS).trigger('change');"
                ),
                "sleep": 1,
            },
            # Establecer estado fisico (solid granular or crystalline -> Ingresado)
            {
                "path": "//*[@id='id_bf-physical_status']",
                "extra_action": "script",
                "value": (
                    "document.getElementById('id_bf-physical_status').value"
                    " = 'solid granular or crystalline';"
                    "$('#id_bf-physical_status').trigger('change');"
                ),
                "sleep": 1,
            },
            # Establecer unidad de medida (Unidades, pk=64)
            {
                "path": "//*[@id='material_modal']//form[@id='box_form']",
                "extra_action": "script",
                "value": (
                    "var optU = new Option('Unidades', '64', true, true);"
                    "$('#id_bf-measurement_unit').append(optU).trigger('change');"
                ),
                "sleep": 1,
            },
            # Ingresar cantidad de unidades por caja (10 unidades)
            {
                "path": "//*[@id='id_bf-quantity']",
                "extra_action": "script",
                "value": "document.getElementById('id_bf-quantity').value = '10';",
                "scroll": "document.querySelector('#box_form').scrollIntoView();",
            },
            # Ingresar numero de cajas (2)
            {
                "path": "//*[@id='id_bf-quantity_box']",
                "extra_action": "script",
                "value": "document.getElementById('id_bf-quantity_box').value = '2';",
            },
            # Ingresar unidades por caja (10)
            {
                "path": "//*[@id='id_bf-units_per_box']",
                "extra_action": "script",
                "value": "document.getElementById('id_bf-units_per_box').value = '10';",
            },
            # Ingresar fecha de vencimiento (formato MM/DD/YYYY)
            {
                "path": "//*[@id='id_bf-reactive_expiration_date']",
                "extra_action": "script",
                "value": "document.getElementById('id_bf-reactive_expiration_date').value = '21/04/2030';",
            },
            # Clic en boton Guardar cambios (formadd-tab dentro del modal)
            {
                "path": "//*[@id='material_modal']//div[contains(@class,'modal-footer')]"
                        "//button[contains(@class,'formadd')]",
                "sleep": 2,
            },
            # Capturar resultado tras guardar
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap3_create_box",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap3_create_box")

    def test_decrease_box(self):
        """Escenario 3.8: Disminuir cantidad de una caja desde la tabla del estante.

        Flujo:
        1. Navegar a rooms -> expandir sala -> expandir mueble -> seleccionar estante
        2. Esperar que cargue la tabla DataTables
        3. Clic en boton disminuir (fa-minus text-danger) de la fila de caja (is_box=true)
        4. Rellenar formulario: sin cambiar seleccion de caja, cantidad=10, descripcion
        5. Guardar cambios

        Fixture: ShelfObject pk=4, shelf=1, object=2 (Butanona), is_box=True,
                 quantity_units=[{code:CAJA-001, units:10}, {code:CAJA-002, units:10}]

        GIF: docs/source/_static/gif/cap3_decrease_box.gif
        """
        self.navigate_to_rooms(org_pk=4, lab_pk=1)

        path_list = [
            # Expandir Sala de Almacenamiento (labroom pk=1)
            {
                "path": "//*[@id='labroom_1']",
                "sleep": 1,
            },
            # Expandir mueble Gabinete Principal (furniture pk=1)
            {
                "path": "//*[@id='furniture_1']",
                "sleep": 1,
            },
            # Seleccionar estante Estante Reactivos A (shelf pk=1)
            {
                "path": "//*[@id='shelf_1']",
                "scroll": "window.scrollTo(0, 250)",
                "sleep": 2,
            },
            # Bajar a la tabla y hacer clic en el boton disminuir de la fila de caja
            {
                "path": "//a[@data-modalid='decreasesomodal' and @data-is-box='true']",
                "scroll": "window.scrollTo(0, document.body.scrollHeight)",
                "sleep": 2,
            },
            # Ingresar cantidad a disminuir (10)
            {
                "path": "//*[@id='id_decrease-amount']",
                "extra_action": "script",
                "value": "document.getElementById('id_decrease-amount').value = '10';",
                "sleep": 1,
            },
            # Ingresar descripcion
            {
                "path": "//*[@id='id_decrease-description']",
                "extra_action": "script",
                "value": "document.getElementById('id_decrease-description').value = 'Prueba de disminucion de caja';",
                "sleep": 1,
            },
            # Clic en boton Guardar cambios (formadd dentro del modal de disminuir)
            {
                "path": "//*[@id='decreasesomodal']//button[contains(@class,'formadd')]",
                "sleep": 2,
            },
            # Capturar resultado tras guardar
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap3_decrease_box",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap3_decrease_box")

    def test_increase_box(self):
        """Escenario 3.9: Agregar cajas a un ShelfObject de tipo caja.

        Flujo:
        1. Navegar a rooms -> expandir sala -> expandir mueble -> seleccionar estante
        2. Esperar que cargue la tabla DataTables
        3. Clic en boton agregar (fa-plus text-success) de la fila de caja (data-box=True)
        4. Rellenar formulario: cantidad=2, numero de factura, sin proveedor, uso
        5. Guardar cambios

        Fixture: ShelfObject pk=4, shelf=1, object=2 (Butanona), is_box=True

        GIF: docs/source/_static/gif/cap3_increase_box.gif
        """
        self.navigate_to_rooms(org_pk=4, lab_pk=1)

        path_list = [
            # Expandir Sala de Almacenamiento (labroom pk=1)
            {
                "path": "//*[@id='labroom_1']",
                "sleep": 1,
            },
            # Expandir mueble Gabinete Principal (furniture pk=1)
            {
                "path": "//*[@id='furniture_1']",
                "sleep": 1,
            },
            # Seleccionar estante Estante Reactivos A (shelf pk=1)
            {
                "path": "//*[@id='shelf_1']",
                "scroll": "window.scrollTo(0, 250)",
                "sleep": 2,
            },
            # Bajar a la tabla y hacer clic en el boton agregar de la fila de caja
            {
                "path": "//a[@data-modalid='increasesomodal' and @data-box='True']",
                "scroll": "window.scrollTo(0, document.body.scrollHeight)",
                "sleep": 2,
            },
            # Ingresar cantidad de cajas a agregar (2)
            {
                "path": "//*[@id='id_increase-amount']",
                "extra_action": "script",
                "value": "document.getElementById('id_increase-amount').value = '2';",
                "sleep": 1,
            },
            # Ingresar numero de factura
            {
                "path": "//*[@id='id_increase-bill']",
                "extra_action": "script",
                "value": "document.getElementById('id_increase-bill').value = 'FACT-2025-001';",
                "sleep": 1,
            },
            # Ingresar uso
            {
                "path": "//*[@id='id_increase-use']",
                "extra_action": "script",
                "value": "document.getElementById('id_increase-use').value = 'Uso en practica de laboratorio';",
                "sleep": 1,
            },
            # Clic en boton Guardar cambios (formadd dentro del modal de agregar)
            {
                "path": "//*[@id='increasesomodal']//button[contains(@class,'formadd')]",
                "sleep": 2,
            },
            # Capturar resultado tras guardar
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap3_increase_box",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap3_increase_box")
