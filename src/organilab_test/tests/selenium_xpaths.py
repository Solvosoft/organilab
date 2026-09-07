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


# ---------------------------------------------------------------------------
# CRUD genérico de gentelella (ObjectCRUD / obj_api_management.js)
# ---------------------------------------------------------------------------
# Doce páginas del proyecto son la misma pantalla con otro dataset: una
# DataTable `<id>`, un botón de alta que DataTables pinta como botón de la barra
# de herramientas, y una columna de acciones con <i> que llaman a
# call_obj_crud_event().  Ver obj_api_management.js: `btn_class.create` es
# 'btn-outline-success mr-4', `btn_class.clear_filters` 'btn-outline-secondary
# mr-4', y los iconos por defecto son fa-eye / fa-edit / fa-trash.
#
# Se selecciona por CLASE y no por el `titleAttr` ("Create"), porque ese texto
# pasa por gettext y en la corrida en español no coincide.

GT_ICON_DETAIL = "fa-eye"
GT_ICON_UPDATE = "fa-edit"
GT_ICON_DELETE = "fa-trash"


def gt_crud_create_btn(table_id):
    """Botón de alta de una tabla ObjectCRUD."""
    return (
        "//*[@id='%s_wrapper']//button[contains(@class, 'btn-outline-success')]"
        % table_id
    )


def gt_crud_clear_filters_btn(table_id):
    """Botón «limpiar filtros» de una tabla ObjectCRUD."""
    return (
        "//*[@id='%s_wrapper']//button[contains(@class, 'btn-outline-secondary')]"
        % table_id
    )


def gt_crud_row_action(table_id, icon, row=1):
    """Acción por fila de una tabla ObjectCRUD, localizada por su icono.

    `icon` es una de las constantes GT_ICON_* (o cualquier clase de Font
    Awesome). Se busca por icono y no por posición dentro de la celda porque el
    orden de las acciones depende de los permisos del usuario.
    """
    return (
        "//*[@id='%s']//tbody/tr[%d]//i[contains(@class, '%s')]"
        % (table_id, row, icon)
    )


def gt_modal_delete_btn(modal_id):
    """Botón de confirmación del modal de borrado (`btn_class: '.delbtn'`)."""
    return "//*[@id='%s']//button[contains(@class, 'delbtn')]" % modal_id


def datatable_page_btn(table_id, page):
    """Botón de una página concreta del paginador (1-based).

    Agnóstico del tag a propósito: DataTables 2 pinta `dt-paging-button` sobre
    el <button>, pero con el estilizado de Bootstrap 5 la clase puede acabar en
    el <li> que lo envuelve. Se busca el elemento con ese número dentro del
    contenedor de paginación, sea cual sea.
    """
    return (
        "//*[@id='%s_wrapper']//*[contains(@class, 'dt-paging')]"
        "//*[normalize-space(text())='%s']" % (table_id, page)
    )


# ---------------------------------------------------------------------------
# Reportes (base_report_form_view.html, base_report_organizations.html,
# regency_report.html y general_organization_report.html)
# ---------------------------------------------------------------------------
# El ciclo es: rellenar el formulario -> #send dispara create_request -> el
# panel de estado hace polling contra report_status -> aparece la descarga.
# Con CELERY_ALWAYS_EAGER (test_settings) la tarea termina dentro del
# create_request, así que se espera a la descarga y no a los 5 s de polling.
REPORT_SEND_BTN = "//*[@id='send']"
REPORT_STATUS_TEXT = "//*[@id='textstatus']"
REPORT_STATUS_PANEL = (
    "//*[contains(@class, 'statuspanel') and not(contains(@class, 'd-none'))]"
)
REPORT_DOWNLOAD_LINK = "//*[@id='download_file']"
REPORT_MODAL = "//*[@id='reportModal']"
REPORT_MODAL_DOWNLOAD = "//*[@id='download-report']"
REPORT_ERROR_BOX = "//*[@id='diverrormessage']"
REPORT_FIELD_ERRORS = "//*[contains(@class, 'report_form_errors')]"


