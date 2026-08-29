from django.test import tag
from organilab_test.tests.selenium_xpaths import select2_result

from laboratory.tests.selenium_tests.laboratory_view.base import (
    LaboratoryViewSeleniumTest,
)


@tag("selenium")
class CreateShelfObject(LaboratoryViewSeleniumTest):

    def setUp(self):
        super().setUp()

        self.select_lab_elements = self.path_base + [
            {"path": "//*[@id='labroom_2']"},
            {"path": "//*[@id='furniture_3']"},
            {"path": "//*[@id='shelf_2']"},
        ]

        self.create_shelfobject_reative_start = self.select_lab_elements + [
            {
                "path": self.shelfobject_toolbar_button("fa-flask"),
                "scroll": "window.scrollTo(0, 250)",
            },
            {"path": "//span[@aria-controls='select2-id_rf-object-container']", "sleep": 1},
            {"path": select2_result(1)},
            {"path": "//span[@aria-controls='select2-id_rf-status-container']", "sleep": 1},
            {"path": select2_result(1)},
            {"path": "//*[@id='id_rf-quantity']"},
            {
                "path": "//*[@id='id_rf-quantity']",
                "extra_action": "setvalue",
                "value": "3",
            },
            {"path": "//span[@aria-controls='select2-id_rf-measurement_unit-container']", "sleep": 1},
            {"path": select2_result(1)},
        ]

        self.create_shelfobject_reative_end = [
            {"path": select2_result(1), "sleep": 1},
            {
                "path": "//*[@id='id_rf-description']",
                "scroll": "$('#reactive_modal').scrollTop(400);",
            },
            {
                "path": "//*[@id='id_rf-description']",
                "extra_action": "setvalue",
                "value": "El cloroformo es un líquido incoloro"
                " de olor dulce y agradable. Se utiliza como disolvente y en la elaboración"
                " de refrigerantes, resinas y plásticos.",
            },
            {"path": "//*[@id='id_rf-batch']"},
            {
                "path": "//*[@id='id_rf-batch']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='id_rf-batch']",
                "extra_action": "setvalue",
                "value": "3092",
            },
        ]

        self.view_transfer_list = self.select_lab_elements + [
            {
                "path": self.shelfobject_toolbar_button("fa-exchange"),
                "scroll": "window.scrollTo(0, 250)",
            }
        ]

        self.approve_transfer_in = self.view_transfer_list + [
            {
                "path": "//table[@id='transfer-list-datatable']//tbody/tr[1]//a[.//i[contains(@class, 'fa-check-circle')]]"
            }
        ]

    def test_go_to_objects_by_furniture_report(self):

        path_list1 = self.path_base + [
            {"path": "//*[@id='labroom_2']"},
            {"path": "//*[@id='collapselabroom']/ul/li[2]/ul/li/a[2]"},
        ]

        path_list2 = [
            {
                "path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div/div/div[2]/div",
                "scroll": "window.scrollTo(0, 70)",
            }
        ]

        general_path_list = [path_list1, path_list2]
        self.create_gif_by_change_focus_tab(
            general_path_list, ["reportbase"], "go_to_objects_by_furniture_report"
        )

    def create_reactive(self, radio_value, container_field, container_type):
        path_list = (
            self.create_shelfobject_reative_start
            + [
                {"path": self.container_radio("reactive_form", radio_value)},
                {
                    "path": "//span[@aria-controls='select2-id_rf-%s-container']"
                    % container_field,
                    "sleep": 1,
                },
            ]
            + self.create_shelfobject_reative_end
            + [{"path": self.get_save_button_modal("reactive_modal")}]
        )

        self.create_gif_process(
            path_list, "create_shelfobject_reactive_with_%s_container" % container_type
        )

    def test_create_shelfobject_reactive_with_clone_container(self):
        self.create_reactive("clone", "container_for_cloning", "clone")

    def test_create_shelfobject_reactive_with_use_selected_container(self):
        self.create_reactive("available", "available_container", "use_selected")

    def test_create_shelfobject_material(self):
        path_list = self.path_base + [
            {"path": "//*[@id='labroom_1']"},
            {"path": "//*[@id='furniture_2']"},
            {"path": "//*[@id='shelf_3']"},
            {
                "path": self.shelfobject_toolbar_button("fa-battery-quarter"),
                "scroll": "window.scrollTo(0, 250)",
            },
            {"path": "//span[@aria-controls='select2-id_mf-object-container']", "sleep": 1},
            {"path": select2_result(1)},
            {"path": "//span[@aria-controls='select2-id_mf-status-container']", "sleep": 1},
            {"path": select2_result(1)},
            {"path": "//*[@id='id_mf-quantity']"},
            {
                "path": "//*[@id='id_mf-quantity']",
                "extra_action": "setvalue",
                "value": "4",
            },
            {"path": "//*[@id='id_mf-description']"},
            {
                "path": "//*[@id='id_mf-description']",
                "extra_action": "setvalue",
                "value": "Contenedor de base cilíndrica para "
                "líquidos con capacidad de 1L.",
            },
            {"path": self.get_save_button_modal("material_modal")},
        ]
        self.create_gif_process(path_list, "create_shelfobject_material")

    def test_create_shelfobject_equipment(self):
        path_list = self.path_base + [
            {"path": "//*[@id='labroom_1']"},
            {"path": "//*[@id='furniture_1']"},
            {"path": "//*[@id='shelf_1']"},
            {
                "path": self.shelfobject_toolbar_button("fa-desktop"),
                "scroll": "window.scrollTo(0, 250)",
            },
            {"path": "//*[@id='select2-id_ef-object-container']", "sleep": 1},
            {"path": select2_result(1)},
            {"path": "//*[@id='select2-id_ef-status-container']", "sleep": 1},
            {"path": select2_result(1)},
            {
                "path": "//*[@id='id_ef-description']",
                "scroll": "$('#equipment_modal').scrollTop(300)",
                "extra_action": "setvalue",
                "value": "Instrumento para calcular la masa de un objeto.",
            },
            {
                "path": "//*[@id='id_ef-shelfobject_code']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='id_ef-shelfobject_code']",
                "extra_action": "setvalue",
                "value": "2000",
            },
            {"path": self.get_save_button_modal("equipment_modal")},
        ]
        self.create_gif_process(path_list, "create_shelfobject_equipment")

    def test_view_containers_by_shelf(self):

        path_list = self.select_lab_elements + [
            {
                "path": self.shelfobject_toolbar_button("fa-cubes"),
                "scroll": "window.scrollTo(0, 250)",
            },
            {
                "path": "//*[@id='container_table']",
                "extra_action": "script",
                "value": "window.scrollTo(0, 50)",
            },
            {
                "path": "//*[@id='container_table']",
                "extra_action": "script",
                "value": "window.scrollTo(0, 100)",
            },
        ]
        self.create_gif_process(path_list, "view_containers_by_shelf")

    def test_approve_transfer_in_shelfobject_with_clone_container(self):

        path_list = self.approve_transfer_in + [
            {
                "path": self.container_radio("transfer_in_approve_with_container_form", "clone")
            },
            {
                "path": "//*[@id='transfer_in_approve_with_container_form']/div[2]/div/span/span/span"
            },
            {
                "path": select2_result(1)
            },
            {
                "path": "//*[@id='transfer_in_approve_with_container_id_modal']/div/div/div[3]/button[2]"
            },
        ]
        self.create_gif_process(
            path_list, "approve_transfer_in_shelfobject_with_clone_container"
        )

    def test_approve_transfer_in_shelfobject_with_available_container(self):

        path_list = self.approve_transfer_in + [
            {
                "path": self.container_radio("transfer_in_approve_with_container_form", "available")
            },
            {
                "path": "//*[@id='transfer_in_approve_with_container_form']/div[3]/div/span/span/span"
            },
            {
                "path": select2_result(1)
            },
            {
                "path": "//*[@id='transfer_in_approve_with_container_id_modal']/div/div/div[3]/button[2]"
            },
        ]
        self.create_gif_process(
            path_list, "approve_transfer_in_shelfobject_with_available_container"
        )

    def test_approve_transfer_in_shelfobject_with_use_source_container(self):

        path_list = self.approve_transfer_in + [
            {
                "path": self.container_radio("transfer_in_approve_with_container_form", "use_source")
            },
            {
                "path": "//*[@id='transfer_in_approve_with_container_id_modal']/div/div/div[3]/button[2]"
            },
        ]
        self.create_gif_process(
            path_list, "approve_transfer_in_shelfobject_with_use_source_container"
        )

    def test_approve_transfer_in_shelfobject_with_new_based_source_container(self):

        path_list = self.approve_transfer_in + [
            {
                "path": self.container_radio("transfer_in_approve_with_container_form", "new_based_source")
            },
            {
                "path": "//*[@id='transfer_in_approve_with_container_id_modal']/div/div/div[3]/button[2]"
            },
        ]
        self.create_gif_process(
            path_list, "approve_transfer_in_shelfobject_with_new_based_source_container"
        )

    def test_deny_transfer_in_shelfobject(self):

        path_list = self.view_transfer_list + [
            {
                "path": "//table[@id='transfer-list-datatable']//tbody/tr[1]//a[.//i[contains(@class, 'fa-times-circle')]]"
            },
            {"path": "//button[contains(@class, 'swal2-confirm')]"},
        ]
        self.create_gif_process(path_list, "deny_transfer_in_shelfobject")
