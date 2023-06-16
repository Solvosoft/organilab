$(document).ready(function() {
datatableelement=createDataTable('#my_procedures', document.myProcedure, {
        columns: [
            {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
            {data: "custom_procedure", name: "custom_procedure__title", title: gettext("Template"), type: "string", visible: true},
            {data: "created_by", name: "created_by", title: gettext("Creator"), type: "string", visible: true},
            {data: "status", name: "status", title: gettext("Status"), type: "string", visible: true},
            {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true, filterable: false, sortable: false}
        ],
     dom: "<'d-flex justify-content-between'<'m-2'l>" +
        "<'m-2 d-flex justify-content-start'f>>" +
        "<'row'tr><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7 m-auto'p>>",
        ajax: {
           url: document.myProcedure,
           type: 'GET',
           data: function(dataTableParams, settings) {
               var data= formatDataTableParams(dataTableParams, settings);
               return data;
           }
       }
    },
    addfilter=false);
        });

function delete_my_procedure(pk){
    let url = document.removeProcedure.replace('0', pk);
    Swal.fire({
    title: gettext("Delete procedure"),
    text: gettext("Do you want to remove the procedure?"),
    icon: "error",
    confirmButtonText: gettext("Yes"),
    denyButtonText: gettext("No"),
    showDenyButton: true,
    showCloseButton: true
    }).then((result) => {
    if (result.isConfirmed) {
        $.ajax({
            url: url,
            type: "POST",
            data: {},
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            success: (success) => {
                Swal.fire(
                   gettext("Successfully deleted"),
                ).then(function(result) {
                    location.reload();
                })
            },
        });
    }
    });
}