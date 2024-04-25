from django.test import tag

from laboratory.tests.selenium_tests.laboratory_view.shelfobject_equipment_view.base import \
    ShelfObjectEquipmentSeleniumTest


@tag('selenium')
class EditShelfObjectEquipment(ShelfObjectEquipmentSeleniumTest):

    def setUp(self):
        super().setUp()


    def test_edit_shelfobject_equipment(self):
        path_list = [

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "edit_shelfobject_equipment")
