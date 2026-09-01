from django.test import tag
from django.utils.timezone import now
from laboratory.tests.selenium_tests.laboratory_view.test_actions_buttons_shelfobject_table_actions_column import (
    ButtonsActionsTableColumnBase,
)


@tag("selenium")
class ShelfObjectInfoButtonsActions(ButtonsActionsTableColumnBase):

    def setUp(self):
        super().setUp()

        self.path_shelfobject_info = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-file-text-o")}
        ]
        self.path_shelfobject_equipment = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-file-text-o", row=2)}
        ]

    def test_view_equipment_details(self):
        # laboratory/tests/selenium_tests/laboratory_view/shelfobject_detail_actions.py
        self.create_gif_process(
            self.path_shelfobject_equipment, "view_shelfobject_equipment"
        )

    def test_change_shelfobject_status(self):
        path_list = [
            {"path": "//*[@data-modalid='status_modal']", "sleep": 10},
            {"path": "//*[@id='status_form']//a[contains(@class, 'add_status')]"},
            {"path": "//input[contains(@class, 'swal2-input')]"},
            {
                "path": "//input[contains(@class, 'swal2-input')]",
                "extra_action": "setvalue",
                "value": "En uso",
            },
            {
                # El fetch de creación + el swal de éxito (timer 1.5s) deben
                # terminar antes de abrir el select2 de estados.
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 30,
            },
            {"path": "//*[@id='status_form']/div/div/span/span/span", "sleep": 10},
            {
                # El estado recién creado se elige por texto: el fixture no
                # trae estados previos, así que la posición no es estable.
                "path": "//li[contains(@class, 'select2-results__option')]"
                        "[normalize-space(.)='En uso']",
                "sleep": 1,
            },
            {"path": "//*[@id='status_form']/div[2]/div/textarea"},
            {
                "path": "//*[@id='status_form']/div[2]/div/textarea",
                "extra_action": "setvalue",
                "value": "Reactivo esta siendo utilizado en la práctica de laboratorio",
            },
            {"path": "//*[@id='status_modal']/div/div/div[3]/button[2]"},
            {
                "path": "//*[@id='observationTable']",
                "extra_action": "script",
                "value": "window.scrollTo(0, 300)",
            },
            {"path": "//*[@id='observationTable']/tbody/tr/td[4]"},
        ]

        general_path_list = [self.path_shelfobject_info, path_list]
        self.create_gif_by_change_focus_tab(
            general_path_list, ["shelfobjectlog"], "change_shelfobject_status"
        )

    def test_add_shelfobject_observation(self):
        current_date, str_date = self.get_format_increase_decrease_date(now(), 0)
        path_list = self.scroll_shelfobject_info + [
            {"path": "//*[@data-modalid='observation_modal']"},
            {"path": "//*[@id='observation_form']/div[2]/div/textarea"},
            {
                "path": "//*[@id='observation_form']/div[2]/div/textarea",
                "extra_action": "setvalue",
                "value": "Reactivo fue entregado al responsable"
                " con ID 23548 el día %s, para uso de las prácticas con estudiantes."
                % str_date,
            },
            {"path": "//*[@id='observation_modal']/div/div/div[3]/button[2]"},
        ]

        general_path_list = [self.path_shelfobject_info, path_list]
        self.create_gif_by_change_focus_tab(
            general_path_list, ["shelfobjectlog"], "add_shelfobject_observation"
        )
