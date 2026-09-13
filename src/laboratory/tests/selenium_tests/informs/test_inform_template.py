from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse

from organilab_test.tests.base import OptimizedSeleniumBase, modifies_db

# Formio builder sidebar component buttons (text-based selectors)
FORMIO_TEXT_FIELD = "//span[contains(@class, 'btn') and contains(., 'Text Field')]"
# Por data-key y no por texto: el palette de Formio se muestra traducido
# (es: "Contraseña", "Casilla…"), así que el título no es estable.
FORMIO_NUMBER = "//span[contains(@class, 'btn') and @data-key='number']"
FORMIO_PASSWORD = "//span[contains(@class, 'btn') and @data-key='password']"
FORMIO_CHECKBOX = "//span[contains(@class, 'btn') and @data-key='checkbox']"
FORMIO_RADIO = "//span[contains(@class, 'btn') and @data-key='radio']"

# Formio builder drop zone (top-level form uses formio-builder-form)
FORMIO_DROP_ZONE = "//*[@id='formio']//div[contains(@class, 'drag-container')]"

# Formio component dialog selectors
FORMIO_DIALOG = "//div[contains(@class, 'formio-dialog-content')]"
FORMIO_DIALOG_TAB_DATA = FORMIO_DIALOG + "//li[2]/a"
FORMIO_DIALOG_TAB_VALIDATION = FORMIO_DIALOG + "//li[3]/a"
FORMIO_DIALOG_LABEL_INPUT = FORMIO_DIALOG + "//input[1]"
FORMIO_DIALOG_SAVE = FORMIO_DIALOG + "//button[contains(@class, 'btn-success')]"

# Edit view page elements
SAVE_FORM_BTN = "//*[@id='save_btn']"
RETURN_TO_LIST_BTN = "//button[@title='Form List']"

# Form table action selectors
FORM_TABLE_PREVIEW_ROW = "//table[@id='form_table']//tbody/tr[{row}]//a[contains(@class, 'preview_btn')]"
FORM_TABLE_EDIT_ROW = "//table[@id='form_table']//tbody/tr[{row}]//a[contains(@class, 'edit_btn')]"
FORM_TABLE_DELETE_ROW = "//table[@id='form_table']//tbody/tr[{row}]//a[contains(@class, 'delete_btn')]"


