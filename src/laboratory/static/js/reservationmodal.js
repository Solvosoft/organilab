var shelf_object_id
var user_id
var object_id
var object_element
const reservation_url=document.api_modal;

/* Function called when the reservation button is clicked.
It gets the shelfObject.pk and user id and saves it as a js variables.
*/
function initialize_modal(shelf_obj_pk, user_pk) {
    $('#alert_message').css('display', 'none');
    shelf_object_id = shelf_obj_pk;
    user_id = user_pk;
}
function initialize_reservation_modal(element,shelf_obj_pk,object_pk, user_pk,units) {
    $('#alert_message').css('display', 'none');
    shelf_object_id = shelf_obj_pk;
    object_id= object_pk;
    user_id = user_pk;
    $('.unit').text(units);
    object_element=element
    get_detail()
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
        </p>
        <p>
            <input type="hidden" name="object" id="id_object" value="${object_id}">
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
    let option=$('#option').find('option:selected').val()
    if(option==1){
    $.get(document.date_validation_script_url, input,
        function({ is_valid }) {
            if (is_valid) {
                $.ajax({
                    url: document.api_modal,
                    type: 'POST',
                    data: data,
                    success: function(data) {
                        const reservation_modal = document.querySelector('#modal_reservation');
                        const modal = bootstrap.Modal.getInstance(reservation_modal);
                        modal.hide();
                        document.querySelector('#option').selectedIndex=0;
                        clear_inputs();
                        Swal.fire(
                                '',
                                'Reservado',
                                'success'
                        )
                    }
                });
            } else {
                error_message('#alert_message')
            }
        });
        }else{
                $.ajax({
                    url: document.api_modal,
                    type: 'POST',
                    data: data,
                    success: function({status,msg,object}) {
                      if(status){
                          message(msg,'success', object);
                       }else{
                          message(msg,'error');
                       }
                    }
                });
        }
    }
function message(msg,icon,object=undefined){
    clear_inputs();
    const reservation_modal = document.querySelector('#modal_reservation');
    const modal = bootstrap.Modal.getInstance(reservation_modal);
    modal.hide();
    Swal.fire(
    '',
    msg,
    icon
    )
    if(option!=3 && object!=undefined && view_search==false){
        object_element.parentElement.children[0].textContent=object.object
   }
    if(option!=3 && object!=undefined && view_search){
        const amount_div = document.querySelector('#o'+shelf_object_id)
        let text = amount_div.children[0].textContent.split(':');
        amount_div.children[0].innerHTML=`<p class="m-0 p-0"><strong>${text[0]}: </strong> ${parseFloat(object.amount).toFixed(3)} ${object.unit} </p>`;
   }
}
function create_reservation() {
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
                    success: function(data) {
                        message('Reservado','success')
                    }
                });
            } else {
                error_message('#alert_message')
            }
        });
}
function error_message(id,msg){
  if ($(`${id}`).css('display') != 'block')
      $("#error_message_object").text(msg);
      $(`${id}`).css('display', 'block');
 }

function clear_inputs(){
    input_fields = $('#modal_reservation_form').find(':input');
    for (const input of input_fields) {
        if(input.type!='hidden' && input.name!='options'){
            input.value='';
        }
    }
}
function select_action(reserved_state, tranfer_state, add_state, subtract_state){
    $('#reserved').css('display',reserved_state);
    $('#tranfer').css('display',tranfer_state);
    $('#add').css('display',add_state);
    $('#subtract').css('display',subtract_state);
}

function choose_action(){
   let option=$('#option').find('option:selected').val();
   select_action('block','none','none','none');
   document.api_modal=reservation_url;
   if(option==3){
    select_action('none','block','none','none');
    document.api_modal=$('#edit_url').val();
 }else if(option==2){
    select_action('none','none','block','none');
     document.api_modal=$('#edit_url').val();
  }else if(option==4){
  select_action('none','none','none','block');
     document.api_modal=$('#edit_url').val();  }
 }
$( document ).ready(()=>{
    choose_action()
});

function get_detail(){
    $.ajax({
       url: $('#detail_url').val(),
       type: 'POST',
       data: {'shelf_object':shelf_object_id},
       success: function({obj}) {
        $('#obj').text(obj)
        }
       });
}