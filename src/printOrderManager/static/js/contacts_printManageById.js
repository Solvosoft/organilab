// This functions is called when the document is ready
// This functions is called when the document is ready
$(document).ready(function () {
    console.log("Valor de id ");

});

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