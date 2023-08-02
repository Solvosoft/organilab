var formmodal = BaseFormModal('#recipientmodal', {});
var request_url = document.urls["add"];
var request_type = "POST";
var add_title = gettext("Added");
formmodal.addBtnForm = function(instance) {

    return function(event) {
        form = instance.form
        let url = request_url;
        request_url = document.urls["add"];
        $.ajax({
            url: url,
            type: request_type,
            dataType: "json",
            data: convertToStringJson(form, prefix=instance.prefix, extras=instance.data_extras),
            headers: {
                    'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': "application/json",
            },
            success: (success) => {
                formmodal.hidemodal();
                Swal.fire({
                    icon: 'success',
                    title: add_title,
                    text: gettext("Saved successfully"),
                }).then(function() {
                    datatableelement.ajax.reload();
                });
            },
            error: function(xhr, resp, text){
                    var errors = xhr.responseJSON.errors;
                    if(errors){
                        form.find('ul.form_errors').remove();
                        form_field_errors(form, errors, instance.prefix);
                    }else{
                        let error_msg = gettext('There was a problem performing your request. Please try again later or contact the administrator.');  // any other error
                        if(xhr.responseJSON.detail){
                            error_msg = xhr.responseJSON.detail;
                        }
                        Swal.fire({
                           icon: 'error',
                           title: gettext('Error'),
                           text: error_msg
                        });
                        }
                        instance.error(instance, xhr, resp, text);
                    }
        });
    }
}

formmodal.init(this);



function add_recipient_size() {
    formmodal.showmodal();
    request_type = "POST";
    add_title = gettext("Added");
}

function edit_recipient_size(pk){

    let url = document.urls["get"];
    let update_url = document.urls['update']
    url = url.replace('0',pk)
    request_url = update_url.replace('0',pk)
    request_type = "PUT";
    $.ajax({
    url: url,
        type: "GET",
        dataType: "json",
        headers: {
                  'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': "application/json",
        },
        success: (success) => {
            formmodal.showmodal();
            $("#id_name").val(success.name);
            $("#id_height").val(success.height);
            $("#id_width").val(success.width);
            $("#id_height_unit").val(success.height_unit).change();
            $("#id_width_unit").val(success.width_unit).change();
            add_title = gettext("Updated");
        },
        error: function(xhr, resp, text){
                    var errors = xhr.responseJSON.errors;
                    let form = $('#recipientmodalform')

                    if(errors){
                        form.find('ul.form_errors').remove();
                        form_field_errors(form, errors, instance.prefix);
                    }else{
                        let error_msg = gettext('There was a problem performing your request. Please try again later or contact the administrator.');
                        if(xhr.responseJSON.detail){
                            error_msg = xhr.responseJSON.detail;
                        }
                        Swal.fire({
                           icon: 'error',
                           title: gettext('Error'),
                           text: error_msg
                        });
                        }
                        instance.error(instance, xhr, resp, text);
      }
    });
}

function delete_recipient_size(pk){
    let url = document.urls['delete'];
    Swal.fire({
    title: gettext("Delete recipient size"),
    text: gettext("Do you want to remove the recipient?"),
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
                    'X-CSRFToken': getCookie('csrftoken'),
            },
            data:{'pk':pk},
            success: (success) => {
                Swal.fire({
                   icon: 'success',
                   title: gettext("Deleted!"),
                   text:gettext("Successfully deleted")
                   }).then(function(result) {
                    datatableelement.ajax.reload();
                })
            },
            error: function(xhr, resp, text){
                    var errors = xhr.responseJSON.errors;
                    console.log(xhr.responseJSON)
                    if(errors){
                        Swal.fire({
                           icon: 'error',
                           title: gettext('Error'),
                           text: errors
                        });
                    }else{
                        let error_msg = gettext('There was a problem performing your request. Please try again later or contact the administrator.');
                    }
            }
        });
    }
    });
}

datatableelement=createDataTable('#recipienttable', document.urls["table_url"], {
    columns: [
        {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
        {data: "height", name: "height", title: gettext("Height"), type: "string", visible: true},
        {data: "height_unit", name: "height_unit", title: gettext("Height Unit"), type: "string", visible: true},
        {data: "width", name: "width", title: gettext("Width"), type: "string", visible: true},
        {data: "width_unit", name: "width_unit", title: gettext("Width Unit"), type: "string", visible: true},
        {data: "actions", name: "actions", title: gettext('Actions'), type: "string", visible: true, sortable: false, filterable: false}
    ],
    buttons: [
        {
            text: '<i class="fa fa-plus" aria-hidden="true"></i> ' + gettext('Add'),
            action: function() {
                add_recipient_size();
            },
            className: 'btn btn-success'
        }
    ],
    dom: "<'d-flex justify-content-between'<'m-2'l>" +
    "<'m-2'B><'m-2 d-flex justify-content-start'f>>" +
    "<'row'tr><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7 m-auto'p>>",
}, addfilter=false);

