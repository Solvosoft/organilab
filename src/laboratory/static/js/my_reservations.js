var reserved_product_id
var table

$(document).ready(function() {
   table = $('#table_id').DataTable();
});

function init_remove_reservation(pk) {
    reserved_product_id = pk;
}

/* Function that returns the fields of the form. In this case the crsf token
*/
function get_form_data(form) {
    const formAttributes = {};
    input_fields = $(form).find(':input');
    for (const input of input_fields) {
        name = input.name;
        value = input.value;
        formAttributes[`${name}`] = value;
    }
    return formAttributes;
}

function remove_reservation(){
    form_modal = $('#modal_reservation_delete_form');
    values = get_form_data(form_modal);
     $.ajax({
        url: document.api_modal_delete.replace(0, reserved_product_id),
        type: 'DELETE',
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRFToken', values.csrfmiddlewaretoken);
        },
        success: function(data) {
            location.reload()
        }
    });
    $("#delete_selected_obj_reservation_modal").modal('hide');
}