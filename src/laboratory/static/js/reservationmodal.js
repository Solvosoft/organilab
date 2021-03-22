var shelf_object_id
var user_id
/* Function called when the reservation button is clicked.
It gets the shelfObject.pk and user id and saves it as a js variables.
*/
function initialize_modal(shelf_obj_pk, user_pk) {
    $('#alert_message').css('display', 'none');
    shelf_object_id = shelf_obj_pk;
    user_id = user_pk;
}
function initialize_reservation_modal(shelf_obj_pk, user_pk,units) {
    $('#alert_message').css('display', 'none');
    shelf_object_id = shelf_obj_pk;
    user_id = user_pk;
    $('#unit').text(units);

    }

/* Function that appends an input field to the form 
before serializing it. In this case the shelf_object field and the user's id.
*/
function get_form_data(form) {
    const formAttributes = {};
    form.append(
        `<p>
            <input type="hidden" name="shelf_object" id="id_shelf_object" value="${shelf_object_id}">
        </p>
        <p>
            <input type="hidden" name="user" id="id_user" value="${user_id}">
        </p>`
    );
    input_fields = $(form).find(':input');
    for (const input of input_fields) {
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
    input = {
        "obj": data.shelf_object,
        "initial_date": data.initial_date,
        "user": data.user,
        "status": 3
    }
    $.get(document.date_validation_script_url, input,
        function({ is_valid }) {
            if (is_valid) {
                $.ajax({
                    url: document.api_modal,
                    type: 'POST',
                    data: data,
                    success: function(data) {}
                });
                $("#modal_reservation").modal('hide');
            } else {
                if ($('#alert_message').css('display') != 'block')
                {
                    $('#alert_message').css('display', 'block');
                }
            }
        });
}

function select_action(reserved_state, tranfer_state, add_state){
    $('#reserved').css('display',reserved_state);
    $('#tranfer').css('display',tranfer_state);
    $('#add').css('display',add_state);
}

function choose_action(){
   let option=$('#option').find('option:selected').val()
    select_action('block','none','none');
   if(option==2){
    select_action('none','block','none');
   }
   if(option==3){
    select_action('none','none','block');
   }
 }