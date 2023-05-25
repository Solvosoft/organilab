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
                instance.hidemodal();
                Swal.fire({
                    icon: 'success',
                    title: gettext('Success'),
                    text: add_translation['successfull'],
                }).then(function() {
                    datatableelement.ajax.reload();
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

function saveForm(state) {
   Swal.fire({
        title: message['title'],
        text: message['text'],
        icon: message['icon'],
        confirmButtonText: message['confirm'],
        denyButtonText: message['deny'],
        showDenyButton: true,
        showCloseButton: true

        }).then((result) => {

        if (result.isConfirmed) {
            $.ajax({
                url: urls['edit'],
                type: "POST",
                dataType: "json",
                data: $('#procedure_form').serialize()+"&status="+state,
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                success: (success) => {
                    Swal.fire(
                        "",
                        saved,
                        "success"
                        )
                    location.href =urls['list'];
                },
            });

        } else if (result.isDenied){
        }
        })
}

function Delete_Inform(id) {
    Swal.fire({
        title: message['title'],
        text: message['text'],
        icon: message['icon'],
        confirmButtonText: message['confirm'],
        denyButtonText: message['deny'],
        showDenyButton: true,
        showCloseButton: true

        }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: urls['edit'],
                type: "POST",
                dataType: "json",
                data: {'id':id},
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                success: (success) => {
                    Swal.fire(
                        '',
                        saved,
                        'success'
                        )
                    location.href =urls['list'];
                },
            });

        } else if (result.isDenied){
        }
        })
}

function edit_comment(pk){
    localStorage.setItem('comment', pk);
    let url = urls['get_comment']+pk;
    $.ajax({
    url: url,
        type: "GET",
        dataType: "json",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        success: (success) => {
            Swal.fire({
                title: update_translation['title'],
                input: 'textarea',
                confirmButtonText: update_translation['accept'],
                denyButtonText: update_translation['deny'],
                showDenyButton: true,
                showCloseButton: true,
                inputValue:success.comment
            }).then(function(result) {
                if (result.isConfirmed) {
                    update_comment(result.value)
                }
            })
        }
    });
}

function update_comment(comment){
     let url = urls['delete_update_comment'].replace('0',localStorage.getItem('comment'));
     localStorage.removeItem('comment');
     $.ajax({
            url: url,
            type: "PUT",
            dataType: "json",
            data: {'comment':comment},
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            success: (success) => {
                Swal.fire(
                    '',
                    update_translation['successfull'],
                    'success'
                ).then(function(result) {
                    datatableelement.ajax.reload();
                })
            },
        });
}
function delete_comment(comment){
    let url = urls['delete_update_comment'].replace('0',comment);
    Swal.fire({
    title: remove_translation["title"],
    text: remove_translation['text'],
    icon: "error",
    confirmButtonText: remove_translation['accept'],
    denyButtonText: remove_translation['deny'],
    showDenyButton: true,
    showCloseButton: true
    }).then((result) => {
    if (result.isConfirmed) {
        $.ajax({
            url: url,
            type: "DELETE",
            dataType: "json",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            success: (success) => {
                Swal.fire(
                   remove_translation['successfull'],
                    ).then(function(result) {
                    datatableelement.ajax.reload();
                })
            },
        });
    }
    });
}

$('#datatableelement tbody').on( 'click', 'i', function () {

    var action = this.className;
    var data = datatableelement.row( $(this).parents('tr') ).data();

    if (action==="fa fa-edit beditbtn") {
        edit_comment(data.id);
    } else if (action=="fa fa-trash deletebtn") {
        delete_comment(data.id);
    }

});

$(document).ready(function() {
    $('.dataTables_filter').addClass('w-100');
    $('.dataTables_filter input').addClass('filter-input').css('width', '96%');
    $('.dataTables_filter label').addClass('filter-label').css('width', '100%');
    $('.dataTables_paginate').removeClass('paging_full_numbers');
    $('.dataTables_paginate').addClass('paging_simple_numbers');
    $('#notificationdatatable').removeClass('dtr-inline');
});


$('.stepradio').on('change', function(e) {
    datatableelement.ajax.reload();
});