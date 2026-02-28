from django.contrib.auth.models import User
from django.urls import reverse

from organilab_test.tests.base import SeleniumBase


class CapacitacionSeleniumBase(SeleniumBase):
    fixtures = ["selenium/capacitacion.json"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Override show_cursor_script to use vanilla JS instead of jQuery ($)
        # since not all pages load jQuery (e.g. SGA, reservations)
        cls.show_cursor_script = """
            if(!document.querySelector('.cursor_pointer')){
        """ + cls.cursor_script + """
            }
            var cursor = document.querySelector(".cursor_pointer");
            cursor.style.zIndex = '9999';
        """

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    def login_as(self, user_pk):
        user = User.objects.get(pk=user_pk)
        self.force_login(
            user=user, driver=self.selenium, base_url=self.live_server_url
        )
        return user

    # --- Navigation helpers ---

    def navigate_to_org_manage(self):
        url = self.live_server_url + str(
            reverse("auth_and_perms:organizationManager")
        )
        self.selenium.get(url)

    def navigate_to_my_labs(self, org_pk):
        url = self.live_server_url + str(
            reverse("laboratory:mylabs", kwargs={"org_pk": org_pk})
        )
        self.selenium.get(url)

    def navigate_to_lab_index(self, org_pk, lab_pk):
        url = self.live_server_url + str(
            reverse("laboratory:labindex", kwargs={"org_pk": org_pk, "lab_pk": lab_pk})
        )
        self.selenium.get(url)

    def navigate_to_rooms(self, org_pk, lab_pk):
        url = self.live_server_url + str(
            reverse("laboratory:rooms_list", kwargs={"org_pk": org_pk, "lab_pk": lab_pk})
        )
        self.selenium.get(url)

    def navigate_to_furniture(self, org_pk, lab_pk):
        url = self.live_server_url + str(
            reverse("laboratory:furniture_list", kwargs={"org_pk": org_pk, "lab_pk": lab_pk})
        )
        self.selenium.get(url)

    def navigate_to_shelfobject_list(self, org_pk, lab_pk):
        url = self.live_server_url + str(
            reverse("laboratory:list_shelfobject", kwargs={"org_pk": org_pk, "lab_pk": lab_pk})
        )
        self.selenium.get(url)

    def navigate_to_procedure_list(self, org_pk):
        url = self.live_server_url + str(
            reverse("academic:procedure_list", kwargs={"org_pk": org_pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_sga_create_substance(self, org_pk):
        url = self.live_server_url + str(
            reverse("sga:create_sustance", kwargs={"org_pk": org_pk})
        )
        self.selenium.get(url)

    def navigate_to_sga_step_two(self, org_pk, pk):
        url = self.live_server_url + str(
            reverse("sga:step_two", kwargs={"org_pk": org_pk, "pk": pk})
        )
        self.selenium.get(url)

    def navigate_to_sga_label_create(self, org_pk):
        url = self.live_server_url + str(
            reverse("sga:add_personal", kwargs={"org_pk": org_pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_msds(self, org_pk):
        url = self.live_server_url + str(
            reverse("msds:index_msds", kwargs={"org_pk": org_pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_reservations(self, org_pk, status=0):
        url = self.live_server_url + str(
            reverse("reservations_management:reservations_list", kwargs={"org_pk": org_pk, "status": status})
        )
        self.selenium.get(url)

    def navigate_to_create_lab(self, org_pk):
        url = self.live_server_url + str(
            reverse("laboratory:create_lab", kwargs={"org_pk": org_pk})
        )
        self.selenium.get(url)

    def navigate_to_risk_zone_list(self, org_pk):
        url = self.live_server_url + str(
            reverse("risk_management:riskzone_list", kwargs={"org_pk": org_pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_reports(self, org_pk):
        url = self.live_server_url + str(
            reverse("laboratory:reports", kwargs={"org_pk": org_pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_precursor_report(self, org_pk):
        url = self.live_server_url + str(
            reverse("report:precursor_report", kwargs={"org_pk": org_pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_msds_create(self, org_pk):
        url = self.live_server_url + str(
            reverse("msds:msds_msdsobject_create", kwargs={"org_pk": org_pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_manage_reservation(self, org_pk, reservation_pk):
        url = self.live_server_url + str(
            reverse(
                "reservations_management:manage_reservation",
                kwargs={"org_pk": org_pk, "pk": reservation_pk},
            )
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_block_notification(self, lab_pk, obj_pk):
        url = self.live_server_url + str(
            reverse(
                "laboratory:block_notification",
                kwargs={"lab_pk": lab_pk, "obj_pk": obj_pk},
            )
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_admin(self, path=""):
        url = self.live_server_url + "/admin/" + path
        self.selenium.get(url)

    def navigate_to_rooms_create(self, org_pk, lab_pk):
        url = self.live_server_url + str(
            reverse("laboratory:rooms_create", kwargs={"org_pk": org_pk, "lab_pk": lab_pk})
        )
        self.selenium.get(url)

    def navigate_to_procedure_create(self, org_pk):
        url = self.live_server_url + str(
            reverse("academic:procedure_create", kwargs={"org_pk": org_pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_my_procedures(self, org_pk, lab_pk):
        url = self.live_server_url + str(
            reverse("academic:get_my_procedures", kwargs={"org_pk": org_pk, "lab_pk": lab_pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    # --- Common XPath patterns ---

    @property
    def side_menu_permisos(self):
        return [
            {"path": ".//ul[@class='nav side-menu']/li[2]/a"},
            {"path": ".//ul[@class='nav side-menu']/li[2]/ul/li/a"},
        ]

    @property
    def button_save_modal1(self):
        return [
            {"path": "//*[@id='modal1']/div/form/div/div[3]/button[2]"}
        ]

    def get_submit_button_path(self, id_modal, button_type="submit"):
        return (
            ".//div[@id='%s']/div/div[@class='modal-content']"
            "/form/div[@class='modal-footer']/button[@type='%s']"
            % (id_modal, button_type)
        )
