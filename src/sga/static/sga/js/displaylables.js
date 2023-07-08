function create_displaylabel(){
    window.location.href=document.urls.substance_create;
}
function objShowBool(data, type, row, meta){ return data ? '<i class="fa fa-check-circle" title="' + data + '">': '<i class="fa fa-times-circle" title="' +  data + '">'; };

function displaylabel_delete(obj, text) {
    let message = gettext("Are you sure you want to delete")
    message = `${message} "${text}"?`
    let url = document.urls.substance_delete.replace('/0/', '/'+obj+'/');
    Swal.fire({ //Confirmation for delete
        icon: "warning",
        title: gettext("Are you sure?"),
        text: message,
        confirmButtonText: gettext("Confirm"),
        showCloseButton: true,
        denyButtonText: gettext('Cancel'),
        showDenyButton: true,
        })
        .then(function(result) {
            if (result.isConfirmed) {
                fetch(url, {
                    method: "delete",
                    headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'}
                    }
                    ).then(response => {
                        if(response.ok){ return response.json(); }
                        return Promise.reject(response);  // then it will go to the catch if it is an error code
                    })
                    .then(data => {
                        Swal.fire({
                            title: gettext('Success'),
                            text: data['detail'],
                            icon: 'success',
                            timer: 1500
                        });
                        datatableelement.ajax.reload();
                    })
                    .catch(response => {
                        let error_msg = gettext('There was a problem performing your request. Please try again later or contact the administrator.');  // any other error
                        response.json().then(data => {  // there was something in the response from the API regarding validation
                            if(data['substance']){
                                error_msg = data['substance'][0];  // specific api validation errors
                            }
                        })
                        .finally(() => {
                            Swal.fire({
                                title: gettext('Error'),
                                text: error_msg,
                                icon: 'error'
                            });
                        });
                    });
            }
        });
}
datatableelement=createDataTable("#substance_table", document.urls.displaylabel_table_url, {
        columns: [
            {data: "pk", name: "pk", title: gettext("Id"), type: "string", visible: false},
            {data: "creation_date", name: "creation_date", title: gettext("Creation Date"), type: "date",  render: DataTable.render.datetime(), visible: true},
            {data: "created_by", name: "created_by", title: gettext("User"), type: "string", visible: true},
            {data: "comercial_name", name: "comercial_name", title: gettext("Comercial Name"), type: "string", visible: true },
            {data: "agrochemical", name: "agrochemical", title: gettext("Agrochemical"), type: "boolean", render: objShowBool, visible: true},
            {data: "uipa_name", name: "uipa_name", title: gettext("UIPA Name"), type: "string", visible: true},
            {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true, filterable: false, sortable: false},
        ],
        buttons: [
            {
                action: create_displaylabel,
                text: '<i class="fa fa-plus" aria-hidden="true"></i> '+gettext('Create Substance'),
                titleAttr: gettext('Create Substance'),
                className: 'btn-sm btn-success ml-4',
            },
        ],
        dom: "<'d-flex justify-content-between'<'m-2'l>" +
        "<'m-2'B><'m-2 d-flex justify-content-start'f>>" +
        "<'row'tr><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7 m-auto'p>>",
        ajax: {
            url: document.urls.displaylabel_table_url,
            type: 'GET',
            data: function(dataTableParams, settings) {
                var data= formatDataTableParams(dataTableParams, settings);
                data['organization'] = $('#id_organization').val();
                return data;
            }
        }
    }, addfilter=false);
