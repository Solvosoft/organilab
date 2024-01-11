from django.contrib.auth.models import User
from django.urls import reverse
from organilab_test.tests.base import SeleniumBase
from django.test import tag

@tag('selenium')
class ProcedureTemplateSeleniumTest(SeleniumBase):
    fixtures = ["selenium/procedure_templates.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)

    def create_procedure(self):
        self.create_directory_path(folder_name="create_procedure_template")

        path_list = [

            {"path": ".//button[@class='btn btn-secondary btn-sm btn-success']"},
            {"path": ".//input[@name='title']","extra_action":"setvalue","value":"Se limpiaran laboratorios"},
            {"path": ".//form[1]",
             "extra_action":'script',
             'value':'tinymce.get("id_description").setContent("<p><strong>Se limpiaran los muebles, frascos entre otras herramientas</strong></p>");'},
            {"path": ".//form/div[@class='text-center']/button[@type='submit']"},
        ]
        self.create_gif_process(path_list, "create_procedure_template")

    def update_procedure(self):
        self.create_directory_path(folder_name="update_procedure_template")

        path_list = [

            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[3]"},
            {"path": ".//input[@name='title']","extra_action":"setvalue","value":"Se limpiaran laboratorios"},
            {"path": ".//form[1]",
             "extra_action":'script',
             'value':'tinymce.get("id_description").setContent("<p><strong>Se limpiaran los muebles, frascos entre otras herramientas</strong></p>");'},
            {"path": ".//form/div[@class='text-center']/button[@type='submit']"},
        ]
        self.create_gif_process(path_list, "update_procedure_template")

    def detail_procedure(self):
        self.create_directory_path(folder_name="detail_procedure_template")

        path_list = [

            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
        ]
        self.create_gif_process(path_list, "detail_procedure_template")


    def delete_procedure(self):
        self.create_directory_path(folder_name="delete_procedure_template")

        path_list = [

            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[4]", "extra_action":'sweetalert_comfirm',
             "comfirm":"""document.querySelector('.swal2-confirm').click();""",
             "ok":"""document.querySelector('.swal2-confirm').click();"""},

        ]
        self.create_gif_process(path_list, "delete_procedure_template")


    def add_step(self):
        self.create_directory_path(folder_name="add_step")

        path_list = [

            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[2]"},
            {"path": ".//input[@name='title']", "extra_action": "setvalue",
             "value": "Paso 1"},
            {"path": ".//form[1]",
             "extra_action": 'script',
             'value': 'tinymce.get("id_description").setContent("<p>Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industrys standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.</p>");'},
            {"path": ".//form/div[@class='text-center']/button[@type='submit']"},

        ]
        self.create_gif_process(path_list, "add_step")

    def update_step(self):
        self.create_directory_path(folder_name="update_step")

        path_list = [

            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": ".//a[@title='Editar']"},
            {"path": ".//input[@name='title']", "extra_action": "setvalue",
             "value": "Paso 1"},
            {"path": ".//form/div[@class='text-center']/button[@type='submit']"},
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},

        ]
        self.create_gif_process(path_list, "update_step")


    def delete_step(self):
        self.create_directory_path(folder_name="delete_step")

        path_list = [

            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": ".//a[@title='Eliminar']"},
        ]
        self.create_gif_process(path_list, "delete_step")


    def add_object(self):
        self.create_directory_path(folder_name="add_object")

        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": ".//a[@title='Editar']"},
            {"path": ".//span[@title='Crear Objecto']"},
            {"path": ".//span[@class='select2-selection select2-selection--single']"},
            {"path": ".//ul[@class='select2-results__options']",
             "extra_action": {"select": ""}},
            {"path": ".//li[text()='BAL847 Balón Fondo Plano no esmerilado 125 mL']"},
            {"path": ".//input[@id='id_quantity']", "extra_action": "setvalue",
             "value": 10},
            {"path": ".//span[@aria-controls='select2-id_unit-container']"},
            {"path": ".//ul[@id='select2-id_unit-results']",
             "extra_action": {"select": ""}},
            {"path": ".//li[text()='Metros']"},
            {"path": ".//div[@class='modal-footer']/button[@class='btn btn-success']"},
            {"path": ".//form/div[@class='text-center']/button[@type='submit']"},

        ]
        self.create_gif_process(path_list, "add_object")

    def add_observacion(self):
        self.create_directory_path(folder_name="add_observation")

        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": ".//a[@title='Editar']"},
            {"path": ".//span[@title='Crear Observación']"},
            {"path": ".//form/textarea[@id='id_procedure_description']","extra_action":"setvalue",
             "value":"Tener cuidado con los envases de materiales biologícos"},
            {"path": ".//form[@class='observation_modal']/div[@class='card']/div[@class='modal-footer'](button[@class='btn btn-success']"},
            {"path": ".//form/div[@class='text-center']/button[@type='submit']"},
        ]
        self.create_gif_process(path_list, "add_observation")


    def test_list_procedure(self):
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)
        self.create_directory_path(folder_name="list_procedure_template")

        path_list = [

            {"path": ".//span[@class='select2-selection select2-selection--single']"},
            {"path": ".//ul[@class='select2-results__options']","extra_action":{"select":""}},
            {"path": ".//li[text()='1 | Organización de Estudiantes']"},
            {"path": "//a[text() =' Mis Laboratorios']"},
            {"path": ".//a//i[@class='fa fa-calendar-check-o']"},
            {"path": ".//a//i[@class='fa fa-list-alt']"}
        ]
        self.create_gif_process(path_list, "list_procedure_template")
        self.create_procedure()
        self.add_step()
        self.edit_step()
        self.add_object()
        self.detail_procedure()

    def remove_observation(self):
        self.create_directory_path(folder_name="remove_observation")

        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": ".//a[@title='Editar']"},
            {"path": ".//tbody[@id='observation_list']/tr[1]/td[2]", "extra_action":'sweetalert_comfirm',
             "comfirm":"""document.querySelector('.swal2-confirm').click();""",
             "ok":"""document.querySelector('.swal2-confirm').click();"""},
        ]
        self.create_gif_process(path_list, "remove_observation")

    def remove_object(self):
        self.create_directory_path(folder_name="remove_object")

        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": ".//a[@title='Editar']"},
            {"path": ".//tbody[@id='object_list']/tr[1]/td[3]", "extra_action":'sweetalert_comfirm',
             "comfirm":"""document.querySelector('.swal2-confirm').click();""",
             "ok":"""document.querySelector('.swal2-confirm').click();"""},
        ]
        self.create_gif_process(path_list, "remove_object")

    def test_observation(self):
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)
        self.selenium.get(self.live_server_url+str(reverse("academic:procedure_list", kwargs={"org_pk":1})))
        self.create_directory_path(folder_name="add_observation")
        self.delete_step()
        path_list = [
            {"path": ".//table[@id= 'procedure']/tbody/tr[1]/td[3]/a[1]"},
            {"path": ".//a[@title='Editar']"},
            {"path": ".//span[@title='Crear Observación']"},
            {"path": ".//form/textarea[@id='id_procedure_description']","extra_action":"setvalue",
             "value":"Tener cuidado con los envases de materiales biologícos"},
            {"path": ".//div[@class='modal-footer']/button[@class='btn btn-success open_modal']"},
            {"path": ".//form/div[@class='text-center']/button[@type='submit']", "scroll":"script", "script_value":"window.scrollTo(0, document.body.scrollHeight)"},
        ]
        #self.create_gif_process(path_list, "add_observation")
        #self.remove_observation()
