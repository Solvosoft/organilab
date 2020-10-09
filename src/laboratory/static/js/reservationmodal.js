var shelf_object_id

function reserve_product(pk){
    shelf_object_id=pk;
}

function add_form_data(form){
    const STATUS_SOLICITED = 3
    form.append(
        `<p>
            <input type="hidden" name="shelf_object" id="id_shelf_object" value="${shelf_object_id}">
        </p>
        <p>
            <input type="hidden" name="status" id="id_status" value="${STATUS_SOLICITED}">
        </p>`
    );
}

function add_reservation() {
    form_modal = $('#modal_reservation_form');
    add_form_data(form_modal);
    data = form_modal.serialize();
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