@tag("selenium")
class InformsSeleniumTest(OptimizedSeleniumBase):
    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    def navigate_to_form_list(self):
        """Navigate directly to the inform template (Formio form) list page."""
        url = self.live_server_url + str(
            reverse("derb:form_list", kwargs={"org_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def _return_and_preview(self, row=1):
        """Common steps: save form, return to list, confirm, preview, return.

        Used at the end of Formio builder tests.
        """
        return [
            {
                "path": SAVE_FORM_BTN,
            },
            {
                "path": RETURN_TO_LIST_BTN,
                "scroll": "window.scrollTo(0, 600)",
                "sleep": 2,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
            {
                "path": FORM_TABLE_PREVIEW_ROW.format(row=row),
                "wait_ready": True,
            },
            {
                "path": "//button[contains(@class, 'btn-primary') and contains(@onclick, 'window.location')]",
                "wait_ready": True,
            },
        ]

    def test_view_informs(self):
        """Test viewing the inform templates list page.

        Flow: Navigate to form list -> View page with DataTable.

        GIF: docs/source/_static/gif/view_inform_templates.gif
        """
        self.navigate_to_form_list()
        path_list = [
            {
                "path": "//h1",
            },
        ]
        self.create_gif_process(path_list, "view_inform_templates")

    @modifies_db
    def test_create_inform_template(self):
        """Test creating a new inform template via SweetAlert input.

        Flow: Navigate to form list -> Click create button -> Enter
        template name in SweetAlert -> Confirm -> View edit page.

        GIF: docs/source/_static/gif/add_inform_template.gif
        """
        self.navigate_to_form_list()
        path_list = [
            {
                "path": "//button[contains(@class, 'create_btn')]",
                "sleep": 1,
            },
            {
                "path": "//div[contains(@class, 'swal2-popup')]//input[contains(@class, 'swal2-input')]",
                "extra_action": "clearinput",
            },
            {
                "path": "//div[contains(@class, 'swal2-popup')]//input[contains(@class, 'swal2-input')]",
                "extra_action": "setvalue",
                "value": "Primer Formulario",
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
            },
            {
                "path": "//*[@id='form_name']",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "add_inform_template")

    @modifies_db
    def test_update_name_inform_template(self):
        """Test renaming an existing inform template.

        Flow: Navigate to form list -> Click edit button on first row
        -> Click rename button -> Enter new name in SweetAlert
        -> Confirm -> Dismiss success alert.

        GIF: docs/source/_static/gif/update_name_inform_template.gif
        """
        self.navigate_to_form_list()
        path_list = [
            {
                "path": FORM_TABLE_EDIT_ROW.format(row=1),
                "sleep": 2,
            },
            {
                "path": "//a[contains(@class, 'edit_name_btn')]",
                "wait_ready": True,
            },
            {
                "path": "//div[contains(@class, 'swal2-popup')]//input[contains(@class, 'swal2-input')]",
                "sleep": 1,
            },
            {
                "path": "//div[contains(@class, 'swal2-popup')]//input[contains(@class, 'swal2-input')]",
                "extra_action": "setvalue",
                "value": "Formulario Prueba",
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "update_name_inform_template")

    @modifies_db
    def test_remove_element(self):
        """Test removing a form element from an inform template.

        Flow: Navigate to form list -> Click edit button on second row
        -> Hover on a component to show action buttons -> Click remove
        -> Save form -> Return to form list -> Confirm in SweetAlert.

        GIF: docs/source/_static/gif/remove_inform_template_element.gif
        """
        self.navigate_to_form_list()
        path_list = [
            {
                "path": FORM_TABLE_EDIT_ROW.format(row=2),
                "sleep": 2,
            },
            {
                "path": "//div[contains(@class, 'formio-component')][1]",
                "hover": "",
                "element": ".component-btn-group",
                "wait_ready": True,
            },
            {
                "path": "//div[contains(@class, 'component-settings-button-remove')] | //div[contains(@class, 'component-btn-group')]/div[1]",
            },
            {
                "path": SAVE_FORM_BTN,
            },
            {
                "path": RETURN_TO_LIST_BTN,
                "scroll": "window.scrollTo(0, 600)",
                "sleep": 2,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "remove_inform_template_element")
        self.view_form()

    @modifies_db
    def test_add_textfield_derb(self):
        """Test adding a text field component to an inform template.

        Flow: Navigate to form list -> Click edit button on first row
        -> Drag Text Field from sidebar to canvas -> Configure Data tab
        (set default value) -> View Validation tab -> Save component
        -> Save form -> Return to form list -> Preview form.

        GIF: docs/source/_static/gif/edit_textfield_inform_template.gif
        """
        self.navigate_to_form_list()
        path_list = [
            {
                "path": FORM_TABLE_EDIT_ROW.format(row=1),
                "sleep": 2,
            },
            {
                "path": FORMIO_TEXT_FIELD,
                "extra_action": "drag_and_drop",
                "x": FORMIO_TEXT_FIELD,
                "y": FORMIO_DROP_ZONE,
                "expect": FORMIO_DIALOG,
                "wait_ready": True,
                "sleep": 3,
            },
            {
                "path": FORMIO_DIALOG_TAB_DATA,
                "sleep": 1,
            },
            {
                "path": FORMIO_DIALOG + "//div[contains(@class, 'tab-pane')][2]//input[1]",
            },
            {
                "path": FORMIO_DIALOG + "//div[contains(@class, 'tab-pane')][2]//input[1]",
                "extra_action": "setvalue",
                "value": "Clark",
            },
            {
                "path": FORMIO_DIALOG_TAB_VALIDATION,
                "screenshot_name": "textfield_validations",
            },
            {
                "path": FORMIO_DIALOG_SAVE,
            },
        ] + self._return_and_preview(row=1)
        self.create_gif_process(path_list, "edit_textfield_inform_template")

    # DISABLED: Calendar widget test - Formio calendar widget interaction is unreliable in Selenium
    # @modifies_db
    # def test_add_textfield_calendar_derb(self):
    #     self.navigate_to_form_list()
    #     path_list = [
    #         {"path": FORM_TABLE_EDIT_ROW.format(row=1), "sleep": 2},
    #         {"path": FORMIO_TEXT_FIELD, "extra_action": "drag_and_drop",
    #          "x": FORMIO_TEXT_FIELD, "y": FORMIO_DROP_ZONE, "wait_ready": True, "sleep": 3},
    #         {"path": FORMIO_DIALOG + "//div[contains(@class, 'formio-component-select')]//div[contains(@class, 'choices')]",
    #          "scroll": '$(".formio-dialog-content").scrollTop(300)', "sleep": 1},
    #         {"path": FORMIO_DIALOG + "//div[contains(@class, 'choices__list--dropdown')]//div[contains(@class, 'choices__item')][2]"},
    #         {"path": FORMIO_DIALOG_SAVE, "scroll": '$(".formio-dialog-content").scrollTop(0)'},
    #         {"path": SAVE_FORM_BTN},
    #         {"path": RETURN_TO_LIST_BTN, "scroll": "window.scrollTo(0, 600)", "sleep": 2},
    #         {"path": "//button[contains(@class, 'swal2-confirm')]", "sleep": 1},
    #         {"path": FORM_TABLE_PREVIEW_ROW.format(row=1), "wait_ready": True},
    #         {"path": "//button[contains(@class, 'btn-primary') and contains(@onclick, 'window.location')]", "wait_ready": True},
    #         {"path": FORM_TABLE_PREVIEW_ROW.format(row=1), "wait_ready": True},
    #         {"path": "//button[contains(@class, 'btn-primary') and contains(@onclick, 'window.location')]", "wait_ready": True},
    #     ]
    #     self.create_gif_process(path_list, "add_calendar_inform_template")

    @modifies_db
    def test_add_number_derb(self):
        """Test adding a number field component to an inform template.

        Flow: Navigate to form list -> Click edit button on first row
        -> Drag Number from sidebar to canvas -> Configure Data tab
        (set default value) -> View Validation tab -> Save component
        -> Save form -> Return to form list -> Preview form.

        GIF: docs/source/_static/gif/number_input_inform_template.gif
        """
        self.navigate_to_form_list()
        path_list = [
            {
                "path": FORM_TABLE_EDIT_ROW.format(row=1),
                "sleep": 2,
            },
            {
                "path": FORMIO_NUMBER,
                "extra_action": "drag_and_drop",
                "x": FORMIO_NUMBER,
                "y": FORMIO_DROP_ZONE,
                "expect": FORMIO_DIALOG,
                "wait_ready": True,
                "sleep": 3,
            },
            {
                "path": FORMIO_DIALOG_TAB_DATA,
                "sleep": 1,
            },
            {
                "path": FORMIO_DIALOG + "//div[contains(@class, 'tab-pane')][2]//input[1]",
            },
            {
                "path": FORMIO_DIALOG + "//div[contains(@class, 'tab-pane')][2]//input[1]",
                "extra_action": "setvalue",
                "value": 2,
            },
            {
                "path": FORMIO_DIALOG_TAB_VALIDATION,
                "screenshot_name": "number_input_data",
            },
            {
                "path": FORMIO_DIALOG_SAVE,
                "screenshot_name": "number_input_validations",
            },
        ] + self._return_and_preview(row=1)
        self.create_gif_process(path_list, "number_input_inform_template")

    @modifies_db
    def test_add_password_derb(self):
        """Test adding a password field component to an inform template.

        Flow: Navigate to form list -> Click edit button on first row
        -> Drag Password from sidebar to canvas -> View Data tab
        -> View Validation tab -> Save component -> Save form
        -> Return to form list -> Preview form.

        GIF: docs/source/_static/gif/password_input_inform_template.gif
        """
        self.navigate_to_form_list()
        path_list = [
            {
                "path": FORM_TABLE_EDIT_ROW.format(row=1),
                "sleep": 2,
            },
            {
                "path": FORMIO_PASSWORD,
                "extra_action": "drag_and_drop",
                "x": FORMIO_PASSWORD,
                "y": FORMIO_DROP_ZONE,
                "expect": FORMIO_DIALOG,
                "wait_ready": True,
                "sleep": 3,
            },
            {
                "path": FORMIO_DIALOG_TAB_DATA,
                "sleep": 1,
            },
            {
                "path": FORMIO_DIALOG_TAB_VALIDATION,
                "screenshot_name": "password_input_data",
            },
            {
                "path": FORMIO_DIALOG_SAVE,
                "screenshot_name": "password_input_validations",
            },
        ] + self._return_and_preview(row=1)
        self.create_gif_process(path_list, "password_input_inform_template")

    @modifies_db
    def test_add_checkbox_derb(self):
        """Test adding a checkbox component to an inform template.

        Flow: Navigate to form list -> Click edit button on first row
        -> Drag Checkbox from sidebar to canvas -> Set label
        -> View Data tab -> View Validation tab -> Save component
        -> Save form -> Return to form list -> Preview form.

        GIF: docs/source/_static/gif/checkbox_input_inform_template.gif
        """
        self.navigate_to_form_list()
        path_list = [
            {
                "path": FORM_TABLE_EDIT_ROW.format(row=1),
                "sleep": 2,
            },
            {
                "path": FORMIO_CHECKBOX,
                "extra_action": "drag_and_drop",
                "x": FORMIO_CHECKBOX,
                "y": FORMIO_DROP_ZONE,
                "expect": FORMIO_DIALOG,
                "wait_ready": True,
                "sleep": 3,
            },
            {
                "path": FORMIO_DIALOG_LABEL_INPUT,
                "sleep": 1,
            },
            {
                "path": FORMIO_DIALOG_LABEL_INPUT,
                "extra_action": "setvalue",
                "value": "¿Es peligroso?",
            },
            {
                "path": FORMIO_DIALOG_TAB_DATA,
            },
            {
                "path": FORMIO_DIALOG_TAB_VALIDATION,
                "screenshot_name": "checkbox_input_data",
            },
            {
                "path": FORMIO_DIALOG_SAVE,
                "screenshot_name": "checkbox_input_validations",
            },
        ] + self._return_and_preview(row=1)
        self.create_gif_process(path_list, "checkbox_input_inform_template")

    @modifies_db
    def test_add_radio_derb(self):
        """Test adding a radio button component to an inform template.

        Flow: Navigate to form list -> Click edit button on first row
        -> Drag Radio from sidebar to canvas -> Set label -> Configure
        Data tab (set radio option value) -> View Validation tab
        -> Save component -> Save form -> Return to form list
        -> Preview form.

        GIF: docs/source/_static/gif/radio_input_inform_template.gif
        """
        self.navigate_to_form_list()
        path_list = [
            {
                "path": FORM_TABLE_EDIT_ROW.format(row=1),
                "sleep": 2,
            },
            {
                "path": FORMIO_RADIO,
                "scroll": "window.scrollTo(0, 110)",
                "extra_action": "drag_and_drop",
                "x": FORMIO_RADIO,
                "y": FORMIO_DROP_ZONE,
                "expect": FORMIO_DIALOG,
                "wait_ready": True,
                "sleep": 3,
            },
            {
                "path": FORMIO_DIALOG_LABEL_INPUT,
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": FORMIO_DIALOG_LABEL_INPUT,
                "extra_action": "setvalue",
                "value": "¿Es peligroso?",
            },
            {
                "path": FORMIO_DIALOG_TAB_DATA,
            },
            {
                "path": FORMIO_DIALOG + "//div[contains(@class, 'tab-pane')][2]//table//tbody/tr[1]/td[2]//input",
                "extra_action": "clearinput",
            },
            {
                "path": FORMIO_DIALOG + "//div[contains(@class, 'tab-pane')][2]//table//tbody/tr[1]/td[2]//input",
                "extra_action": "setvalue",
                "value": "Si",
            },
            {
                "path": FORMIO_DIALOG_TAB_VALIDATION,
                "screenshot_name": "radio_input_data",
            },
            {
                "path": FORMIO_DIALOG_SAVE,
                "screenshot_name": "radio_input_validations",
            },
        ] + self._return_and_preview(row=1)
        self.create_gif_process(path_list, "radio_input_inform_template")

    def test_view_inform_template(self):
        """Test previewing an inform template with Formio form.

        Flow: Navigate to form list -> Click preview button on third
        row -> View Formio form preview -> Return to form list.

        GIF: docs/source/_static/gif/view_inform_template.gif
        """
        self.navigate_to_form_list()
        path_list = [
            {
                "path": FORM_TABLE_PREVIEW_ROW.format(row=3),
                "sleep": 2,
            },
            {
                "path": "//button[contains(@class, 'btn-primary') and contains(@onclick, 'window.location')]",
                "sleep": 5,
            },
        ]
        self.create_gif_process(path_list, "view_inform_template")

    @modifies_db
    def test_delete_inform_template(self):
        """Test deleting an inform template.

        Flow: Navigate to form list -> Click delete button on third
        row -> Confirm in SweetAlert -> Dismiss success alert.

        GIF: docs/source/_static/gif/remove_inform_template.gif
        """
        self.navigate_to_form_list()
        path_list = [
            {
                "path": FORM_TABLE_DELETE_ROW.format(row=3),
                "sleep": 1,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "remove_inform_template")

    def view_form(self):
        """Preview a form template and return to list.

        Flow: Click preview on first row -> View preview -> Return
        to form list.

        GIF: docs/source/_static/gif/drag_drop_form.gif
        """
        path_list = [
            {
                "path": FORM_TABLE_PREVIEW_ROW.format(row=1),
                "wait_ready": True,
            },
            {
                "path": "//button[contains(@class, 'btn-primary') and contains(@onclick, 'window.location')]",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "drag_drop_form")
