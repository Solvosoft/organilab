var shelf_object_id

function reserve_product(pk){
    shelf_object_id=pk;
}

function add_reservation() {
    form_modal = $('#modal_reservation_form');
    data = form_modal.serialize();
    console.log(data)
    data["shelf_object"] = shelf_object_id;
    console.log(data)
    $.ajax({
        url: document.api_modal,
        type: 'POST',
        data: data,
        success: function (data) {
            location.reload();
        }
    });
}