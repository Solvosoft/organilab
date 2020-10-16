// ############### USEFULL METHODS ############### 
const get_html_element = (element_id, option = 'js') => {
    let element = null;
    try {
        if (option == 'js') {
            element = document.querySelector(`${element_id}`);
        }
        else if (option == 'jq') {
            element = $(`${element_id}`);
        }

    } catch (error) {
        console.log(`This id : ${element_id} does not exists in the page`);
    }
    return element;
}

const get_modal_product_elements = () => {
    let data = {};
    const modal_form = get_html_element('#modal_form');

    if (modal_form) {
        const modal_title = get_html_element('#product_name');
        const status_select = modal_form.querySelector('#id_status');
        const is_returnable_checkbox = modal_form.querySelector('#id_is_returnable');
        const amount_required = modal_form.querySelector('#id_amount_required');
        const amount_returned = modal_form.querySelector('#id_amount_returned');
        amount_returned.readOnly = true;
        const initial_date = modal_form.querySelector('#id_initial_date');
        const final_date = modal_form.querySelector('#id_final_date');
        const csrf_token = modal_form.querySelector('input[type=hidden]').value;
        data = {
            'modal_form': modal_form,
            'modal_title': modal_title,
            'status_select': status_select,
            'is_returnable_checkbox': is_returnable_checkbox,
            'amount_required': amount_required,
            'amount_returned': amount_returned,
            'initial_date': initial_date,
            'final_date': final_date,
            'csrf_token': csrf_token
        }
    }
    return data;
}

// VARIABLES 
let methods_urls = {}
let status_select = null;
let amount_returned = null;
let is_returnable_checkbox = null;
let api_reserved_product_CRUD_url = get_html_element('#api_reserved_product_CRUD_url', 'js');
let api_reserved_products_list_url = get_html_element('#api_reserved_products_list_url', 'js');

const reserved_products_table_body = document.querySelector('#reserved_products_table_body');
const error_message = document.querySelector('#error_message');
const cancel_button = get_html_element('#cancel-button');
const modal_elements = get_modal_product_elements();



const reserved_product_status = {
    0: {
        status: 'Solicitado',
        color: 'text-warning '
    },
    1: {
        status: 'Prestado',
        color: 'text-info'
    },
    2: {
        status: 'Denegado',
        color: 'text-danger'
    },
    3: {
        status: 'Seleccionado',
        color: 'text-dark'
    },
    4: {
        status: 'Retornado',
        color: 'text-success'
    }
};

if (get_html_element('#manage_urls')) {
    methods_urls = {
        'get_product_name_and_quantity_url': document.querySelector('#get_product_name_and_quantity').value,
        'validate_reservation_url': document.querySelector('#validate_reservation').value,
        'increase_stock': document.querySelector('#increase_stock').value
    }
}



const store_reserved_product_info = (data) => {
    sessionStorage.setItem('initial_date', data['initial_date']);
    sessionStorage.setItem('final_date', data['final_date']);
    sessionStorage.setItem('id', data['id']);
    sessionStorage.setItem('reservation', data['reservation']);
    sessionStorage.setItem('shelf_object', data['shelf_object']);
    sessionStorage.setItem('last_status', data['status']);
}

const get_stored_reserved_product_info = () => {
    data = {
        'initial_date': sessionStorage.getItem('initial_date'),
        'final_date': sessionStorage.getItem('final_date'),
        'id': parseInt(sessionStorage.getItem('id')),
        'reservation': parseInt(sessionStorage.getItem('reservation')),
        'shelf_object': parseInt(sessionStorage.getItem('shelf_object'))
    };

    return data;
}

const load_product_information = async (data) => {
    store_reserved_product_info(data);
    modal_elements.is_returnable_checkbox.checked = data.is_returnable;
    modal_elements.status_select.selectedIndex = data.status
    modal_elements.amount_required.value = data.amount_required;
    modal_elements.amount_returned.value = data.amount_returned;
    modal_elements.initial_date.value = new Date(data.initial_date).toString();
    modal_elements.final_date.value = new Date(data.final_date).toString();
    $.get(methods_urls.get_product_name_and_quantity_url, { 'id': data.id }, function ({ product_name }) {
        modal_elements.modal_title.textContent = product_name.toUpperCase();
    });
}

