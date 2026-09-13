"""
Centralized XPath selectors and helper functions for Selenium tests.

Keeps reusable selectors in one place so that future template changes
only require updates here rather than across dozens of test files.
"""

# ---------------------------------------------------------------------------
# Select2 selectors (org selection page)
# ---------------------------------------------------------------------------
SELECT2_ORG_PICKER = "//span[contains(@class, 'select2-selection')]"
SELECT2_RESULTS = "//ul[contains(@class, 'select2-results__options')]"

# Un <li> de resultados de select2 puede ser tres cosas distintas: un resultado
# real, el "Searching…" que se pinta mientras vuelve el AJAX (.loading-results)
# o un aviso como "No results found" (.select2-results__message).  Hacer click
# en los dos últimos no selecciona nada: el evento select2:select nunca dispara
# y el paso siguiente falla con un error que aparenta ser un selector roto.  Por
# eso nunca debe usarse un `/li[N]` posicional sobre los resultados.
# Los <li> de cabecera de un optgroup tampoco son seleccionables y se
# distinguen porque contienen el <ul> con sus hijos.
SELECT2_REAL_RESULT = (
    "//li[contains(@class, 'select2-results__option')]"
    "[not(contains(@class, 'loading-results'))]"
    "[not(contains(@class, 'select2-results__message'))]"
    "[not(ul)]"
)


def select2_result(index=1):
    """N-ésimo resultado real de un select2 (1-based).

    Los paréntesis son obligatorios: `//li[...][1]` filtra por posición dentro
    de cada padre, mientras que `(//li[...])[1]` opera sobre el conjunto ya
    aplanado, que es lo que se quiere.
    """
    return "(%s)[%d]" % (SELECT2_REAL_RESULT, index)


# ---------------------------------------------------------------------------
# Common buttons
# ---------------------------------------------------------------------------
CONFIRM_DELETE_BTN = "//input[@type='submit' and contains(@class, 'btn-danger')]"
CONFIRM_DELETE_BTN_OUTLINE = (
    "//input[@type='submit' and contains(@class, 'btn-outline-danger')]"
)
SWEETALERT_CONFIRM = "//button[contains(@class, 'swal2-confirm')]"
SWEETALERT_CHECKBOX = "//*[@id='swal2-checkbox']"


# ---------------------------------------------------------------------------
# Organization selection page helpers
# ---------------------------------------------------------------------------
def org_info_link(index):
    """Return XPath for the N-th action link inside #orginfo (1-based)."""
    return "//*[@id='orginfo']//a[%d]" % index


# ---------------------------------------------------------------------------
# Laboratory index page helpers
# ---------------------------------------------------------------------------
def lab_index_left_item(li_index):
    """Return XPath for a left-column list item on laboratory index (1-based)."""
    return (
        "//*[@id='index_labview_id']/ancestor::div[contains(@class,'col-md-6')]"
        "//ul[contains(@class,'list-group')]/li[%d]/a" % li_index
    )


def lab_index_right_item(li_index):
    """Return XPath for a right-column list item on laboratory index (1-based)."""
    return (
        "//*[@id='index_manage_id']/ancestor::div[contains(@class,'col-md-6')]"
        "//ul[contains(@class,'list-group')]/li[%d]//a[1]" % li_index
    )


# ---------------------------------------------------------------------------
# Modal helpers
# ---------------------------------------------------------------------------
def modal_submit_btn(modal_id):
    """Return XPath for the submit/save button inside a modal."""
    return (
        "//*[@id='%s']//div[contains(@class, 'modal-footer')]"
        "//button[@type='submit' or contains(@class, 'formadd')]"
        % modal_id
    )


def modal_close_btn(modal_id):
    """Return XPath for the close button inside a modal."""
    return (
        "//*[@id='%s']//button[contains(@class, 'btn-secondary')]"
        % modal_id
    )


def modal_body(modal_id):
    """Return XPath for the modal body."""
    return "//*[@id='%s']//div[contains(@class, 'modal-body')]" % modal_id


# ---------------------------------------------------------------------------
# DataTable helpers
# ---------------------------------------------------------------------------
def datatable_row_action(table_id, row=1, col_index=-1, action_index=1):
    """Return XPath for an action link in a DataTable row.

    Args:
        table_id: The table element ID (e.g. 'table', 'equipment_table')
        row: Row number (1-based)
        col_index: Column index (negative means last column)
        action_index: Which action link within the cell (1-based)
    """
    if col_index < 0:
        return (
            "//*[@id='%s']//tbody/tr[%d]/td[last()]//a[%d]"
            % (table_id, row, action_index)
        )
    return (
        "//*[@id='%s']//tbody/tr[%d]/td[%d]//a[%d]"
        % (table_id, row, col_index, action_index)
    )


def datatable_search_input(table_id):
    """Return XPath for the DataTable global search input."""
    return "//*[@id='%s_wrapper']//input[@type='search']" % table_id


