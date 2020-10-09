var shelf_object_id

/* Function called when the reservation button is clicked. 
It gets the shelfObject.pk and saves it as a js variable.
*/
function get_shelf_object_id(pk){
    shelf_object_id=pk;
}

/* Function that appends an input field to the form 
before serializing it. In this case the shelf_object field.
*/
function get_form_data(form){
    const formAttributes = {};
    form.append(
        `<p>
            <input type="hidden" name="shelf_object" id="id_shelf_object" value="${shelf_object_id}">
        </p>`
    );
    input_fields = $(form).find(':input');
    for (const input of input_fields){
        name = input.name;
        value = input.value;
        formAttributes[`${name}`] = value;
    }
    return formAttributes;
}

/* Function called when the modal Save changes button is clicked.
It sends the data of the form to the database via API.
*/
function add_reservation() {
    form_modal = $('#modal_reservation_form');
    data = get_form_data(form_modal);
    $.ajax({
        url: document.api_modal,
        type: 'POST',
        data: data,
        success: function (data) {
            location.reload();
        }
    });
}