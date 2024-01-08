from django.contrib.auth.models import User
from django.urls import reverse
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from organilab_test.tests.base import SeleniumBase
from django.utils.translation import gettext_lazy as _
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
            {"path": ".//div[@class='d-flex']/a[@class='btn-primary']"},

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
        self.update_procedure()
        self.delete_procedure()