# ---------------------------------------------------------------------------
# Risk management selectors
# ---------------------------------------------------------------------------
RISKZONE_NEW_BTN = "//a[contains(@class, 'btn-outline-success') and contains(@href, 'riskzone_create')]"
RISKZONE_CARD_TITLE = "//h3[contains(@class, 'heading-1')]/span"
RISKZONE_SAVE_BTN = "//*[@id='btnsave']"

RISK_CARD_EDIT_BTN = (
    "//div[contains(@class, 'card-footer')]//a[contains(@class, 'btn-outline-warning')]"
)
RISK_CARD_DELETE_BTN = (
    "//div[contains(@class, 'card-footer')]//a[contains(@class, 'btn-outline-danger')]"
)
RISK_CARD_DETAIL_LINK = "//div[contains(@class, 'card-header')]//a[contains(@href, 'riskzone_detail')]"


def risk_card_nth(n):
    """Return XPath for the N-th risk zone card (1-based)."""
    return "(//div[contains(@class, 'col-md-4')]//div[contains(@class, 'card')])[%d]" % n


def risk_card_nth_edit(n):
    """Return XPath for the edit button on the N-th risk card."""
    return "(%s)[%d]" % (RISK_CARD_EDIT_BTN, n)


def risk_card_nth_delete(n):
    """Return XPath for the delete button on the N-th risk card."""
    return "(%s)[%d]" % (RISK_CARD_DELETE_BTN, n)


def risk_card_nth_detail(n):
    """Return XPath for the detail link on the N-th risk card."""
    return "(%s)[%d]" % (RISK_CARD_DETAIL_LINK, n)


# ---------------------------------------------------------------------------
# Risk zone detail page selectors
# ---------------------------------------------------------------------------
RISKZONE_DETAIL_TITLE = "//h3[contains(@class, 'heading-1')]/span"
RISKZONE_DETAIL_EDIT_BTN = (
    "//a[contains(@class, 'btn-outline-warning') and contains(@href, 'riskzone_update')]"
)
INCIDENT_NEW_BTN = "//a[contains(@class, 'btn-outline-success') and @id='btn_manage_obj']"
INCIDENT_DROPDOWN_BTN = (
    "//button[contains(@class, 'btn-outline-secondary') and contains(@class, 'dropdown-toggle')]"
)

# Incident list selectors
INCIDENT_LIST_TITLE = "//h3[contains(@class, 'heading-1')]"
INCIDENT_EDIT_BTN = "//a[contains(@class, 'btn-outline-warning') and contains(@href, 'incident_update')]"
INCIDENT_DELETE_BTN = "//a[contains(@class, 'btn-outline-danger') and contains(@href, 'incident_delete')]"
INCIDENT_DETAIL_LINK = "//li[contains(@class, 'list-group-item')]//a[contains(@href, 'incident_detail')]"
INCIDENT_SAVE_BTN = "//button[@type='submit' and contains(@class, 'btn-outline-success')]"


# ---------------------------------------------------------------------------
# Organization management selectors
# ---------------------------------------------------------------------------
ORG_SIDE_MENU_ITEM = ".//ul[@class='nav side-menu']/li[2]/a"
ORG_SIDE_MENU_SUB_ITEM = ".//ul[@class='nav side-menu']/li[2]/ul/li/a"

# Modals
ORG_ADD_MODAL = "addOrganizationmodal"
ORG_ACTIONS_MODAL = "actionsmodal"
ORG_ADD_ROL_MODAL = "addrolmodal"
ORG_REL_PROFILE_LAB_MODAL = "relprofilelabmodal"
ORG_BY_USER_MODAL = "orgbyusermodal"
ORG_ROL_DETAILS_MODAL = "rol_details"
ORG_REL_ORG_MODAL = "relOrganizationmodal"

# Tab IDs
TAB_BY_LABS = "navbylabs"
TAB_BY_ORGS = "navbyorgs"
TAB_BY_PROFILE = "navbyprofile"

# Button IDs in addrolmodal
BTN_ADD_ROL = "btn_add_rol"
BTN_COPY_ROL = "btn_copy_rol"
BTN_SAVE_ROL = "saveroluserorg"
ROL_NAME_INPUT = "rolname"

# ---------------------------------------------------------------------------
# Lab view selectors
# ---------------------------------------------------------------------------
LAB_VIEW_TAB = (
    "//ul[contains(@class, 'list-group')]"
)


# ---------------------------------------------------------------------------
# Inform template selectors
# ---------------------------------------------------------------------------
INFORM_TEMPLATE_LIST_BTN = (
    "//a[contains(@class, 'btn-outline-success') and contains(@href, 'form_list')]"
)


# ---------------------------------------------------------------------------
# Sidebar menu helpers (gentelella navigation)
# ---------------------------------------------------------------------------
def sidebar_menu_item(li_index, sub_li_index=None):
    """Return XPath for a sidebar menu item.

    Args:
        li_index: Index of the main menu item (1-based)
        sub_li_index: If given, index of the sub-menu item (1-based)
    """
    base = ".//ul[@class='nav side-menu']/li[%d]/a" % li_index
    if sub_li_index is not None:
        base = ".//ul[@class='nav side-menu']/li[%d]/ul/li[%d]/a" % (
            li_index,
            sub_li_index,
        )
    return base
