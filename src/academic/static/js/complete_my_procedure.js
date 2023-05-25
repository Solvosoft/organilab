var formmodal = BaseFormModal('#commentmodal', {});

formmodal.addBtnForm = function(instance) {

    return function(event) {
        var dataAsString = convertToStringJson(instance.form, prefix=instance.prefix, extras=instance.data_extras);
        var dataAsJson = JSON.parse(dataAsString);

        $.ajax({
            url: urls['add_comment'],
            type: "POST",
            data: {'comment': dataAsJson.comment, 'procedure_step': step_pk = $('.stepradio:checked').val(), 'my_procedure': my_procedure['pk']},
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            success: (success) => {
                datatableelement.ajax.reload();
                instance.hidemodal();
                Swal.fire({
                    icon: 'success',
                    title: gettext('Success'),
                    text: add_translation['successfull'],
                    timer: 1500
                });
            },
        });

    }
}

formmodal.init(this);

function add_comment() {
    var step_pk = undefined;
    step_pk = $('.stepradio:checked').val();
    if (step_pk === undefined) {
        Swal.fire({
            title: no_step_selected['title'],
            text: no_step_selected['text'],
        });
    } else {
        formmodal.showmodal();
    }
}