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

// VARIABLES 
const api_url = get_html_element('#api_url', 'js').value;
const modal_form = get_html_element('#modal_form');
const status_select = modal_form.querySelector('#id_status');

const methods_urls = {
    'get_product_name_url': document.querySelector('#get_product_name').value,
    'validate_reservation_url': document.querySelector('#validate_reservation').value
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

const retrieve_update_object = (product_id = 0, method = 'get') => {
    $.ajax({
        url: api_url.replace('0', product_id),
        type: 'GET',
        // beforeSend: function (xhr) {
        //     xhr.setRequestHeader('Authorization', `Token ${user_token}`);
        // },
        success: function (data) {
            if (method === 'get') {
                load_product_information(data);
                document.querySelector('#selected_product_id').value = product_id;
            }
            else if (method === 'put') {
                update_product_information(data);
            }
        }
    });
}


const load_product_information = async (data) => {
    const modal_elements = get_modal_product_elements();
    modal_elements.is_returnable_checkbox.checked = data.is_returnable;
    modal_elements.status_select.selectedIndex = data.status
    modal_elements.amount_required.value = data.amount_required;
    modal_elements.initial_date.value = new Date(data.initial_date).toString();
    modal_elements.final_date.value = new Date(data.final_date).toString();

    $.get(methods_urls.get_product_name_url, { 'id': data.id }, function ({ product_name }) {
        modal_elements.modal_title.textContent = product_name.toUpperCase();
    });
}

const update_product_information = (data) => {
    const modal_elements = get_modal_product_elements();
    data.status = modal_elements.status_select.selectedIndex;
    data.is_returnable = modal_elements.is_returnable_checkbox.checked;

    $.ajax({
        url: api_url.replace('0', data.id),
        type: 'PUT',
        data: data,
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRFToken', modal_elements.csrf_token);
            // xhr.setRequestHeader('Authorization', `Token ${user_token}`);
        },
        success: function (data) {
            if(data){
                $('#exampleModal').modal('hide');
                location.reload();
            }
            
        }
    });
}

const validate_reservation = (product_id) => {
    $.get(methods_urls.validate_reservation_url, { 'id': product_id },
        function ({ is_valid }) {
            console.log(is_valid)
        });

}

status_select.addEventListener('change', (event) => {
    const product_id = document.querySelector('#selected_product_id').value;
    validate_reservation(product_id);

});



