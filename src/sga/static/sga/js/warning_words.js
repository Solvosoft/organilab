var formmodal = BaseFormModal('#warningwordmodal', {});
var request_url = document.url_add_warning_word;
var request_type = "POST";
var add_title = gettext("Added");

formmodal.addBtnForm = function(instance) {

    return function(event) {
        var dataAsString = convertToStringJson(instance.form, prefix=instance.prefix, extras=instance.data_extras);
        var dataAsJson = JSON.parse(dataAsString);
        let url = request_url;
        request_url = document.url_add_warning_word;

        $.ajax({
            url: url,
            type: request_type,
            dataType: "json",
            data: {'name': dataAsJson.name, 'weigth': dataAsJson.weigth},
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
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
        });
    }
}

formmodal.init(this);



function add_warning_word() {
    formmodal.showmodal();
    document.getElementById("id_name").value = "";
    document.getElementById("id_weigth").value = "";
    request_type = "POST";
    add_title = gettext("Added");
}

function edit_warning_word(pk){
    localStorage.setItem('warningword', pk);
    let url = document.url_get_warning_word.replace('0', pk);
    request_url = document.url_update_warning_word.replace('0', pk)
    request_type = "PUT";
    $.ajax({
    url: url,
        type: "GET",
        dataType: "json",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        success: (success) => {
            formmodal.showmodal();
            document.getElementById("id_name").value = success.name;
            document.getElementById("id_weigth").value = success.weigth;
            add_title = gettext("Updated");
        }
    });
}

function delete_warning_word(pk){
    let url = document.url_delete_warning_word.replace('0', pk);
    Swal.fire({
    title: gettext("Delete warning word"),
    text: gettext("Do you want to remove the warning word?"),
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
                "Content-Type": "application/json",
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

datatableelement=createDataTable('#warningwordtable', document.url_warnings_table, {
    columns: [
        {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
        {data: "weigth", name: "weigth", title: gettext("Weight"), type: "string", visible: true},
        {data: "actions", name: "actions", title: gettext('Actions'), type: "string", visible: true, sortable: false, filterable: false}
    ],
    buttons: [
        {
            text: '<i class="fa fa-plus" aria-hidden="true"></i> ' + gettext('Add'),
            action: function() {
                add_warning_word();
            },
            className: 'btn btn-success'
        }
    ],
    dom: "<'d-flex justify-content-between'<'m-2'l>" +
    "<'m-2'B><'m-2 d-flex justify-content-start'f>>" +
    "<'row'tr><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7 m-auto'p>>",
}, addfilter=false);

