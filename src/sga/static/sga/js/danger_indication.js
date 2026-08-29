function delete_danger_indication(pk){
    let url = document.url_delete_danger_indication.replace('/0/', '/' + pk + '/');
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
var datatableConfig = {
    columns: [
        {data: "code", name: "code", title: gettext("Code"), type: "string", visible: true},
        {data: "description", name: "description", title: gettext("Description"), type: "string", visible: true},
        {data: "warning_words", name: "warning_words", title: gettext("Warning Words"), type: "string", visible: true},
        {data: "actions", name:"actions", title: gettext("Actions"), type: "string", visible: true, sortable: false},
    ],
    layout: {
        topStart: 'pageLength',
        top: 'buttons',
        topEnd: 'search',
        bottomStart: 'info',
        bottomEnd: 'paging'
    },
};

if (has_perm) {
    datatableConfig.buttons = [
        {
            text: '<i class="fa fa-plus" aria-hidden="true"></i> ' + gettext('Add'),
            className: 'btn btn-success',
            action: function (e, dt, node, config) {
                window.location.href = document.url_add_danger_indication;
            }
        }
    ];
}

datatableelement=createDataTable('#dangerindicationtable', document.url_dangers_table, datatableConfig, addfilter=false);

