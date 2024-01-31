from django.test import tag

from laboratory.tests.selenium_tests.manage_organizations.base import ManageOrganizationsSeleniumTest


@tag('selenium')
class ProfileTabTest(ManageOrganizationsSeleniumTest):

    def test_change_profile_permission_group_by_org(self):
        path_list = self.path_base + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div[1]/div[3]/div/div/div[1]/div[1]/div[2]/div/ins"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/ul/li[3]/a"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/div/div[@id='byprofile']/form/div/div/span/span/span"},
            {"path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span[2]/ul/li[2]"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/div/div[@id='byprofile']/form/div[2]/div/span/span/span"},
            {"path": "/html/body/span/span[@class='select2-dropdown select2-dropdown--below']/span/ul/li[3]"},
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div/div[2]/div/div/div[@id='byprofile']/form/button[@id='savegroupsbyprofile']"},
        ]
        self.create_gif_process(path_list, "change_profile_permission_group_by_org")

