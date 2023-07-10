let message_title = procedure_info['status'] == 'Eraser'? gettext("Do you want to send the report for review?") : gettext("Do you want to finish the report?");
var formmodal = BaseFormModal('#commentmodal', {});

formmodal.addBtnForm = function(instance) {

    return function(event) {
        var dataAsString = convertToStringJson(instance.form, prefix=instance.prefix, extras=instance.data_extras);
        var dataAsJson = JSON.parse(dataAsString);

        $.ajax({
            url: urls['add_comment'],
            type: "POST",
            data: {'comment': dataAsJson.comment, 'procedure_step': step_pk = $('.stepradio:checked').val(), 'my_procedure': procedure_info['pk']},
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            success: (success) => {
                instance.hidemodal();
                Swal.fire({
                    icon: 'success',
                    title: gettext("Added"),
                    text: gettext("Saved successfully"),
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
            title: gettext("No step selected"),
            text: gettext("You must select a step to add comments."),
        });
    } else {
        formmodal.showmodal();
    }
}

function saveForm(state) {
   Swal.fire({
        title: message_title,
        text: gettext("Discarding cannot be undone."),
        icon: "warning",
        confirmButtonText: gettext("Save"),
        denyButtonText: gettext("Cancel"),
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
                        gettext("Saved successfully"),
                        "success"
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
    let url = urls['get_comment'].replace('0', pk);
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
                title: gettext("Update the observation"),
                input: 'textarea',
                confirmButtonText: gettext("Yes"),
                denyButtonText: gettext("No"),
                showDenyButton: true,
                showCloseButton: true,
                inputValue:success.comment
            }).then(function(result) {
                if (result.isConfirmed) {
                    update_comment(result.value, pk)
                }
            })
        }
    });
}

function update_comment(comment, pk){
     let url = urls['update_comment'].replace('0', pk);
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
                    gettext("Successfully updated"),
                    'success'
                ).then(function(result) {
                    datatableelement.ajax.reload();
                })
            },
        });
}

function delete_comment(comment){
    let url = urls['delete_comment'].replace('0',comment);
    Swal.fire({
    title: gettext("Delete the observation"),
    text: gettext("Do you want to remove the observation?"),
    icon: "error",
    confirmButtonText: gettext("Yes"),
    denyButtonText: gettext("No"),
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
                   gettext("Successfully deleted"),
                    ).then(function(result) {
                    datatableelement.ajax.reload();
                })
            },
        });
    }
    });
}

document.table_default_dom = "<'row'<'col-sm-6 col-md-6 p-0' f>" +
             "<'col-sm-11 col-md-11 mt-1 p-0 d-flex align-items-center justify-content-start'l>" +
             "<'col-sm-1 col-md-1 mt-1 d-flex align-items-center justify-content-end 'B>>" +
             "<'row'<'col-sm-12'tr>><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>";

datatableelement=createDataTable('#datatableelement', urls['get_datatable_info'], {
 columns: [
        {data: "created_by", name: "created_by", title: gettext("Creator"), type: "string", visible: true},
        {data: "created_by_at", name: "created_by_at", title: gettext("Creation Date"), type: "date", visible: true, "dateformat":  urls['datetime_format']},
        {data: "comment", name: "comment", title: gettext("Comment"), type: "string", visible: true}
    ],
    ajax: {
        url: urls['get_datatable_info'],
        type: 'GET',
        data: function(dataTableParams, settings) {
            var data = formatDataTableParams(dataTableParams, settings);
            data['procedure_step'] = $('.stepradio:checked').val();
            data['my_procedure'] = procedure_info["pk"];
            return data;
        }
    },
    columnDefs: [
        {
            targets: 3,
            data: null,
            render: function ( data, type, row, meta ) {
                return `<div class="text-end" style="top:0;">
                            <i  data-id="${row.id}" class="fa fa-edit beditbtn"></i>
                            <i  data-id="${row.id}" class="fa fa-trash deletebtn"></i></div>
                        <div>`;
            }
        }
    ],
    buttons: [
        {
            text: '<i class="fa fa-plus" aria-hidden="true"></i>',
            action: function() {
                add_comment();
            }
        }
    ]
}, addfilter=true);


$(document).ready(function() {
    $('.dataTables_filter').addClass('w-100');
    $('.dataTables_filter input').addClass('filter-input').css('width', '96%');
    $('.dataTables_filter label').addClass('filter-label').css('width', '100%');
    $('.dataTables_paginate').removeClass('paging_full_numbers');
    $('.dataTables_paginate').addClass('paging_simple_numbers');
    $('#datatableelement').removeClass('dtr-inline');
});

$('#datatableelement tbody').on( 'click', 'i', function () {

    var action = this.className;
    var id = this.dataset.id;

    if (action==="fa fa-edit beditbtn") {
        edit_comment(id);
    } else if (action=="fa fa-trash deletebtn") {
        delete_comment(id);
    }

});

document.getElementById("form_name").textContent = procedure_info["name"];

$('.stepradio').on('change', function(e) {
    datatableelement.ajax.reload();
});
