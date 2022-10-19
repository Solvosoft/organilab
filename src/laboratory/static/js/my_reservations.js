//########################################VARIABLES
var reserved_product_id
var table
var values

//########################################FUNCTIONS USED BY OTHER FUNCTIONS
/*Function necessary to filter an array and only have the distinct elements*/
function onlyUnique(value, index, self) {
  return self.indexOf(value) === index;
}

/*Function to get all elements with an specific name*/
function get_all_elements_with_name(name){
    list = [];
    var inputs = document.getElementsByName(name);
    for (i=0; i < inputs.length; i++){
        list[i] = inputs[i].value;
    }
    return list
}

/*Function necessary to ge the crsf_token to use with ajax*/
function get_csrf_token(){
    form_modal = $('#modal_reservation_delete_form');
    crsftoken = get_form_data(form_modal);
    return crsftoken.csrfmiddlewaretoken
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

/*Function to disable or enable the reservation button of My Reservations view if SOLICITED ITEMS are on*/
function status_of_reservation_buttons(all_status_codes){
   disable_reservation_button = true;
   for (let i=0; i < all_status.length; i++){
        if (all_status[i] == 3){
            disable_reservation_button = false;
        }
   }
   btnReserve = document.getElementById("reserve_btn");
   btnReserve.disabled = disable_reservation_button;
   btnCancelProducts = document.getElementById("cancel_all_products_btn");
   btnCancelProducts.disabled = disable_reservation_button;
}

//########################################FUNCTIONS MODAL CALLED IN THE HTML ONCLICK
/*When the deletion modal is opened (a delete button is clicked), this methods gets the id of the reserved product*/
function init_remove_reservation(pk) {
    reserved_product_id = pk;
}

//########################################MAIN FUNCTIONS
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

/*Function to remove all items that have a status of selected on the My Reservations View*/
function delete_reserved_products(){
    all_reserved_products_ids = get_all_elements_with_name("rp_id");
    console.log(all_reserved_products_ids)
    for (let i=0; i<all_reserved_products_ids.length;i++){
        $.ajax({
            url: document.api_modal_delete.replace(0, all_reserved_products_ids[i]),
            type: 'DELETE',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', get_csrf_token());
            },
            success: function(data) {
                location.reload()
            }
        });
    }
    $("#delete_all_obj_reservation_modal").modal('hide');
}

/*Function to update the products now that the reservations have been made*/
function update_reserved_products(data_info){
    var reservedProduct;
    var reservation;
    var shelf_obj;

    for (var x=0; x < data_info.length; x++){
        reservedProduct = data_info[x][0];
        reservation = data_info[x][1];
        shelf_obj = data_info[x][2];
        data = {
            "reservation": reservation,
            "status": 0
        }
        $.ajax({
            url: document.api_update_product.replace(0, reservedProduct),
            type: 'PUT',
            data: data,
            beforeSend: function (xhr) {
              xhr.setRequestHeader('X-CSRFToken', get_csrf_token());
            },
            success: function(data) {
                location.reload()
            }
        });
    }
}

/*Function to send the requests for the shelfobjects to each admin of the lab that shelfobject is in*/
function make_reservation(){
    var lab_to_make_reservation = [];
    var shelf_object_ids_list;
    var reserved_products_ids_list;
    var info_update = [];
    var user;

    reserved_products_ids_list = get_all_elements_with_name("rp_id") //Get all elements with the name rp_id (Reserved Products Ids)
    shelf_object_ids_list = get_all_elements_with_name("so_id") //Get all elements with the name so_id (Shelf Objects Ids)
    user = document.getElementsByName("user_id")[0].value; //Get the user

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
                    for (j=0; j < reserved_products_ids_list.length; j++){
                       if(lab_ids[j] == data["laboratory"]){
                           info_update[j] = [
                                reserved_products_ids_list[j],
                                data["id"],
                                shelf_object_ids_list[j]
                           ];
                       }
                    }
                    update_reserved_products(info_update);
                }
            });
        }
    });
}

//########################################INIT
/*Function necessary for the datatables to work*/
$(document).ready(function() {
   table = $('#table_id').DataTable();
   all_status = get_all_elements_with_name("status_num");
   status_of_reservation_buttons(all_status);
});

function formatDate(date){
    var newDate;

           let tmp=date.replace('.',',');
           tmp=tmp.split(',');
           let month=tmp[0].trim();
           let day=tmp[1].trim();
           let year=tmp[2].trim();
           //let hour=tmp[3].trim();
           newDate=year+"/"+month+"/"+day

    return newDate;
}
/*
function infoTable(...list){
console.log(list.length,"argumentos")
    var data=[];
    for(let i=0;i<list.length-1;i++){

        let element={
        obj_user_id: list[0][i],
        obj_product_id: list[1][i]
        obj_product_shelf_object_id: list[2][0],
        obj_shelf_object: list[3][i],
        obj_amount_required: list[4][i],
        obj_initial_date: list[][i],
        obj_final_date: list[3][i],
        obj_get_status_display: list[4][i],
        obj_tmp_final_date: formatDate(list[3][i])

        }

        data.push(element);
    }
    console.log(data,"data")
    return data;
}

function switchButton(){

    var showAllProductsCheckBox = document.getElementById('showAllProducts').checked;

    var reserved_products_obj_user_ids_list = get_all_elements_with_name("user_id")
    var reserved_products_ids_list = get_all_elements_with_name("rp_id")
    var reserved_products_obj_shelf_object_ids_list = get_all_elements_with_name("so_id")

    var reserved_products_obj_shelf_object_list = get_all_elements_with_name("obj_shelf_object")
    var reserved_products_obj_amount_required_list = get_all_elements_with_name("obj_amount_required")
    var reserved_products_obj_initial_date_list = get_all_elements_with_name("obj_initial_date")
    var reserved_products_obj_final_date_list = get_all_elements_with_name("obj_final_date")
    var reserved_products_obj_get_status_display_list = get_all_elements_with_name("obj_get_status_display")

    infoTable(reserved_products_obj_user_ids_list,
              reserved_products_ids_list,
              reserved_products_obj_shelf_object_ids_list,
              reserved_products_obj_shelf_object_list,
              reserved_products_obj_amount_required_list,
              reserved_products_obj_initial_date_list,
              reserved_products_obj_final_date_list,
              reserved_products_obj_get_status_display_list);

   /* var date_now = new Date();
    date_now.setHours(0,0,0,0);

    if(showAllProductsCheckBox){
        //for
        var date_product = new Date(formatDate(reserved_products_final_date_list)[0]);
        if(date_product.getTime()>=date_now.getTime()){



        }
    }

}
*/