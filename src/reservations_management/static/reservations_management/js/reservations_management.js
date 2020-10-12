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
    const modal_form = get_html_element('#modal_form');
    const modal_title = get_html_element('#product_name');
    const status_select = modal_form.querySelector('#id_status');
    const is_returnable_checkbox = modal_form.querySelector('#id_is_returnable');
    const amount_required = modal_form.querySelector('#id_amount_required');
    const initial_date = modal_form.querySelector('#id_initial_date');
    const final_date = modal_form.querySelector('#id_final_date');
    const csrf_token = modal_form.querySelector('input[type=hidden]').value;
    return {
        'modal_form': modal_form,
        'modal_title': modal_title,
        'status_select': status_select,
        'is_returnable_checkbox': is_returnable_checkbox,
        'amount_required': amount_required,
        'initial_date': initial_date,
        'final_date': final_date,
        'csrf_token': csrf_token
    }
}

// VARIABLES 
const api_reserved_product_CRUD_url = get_html_element('#api_reserved_product_CRUD_url', 'js').value;
const api_reserved_products_list_url = get_html_element('#api_reserved_products_list_url', 'js').value;
const modal_form = get_html_element('#modal_form');
const error_message = document.querySelector('#error_message');
const cancel_button = document.querySelector('#cancel-button');
const modal_elements = get_modal_product_elements();
const reserved_products_table_body = document.querySelector('#reserved_products_table_body');
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
const methods_urls = {
    'get_product_name_and_quantity_url': document.querySelector('#get_product_name_and_quantity').value,
    'validate_reservation_url': document.querySelector('#validate_reservation').value
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

const update_product_information = (product_id) => {
    data = get_stored_reserved_product_info();
    data['status'] = modal_elements.status_select.selectedIndex;
    data['is_returnable'] = modal_elements.is_returnable_checkbox.checked;
    data['amount_required'] = parseFloat(modal_elements.amount_required.value);
    $.ajax({
        url: api_reserved_product_CRUD_url.replace('0', data.id),
        type: 'PUT',
        data: data,
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

const validate_reservation = () => {
    const status_select = modal_form.querySelector('#id_status');
    const last_status = sessionStorage.getItem('last_status');
    const product_id = sessionStorage.getItem('id');

    //Si quiero aceptar la solicitud
    if (status_select.selectedIndex === 1) {

        $.get(methods_urls.validate_reservation_url, { 'id': product_id },
            function ({ is_valid, available_quantity }) {
                if (is_valid) {
                    // Asignar el nuevo amount required
                    modal_elements.amount_required.value = available_quantity;
                    update_product_information(product_id);
                }
                else {
                    $.get(methods_urls.get_product_name_and_quantity_url, { 'id': product_id }, function ({ product_name }) {
                        error_message.innerHTML = `No hay suficiente ${product_name} en el inventario`;
                    });
                }
            });
    }
    else if (status_select.selectedIndex === 4) {
        if (last_status === 1) {
            console.log('Returned');
            console.log(last_status);
        }

    }
    else {
        update_product_information(product_id);
    }

}

cancel_button.addEventListener('click', () => {
    error_message.innerHTML = '';
});


const load_reserved_products_list = () => {
    const reservation_id = document.querySelector('#reservation_id').value;
    reserved_products_table_body.innerHTML = '';

    $.get(api_reserved_products_list_url.replace(0, reservation_id),
        function (reserved_products) {
            for (const reserved_product of reserved_products) {
                $.get(methods_urls.get_product_name_and_quantity_url, { 'id': reserved_product.id }, function ({ product_name, product_quantity }) {
                    fill_reserved_products_table(reserved_product, product_name, product_quantity);
                });
            }
        });
}

const fill_reserved_products_table = (reserved_product, product_name, product_quantity) => {
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
    ${product_quantity}
    </td>

    <td id="amount_required">
    ${reserved_product.amount_required}
    </td>

    <td id="initial_date">
    ${new Date(reserved_product.initial_date).toString()}
    </td>

    <td id="final_date">
    ${new Date(reserved_product.initial_date).toString()}
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

load_reserved_products_list();