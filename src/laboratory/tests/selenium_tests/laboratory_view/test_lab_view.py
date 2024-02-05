from django.test import tag

from laboratory.tests.selenium_tests.laboratory_view.base import LaboratoryViewSeleniumTest


@tag('selenium')
class LabViewTest(LaboratoryViewSeleniumTest):



    def test_create_shelfobject_equipment(self):
        path_list = self.path_base + [
            {"path": "//*[@id='labroom_1']"},
            {"path": "//*[@id='furniture_1']"},
            {"path": "//*[@id='shelf_1']", "scroll": "window.scrollTo(0, 250)"},
            {"path": "//*[@id='shelfobjecttable_wrapper']/div/div[2]/div/button"},
            {"path": "//*[@id='select2-id_ef-object-container']"},
            {"path": "//*[@id='equipment_form']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='select2-id_ef-status-container']"},
            {"path": "//*[@id='equipment_form']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='equipment_form']/div[3]/div/input"},
            {"path": "//*[@id='equipment_form']/div[3]/div/input",
             "extra_action": "setvalue", "value": "2"},
            {"path": "//*[@id='equipment_form']/div[5]/div/textarea"},
            {"path": "//*[@id='equipment_form']/div[5]/div/textarea",
             "extra_action": "setvalue", "value": "Instrumento para calcular la masa de un objeto."},
            {"path": "//*[@id='equipment_modal']/div/div/div[3]/button[2]"}
        ]
        self.create_gif_process(path_list, "create_shelfobject_equipment")
