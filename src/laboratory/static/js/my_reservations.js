var reserved_product_id
var table
var values

/*Function necessary to filter an array and only have the distinct elements*/
function onlyUnique(value, index, self) {
  return self.indexOf(value) === index;
}

/*Function necessary for the datatables to work*/
$(document).ready(function() {
   table = $('#table_id').DataTable();
});

function get_csrf_token(){
    form_modal = $('#modal_reservation_delete_form');
    crsftoken = get_form_data(form_modal);
    return crsftoken.csrfmiddlewaretoken
}

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
     $.ajax({
        url: document.api_modal_delete.replace(0, reserved_product_id),
        type: 'DELETE',
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-CSRFToken', get_csrf_token());
        },
        success: function(data) {
            location.reload()
        }
    });
    $("#delete_selected_obj_reservation_modal").modal('hide');
}

/*Function to update the products now that the reservations have been made*/
function update_reserved_products(data_info){
    for (i=0; i < data_info.length; i++){
        var reservation = data_info[i][2];
        $.ajax({
            url: document.api_get_product.replace(0, data_info[i][0]),
            type: 'GET',
            success: function(data) {
                data["reservation"] = reservation;
                data["status"] = 0;
                console.log("Data Modificada")
                console.log(data)
                $.ajax({
                    url: document.api_update_product,
                    type: 'PUT',
                    data: data,
                    beforeSend: function (xhr) {
                      xhr.setRequestHeader('X-CSRFToken', get_csrf_token());
                    },
                    success: function(data) {

                    }
                });
            }
        });
    }
}


/*Function to send the requests for the shelfobjects to each admin of the lab that shelfobject is in*/
function make_reservation(){
    var lab_to_make_reservation = [];
    var shelf_object_ids_list = [];
    var reserved_products_ids_list = [];
    var info_update = [];

    var inputs = document.getElementsByName("rp_id"); //Get all elements with the name rp_id (Reserved Products Ids)
    for (i=0; i < inputs.length; i++){
        reserved_products_ids_list[i] = inputs[i].value; //Saving them in reserved_products_ids_list
    }

    var shelf_objects = document.getElementsByName("so_id"); //Get all elements with the name so_id (Shelf Objects Ids)
    for (i=0; i < shelf_objects.length; i++){
        shelf_object_ids_list[i] = shelf_objects[i].value; //Saving them in shelf_object_ids_list
    }

    var user = document.getElementsByName("user_id")[0].value; //Get the user
    input = {
        "ids": shelf_object_ids_list
    }

    $.get(document.get_lab_id_script_url, input,
    function({ lab_ids }) {
        lab_to_make_reservation = lab_ids.filter(onlyUnique); //We only need the individual lab id's
        for (i=0; i < lab_to_make_reservation.length; i++){
            data = {
                "user": user,
                "laboratory": lab_to_make_reservation[i],
                //status default is REQUESTED (0), comments can be null, is_massive default is false
            }
            $.ajax({
                url: document.api_create_reservation,
                type: 'POST',
                data: data,
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-CSRFToken', get_csrf_token());
                },
                success: function(data) {
                    console.log(data)
                    for (j=0; j < reserved_products_ids_list.length; j++){
                       if(lab_ids[j] == data["laboratory"]){
                           info_update[j] = [
                                reserved_products_ids_list[j],
                                lab_ids[j],
                                data["id"]
                           ];
                       }
                    }
                    console.log("info_update:")
                    console.log(info_update)
                    update_reserved_products(info_update);
                }
            });
        }
    });
}