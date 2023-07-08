function delete_danger_indication(pk){
    let url = document.url_delete_danger_indication.replace('0', pk);
    Swal.fire({
    title: gettext("Delete danger indication"),
    text: gettext("Do you want to remove the danger indication?"),
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
                "X-CSRFToken": getCookie("csrftoken"),
            },
            success: (success) => {
                Swal.fire(
                    gettext("Successfully deleted"),
                    ).then(function(result) {
                        datatableelement.ajax.reload();
                    })
            },
            error: function( request, status, error ){
                Swal.fire({
                  icon: 'error',
                  title: gettext('Error'),
                  text: gettext('An error has occurred'),
                }).then(function(result) {
                datatableelement.ajax.reload();
                })
            }
        });
    }
    });
}
datatableelement=createDataTable('#dangerindicationtable', document.url_dangers_table, {
    columns: [
        {data: "code", name: "code", title: gettext("Code"), type: "string", visible: true},
        {data: "description", name: "description", title: gettext("Description"), type: "string", visible: true},
        {data: "warning_words", name: "warning_words", title: gettext("Warning Words"), type: "string", visible: true},
        {data: "actions", name:"actions", title: gettext("Actions"), type: "string", visible: true, sortable: false},
    ],
    buttons: [
        {
            text: '<i class="fa fa-plus" aria-hidden="true"></i> ' + gettext('Add'),
            className: 'btn btn-success',
            action: function (e, dt, node, config) {
                window.location.href = document.url_add_danger_indication;
            }
        }
    ],
    dom: "<'d-flex justify-content-between'<'m-2'l>" +
    "<'m-2'B><'m-2 d-flex justify-content-start'f>>" +
    "<'row'tr><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7 m-auto'p>>",
}, addfilter=false);
