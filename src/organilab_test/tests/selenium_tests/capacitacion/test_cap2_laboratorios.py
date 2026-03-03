from django.test import tag

from organilab_test.tests.selenium_tests.capacitacion.base import (
    CapacitacionSeleniumBase,
)


@tag("selenium")
class Cap2LabStructureTest(CapacitacionSeleniumBase):
    """Capitulo 2: Creacion de estructura de laboratorio."""

    def test_create_laboratory(self):
        """Escenario 2.1: Crear un laboratorio."""
        self.navigate_to_create_lab(org_pk=4)

        path_list = [
            # Campo nombre
            {
                "path": ".//input[@name='name']",
                "extra_action": "setvalue",
                "value": "Laboratorio de Quimica Analitica",
            },
            # Campo ubicacion
            {
                "path": ".//input[@name='location']",
                "extra_action": "setvalue",
                "value": "Edificio C, Piso 1, Aula 201",
            },
            # Campo telefono
            {
                "path": ".//input[@name='phone_number']",
                "extra_action": "setvalue",
                "value": "2511-4000",
            },
            # Campo email
            {
                "path": ".//input[@name='email']",
                "extra_action": "setvalue",
                "value": "quimica.analitica@universidad.ac.cr",
                "scroll": "window.scrollTo(0, 300)",
            },
            # Guardar
            {
                "path": ".//button[@type='submit' and contains(@class,'btn-success')]",
                "scroll": "window.scrollTo(0, document.body.scrollHeight)",
            },
        ]
        self.create_gif_process(path_list, "cap2_create_lab")

    def test_create_room(self):
        """Escenario 2.2: Crear una sala de laboratorio."""
        self.navigate_to_rooms_create(org_pk=4, lab_pk=1)

        path_list = [
            # Campo nombre de la sala
            {
                "path": ".//input[@name='name']",
                "extra_action": "setvalue",
                "value": "Sala de Instrumentacion",
            },
            # Guardar (boton con clase btn-outline-success para creacion)
            {
                "path": ".//button[@type='submit' and contains(@class,'btn-outline')]",
                "scroll": "window.scrollTo(0, document.body.scrollHeight)",
            },
        ]
        self.create_gif_process(path_list, "cap2_create_room")

    def test_create_furniture(self):
        """Escenario 2.3: Crear un mueble en una sala."""
        self.navigate_to_rooms_create(org_pk=4, lab_pk=1)

        path_list = [
            # Abrir modal de mueble (boton en el formulario de sala)
            {
                "path": ".//button[@data-bs-target='#furnitureModal']",
                "sleep": 1,
            },
            # Campo nombre del mueble dentro del modal
            {
                "path": ".//div[@id='furnitureModal']//input[@name='name']",
                "extra_action": "setvalue",
                "value": "Campana de Extraccion",
                "sleep": 1,
            },
            # Guardar mueble (boton btn-primary dentro del modal)
            {
                "path": ".//div[@id='furnitureModal']//button[@type='submit']",
            },
        ]
        self.create_gif_process(path_list, "cap2_create_furniture")

    def test_view_lab_structure(self):
        """Escenario 2.4: Ver estructura del laboratorio (salas, muebles, estantes)."""
        self.navigate_to_rooms(org_pk=4, lab_pk=1)

        path_list = [
            # Ver la estructura del laboratorio (tree de salas y muebles)
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap2_lab_structure",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap2_view_lab_structure")


@tag("selenium")
class Cap2InventoryTest(CapacitacionSeleniumBase):
    """Capitulo 2: Vista del inventario del laboratorio."""

    def test_view_shelf_objects(self):
        """Escenario 2.5: Ver inventario del laboratorio."""
        self.navigate_to_rooms(org_pk=4, lab_pk=1)

        path_list = [
            # Capturar vista del inventario (arbol de salas, muebles y estantes)
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap2_shelf_inventory",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap2_view_objects")

    def test_view_shelf_object_details(self):
        """Escenario 2.5: Ver detalles de un objeto en el laboratorio.

        Flujo: Expandir Sala de Almacenamiento -> Expandir mueble ->
        Seleccionar estante -> Clic en boton ojo de un registro ->
        Scroll en el modal de detalles.

        GIF: docs/source/_static/gif/cap2_view_shelf_object_details.gif
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
            # Clic en boton ojo (ver detalles) del primer registro de la tabla
            {
                "path": "//*[@id='shelfobjecttable']/tbody/tr[1]//a[.//i[contains(@class,'fa-eye')]]",
                "sleep": 2,
            },
            # Scroll en el modal de detalles
            {
                "path": "//*[@id='shelfobject_detail_modal_body']",
                "extra_action": "script",
                "value": "$('#shelfobject_detail_modal_body').scrollTop(150);",
                "sleep": 1,
            },
            {
                "path": "//*[@id='shelfobject_detail_modal_body']",
                "extra_action": "script",
                "value": "$('#shelfobject_detail_modal_body').scrollTop(300);",
                "sleep": 1,
            },
            {
                "path": "//*[@id='shelfobject_detail_modal_body']",
                "extra_action": "script",
                "value": "$('#shelfobject_detail_modal_body').scrollTop(450);",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "cap2_view_shelf_object_details")


@tag("selenium")
class Cap2ReportsTest(CapacitacionSeleniumBase):
    """Capitulo 2: Reportes del laboratorio."""

    def test_view_reports_menu(self):
        """Escenario 2.6: Ver menu de reportes del laboratorio."""
        self.navigate_to_reports(org_pk=4)

        path_list = [
            # Capturar vista del menu de reportes
            {
                "path": "//body",
                "wait_ready": True,
                "screenshot_name": "cap2_reports_menu",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap2_reports_menu")

    def test_view_pdf_report(self):
        """Escenario 2.7: Ver opciones de generacion de reporte PDF."""
        self.navigate_to_reports(org_pk=4)

        path_list = [
            # Navegar a la seccion de reportes de inventario
            {
                "path": "//body",
                "wait_ready": True,
            },
            # Capturar la pagina de opciones de reporte
            {
                "path": "//body",
                "screenshot_name": "cap2_pdf_report",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "cap2_pdf_report")
