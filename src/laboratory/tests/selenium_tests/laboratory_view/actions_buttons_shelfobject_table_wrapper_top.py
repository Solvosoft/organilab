from django.test import tag
from django.utils.timezone import now

from laboratory.tests.selenium_tests.laboratory_view.base import LaboratoryViewSeleniumTest


@tag('selenium')
class CreateShelfObject(LaboratoryViewSeleniumTest):

    def setUp(self):
        super().setUp()

        self.select_lab_elements = self.path_base + [
            {"path": "//*[@id='labroom_2']"},
            {"path": "//*[@id='furniture_3']"},
            {"path": "//*[@id='shelf_2']"},
        ]

        self.create_shelfobject_reative_start = self.select_lab_elements + [
            {"path": "//*[@id='shelfobjecttable_wrapper']/div/div[2]/div/button[3]",
             "scroll": "window.scrollTo(0, 250)"},
            {"path": "//*[@id='reactive_form']/div/div/span/span/span"},
            {"path": "//*[@id='reactive_form']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='reactive_form']/div[2]/div/span/span/span"},
            {"path": "//*[@id='reactive_form']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='reactive_form']/div[3]/div/input"},
            {"path": "//*[@id='reactive_form']/div[3]/div/input",
             "extra_action": "setvalue", "value": "3"},
            {"path": "//*[@id='reactive_form']/div[4]/div/span/span/span"},
            {"path": "//*[@id='reactive_form']/span/span/span[2]/ul/li"}
        ]

        self.create_shelfobject_reative_end = [
            {"path": "//*[@id='reactive_form']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='reactive_form']/div[8]/div/textarea",
             "scroll": "$('#reactive_modal').scrollTop(400);"},
            {"path": "//*[@id='reactive_form']/div[8]/div/textarea",
             "extra_action": "setvalue", "value": "El cloroformo es un líquido incoloro"
             " de olor dulce y agradable. Se utiliza como disolvente y en la elaboración"
             " de refrigerantes, resinas y plásticos."},
            {"path": "//*[@id='reactive_form']/div[10]/div/input"},
            {"path": "//*[@id='reactive_form']/div[10]/div/input",
             "extra_action": "clearinput"},
            {"path": "//*[@id='reactive_form']/div[10]/div/input",
             "extra_action": "setvalue", "value": "3092"}
        ]

        self.view_transfer_list = self.select_lab_elements + [
            {"path": "//*[@id='shelfobjecttable_wrapper']/div/div[2]/div/button[5]",
             "scroll": "window.scrollTo(0, 250)"}
        ]

        self.approve_transfer_in = self.view_transfer_list + [
            {"path": "//*[@id='transfer-list-modal']/div/div/div[2]/div/div[2]/div/table//tbody/tr/td[6]/a"}
        ]

    def test_go_to_objects_by_furniture_report(self):

        path_list1 = self.path_base + [
            {"path": "//*[@id='labroom_2']"},
            {"path": "//*[@id='collapselabroom']/ul/li[2]/ul/li/a[2]"}
        ]

        path_list2 = [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div/div/div[2]/div",
            "scroll": "window.scrollTo(0, 70)"}
        ]

        general_path_list = [path_list1, path_list2]
        self.create_gif_by_change_focus_tab(general_path_list, ["reportbase"],
                                            "go_to_objects_by_furniture_report")

    def create_reactive(self, row_ins_position, select_container_position,
                        container_type, ins_position=""):
        path_list = self.create_shelfobject_reative_start + [
            {"path": "//*[@id='reactive_form']/div[%d]/div/div/div%s/ins" %
                     (row_ins_position, ins_position)},
            {"path": "//*[@id='reactive_form']/div[%d]/div/span/span/span" % select_container_position},
        ] + self.create_shelfobject_reative_end + [
            {"path": self.get_save_button_modal("reactive_modal")}
        ]

        self.create_gif_process(path_list, "create_shelfobject_reactive_with_%s_container" % container_type)

    def test_create_shelfobject_reactive_with_clone_container(self):
        self.create_reactive(5, 6, "clone")

    def test_create_shelfobject_reactive_with_use_selected_container(self):
        self.create_reactive(5, 7, "use_selected",
                             ins_position="[2]")

    def test_create_shelfobject_material(self):
        path_list = self.path_base + [
            {"path": "//*[@id='labroom_1']"},
            {"path": "//*[@id='furniture_2']"},
            {"path": "//*[@id='shelf_3']"},
            {"path": "//*[@id='shelfobjecttable_wrapper']/div/div[2]/div/button[2]",
             "scroll": "window.scrollTo(0, 250)"},
            {"path": "//*[@id='material_form']/div/div/span/span/span"},
            {"path": "//*[@id='material_form']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='material_form']/div[2]/div/span/span/span"},
            {"path": "//*[@id='material_form']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='material_form']/div[3]/div/input"},
            {"path": "//*[@id='material_form']/div[3]/div/input",
             "extra_action": "setvalue", "value": "4"},
            {"path": "//*[@id='material_form']/div[5]/div/textarea"},
            {"path": "//*[@id='material_form']/div[5]/div/textarea",
             "extra_action": "setvalue", "value": "Contenedor de base cilíndrica para "
                                                  "líquidos con capacidad de 1L."},
            {"path": self.get_save_button_modal("material_modal")}
        ]
        self.create_gif_process(path_list, "create_shelfobject_material")

    def test_create_shelfobject_equipment(self):
        initial_date, initial_date_strftime = self.get_format_increase_decrease_date(now(), 1)
        final_date, final_date_strftime = self.get_format_increase_decrease_date(initial_date, 5)

        path_list = self.path_base + [
            {"path": "//*[@id='labroom_1']"},
            {"path": "//*[@id='furniture_1']"},
            {"path": "//*[@id='shelf_1']"},
            {"path": "//*[@id='shelfobjecttable_wrapper']/div/div[2]/div/button",
             "scroll": "window.scrollTo(0, 250)"},
            {"path": "//*[@id='select2-id_ef-object-container']"},
            {"path": "//*[@id='equipment_form']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='select2-id_ef-status-container']"},
            {"path": "//*[@id='equipment_form']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='equipment_form']/div[4]/div/textarea",
             "extra_action": "setvalue", "value": "Instrumento para calcular la masa de un objeto."},
            {"path": "//*[@id='equipment_form']/div[7]/div/input","extra_action":"clearinput"},
            {"path": "//*[@id='equipment_form']/div[7]/div/input", "extra_action": "setvalue", "value": "2000"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[11]/div/div/div[2]/div/div[2]/form/div[8]/div/div/input","scroll": "$('#equipment_modal').scrollTop(300)"},
            {"path": "//*[@data-day='%s']" % initial_date_strftime},
            {"path": "//html/body/div[1]/div/div[3]/div/div/div[11]/div/div/div[2]/div/div[2]/form/div[9]/div/div/input"},
            {"path": "//*[@data-day='%s']" % final_date_strftime},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[11]/div/div/div[2]/div/div[2]/form/div[10]/div/span","scroll": "$('#equipment_modal').scrollTop(600)"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[11]/div/div/div[2]/div/div[2]/form/div[12]/div/span"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[11]/div/div/div[2]/div/div[2]/form/div[14]/div/textarea",
             "extra_action":"setvalue", "value":"Es un equipo nuevo"},

            {"path": self.get_save_button_modal("equipment_modal")}
        ]
        #"scroll": "$('#equipment_modal').scrollTop(300);
        self.create_gif_process(path_list, "create_shelfobject_equipment")

    def test_view_containers_by_shelf(self):

        path_list = self.select_lab_elements + [
            {"path": "//*[@id='shelfobjecttable_wrapper']/div/div[2]/div/button[4]",
             "scroll": "window.scrollTo(0, 250)"},
            {"path": "//*[@id='container_table']", "extra_action": "script",
             "value": "window.scrollTo(0, 50)"},
            {"path": "//*[@id='container_table']", "extra_action": "script",
             "value": "window.scrollTo(0, 100)"}
        ]
        self.create_gif_process(path_list, "view_containers_by_shelf")

    def test_approve_transfer_in_shelfobject_with_clone_container(self):

        path_list = self.approve_transfer_in + [
            {"path": "//*[@id='transfer_in_approve_with_container_form']/div/div/div/div/ins"},
            {"path": "//*[@id='transfer_in_approve_with_container_form']/div[2]/div/span/span/span"},
            {"path": "//*[@id='transfer_in_approve_with_container_id_modal']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='transfer_in_approve_with_container_id_modal']/div/div/div[3]/button[2]"}
        ]
        self.create_gif_process(path_list, "approve_transfer_in_shelfobject_with_clone_container")

    def test_approve_transfer_in_shelfobject_with_available_container(self):

        path_list = self.approve_transfer_in + [
            {"path": "//*[@id='transfer_in_approve_with_container_form']/div/div/div/div[2]/ins"},
            {"path": "//*[@id='transfer_in_approve_with_container_form']/div[3]/div/span/span/span"},
            {"path": "//*[@id='transfer_in_approve_with_container_id_modal']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='transfer_in_approve_with_container_id_modal']/div/div/div[3]/button[2]"}
        ]
        self.create_gif_process(path_list, "approve_transfer_in_shelfobject_with_available_container")

    def test_approve_transfer_in_shelfobject_with_use_source_container(self):

        path_list = self.approve_transfer_in + [
            {"path": "//*[@id='transfer_in_approve_with_container_form']/div/div/div/div[3]/ins"},
            {"path": "//*[@id='transfer_in_approve_with_container_id_modal']/div/div/div[3]/button[2]"}
        ]
        self.create_gif_process(path_list, "approve_transfer_in_shelfobject_with_use_source_container")

    def test_approve_transfer_in_shelfobject_with_new_based_source_container(self):

        path_list = self.approve_transfer_in + [
            {"path": "//*[@id='transfer_in_approve_with_container_form']/div/div/div/div[4]/ins"},
            {"path": "//*[@id='transfer_in_approve_with_container_id_modal']/div/div/div[3]/button[2]"}
        ]
        self.create_gif_process(path_list, "approve_transfer_in_shelfobject_with_new_based_source_container")

    def test_deny_transfer_in_shelfobject(self):

        path_list = self.view_transfer_list + [
            {"path": "//*[@id='transfer-list-modal']/div/div/div[2]/div/div[2]/div/table//tbody/tr/td[6]/a[2]"},
            {"path": "/html/body/div[4]/div/div[3]/button[1]"},
        ]
        self.create_gif_process(path_list, "deny_transfer_in_shelfobject")