# ---------------------------------------------------------------------------
# Asistentes por pasos (sga/substance/steps.html, sgalabel/steps.html)
# ---------------------------------------------------------------------------
def wizard_step(step):
    """Pestaña del paso N del asistente (1-based).

    El índice es semántico —el paso number N del asistente—, no una posición
    arbitraria dentro de la plantilla.
    """
    return "//*[@id='wizard']//ul//li[%d]//a" % step


# ---------------------------------------------------------------------------
# Editor de plantillas SGA
# ---------------------------------------------------------------------------
SGA_EDITOR_IFRAME = "//*[@id='editoriframe']"
SGA_EDITOR_SAVE = "//*[@id='editor_save']"
# Modal de previsualización (personal_template.html, check_substances.html).
SGA_LABEL_PREVIEW_MODAL = "//*[@id='svgtemplate']"


# ---------------------------------------------------------------------------
# Acordeón de Bootstrap (paso 4 del asistente de sustancias)
# ---------------------------------------------------------------------------
def accordion_toggle(collapse_id):
    """Cabecera que despliega un panel del acordeón."""
    return "//*[@data-bs-target='#%s' or @href='#%s']" % (collapse_id, collapse_id)


def accordion_body(collapse_id):
    """Cuerpo desplegado de un panel del acordeón."""
    return "//*[@id='%s' and contains(@class, 'show')]" % collapse_id


# ---------------------------------------------------------------------------
# select2 acotado a un campo
# ---------------------------------------------------------------------------
def select2_field(field_id):
    """Caja de un select2 concreto, por el id del <select> al que envuelve.

    `select2_result()` opera sobre los resultados ya desplegados, que son
    globales al documento; para ABRIR el desplegable correcto en una página con
    varios select2 hace falta acotar por campo.
    """
    return (
        "//*[@id='%s']/following-sibling::span"
        "//span[contains(@class, 'select2-selection')]" % field_id
    )


# ---------------------------------------------------------------------------
# Subida encadenada (chunked upload de gentelella)
# ---------------------------------------------------------------------------
# El <input type=file> visible solo alimenta la subida por trozos: el valor real
# viaja en un campo oculto que el JS rellena al terminar.  Por eso se hace
# send_keys sobre el input visible y se espera al indicador de estado, nunca al
# campo oculto.
def chunked_file_input(field_name):
    return "//input[@type='file' and contains(@id, '%s')]" % field_name


SDS_AUTOFILL_STATUS = "//*[contains(@class, 'sds-autofill-status')]"


# ---------------------------------------------------------------------------
# Catálogos SGA (base_modal_management.js) — OTRA familia de tablas
# ---------------------------------------------------------------------------
# Ojo: los catálogos de SGA (warning_words, danger_indications, prudence_advices,
# recipient_size) NO usan el ObjectCRUD de gentelella, sino
# `laboratory/js/base_modal_management.js` con un JS propio por catálogo. Las
# diferencias que importan:
#
#   - el botón de alta es `btn btn-success`, no `btn-outline-success`
#     (por suerte 'btn-outline-success' no contiene la subcadena 'btn-success',
#      así que los dos selectores no se pisan);
#   - la acción de borrar se pinta con `fa-close`, no con `fa-trash`
#     (sga/api/serializers.py: get_actions);
#   - el borrado confirma por SweetAlert, no por un modal `.delbtn`.
SGA_ICON_UPDATE = "fa-edit"
SGA_ICON_DELETE = "fa-close"


def sga_catalog_add_btn(table_id):
    """Botón «Add» de un catálogo SGA."""
    return (
        "//*[@id='%s_wrapper']//button[contains(@class, 'btn-success')]" % table_id
    )


def datatable_row_icon(table_id, icon, row=1):
    """Acción por fila localizada por icono, válida para ambas familias de tabla."""
    return (
        "//*[@id='%s']//tbody/tr[%d]//i[contains(@class, '%s')]"
        % (table_id, row, icon)
    )
