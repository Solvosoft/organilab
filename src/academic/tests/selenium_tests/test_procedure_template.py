from django.contrib.auth.models import User
from django.test import tag
from organilab_test.tests.selenium_xpaths import select2_result
from django.urls import reverse

from organilab_test.tests.base import OptimizedSeleniumBase, modifies_db


@tag("selenium")
class ProcedureTemplateSeleniumTest(OptimizedSeleniumBase):
    fixtures = ["selenium/base_selenium.json", "selenium/procedure_delta.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )
        self.navigate_to_procedure_list()

    def navigate_to_procedure_list(self):
        """Navigate directly to the procedure list page."""
        url = self.live_server_url + str(
            reverse("academic:procedure_list", kwargs={"org_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    @modifies_db
    def test_procedure_crud(self):
        """Test full CRUD cycle for procedure templates.

        Chains: create procedure -> update procedure -> view detail
        -> CRUD steps (add step, object, observation, update step,
        delete step, delete procedure).
        """
        path_list = [
            {
                "path": "//div[contains(@class, 'dt-buttons')]//button[contains(@class, 'btn-success')]",
                "wait_ready": True,
                "sleep": 3,
            },
            {
                "path": "//input[@name='title']",
                "extra_action": "setvalue",
                "value": "Se limpiaran laboratorios",
                "wait_ready": True,
            },
            {
                "path": "//form[1]",
                "extra_action": "script",
                "value": 'tinymce.get("id_description").setContent("<p><strong>Se limpiaran los muebles, frascos entre otras herramientas</strong></p>");',
            },
            {
                "path": "//form//button[@type='submit'] | //form//a[contains(@class, 'btn-success')]",
            },
        ]
        self.create_gif_process(path_list, "create_procedure_template")
        self.update_procedure()
        self.detail_procedure()
        self.crud_step()

    def update_procedure(self):
        """Update a procedure template.

        Flow: Navigate to procedure list -> Click edit icon on
        first row -> Update title and description -> Submit.

        GIF: docs/source/_static/gif/update_procedure_template.gif
        """
        self.navigate_to_procedure_list()
        path_list = [
            {
                "path": "//table[@id='procedure']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "sleep": 2,
            },
            {
                "path": "//input[@name='title']",
                "extra_action": "clearinput",
                "wait_ready": True,
            },
            {
                "path": "//input[@name='title']",
                "extra_action": "setvalue",
                "value": "Se limpiaran laboratorios",
            },
            {
                "path": "//form[1]",
                "extra_action": "script",
                "value": 'tinymce.get("id_description").setContent("<p><strong>Se limpiaran los muebles, frascos entre otras herramientas</strong></p>");',
            },
            {
                "path": "//form//button[@type='submit'] | //form//a[contains(@class, 'btn-success')]",
            },
        ]
        self.create_gif_process(path_list, "update_procedure_template")

    def detail_procedure(self):
        """View procedure template detail with steps.

        Flow: Navigate to procedure list -> Click detail icon on
        first row -> Click back to list.

        GIF: docs/source/_static/gif/detail_procedure_template.gif
        """
        self.navigate_to_procedure_list()
        path_list = [
            {
                "path": "//table[@id='procedure']//tbody/tr[1]//i[contains(@class, 'fa-eye')]",
                "sleep": 2,
            },
            {
                "path": "//a[contains(@class, 'btn-primary') and contains(@href, 'procedure_list')]",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "detail_procedure_template")

    def delete_procedure(self):
        """Delete a procedure template.

        Flow: Navigate to procedure list -> Click delete icon on
        first row -> Confirm in SweetAlert.

        GIF: docs/source/_static/gif/delete_procedure_template.gif
        """
        self.navigate_to_procedure_list()
        path_list = [
            {
                "path": "//table[@id='procedure']//tbody/tr[1]//i[contains(@class, 'fa-trash')]",
                "extra_action": "sweetalert_comfirm",
                "comfirm": """document.querySelector('.swal2-confirm').click();""",
                "sleep": 2,
            },
        ]
        self.create_gif_process(path_list, "delete_procedure_template")

    def crud_step(self):
        """Test CRUD operations on procedure steps.

        Flow: Navigate to procedure list -> Click add step icon ->
        Fill step form -> Add a textfield to the formio builder ->
        Submit -> Chain sub-operations.

        GIF: docs/source/_static/gif/add_step.gif
        """
        self.navigate_to_procedure_list()
        set_form_schema = (
            "var mySchema = {display:'form', components:[{"
            "type:'textfield', key:'observacion', label:'Observacion', input:true"
            "}]};"
            "Object.defineProperty(stepFormBuilder, 'form', "
            "{get: function(){ return mySchema; }, configurable: true});"
        )
        path_list = [
            {
                "path": "//table[@id='procedure']//tbody/tr[1]//i[contains(@class, 'fa-plus')]",
                "sleep": 2,
            },
            {
                "path": "//input[@name='title']",
                "extra_action": "setvalue",
                "value": "Paso 1",
                "wait_ready": True,
            },
            {
                "path": "//form[1]",
                "extra_action": "script",
                "value": 'tinymce.get("id_description").setContent("<p>Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industrys standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.</p>");',  # noqa: E501
            },
            {
                "path": "//div[@id='formio_step_builder']",
                "extra_action": "script",
                "value": set_form_schema,
                "scroll": "window.scrollTo(0, 400)",
                "sleep": 1,
            },
            {
                "path": "//button[contains(@class, 'step_save')] | //button[contains(@class, 'btn-success') and @type='submit']",
                "scroll": "window.scrollTo(0, 300)",
            },
        ]
        self.create_gif_process(path_list, "add_step")
        self.object_step()
        self.observation()
        self.update_step()
        self.delete_step()
        self.delete_procedure()

    def update_step(self):
        """Update a procedure step.

        Flow: Navigate to procedure list -> Click detail -> Click
        edit step -> Update title -> Submit -> Return to list.

        GIF: docs/source/_static/gif/update_step.gif
        """
        self.navigate_to_procedure_list()
        path_list = [
            {
                "path": "//table[@id='procedure']//tbody/tr[1]//i[contains(@class, 'fa-eye')]",
                "sleep": 2,
            },
            {
                "path": "//a[.//span[contains(@class, 'fa-edit') and contains(@class, 'text-success')]]",
                "wait_ready": True,
            },
            {
                "path": "//input[@name='title']",
                "extra_action": "clearinput",
                "wait_ready": True,
            },
            {
                "path": "//input[@name='title']",
                "extra_action": "setvalue",
                "value": "Paso 1",
            },
            {
                "path": "//button[contains(@class, 'step_save')] | //button[contains(@class, 'btn-success') and @type='submit']",
                "scroll": "window.scrollTo(0, 100)",
            },
            {
                "path": "//table[@id='procedure']//tbody/tr[1]//i[contains(@class, 'fa-eye')]",
                "sleep": 2,
            },
            {
                "path": "//a[contains(@class, 'btn-primary') and contains(@href, 'procedure_list')]",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "update_step")

    def delete_step(self):
        """Delete a procedure step.

        Flow: Navigate to procedure list -> Click detail -> Click
        delete step -> Confirm in SweetAlert -> Return to list.

        GIF: docs/source/_static/gif/delete_step.gif
        """
        self.navigate_to_procedure_list()
        path_list = [
            {
                "path": "//table[@id='procedure']//tbody/tr[1]//i[contains(@class, 'fa-eye')]",
                "sleep": 2,
            },
            {
                "path": "//*[contains(@class, 'fa-trash') and contains(@class, 'text-danger')]",
                "extra_action": "sweetalert_comfirm",
                "comfirm": """document.querySelector('.swal2-confirm').click();""",
                "wait_ready": True,
            },
            {
                "path": "//a[contains(@class, 'btn-primary') and contains(@href, 'procedure_list')]",
                "sleep": 2,
            },
        ]
        self.create_gif_process(path_list, "delete_step")

    def object_step(self):
        """Add an object to a procedure step.

        Flow: Navigate to procedure list -> Click detail -> Click
        add object -> Fill object form (select object, quantity,
        unit) -> Save -> Submit step form.

        GIF: docs/source/_static/gif/add_step_object.gif
        """
        self.navigate_to_procedure_list()
        path_list = [
            {
                "path": "//table[@id='procedure']//tbody/tr[1]//i[contains(@class, 'fa-eye')]",
                "sleep": 2,
            },
            {
                "path": "//a[.//span[contains(@class, 'fa-edit') and contains(@class, 'text-success')]]",
                "wait_ready": True,
            },
            {
                "path": "//button[contains(@class, 'create-reqobj-btn')]",
                "scroll": "window.scrollTo(0, 300)",
                "wait_ready": True,
            },
            {
                "path": "//span[@aria-controls='select2-id_reqobj-object-container']",
                "sleep": 1,
            },
            {
                "path": select2_result(2),
            },
            {
                "path": "//input[@id='id_reqobj-quantity']",
                "extra_action": "clearinput",
            },
            {
                "path": "//input[@id='id_reqobj-quantity']",
                "extra_action": "setvalue",
                "value": "10",
            },
            {
                "path": "//span[@aria-controls='select2-id_reqobj-measurement_unit-container']",
            },
            {
                "path": "//li[text()='Metros']",
            },
            {
                "path": "//*[@id='object_modal']//button[contains(@class, 'formadd')]",
            },
            {
                "path": "//button[@id='save_step'] | //button[contains(@class, 'step_save')]",
            },
        ]
        self.create_gif_process(path_list, "add_step_object")
        self.remove_object()

    def remove_object(self):
        """Remove an object from a procedure step.

        Flow: Navigate to procedure list -> Click detail -> Click
        edit step -> Click delete on object row -> Confirm ->
        Submit step form.

        GIF: docs/source/_static/gif/remove_step_object.gif
        """
        self.navigate_to_procedure_list()
        self.create_directory_path(folder_name="remove_step_object")
        path_list = [
            {
                "path": "//table[@id='procedure']//tbody/tr[1]//i[contains(@class, 'fa-eye')]",
                "sleep": 2,
            },
            {
                "path": "//a[.//span[contains(@class, 'fa-edit') and contains(@class, 'text-success')]]",
                "wait_ready": True,
            },
            {
                "path": "//table[@id='table-reqobj']//tbody/tr[1]//i[contains(@class, 'fa-trash')]",
                "scroll": "window.scrollTo(0, 400)",
                "wait_ready": True,
            },
            {
                "path": "//*[@id='delete_object_modal']//button[contains(@class, 'delbtn')]",
                "sleep": 1,
            },
            {
                "path": "//button[@id='save_step'] | //button[contains(@class, 'step_save')]",
            },
        ]
        self.create_gif_process(path_list, "remove_step_object")

    def observation(self):
        """Add an observation to a procedure step.

        Flow: Navigate to procedure list -> Click detail -> Click
        edit step -> Click add observation -> Enter description ->
        Save observation -> Submit step form.

        GIF: docs/source/_static/gif/add_step_observation.gif
        """
        self.navigate_to_procedure_list()
        self.create_directory_path(folder_name="add_step_observation")
        path_list = [
            {
                "path": "//table[@id='procedure']//tbody/tr[1]//i[contains(@class, 'fa-eye')]",
                "sleep": 2,
            },
            {
                "path": "//a[.//span[contains(@class, 'fa-edit') and contains(@class, 'text-success')]]",
                "wait_ready": True,
            },
            {
                "path": "//button[contains(@class, 'create-obs-btn')]",
                "scroll": "window.scrollTo(0, 350)",
                "wait_ready": True,
            },
            {
                "path": "//textarea[@id='id_obs-description']",
                "extra_action": "setvalue",
                "value": "Tener cuidado con los envases de materiales biologícos",
                "sleep": 1,
            },
            {
                "path": "//*[@id='observation_modal']//button[contains(@class, 'formadd')]",
                "scroll": "window.scrollTo(0, document.body.scrollHeight)",
            },
            {
                "path": "//button[@id='save_step'] | //button[contains(@class, 'step_save')]",
            },
        ]
        self.create_gif_process(path_list, "add_step_observation")
        self.remove_observation()

    def remove_observation(self):
        """Remove an observation from a procedure step.

        Flow: Navigate to procedure list -> Click detail -> Click
        edit step -> Click delete on observation row -> Confirm ->
        Submit step form.

        GIF: docs/source/_static/gif/remove_step_observation.gif
        """
        self.navigate_to_procedure_list()
        self.create_directory_path(folder_name="remove_step_observation")
        path_list = [
            {
                "path": "//table[@id='procedure']//tbody/tr[1]//i[contains(@class, 'fa-eye')]",
                "sleep": 2,
            },
            {
                "path": "//a[.//span[contains(@class, 'fa-edit') and contains(@class, 'text-success')]]",
                "wait_ready": True,
            },
            {
                "path": "//table[@id='table-obs']//tbody/tr[1]//i[contains(@class, 'fa-trash')]",
                "scroll": "window.scrollTo(0, 600)",
                "wait_ready": True,
            },
            {
                "path": "//*[@id='delete_observation_modal']//button[contains(@class, 'delbtn')]",
                "sleep": 1,
            },
            {
                "path": "//button[@id='save_step'] | //button[contains(@class, 'step_save')]",
                "scroll": "window.scrollTo(0, 100)",
            },
        ]
        self.create_gif_process(path_list, "remove_step_observation")
