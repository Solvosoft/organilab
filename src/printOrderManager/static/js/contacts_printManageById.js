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
var table = undefined;

// Values required to update a contact
var formValues = new Array();


// Define the errors validation of the form

var errorsValidation = $('.updateContact-card form');


// This functions is called when the document is ready


$(document).ready(function () {
    loadTable();
    defineErrors();
    defineValidations();
    defineValues(0, 0, "", "", "", "", 0);
});

// Define the errors for the contact page


function defineErrors() {
    errors["404 Not Found"] = "The " + object + " has not been found and therefore has not been deleted";
}

// Load the table


function loadTable() {
    if (table == undefined) {
        table = $('#' + tableId).DataTable({
            "ajax": {
                "url": '/printOrderManager/listContactByPrint',
                "data": { //Parameters send it in a POST
                    "pk": printObjectId,
                }
            }, // Data sent with the delete request
            responsive: true,
            "fixedHeader": true,
            "language": {
                "url": "/get_dataset_translation"
            },
            "columnDefs": [{
                "width": "30%",
                "targets": 3
            }]
            /*"scrollY": 200,
            "scrollX": true*/
        });
    } else {
        table.ajax.reload(null, false);
    }
}

// Set the permissions to an user


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

// Return the icon in accordance with the permission


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

// Return the notify in accordance with the value


function getTypeNotify(value) {
    if (value == true) {
        return 'info';
    } else {
        return 'success';
    }
}

// Function to delete a contact from a printObject


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
            loadTable();
            swal("Contact Deleted!", "The " + object + " with the user name " + userName + " was deleted successfully", "success");
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

// This function define the validations

function defineValidations() {
    /**
     * Custom validator for phone number
     */
    $.validator.addMethod("phoneNumberS", function (value, element) {
        return this.optional(element) || /^\+?1?\d{9,15}$/i.test(value); //Regex validation
    }, "Phone number must be entered in the format: '+55577777777'");

    errorsValidation.validate({
        rules: {
            userPhoneNumber: {
                required: false,
                maxlength: 15,
                phoneNumberS: true,
                //regex: "/^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])\w{6,}$/",
            },
        },
        errorElement: 'span',
        errorClass: 'help-block colorError',
        errorPlacement: function (error, element) {
            if (element.parent('.input-group').length) {
                error.insertAfter(element.parent());
            } else {
                error.insertAfter(element);
            }
        },
        highlight: function (element) {
            $(element).closest('.form-group, .has-feedback').removeClass('has-success').addClass('has-error');
        },

        unhighlight: function (element) {
            $(element).closest('.form-group, .has-feedback').removeClass('has-error').addClass('has-success');
        }
    });

}


// Clean the inputs of the form

function cleanForm() {
    $('#userPhoneNumber').val("");
    var validations = errorsValidation.validate(); //Validate the form
    validations.resetForm();
    $('.form-group').each(function () {
        $(this).removeClass('has-success');
    });
    $('.form-group').each(function () {
        $(this).removeClass('has-error');
    });
    $('.form-group').each(function () {
        $(this).removeClass('has-feedback');
    });
}


// Define the values of the form

function defineValues(printId, userId, userName, userFullName, userState, userPhone, contactId) {
    formValues["printId"] = printId;
    formValues["userId"] = userId;
    formValues["userName"] = userName;
    formValues["userFullName"] = userFullName;
    formValues["contactPhoneNumber"] = userPhone;
    formValues["contactState"] = userState;
    formValues["contactId"] = contactId;   
}


// Set the values to the form


function defineValuesForm(printId, userId, userName, userFullName, userState, userPhone, contactId) {
    cleanForm();
    defineValues(printId, userId, userName, userFullName, userState, userPhone, contactId);
    if (userFullName != " ") {
        $('#userId').text(userName + " : " + userFullName);
    } else {
        $('#userId').text(userName);
    }
    $('#userPhoneNumber').val(formValues["contactPhoneNumber"]);
    $('#stateContact').val(formValues["contactState"]);
}


// Update the contact


function updateContact() {
    errorsValidation.validate(); //Validate the form
    if (errorsValidation.valid() == true) {
        //Reload the values
        formValues["contactPhoneNumber"] = $('#userPhoneNumber').val();
        formValues["contactState"] = $('#stateContact').val();

        //Partial Update the contact object with Django REST Framework
        // Interact with the API endpoint to update the contact
        var action = ["contacts", "partial_update"]
        var params = {
            id: formValues["contactId"],
            phone: formValues["contactPhoneNumber"],
            state: formValues["contactState"],
        }
        client.action(schema, action, params).then(function (result) {
            // Return value is in 'result'
            swal("Contact updated!", "The " + object + " with the assigned user  " + formValues["userName"] + " was updated successfully", "success");
            loadTable();
        }).catch(function (error) {
            swal("Contact not updated!", errors[error.message], "error");
            // Handle error case where eg. user provides incorrect credentials.
        })
        $("#closeModal").click(); //Close Modal

    }
}