/**
 * Created by jaquer on 13/12/16.
 */

$(document).ready(function () {
    $('#id_type').change(update_form);
    update_form();
});

function update_form() {
    var select_widget = $('#id_type');
    var selected_option = select_widget.find('option:selected').val();
    var form = $('#objectview_form');

    if (selected_option == '0') {
        console.log('show');
        show_reactive_options();
    } else {
        console.log('hide');
        hide_reactive_options();
    }
}

var ids = [
    "id_molecular_formula",
    "id_cas_id_number",
    "id_security_sheet",
    "id_imdg_code",
    "id_is_precursor"
];

function show_reactive_options() {
    for (var i = 0; i < ids.length; i++) {
        $('#' + ids[i]).parents('.form-group').show();
    }
}

function hide_reactive_options() {
    for (var i = 0; i < ids.length; i++) {
        $('#' + ids[i]).parents('.form-group').hide();
        document.getElementById(ids[i]).required = false;
    }
}
