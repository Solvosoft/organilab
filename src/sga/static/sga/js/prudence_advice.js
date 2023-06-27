var formmodal = BaseFormModal('#prudenceadvicemodal', {});
var request_url = document.url_add_prudence_advice;
var request_type = "POST";
var success_title = gettext("Added");

formmodal.addBtnForm = function(instance) {

    return function(event) {
        var dataAsString = convertToStringJson(instance.form, prefix=instance.prefix, extras=instance.data_extras);
        var dataAsJson = JSON.parse(dataAsString);
        let url = request_url;
        request_url = document.url_add_prudence_advice;

        $.ajax({
            url: url,
            type: request_type,
            dataType: "json",
            data: {'code': dataAsJson.code, 'name': dataAsJson.name, 'prudence_advice_help': dataAsJson.prudence_advice_help},
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
            },
            success: (success) => {
                formmodal.hidemodal();
                Swal.fire({
                    icon: 'success',
                    title: success_title,
                    text: gettext("Saved successfully"),
                }).then(function() {
                    datatableelement.ajax.reload();
                });
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
}

formmodal.init(this);

function add_prudence_advice() {
    formmodal.showmodal();
    document.getElementById("id_code").value = "";
    document.getElementById("id_name").value = "";
    document.getElementById("id_prudence_advice_help").value = "";
    request_type = "POST";
    success_title = gettext("Added");
}

function edit_prudence_advice(pk) {
    localStorage.setItem('prudenceadvice', pk);
    let url = document.url_get_prudence_advice.replace('0', pk);
    request_url = document.url_update_prudence_advice.replace('0', pk);
    request_type = "PUT";
    $.ajax({
        url: url,
        type: "GET",
        dataType: "json",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
        },
        success: (success) => {
            formmodal.showmodal();
            document.getElementById("id_code").value = success.code;
            document.getElementById("id_name").value = success.name;
            document.getElementById("id_prudence_advice_help").value = success.prudence_advice_help;
            success_title = gettext("Updated");
        }
    });
}

function delete_prudence_advice(pk) {
    let url = document.url_delete_prudence_advice.replace('0', pk);
    Swal.fire({
    title: gettext("Delete prudence advice"),
    text: gettext("Do you want to remove the prudence advice?"),
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

datatableelement=createDataTable('#prudenceadvicetable', document.url_advices_table, {
    columns: [
        {data: "code", name: "code", title: gettext("Code"), type: "string", visible: true},
        {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
        {data: "prudence_advice_help", name: "prudence_advice_help", title: gettext("Help message"), defaultContent:gettext("Unknown"), type: "string", visible: true},
        {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true, sortable: false}
    ],
    buttons: [
        {
            text: '<i class="fa fa-plus" aria-hidden="true"></i> ' + gettext('Add'),
            action: function() {
                add_prudence_advice();
            },
            className: 'btn btn-success'
        }
    ],
    dom: "<'d-flex justify-content-between'<'m-2'l>" +
    "<'m-2'B><'m-2 d-flex justify-content-start'f>>" +
    "<'row'tr><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7 m-auto'p>>",
}, addfilter=false);