const retrieve_object = (product_id = 0) => {
    $.ajax({
        url: api_reserved_product_CRUD_url.replace('0', product_id),
        type: 'GET',
        // beforeSend: function (xhr) {
        //     xhr.setRequestHeader('Authorization', `Token ${user_token}`);
        // },
        success: function (data) {
            load_product_information(data);
        }
    });
}

const increase_stock = (product_id, amount_to_return) => {
    $.get(
        methods_urls.increase_stock,
        {
            'id': product_id,
            'amount_to_return': amount_to_return
        },
        function ({ was_increase }) {
            console.log('Was increased : ', was_increase)
        });
}

const can_increase_and_update = (data) => {
    can_increase = false;
    can_update = true;
    let amount_to_return = 0;

    if ((!modal_elements.is_returnable_checkbox.checked && data['status'] === 1)
        || (modal_elements.is_returnable_checkbox.checked && data['status'] === 4)) {

        can_increase = true;
        amount_to_return = (modal_elements.is_returnable_checkbox.checked) ? data['amount_returned'] : data['amount_required'];

        if (amount_to_return > data['amount_required']) {
            can_update = false
            can_increase = false;
        }
        else if (amount_to_return <= 0) {
            can_increase = false;
        }
    }

    return {
        'can_increase': can_increase,
        'can_update': can_update,
        'amount_to_return': amount_to_return
    }
}

const update_product_information = () => {
    const error = 'No se puede retornar la cantidad indicada';
    const data = get_stored_reserved_product_info();
    data['status'] = modal_elements.status_select.selectedIndex;
    data['is_returnable'] = modal_elements.is_returnable_checkbox.checked;
    data['amount_required'] = parseFloat(modal_elements.amount_required.value);
    data['amount_returned'] = parseFloat(modal_elements.amount_returned.value);

    const results = can_increase_and_update(data);
    const can_update = results.can_update;
    const can_increase = results.can_increase;
    const amount_to_return = results.amount_to_return;

    if (can_increase && amount_to_return > 0) {
        console.log(can_increase);
        increase_stock(data['id'], amount_to_return);
    }

    else {
        error_message.innerHTML = error;
    }

    if (can_update) {
        error_message.innerHTML = '';
        send_update_request(data);
    }
}

const send_update_request = (product_data) => {
    $.ajax({
        url: api_reserved_product_CRUD_url.replace('0', product_data.id),
        type: 'PUT',
        data: product_data,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRFToken', modal_elements.csrf_token);
            // xhr.setRequestHeader('Authorization', `Token ${user_token}`);
        },
        success: function (data) {
            if (data) {
                $('#exampleModal').modal('hide');
                load_reserved_products_list();
            }
        }
    });
}

const load_reserved_products_list = () => {
    const reservation_id = document.querySelector('#reservation_id').value;
    reserved_products_table_body.innerHTML = '';

    $.get(api_reserved_products_list_url.replace(0, reservation_id),
        function (reserved_products) {
            for (const reserved_product of reserved_products) {
                $.get(methods_urls.get_product_name_and_quantity_url, { 'id': reserved_product.id }, function ({ product_name, product_quantity, product_unit }) {
                    fill_reserved_products_table(reserved_product, product_name, product_quantity, product_unit);
                });
            }
        });
}

const fill_reserved_products_table = (reserved_product, product_name, product_quantity, product_unit) => {
    const is_returnable = (reserved_product.is_returnable) ? 'Si' : 'No';
    const table_row_template = `<tr>
    <td id="product_name">
    <a href='#' data-toggle="modal" data-target="#exampleModal"
             id='product-${reserved_product.id}'
             onclick="retrieve_object(${reserved_product.id})">
             ${product_name}
         </a>
    </td>

    <td id="product_quantity">
    ${product_quantity} ${product_unit.toLowerCase()}
    </td>

    <td id="amount_required">
    ${reserved_product.amount_required} ${product_unit.toLowerCase()}
    </td>

    <td id="amount_required">
    ${reserved_product.amount_returned} ${product_unit.toLowerCase()}
    </td>

    <td id="initial_date">
    ${new Date(reserved_product.initial_date).toString()}
    </td>

    <td id="final_date">
    ${new Date(reserved_product.final_date).toString()}
    </td>
    <td id="is_returnable">
        ${is_returnable} 
    </td>
    <td id="status">
        <strong class="${reserved_product_status[reserved_product.status]['color']}">
            ${reserved_product_status[reserved_product.status]['status']} </strong>
    </td>
</tr>`
    reserved_products_table_body.innerHTML += table_row_template;
}

