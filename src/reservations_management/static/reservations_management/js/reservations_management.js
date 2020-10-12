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
const api_url = get_html_element('#api_url', 'js').value;
const modal_form = get_html_element('#modal_form');
const error_message = document.querySelector('#error_message');
const cancel_button = document.querySelector('#cancel-button');
const modal_elements = get_modal_product_elements();

const methods_urls = {
    'get_product_name_url': document.querySelector('#get_product_name').value,
    'validate_reservation_url': document.querySelector('#validate_reservation').value
}

const store_reserved_product_info = (data) => {
    sessionStorage.setItem('initial_date', data['initial_date']);
    sessionStorage.setItem('final_date', data['final_date']);
    sessionStorage.setItem('id', data['id']);
    sessionStorage.setItem('reservation', data['reservation']);
    sessionStorage.setItem('shelf_object', data['shelf_object']);
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
    $.get(methods_urls.get_product_name_url, { 'id': data.id }, function ({ product_name }) {
        modal_elements.modal_title.textContent = product_name.toUpperCase();
    });
}


const retrieve_object = (product_id = 0, method = 'get') => {
    $.ajax({
        url: api_url.replace('0', product_id),
        type: 'GET',
        // beforeSend: function (xhr) {
        //     xhr.setRequestHeader('Authorization', `Token ${user_token}`);
        // },
        success: function (data) {
            console.log(data);
            load_product_information(data);
            document.querySelector('#selected_product_id').value = product_id;
        }
    });
}

const update_product_information = (product_id) => {
    data = get_stored_reserved_product_info();
    data['status'] = modal_elements.status_select.selectedIndex;
    data['is_returnable'] = modal_elements.is_returnable_checkbox.checked;
    data['amount_required'] = parseFloat(modal_elements.amount_required.value);
    $.ajax({
        url: api_url.replace('0', data.id),
        type: 'PUT',
        data: data,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRFToken', modal_elements.csrf_token);
            // xhr.setRequestHeader('Authorization', `Token ${user_token}`);
        },
        success: function (data) {
            if (data) {
                $('#exampleModal').modal('hide');
                location.reload();
            }

        }
    });
}

const validate_reservation = (product_id) => {
    const status_select = modal_form.querySelector('#id_status');

    //Si quiero aceptar la solicitud
    if (status_select.selectedIndex === 1) {

        $.get(methods_urls.validate_reservation_url, { 'id': product_id },
            function ({ is_valid, available_quantity }) {
                console.log(is_valid, available_quantity)
                if (is_valid) {
                    console.log('valido');
                    // Asignar el nuevo amount required
                    modal_elements.amount_required.value = available_quantity;
                    update_product_information(product_id);
                }
                else {
                    $.get(methods_urls.get_product_name_url, { 'id': product_id }, function ({ product_name }) {
                        error_message.innerHTML = `No hay suficiente ${product_name} en el inventario`;
                    });
                }
            });
    }
    else if (status_select === 4) {
        console.log(Returned);

    }
    else {
        update_product_information(product_id);
    }

}

cancel_button.addEventListener('click', () => {
    error_message.innerHTML = '';
});

// status_select.addEventListener('change', (event) => {
//     const product_id = document.querySelector('#selected_product_id').value;
//     // validate_reservation(product_id);

// });

