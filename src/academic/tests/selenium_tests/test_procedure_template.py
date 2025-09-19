from django.contrib.auth.models import User
from django.urls import reverse
from organilab_test.tests.base import SeleniumBase
from django.test import tag


@tag("selenium")
class ProcedureTemplateSeleniumTest(SeleniumBase):
    fixtures = ["selenium/procedure_templates.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )
        self.selenium.get(
            self.live_server_url
            + str(reverse("academic:procedure_list", kwargs={"org_pk": 1}))
        )

    def test_procedure_crud(self):
        path_list = [
            {"path": ".//button[@class='btn btn-secondary btn-sm btn-success']"},
            {
                "path": ".//input[@name='title']",
                "extra_action": "setvalue",
                "value": "Se limpiaran laboratorios",
            },
            {
                "path": ".//form[1]",
                "extra_action": "script",
                "value": 'tinymce.get("id_description").setContent("<p><strong>Se limpiaran los muebles, frascos entre otras herramientas</strong></p>");',
            },
            {"path": ".//form/div[@class='text-center']/button[@type='submit']"},
        ]
        self.create_gif_process(path_list, "create_procedure_template")
        self.update_procedure()
        self.detail_procedure()
        self.crud_step()

    def update_procedure(self):
        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[3]"},
            {"path": ".//input[@name='title']", "extra_action": "clearInput"},
            {
                "path": ".//input[@name='title']",
                "extra_action": "setvalue",
                "value": "Se limpiaran laboratorios",
            },
            {
                "path": ".//form[1]",
                "extra_action": "script",
                "value": 'tinymce.get("id_description").setContent("<p><strong>Se limpiaran los muebles, frascos entre otras herramientas</strong></p>");',
            },
            {"path": ".//form/div[@class='text-center']/button[@type='submit']"},
        ]
        self.create_gif_process(path_list, "update_procedure_template")

    def detail_procedure(self):
        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": ".//div[1]/div/div[3]/div/div/div[1]/a[1]"},
        ]
        self.create_gif_process(path_list, "detail_procedure_template")

    def delete_procedure(self):
        path_list = [
            {
                "path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[4]",
                "extra_action": "sweetalert_comfirm",
                "comfirm": """document.querySelector('.swal2-confirm').click();""",
            },
        ]
        self.create_gif_process(path_list, "delete_procedure_template")

    def crud_step(self):
        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[2]"},
            {
                "path": ".//input[@name='title']",
                "extra_action": "setvalue",
                "value": "Paso 1",
            },
            {
                "path": ".//form[1]",
                "extra_action": "script",
                "value": 'tinymce.get("id_description").setContent("<p>Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industrys standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.</p>");',  # noqa: E501
            },
            {
                "path": ".//form/div[@class='text-center']/button[@type='submit']",
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
        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": ".//a[@title='Editar']"},
            {"path": ".//input[@name='title']", "extra_action": "clearinput"},
            {
                "path": ".//input[@name='title']",
                "extra_action": "setvalue",
                "value": "Paso 1",
            },
            {
                "path": ".//form/div[@class='text-center']/button[@type='submit']",
                "scroll": "window.scrollTo(0, 100)",
            },
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": ".//div[1]/div/div[3]/div/div/div[1]/a[1]"},
        ]
        self.create_gif_process(path_list, "update_step")

    def delete_step(self):
        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {
                "path": ".//div[1]/div/div[3]/div/div/div[3]/div[2]/a[1]",
                "extra_action": "sweetalert_comfirm",
                "comfirm": """document.querySelector('.swal2-confirm').click();""",
                "ok": """document.querySelector('.swal2-confirm').click();""",
            },
            {"path": ".//div[1]/div/div[3]/div/div/div[1]/a[1]"},
        ]
        self.create_gif_process(path_list, "delete_step")

    def object_step(self):
        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div[2]/a[2]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div[2]/div/div/span",
                "scroll": "window.scrollTo(0, 300)",
            },
            {"path": ".//span[@class='select2-selection select2-selection--single']"},
            {"path": ".//ul[@class='select2-results__options']"},
            {"path": ".//input[@id='id_quantity']", "extra_action": "clearInput"},
            {
                "path": ".//input[@id='id_quantity']",
                "extra_action": "setvalue",
                "value": 10,
            },
            {"path": ".//span[@aria-controls='select2-id_unit-container']"},
            {
                "path": ".//ul[@id='select2-id_unit-results']",
                "extra_action": {"select": ""},
            },
            {"path": ".//li[text()='Metros']"},
            {"path": ".//div[@class='modal-footer']/button[@class='btn btn-success']"},
            {
                "path": ".//div[1]/div/div[3]/div/div/div[1]/div[1]/div/form/div[3]/button"
            },
        ]
        self.create_gif_process(path_list, "add_step_object")
        self.remove_object()

    def remove_object(self):
        self.create_directory_path(folder_name="remove_step_object")

        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": ".//a[@title='Editar']"},
            {
                "path": ".//tbody[@id='object_list']/tr[1]/td[3]",
                "scroll": "window.scrollTo(0, 400)",
                "extra_action": "sweetalert_comfirm",
                "comfirm": """document.querySelector('.swal2-confirm').click();""",
                "ok": """document.querySelector('.swal2-confirm').click();""",
            },
            {
                "path": ".//div[1]/div/div[3]/div/div/div[1]/div[1]/div/form/div[3]/button"
            },
        ]
        self.create_gif_process(path_list, "remove_step_object")

    def observation(self):
        self.create_directory_path(folder_name="add_step_observation")

        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": ".//a[@title='Editar']"},
            {
                "path": ".//span[@title='Crear Observación']",
                "scroll": "window.scrollTo(0, 350)",
            },
            {
                "path": ".//form/textarea[@id='id_procedure_description']",
                "extra_action": "setvalue",
                "value": "Tener cuidado con los envases de materiales biologícos",
            },
            {
                "path": ".//div[1]/div/div[3]/div/div/div[3]/div/div/div[3]/button[2]",
                "scroll": "window.scrollTo(0, document.body.scrollHeight)",
            },
            {"path": ".//form/div[@class='text-center']/button[@type='submit']"},
        ]
        self.create_gif_process(path_list, "add_step_observation")
        self.remove_observation()

    def remove_observation(self):
        self.create_directory_path(folder_name="remove_step_observation")

        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": ".//a[@title='Editar']"},
            {
                "path": ".//tbody[@id='observation_list']/tr[1]/td[2]",
                "scroll": "window.scrollTo(0, 600)",
                "extra_action": "sweetalert_comfirm",
                "comfirm": """document.querySelector('.swal2-confirm').click();""",
                "ok": """document.querySelector('.swal2-confirm').click();""",
                "scroll": "window.scrollTo(0, document.body.scrollHeight)",
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div[1]/div/form/div[3]/button",
                "scroll": "window.scrollTo(0, 100)",
            },
        ]
        self.create_gif_process(path_list, "remove_step_observation")
