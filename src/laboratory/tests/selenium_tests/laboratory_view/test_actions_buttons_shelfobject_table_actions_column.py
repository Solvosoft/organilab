import time
from datetime import timedelta

from django.test import tag
from django.utils.timezone import localdate, localtime
from organilab_test.tests.selenium_xpaths import select2_result

from reservations_management.models import ReservedProducts

from laboratory.tests.selenium_tests.laboratory_view.base import (
    LaboratoryViewSeleniumTest,
)


class ButtonsActionsTableColumnBase(LaboratoryViewSeleniumTest):
    def setUp(self):
        super().setUp()

        self.buttons_actions_path = self.path_base + [
            {"path": "//*[@id='labroom_2']"},
            {"path": "//*[@id='furniture_3']"},
            {"path": "//*[@id='shelf_2']", "scroll": "window.scrollTo(0, 250)"},
        ]

        self.path_shelfobject_info = ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div/div/div[2]/div/div"

        self.scroll_shelfobject_info = [
            {
                "path": self.path_shelfobject_info,
                "extra_action": "script",
                "value": "window.scrollTo(0, 100)",
            },
            {
                "path": self.path_shelfobject_info,
                "extra_action": "script",
                "value": "window.scrollTo(0, 200)",
            },
            {
                "path": self.path_shelfobject_info,
                "extra_action": "script",
                "value": "window.scrollTo(0, 300)",
            },
        ]


