var reserved_product_id
var table

/*Function necessary to filter an array and only have the distinct elements*/
function onlyUnique(value, index, self) {
  return self.indexOf(value) === index;
}

/*Function necessary for the datatables to work*/
$(document).ready(function() {
   table = $('#table_id').DataTable();
});

/*When the deletion modal is opened (a delete button is clicked), this methods gets the id of the reserved product*/
function init_remove_reservation(pk) {
    reserved_product_id = pk;
}

/* Function that returns the fields of the form. In this case the crsf token*/
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

/*Function to remove a shelf object from the My Reservations view*/
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

/*Function to send the requests for the shelfobjects to each admin of the lab that shelfobject is in*/
function make_reservation(){
    var reserved_products_ids_list = []
    var shelf_object_ids_list = []

    var inputs = document.getElementsByName("rp_id"); //Get all elements with the name rp_id (Reserved Products Ids)
    for (i=0; i < inputs.length; i++){
        reserved_products_ids_list[i] = inputs[i].value; //Saving them in reserved_products_ids_list
    }

//    for (x in reserved_products_ids_list){
//        console.log(reserved_products_ids_list[x]) //This is for DEBUG (DELETE LATER)
//    }

    var shelf_objects = document.getElementsByName("so_id"); //Get all elements with the name so_id (Shelf Objects Ids)
    for (i=0; i < shelf_objects.length; i++){
        shelf_object_ids_list[i] = shelf_objects[i].value; //Saving them in shelf_object_ids_list
    }
    shelf_object_ids_list = shelf_object_ids_list.filter(onlyUnique); //We only need the individual shelf objects id's

    for (x in shelf_object_ids_list){
        console.log(shelf_object_ids_list[x]) //This line is for DEBUG (DELETE LATER)
    }

    input = {
        "ids": shelf_object_ids_list
    }
    $.get("returnLabId", input,
    function(response) {
        console.log(response)
    });

}