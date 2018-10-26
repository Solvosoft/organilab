// GLOBAL VARS
// Django REST Framework
const coreapi = window.coreapi // Loaded by `coreapi.js`
const schema = window.schema // Loaded by `schema.js`
// Initialize a client
let auth = new coreapi.auth.SessionAuthentication({
    csrfCookieName: 'csrftoken',
    csrfHeaderName: 'X-CSRFToken'
})
let client = new coreapi.Client({
    auth: auth
})

var errors = new Array();
const object = "contact";
const tableId = "contacts";

// This functions is called when the document is ready
$(document).ready(function () {
    loadTable();
    defineErrors();
});

function defineErrors() {
    errors["404 Not Found"] = "The " + object + " has not been found and therefore has not been deleted";
}

function loadTable() {
    $('#' + tableId).DataTable({
        "ajax": {
            "url": '/printOrderManager/listContactByPrint',
            "data": { //Parameters send it in a POST
                "pk": printObjectId,
            }
        }, // Data sent with the delete request
        "destroy": true, // Allow reload table
        responsive: true,
        "fixedHeader": true,
        "language": {
            "url": "/get_dataset_translation"
        }
        /*"columnDefs": [{
            "width": "58%",
            "targets": 2
        }]
        "scrollY": 200,
        "scrollX": true*/
    });
}

function permissionsUser(printId, userId, permission) {
    $.ajax({
        url: "../giveDropPermissionsById", // Name of the method in views.py (the endpoint)
        data: { //Parameters send it in a POST
            pk: printId,
            userID: userId,
            permissionType: permission,
            action: $('#' + permission + userId).prop("checked"),
        }, // Data sent with the delete request
        success: function (json) { //If the result is success return a JSON value
            if (json.status == 0) { // Success
                $.notify({
                    // options
                    icon: getIcon(permission),
                    message: json.msg
                }, {
                    // settings
                    type: getTypeNotify($('#' + permission + userId).prop("checked")),
                    delay: 4500,
                    animate: {
                        enter: "animated fadeInUp",
                        exit: "animated fadeOutDown"
                    }
                });
            } else {
                if (json.status == 1) { // Warning
                    $.notify({
                        // options
                        icon: getIcon(permission),
                        message: json.msg
                    }, {
                        // settings
                        type: 'warning',
                        delay: 4500,
                        animate: {
                            enter: "animated fadeInUp",
                            exit: "animated fadeOutDown"
                        }
                    });
                    //alert(json.msg);
                } else { //Error
                    $.notify({
                        // options
                        icon: getIcon(permission),
                        message: json.msg
                    }, {
                        // settings
                        type: 'danger',
                        delay: 4500,
                        animate: {
                            enter: "animated fadeInUp",
                            exit: "animated fadeOutDown"
                        }
                    });
                    //alert(json.msg);
                }
            }
        },
        error: function (xhr, errmsg, err) { //If the result is an error return an error message
            console.log(xhr.status + ": " + xhr.responseText); // Provide a bit more info about the error to the console
        }
    });
}

function getIcon(permission) {
    if (permission == 'i') {
        return 'fas fa-info-circle';
    } else {
        if (permission == 'c') {
            return 'fas fa-users';
        } else {
            if (permission == 'p') {
                return 'fas fa-paper-plane';
            } else {
                if (permission == 's') {
                    return 'fas fa-calendar-alt';
                } else {
                    if (permission == 'a') {
                        return 'fas fa-bell';
                    }
                }

            }
        }
    }
}

function getTypeNotify(value) {
    if (value == true) {
        return 'info';
    } else {
        return 'success';
    }
}

function deleteContact(pkContact, userName) {
    swal({
        title: 'Are you sure?',
        text: "Once deleted, you will not be able to recover the " + object + " with the user name: " + userName,
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        // Interact with the API endpoint
        var action = ["contacts", "delete"]
        var params = {
            id: pkContact,
        }
        client.action(schema, action, params).then(function (result) {
            // Return value is in 'result'
            swal("Contact Deleted!", "The " + object + " with the user name " + userName + " was deleted successfully", "success");
            loadTable();
        }).catch(function (error) {
            swal("Contact Undeleted!", errors[error.message], "error");
            // Handle error case where eg. user provides incorrect credentials.
        })
    }, function (dismiss) {
        if (dismiss === 'cancel' || dismiss === 'close') {
            swal("Contact Undeleted!", "The " + object + " with the user name " + userName + " hasn't been deleted!", "info");
        }
    })


}