@tag("selenium")
class ButtonsActionsTableColumn(ButtonsActionsTableColumnBase):

    def setUp(self):
        super().setUp()

        self.move_shelfobject_form_path = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-arrows"), "sleep": 30},
            {
                "path": "//*[@id='movesocontainerform']/div/div/span/span/span",
                "scroll": "$('#movesocontainermodal').scrollTop(150);",
            },
            {"path": select2_result(1)},
            {"path": "//*[@id='movesocontainerform']/div[2]/div/span/span/span"},
            {"path": select2_result(1)},
            {"path": "//*[@id='movesocontainerform']/div[3]/div/span/span/span"},
            {"path": select2_result(1)},
        ]

    def test_view_shelfobject_detail(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-eye")},
            {
                "path": "//*[@id='shelfobject_detail_modal_body']",
                "extra_action": "script",
                "value": "$('#shelfobject_detail_modal_body').scrollTop(150);",
            },
            {
                "path": "//*[@id='shelfobject_detail_modal_body']",
                "extra_action": "script",
                "value": "$('#shelfobject_detail_modal_body').scrollTop(300);",
            },
            {
                "path": "//*[@id='shelfobject_detail_modal_body']",
                "extra_action": "script",
                "value": "$('#shelfobject_detail_modal_body').scrollTop(450);",
            },
            {"path": "//*[@id='detail_modal_container']/div/div/div[3]/button"},
        ]
        self.create_gif_process(path_list, "view_shelfobject_detail")

    def open_datepicker_on(self, input_id, target_date):
        """Pasos para abrir el datepicker de `input_id` mostrando el mes de `target_date`.

        El bootstrap-datetimepicker de gentelella sólo se abre con el evento
        `focus` del input, y las celdas `data-day` sólo existen mientras está
        abierto. Si el click real cae en el fallback por JS (click
        interceptado bajo carga) o la ventana no tiene el foco del sistema,
        `focus` no se dispara y el día nunca aparece. Además el picker abre
        en el mes de "hoy" según el reloj del navegador, no en el del
        servidor. Por eso, tras el click que se ve en el GIF, se asegura por
        la API del widget que esté abierto y se navega con sus propias
        flechas de mes hasta el del día objetivo (viewDate() sólo cambia el
        estado interno, no vuelve a pintar la cuadrícula). El día se sigue
        eligiendo con un click real.
        """
        return [
            {"path": "//*[@id='%s']" % input_id, "sleep": 15},
            {
                "path": "//*[@id='%s']" % input_id,
                "extra_action": "script",
                "value": (
                    "var input = $('#%(id)s'), dp = input.data('DateTimePicker');"
                    "dp.show();"
                    "var widget = input.parent().find('.bootstrap-datetimepicker-widget');"
                    "var target = moment('%(day)s', 'YYYY-MM-DD');"
                    "for (var i = 0; i < 24 && !widget.find(\"td[data-day='%(cell)s']\").length; i++) {"
                    "  var arrow = dp.viewDate().isAfter(target, 'month') ? 'previous' : 'next';"
                    "  widget.find('.datepicker-days [data-action=' + arrow + ']').click();"
                    "}"
                )
                % {
                    "id": input_id,
                    "day": target_date.strftime("%Y-%m-%d"),
                    "cell": target_date.strftime("%m/%d/%Y"),
                },
            },
        ]

    def day_cell(self, form_id, target_date):
        # data-day sale de moment().format('L'); la página carga moment en
        # inglés, así que el formato es MM/DD/YYYY. Se acota al formulario
        # para no casar con otro datepicker de la página.
        return "//*[@id='%s']//td[@data-day='%s']" % (
            form_id,
            target_date.strftime("%m/%d/%Y"),
        )

    def test_reserve_shelfobject(self):
        # Fechas de calendario en la zona del proyecto (America/Costa_Rica)
        # y no en UTC: entre las 18:00 y las 24:00 de Costa Rica now() ya es
        # el día siguiente. Con viewDate el mes visible deja de importar, así
        # que el margen de días ya no depende de la fecha de la corrida.
        initial_date = localdate() + timedelta(days=2)
        final_date = initial_date + timedelta(days=1)

        path_list = (
            self.buttons_actions_path
            + [
                {"path": self.shelfobject_row_action("fa-shopping-basket")},
                {"path": "//*[@id='reservesoform']/div/div/input"},
                {
                    "path": "//*[@id='reservesoform']/div/div/input",
                    "extra_action": "setvalue",
                    "value": "2",
                },
            ]
            + self.open_datepicker_on("id_reserve-initial_date", initial_date)
            + [
                {"path": self.day_cell("reservesoform", initial_date), "sleep": 1},
                {"path": "//*[@id='reservesomodal']//h4 | //*[@id='reservesomodal']//h5", "sleep": 1},
            ]
            + self.open_datepicker_on("id_reserve-final_date", final_date)
            + [
                {"path": self.day_cell("reservesoform", final_date), "sleep": 1},
                {"path": "//*[@id='reservesomodal']//h4 | //*[@id='reservesomodal']//h5", "sleep": 1},
                {"path": self.get_save_button_modal("reservesomodal"), "sleep": 5},
            ]
        )
        self.create_gif_process(path_list, "reserve_shelfobject")

        # La reserva tiene que haberse guardado con los días elegidos en el
        # calendario; si el picker eligió otro día o el POST falló, aquí se ve.
        reserved = self.wait_for_reservation()
        self.assertEqual(reserved.amount_required, 2)
        self.assertEqual(localtime(reserved.initial_date).date(), initial_date)
        self.assertEqual(localtime(reserved.final_date).date(), final_date)

    def wait_for_reservation(self, timeout=10):
        # El guardado es un POST por AJAX: el último paso no espera su respuesta.
        deadline = time.monotonic() + timeout
        while True:
            reserved = ReservedProducts.objects.order_by("-pk").first()
            if reserved is not None or time.monotonic() > deadline:
                break
            time.sleep(0.2)
        self.assertIsNotNone(reserved, "no se guardó la reserva del objeto")
        return reserved

    def test_increase_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-plus")},
            {"path": "//*[@id='id_increase-amount']"},
            {
                "path": "//*[@id='id_increase-amount']",
                "extra_action": "setvalue",
                "value": "5",
            },
            {"path": "//*[@id='id_increase-bill']"},
            {
                "path": "//*[@id='id_increase-bill']",
                "extra_action": "setvalue",
                "value": "R78509",
            },
            {"path": "//span[@aria-controls='select2-id_increase-measurement_unit-container']"},
            {"path": select2_result(1), "sleep": 1},
            {"path": self.get_save_button_modal("increasesomodal")},
        ]
        self.create_gif_process(path_list, "increase_shelfobject")

    def test_transfer_out_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-window-restore")},
            {"path": "//*[@id='id_amount_to_transfer']"},
            {
                "path": "//*[@id='id_amount_to_transfer']",
                "extra_action": "setvalue",
                "value": "2",
            },
            {"path": "//*[@id='transfer_out_form']/div[2]/div/span/span/span"},
            {"path": select2_result(2)},
            {"path": self.get_save_button_modal("transfer_out_obj_id_modal")},
        ]
        self.create_gif_process(path_list, "transfer_out_shelfobject")

    def test_transfer_out_shelfobject_refuse(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-window-restore")},
            {"path": "//*[@id='id_amount_to_transfer']"},
            {
                "path": "//*[@id='id_amount_to_transfer']",
                "extra_action": "setvalue",
                "value": "2",
            },
            {"path": "//*[@id='transfer_out_form']/div[2]/div/span/span/span"},
            {"path": select2_result(2)},
            {
                "path": "//*[@id='transfer_out_form']//input[@name='mark_as_discard']",
                "extra_action": "script",
                "value": "$('#transfer_out_form input[name=mark_as_discard]')"
                         ".prop('checked', true).trigger('change')",
            },
            {"path": self.get_save_button_modal("transfer_out_obj_id_modal")},
        ]
        self.create_gif_process(path_list, "transfer_out_shelfobject_refuse")

    def test_decrease_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-minus")},
            {"path": "//*[@id='id_decrease-amount']"},
            {
                "path": "//*[@id='id_decrease-amount']",
                "extra_action": "setvalue",
                "value": "3",
            },
            {"path": "//*[@id='id_decrease-description']"},
            {
                "path": "//*[@id='id_decrease-description']",
                "extra_action": "setvalue",
                "value": "Práctica de laboratorio",
            },
            {"path": self.get_save_button_modal("decreasesomodal")},
        ]
        self.create_gif_process(path_list, "decrease_shelfobject")

    def test_view_shelfobject_logs(self):
        path_list1 = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-file-text-o")}
        ]
        general_path_list = [path_list1, self.scroll_shelfobject_info]
        self.create_gif_by_change_focus_tab(
            general_path_list, ["shelfobjectlog"], "view_shelfobject_logs"
        )

    def test_manage_shelfobject_container_clone(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-hourglass-end")},
            {"path": self.container_radio("manageconteinerform", "clone")},
            {"path": "//*[@id='manageconteinerform']/div[2]/div/span/span/span"},
            {"path": select2_result(1)},
            {"path": self.get_save_button_modal("managecontainermodal")},
        ]
        self.create_gif_process(path_list, "manage_shelfobject_container_clone")

    def test_manage_shelfobject_container_available(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-hourglass-end")},
            {"path": self.container_radio("manageconteinerform", "available")},
            {"path": "//*[@id='manageconteinerform']/div[3]/div/span/span/span"},
            {"path": select2_result(2)},
            {"path": self.get_save_button_modal("managecontainermodal")},
        ]
        self.create_gif_process(path_list, "manage_shelfobject_container_available")

    def test_move_shelfobject_with_clone_container(self):
        path_list = self.move_shelfobject_form_path + [
            {"path": self.container_radio("movesocontainerform", "clone")},
            {
                "path": self.container_radio("movesocontainerform", "clone"),
                "extra_action": "script",
                "value": "$('#movesocontainermodal').scrollTop(300);",
            },
            {"path": "//*[@id='movesocontainerform']/div[6]/div/span/span/span"},
            {"path": select2_result(1)},
            {"path": self.get_save_button_modal("movesocontainermodal")},
        ]
        self.create_gif_process(path_list, "move_shelfobject_with_clone_container")

    def test_move_shelfobject_with_available_container(self):
        path_list = self.move_shelfobject_form_path + [
            {"path": self.container_radio("movesocontainerform", "available")},
            {
                "path": self.container_radio("movesocontainerform", "available"),
                "extra_action": "script",
                "value": "$('#movesocontainermodal').scrollTop(300);",
            },
            {"path": "//*[@id='movesocontainerform']/div[7]/div/span/span/span"},
            {"path": select2_result(1)},
            {"path": self.get_save_button_modal("movesocontainermodal")},
        ]
        self.create_gif_process(path_list, "move_shelfobject_with_available_container")

    def test_move_shelfobject_with_use_source_container(self):
        path_list = self.move_shelfobject_form_path + [
            {"path": self.container_radio("movesocontainerform", "use_source")},
            {
                "path": self.container_radio("movesocontainerform", "use_source"),
                "extra_action": "script",
                "value": "$('#movesocontainermodal').scrollTop(300);",
            },
            {"path": self.get_save_button_modal("movesocontainermodal")},
        ]
        self.create_gif_process(path_list, "move_shelfobject_with_use_source_container")

    def test_move_shelfobject_with_new_based_source_container(self):
        path_list = self.move_shelfobject_form_path + [
            {"path": self.container_radio("movesocontainerform", "new_based_source")},
            {
                "path": self.container_radio("movesocontainerform", "new_based_source"),
                "extra_action": "script",
                "value": "$('#movesocontainermodal').scrollTop(300);",
            },
            {"path": self.get_save_button_modal("movesocontainermodal")},
        ]
        self.create_gif_process(
            path_list, "move_shelfobject_with_new_based_source_container"
        )

    def test_download_shelfobject_info(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-download")}
        ]
        self.create_gif_process(path_list, "download_shelfobject_info")

    def test_delete_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-close")},
            {"path": self.get_save_button_modal("delete_shelfobject_modal")},
        ]
        self.create_gif_process(path_list, "delete_shelfobject")

    def test_delete_shelfobject_and_its_container(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-close")},
            {
                "path": "//*[@id='id_delete_container']",
                "extra_action": "script",
                "value": "$('#id_delete_container')"
                         ".prop('checked', true).trigger('change')",
            },
            {"path": self.get_save_button_modal("delete_shelfobject_modal")},
        ]
        self.create_gif_process(path_list, "delete_shelfobject_and_its_container")
