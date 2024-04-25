from django.test import tag

from laboratory.tests.selenium_tests.laboratory_view.shelfobject_equipment_view.base import \
    ShelfObjectEquipmentSeleniumTest


@tag('selenium')
class EditShelfObjectEquipment(ShelfObjectEquipmentSeleniumTest):

    def setUp(self):
        super().setUp()


    def test_edit_shelfobject_equipment(self):
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/h3",
             "scroll": "window.scrollTo(0, 250)"},
            {"path": "//*[@id='id_description']"},
            {"path": "//*[@id='id_description']"},
            {"path": "//*[@id='id_description']", "extra_action": "setvalue",
             "value": "Instrumento de medición el cual determina la masa de un objeto."},
            {"path": "//*[@id='select2-id_provider-container']"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[1]/form/span/span/span[2]/ul/li[2]"},
            {"path": "//*[@id='id_equipment_price']", "scroll": "window.scrollTo(0, 500)"},
            {"path": "//*[@id='id_equipment_price']", "extra_action": "clearinput"},
            {"path": "//*[@id='id_equipment_price']", "extra_action": "setvalue",
            "value": "44,999.00"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[1]/form/div[9]/div/span",
             "scroll": "window.scrollTo(0, 700)"},
            {"path": "//*[@id='id_notes']"},
            {"path": "//*[@id='id_notes']", "extra_action": "setvalue",
             "value": "El límite de peso de la balanza es de 120 kg."},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/button"},
        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "edit_shelfobject_equipment")
