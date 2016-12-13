/**
 * Created by jaquer on 13/12/16.
 */

$(document).ready(function () {
    $('#id_type').change(update_form);
});

function update_form() {
    var select_widget = $('#id_type');
    var selected_option = select_widget.find('option:selected').val();
    var form = $('#objectview_form');

    if (selected_option == '0') {
        form.html(get_extended_form(1));
    } else {
        form.html(get_extended_form(0));
        select_widget.find('option[value="' + selected_option + '"]').attr("selected", "selected");
        select_widget.change(update_form);
    }
}

function get_extended_form(extended) {
    var extended_form = '';
    $.ajax({
        url: '/get_extended_form?extended=' + extended,
        data: $('#objectview_form').serialize(),
        async: false,
        method: 'post',
        success: function (data) {
            extended_form = data.content;
        }
    });
    console.log(extended_form);
    return extended_form;
}