from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse

from organilab_test.tests.base import OptimizedSeleniumBase, modifies_db


@tag("selenium")
class MyProcedureSeleniumTest(OptimizedSeleniumBase):
    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    def navigate_to_my_procedures(self):
        """Navigate directly to the my procedures list page."""
        url = self.live_server_url + str(
            reverse(
                "academic:get_my_procedures",
                kwargs={"org_pk": 1, "lab_pk": 1},
            )
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def test_view_my_procedure(self):
        """Test viewing the my procedures list page.

        Flow: Navigate to my procedures list -> View page.

        GIF: docs/source/_static/gif/view_my_procedure.gif
        """
        self.navigate_to_my_procedures()
        path_list = [
            {
                "path": "//h1//span | //h1",
                "screenshot_name": "view_my_procedure",
            },
        ]
        self.create_gif_process(path_list, "view_my_procedure")

    @modifies_db
    def test_add_my_procedure(self):
        """Test adding a new personal procedure.

        Flow: Navigate to my procedures list -> Click create button
        -> Fill name -> Select procedure template -> Save.

        GIF: docs/source/_static/gif/add_my_procedure.gif
        """
        self.navigate_to_my_procedures()
        path_list = [
            {
                "path": "//div[contains(@class, 'dt-buttons')]//button[contains(@class, 'btn-success')]",
                "sleep": 2,
                "wait_ready": True,
            },
            {
                "path": "//*[@id='id_name']",
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Primer Procedimiento",
            },
            {
                "path": "//*[@id='add_my_procedures']//span[contains(@class, 'select2-selection')]",
                "sleep": 1,
            },
            {
                "path": "//ul[contains(@class, 'select2-results__options')]/li[1]",
            },
            {
                "path": "//*[@id='add_my_procedures']//button[contains(@class, 'btn-primary')]",
            },
        ]
        self.create_gif_process(path_list, "add_my_procedure")

    @modifies_db
    def test_delete_myprocedure(self):
        """Test deleting a personal procedure.

        Flow: Navigate to my procedures list -> Click delete icon
        on first row -> Confirm in SweetAlert.

        GIF: docs/source/_static/gif/delete_myprocedure.gif
        """
        self.navigate_to_my_procedures()
        path_list = [
            {
                "path": "//table[@id='my_procedures']//tbody/tr[1]//i[contains(@class, 'fa-trash')]",
                "sleep": 2,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
            },
        ]
        self.create_gif_process(path_list, "delete_myprocedure")

    @modifies_db
    def test_myprocedure_reservation(self):
        """Test creating a reservation for a personal procedure.

        Flow: Navigate to my procedures list -> Click reserved icon
        on first row -> Set initial date -> Set final date -> Save
        -> Confirm.

        GIF: docs/source/_static/gif/myprocedure_reservation.gif
        """
        tomorrow = date.today() + relativedelta(days=1)
        day_after = date.today() + relativedelta(days=2)
        initial_date = tomorrow.strftime("%m/%d/%Y") + " 14:36 PM"
        final_date = day_after.strftime("%m/%d/%Y") + " 01:00 AM"
        set_initial_date = (
            "document.querySelector('#id_initial_date').value='%s'" % initial_date
        )
        set_final_date = (
            "document.querySelector('#id_final_date').value='%s'" % final_date
        )
        self.navigate_to_my_procedures()
        path_list = [
            {
                "path": "//table[@id='my_procedures']//tbody/tr[1]//i[contains(@class, 'fa-book')]",
                "sleep": 2,
            },
            {
                "path": "//*[@id='id_initial_date']",
                "sleep": 1,
            },
            {
                "path": "//*[@id='id_initial_date']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='reservation_modal']//form",
                "extra_action": "script",
                "value": set_initial_date,
            },
            {
                "path": "//*[@id='reservation_modal']",
                "extra_action": "script",
                "value": "document.querySelector('#id_initial_date').blur()",
            },
            {
                "path": "//*[@id='id_final_date']",
            },
            {
                "path": "//*[@id='id_final_date']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='reservation_modal']//form",
                "extra_action": "script",
                "value": set_final_date,
            },
            {
                "path": "//*[@id='reservation_modal']",
                "extra_action": "script",
                "value": "document.querySelector('#id_final_date').blur()",
            },
            {
                "path": "//*[@id='reservation_modal']//button[contains(@class, 'btn-success')]",
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 2,
            },
        ]
        self.create_gif_process(path_list, "myprocedure_reservation")

    @modifies_db
    def test_add_observation_my_procedure(self):
        """Test adding an observation and filling the step formio form.

        Flow: Navigate to my procedures list -> Click edit icon
        on first row -> Select a step -> Fill formio form field ->
        Save form -> Click add comment -> Enter comment -> Save.

        GIF: docs/source/_static/gif/add_my_procedure_observation.gif
        """
        self.navigate_to_my_procedures()
        path_list = [
            {
                "path": "//table[@id='my_procedures']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "sleep": 2,
            },
            {
                "path": "//input[contains(@class, 'stepradio')]",
                "wait_ready": True,
            },
            {
                "path": "//details[@id='form']",
                "extra_action": "script",
                "value": "document.getElementById('form').setAttribute('open','')",
                "sleep": 2,
            },
            {
                "path": "//div[@id='formio']",
                "extra_action": "script",
                "value": (
                    "var inp = document.querySelector('#formio input[type=\"text\"]');"
                    "if(inp){"
                    "  inp.value='Muestra de laboratorio A';"
                    "  inp.dispatchEvent(new Event('input',{bubbles:true}));"
                    "  inp.dispatchEvent(new Event('change',{bubbles:true}));"
                    "}"
                ),
                "scroll": "window.scrollTo(0, 300)",
                "sleep": 1,
            },
            {
                "path": "//*[@id='save-step-form-btn']",
                "sleep": 1,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
            {
                "path": "//details[@id='observation']",
                "extra_action": "script",
                "value": "document.getElementById('observation').setAttribute('open','')",
                "scroll": "window.scrollTo(0, 0)",
                "sleep": 1,
            },
            {
                "path": "//*[@id='datatableelement_wrapper']//button[.//i[contains(@class, 'fa-plus')]]",
                "sleep": 1,
            },
            {
                "path": "//*[@id='id_comment']",
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": "//*[@id='id_comment']",
                "extra_action": "setvalue",
                "value": "Se ve excelente el procedimiento",
            },
            {
                "path": "//*[@id='commentmodal']//button[contains(@class, 'btn-primary')]",
            },
        ]
        self.create_gif_process(path_list, "add_my_procedure_observation")

    @modifies_db
    def test_update_observation_my_procedure(self):
        """Test updating an observation on a personal procedure.

        Flow: Navigate to my procedures list -> Click edit icon ->
        Select step -> Click edit observation icon -> Update comment
        -> Confirm.

        GIF: docs/source/_static/gif/update_my_procedure_observation.gif
        """
        self.navigate_to_my_procedures()
        path_list = [
            {
                "path": "//table[@id='my_procedures']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "sleep": 2,
            },
            {
                "path": "//input[contains(@class, 'stepradio')]",
                "wait_ready": True,
            },
            {
                "path": "//input[contains(@class, 'stepradio')]",
                "extra_action": "script",
                "value": "null",
                "sleep": 3,
            },
            {
                "path": "//i[contains(@class, 'beditbtn')]",
                "scroll": "window.scrollTo(0, 0)",
                "sleep": 1,
            },
            {
                "path": "//div[contains(@class, 'swal2-popup')]//textarea",
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": "//div[contains(@class, 'swal2-popup')]//textarea",
                "extra_action": "setvalue",
                "value": "Revisar de nuevo la lista de objectos",
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "update_my_procedure_observation")

    @modifies_db
    def test_delete_observation_my_procedure(self):
        """Test deleting an observation from a personal procedure.

        Flow: Navigate to my procedures list -> Click edit icon ->
        Select step -> Click delete observation icon -> Confirm.

        GIF: docs/source/_static/gif/delete_my_procedure_observation.gif
        """
        self.navigate_to_my_procedures()
        path_list = [
            {
                "path": "//table[@id='my_procedures']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "sleep": 2,
            },
            {
                "path": "//input[contains(@class, 'stepradio')]",
                "wait_ready": True,
            },
            {
                "path": "//input[contains(@class, 'stepradio')]",
                "extra_action": "script",
                "value": "null",
                "sleep": 3,
            },
            {
                "path": "//details[@id='observation']",
                "extra_action": "script",
                "value": "document.getElementById('observation').setAttribute('open','')",
                "sleep": 1,
            },
            {
                "path": "//i[contains(@class, 'deletebtn')]",
                "scroll": "window.scrollTo(0, 0)",
                "sleep": 1,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
            },
        ]
        self.create_gif_process(path_list, "delete_my_procedure_observation")

    def finalize_myprocedure(self):
        """Finalize a personal procedure.

        Flow: Navigate to my procedures list -> Click edit icon ->
        Click finalize button -> Confirm.

        GIF: docs/source/_static/gif/finalize_my_procedure.gif
        """
        self.navigate_to_my_procedures()
        path_list = [
            {
                "path": "//table[@id='my_procedures']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "sleep": 2,
            },
            {
                "path": "//button[contains(@onclick, 'saveForm')]",
                "scroll": "window.scrollTo(0, document.body.scrollHeight)",
                "wait_ready": True,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "finalize_my_procedure")

    @modifies_db
    def test_review_myprocedure(self):
        """Test reviewing and finalizing a personal procedure.

        Flow: Navigate to my procedures list -> Click edit icon ->
        Click review/finalize button -> Confirm -> Chain finalize.

        GIF: docs/source/_static/gif/review_my_procedure.gif
        """
        self.navigate_to_my_procedures()
        path_list = [
            {
                "path": "//table[@id='my_procedures']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "sleep": 2,
            },
            {
                "path": "//button[contains(@onclick, 'saveForm')]",
                "scroll": "window.scrollTo(0, document.body.scrollHeight)",
                "wait_ready": True,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "review_my_procedure")
        self.finalize_myprocedure()

    def test_download_myprocedure_pdf(self):
        """Test that the PDF download link exists and points to the correct endpoint.

        Flow: Navigate to my procedures list -> Wait for table ->
        Read the href of the download icon on first row ->
        Assert the URL contains the download endpoint.

        GIF: docs/source/_static/gif/download_myprocedure_pdf.gif
        """
        self.navigate_to_my_procedures()
        path_list = [
            {
                "path": "//table[@id='my_procedures']//tbody/tr[1]//i[contains(@class, 'fa-download')]",
                "sleep": 2,
                "screenshot_name": "download_myprocedure_pdf",
            },
        ]
        self.create_gif_process(path_list, "download_myprocedure_pdf")
        download_href = self.selenium.execute_script(
            "return document.querySelector("
            "\"table#my_procedures tbody tr:first-child a[href*='download']\""
            ").href;"
        )
        self.assertIn("download_my_procedures", download_href)
