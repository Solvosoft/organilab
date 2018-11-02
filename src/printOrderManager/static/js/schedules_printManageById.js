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
const object = "schedule";
const tableId = "schedules";
var table = undefined;

// Values required to update a schedule
var formValues = new Array();


// Define the errors validation of the form

var errorsValidation = $('.createSchedule-card form');


// This functions is called when the document is ready


$(document).ready(function () {
    defineErrors();
    defineValues(0, "", "", "", "","","","");
    defineValidations();
    defineClockPicker();
    defineDisableKeyBoard();
    loadTable();
});


// This function disable the Key Board of the input with Clock Picker
function defineDisableKeyBoard() {
    $('#startTime').keypress(function (event) {
        event.preventDefault();
        return false;
    });
    $('#closeTime').keypress(function (event) {
        event.preventDefault();
        return false;
    });
}

// Define the errors for the contact page


function defineErrors() {
    errors["404 Not Found"] = "The " + object + " has not been found and therefore has not been deleted";
}

// Load the table


function loadTable() {
    if (table == undefined) {
        table = $('#' + tableId).DataTable({
            "ajax": {
                "url": '/printOrderManager/listScheduleByPrint',
                "data": { //Parameters send it in a POST
                    "pk": printObjectId,
                }
            }, // Data sent with the delete request
            responsive: true,
            "fixedHeader": true,
            "language": {
                "url": "/get_dataset_translation"
            },
            /*"scrollY": 200,
            "scrollX": true*/
        });
    } else {
        table.ajax.reload(null, false);
    }
}


// Function to delete a contact from a printObject


function deleteSchedule(pkSchedule, name) {
    swal({
        title: 'Are you sure?',
        text: "Once deleted, you will not be able to recover the " + object + " with the name: " + name,
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        // Interact with the API endpoint
        var action = ["schedule", "delete"]
        var params = {
            id: pkSchedule,
        }
        client.action(schema, action, params).then(function (result) {
            // Return value is in 'result'
            loadTable();
            swal("Schedule Deleted!", "The " + object + " with the name " + name + " was deleted successfully", "success");
        }).catch(function (error) {
            swal("Schedule Undeleted!", errors[error.message], "error");
            // Handle error case where eg. user provides incorrect credentials.
        })
    }, function (dismiss) {
        if (dismiss === 'cancel' || dismiss === 'close') {
            swal("Schedule Undeleted!", "The " + object + " with the name " + name + " hasn't been deleted!", "info");
        }
    })
}

// This function define the validations

function defineValidations() {
    errorsValidation.validate({
        rules: {
            nameSchedule: {
                required: true,
                maxlength: 255,
            },
            startTime: {
                required: true,
                maxlength: 255,
            },
            closeTime: {
                required: true,
                maxlength: 255,
            },
            stateSchedule: {
                required: true,
                maxlength: 15,
            },
            descriptionSchedule: {
                required: false,
                maxlength: 255,
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
    document.getElementById("updateScheduleForm").reset();
    var validations = errorsValidation.validate(); //Validate the form
    validations.resetForm(); // Reset the validations
    // Clean the colors
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


// This function inits the Clock Picker

function defineClockPicker() {
    $('.clockpicker').clockpicker({
        placement: 'top',
        align: 'left',
        donetext: 'Done',
        twelvehour: true, //Define the 12 Hour Clock
    });
}



// Define the values of the form

function defineValues(idSchedule, name, startTime, closeTime, startDay, closeDay, description, state) {
    formValues["idSchedule"] = idSchedule;
    formValues["name"] = name;
    formValues["startTime"] = startTime;
    formValues["closeTime"] = closeTime;
    formValues["startDay"] = startDay;
    formValues["closeDay"] = closeDay;
    formValues["description"] = description;
    formValues["state"] = state;
}


// Set the values to the form


function defineValuesForm(idSchedule, name, startTime, closeTime, startDay, closeDay, description, state) {
    cleanForm();
    defineValues(idSchedule, name, startTime, closeTime, startDay, closeDay, description, state);
    $('#nameSchedule').val(formValues["name"]);
    $('#stateSchedule').val(formValues["state"]);
    $('#descriptionSchedule').val(formValues["description"]);
    $('#startDay').val(formValues["startDay"]);
    $('#closeDay').val(formValues["closeDay"]);
    $('#startTime').val(formValues["startTime"]);
    $('#closeTime').val(formValues["closeTime"]);
}


// Update the schedule


function updateSchedule() {
    errorsValidation.validate(); //Validate the form
    if (errorsValidation.valid() == true) {
        //Reload the values
        defineValues(formValues["idSchedule"], $('#nameSchedule').val(), $('#startTime').val(), $('#closeTime').val(), $('#startDay').val(), $('#closeDay').val(), $('#descriptionSchedule').val(),  $('#stateSchedule').val());

        //Partial Update the schedule object with Django REST Framework
        // Interact with the API endpoint to update the schedule
        var action = ["schedule", "partial_update"]
        var params = {
            id: formValues["idSchedule"],
            name: formValues["name"],
            startTime: formValues["startTime"],
            closeTime: formValues["closeTime"],
            startDay: formValues["startDay"],
            closeDay: formValues["closeDay"],
            description: formValues["description"],
            state: formValues["state"],
        }
        client.action(schema, action, params).then(function(result) {
            // Return value is in 'result'
            swal("Schedule updated!", "The " + object + " was updated successfully", "success");
            loadTable();
        }).catch(function (error) {
            swal("Schedule not updated!", errors[error.message], "error");
            // Handle error case where eg. user provides incorrect credentials.
        })
        $("#closeModal").click(); //Close Modal
    }
}