const validate_reservation = () => {
    const last_status = parseInt(sessionStorage.getItem('last_status'));
    const product_id = sessionStorage.getItem('id');

    //Si quiero aceptar la solicitud
    if (last_status === 0 && status_select.selectedIndex === 1) {
        $.get(methods_urls.validate_reservation_url, { 'id': product_id }, function ({ is_valid, available_quantity }) {
            if (is_valid) {
                // Asignar el nuevo amount required
                modal_elements.amount_required.value = available_quantity;
                update_product_information();
            }
            else {
                if (!is_valid && available_quantity < 0) {
                    error_message.innerHTML = `No es posible aceptar una solicitud con fecha y hora menor a la actual`;
                }
                else {
                    $.get(methods_urls.get_product_name_and_quantity_url, { 'id': product_id }, function ({ product_name }) {
                        error_message.innerHTML = `No hay suficiente ${product_name} en el inventario`;
                    });
                }

            }
        });
    }
    else {
        const response = get_action_message(status_select.selectedIndex, last_status);
        error_message.innerHTML = response.error_message;
        if (response.can_update) {
            update_product_information();
        }
    }
}

const get_action_message = (selectd_status, last_status) => {
    let error_message = ''
    let can_update = true;

    if (selectd_status === 0) {
        if (last_status !== selectd_status) {
            error_message = `No es posible poner como ${reserved_product_status[selectd_status]['status'].toLowerCase()} un producto que ha sido previamente ${reserved_product_status[last_status]['status'].toLowerCase()}.`;
            can_update = false;
        }
    }
    else if (selectd_status === 2) {
        if (last_status !== selectd_status && last_status !== 0) {
            error_message = `No es posible poner como ${reserved_product_status[selectd_status]['status'].toLowerCase()} un producto que ha sido previamente ${reserved_product_status[last_status]['status'].toLowerCase()}.`;
            can_update = false;
        }
    }
    else if (selectd_status === 3) {
        error_message = `No es posible poner como ${reserved_product_status[selectd_status]['status'].toLowerCase()} un producto en esta etapa de aprobación.`;
        can_update = false;
    }
    else if (selectd_status === 4) {
        if (last_status !== 1 && last_status !== 4) {
            error_message = `No es posible poner como ${reserved_product_status[selectd_status]['status'].toLowerCase()} un producto que no ha sido previamente prestado.`;
            can_update = false;
        }
    }

    return {
        'error_message': error_message,
        'can_update': can_update
    }
}

// ############################# EVENTS AND SOME CONFIG TO AVOID ERRORS##########################################


if (api_reserved_product_CRUD_url) {
    api_reserved_product_CRUD_url = api_reserved_product_CRUD_url.value;
}

if (api_reserved_products_list_url) {
    api_reserved_products_list_url = api_reserved_products_list_url.value;
}

if (modal_elements) {
    status_select = modal_elements.status_select;
    amount_returned = modal_elements.amount_returned;
    is_returnable_checkbox = modal_elements.is_returnable_checkbox;
}

if (status_select) {
    if (status_select.selectedIndex === 4) {
        amount_returned.readOnly = false;
    }
    else {
        amount_returned.readOnly = true;
    }

    status_select.addEventListener('change', (event) => {
        const last_status = parseInt(sessionStorage.getItem('last_status'));

        if (status_select.selectedIndex === 4 && last_status === 1) {
            amount_returned.readOnly = false;
        }
        else {
            amount_returned.readOnly = true;
        }
    });
}

if (cancel_button) {
    cancel_button.addEventListener('click', () => {
        error_message.innerHTML = '';
    });
}

if (get_html_element('#reserved_products_table')) {
    load_reserved_products_list();
}
