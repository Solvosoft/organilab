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


// Values required to register a schedule

var formValues = new Array();


// Define the errors validation of the form

var errorsValidation = $('.createSchedule-card form');

// This functions is called when the document is ready


$(document).ready(function () {
    defineErrors();
    defineValues("", 0, "", "", 0, 0, 0);
    defineValidations();
    defineClockPicker();
    defineDisableKeyBoard();
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

// This function inits the Clock Picker

function defineClockPicker() {
    $('.clockpicker').clockpicker({
        placement: 'top',
        align: 'left',
        donetext: 'Done',
        twelvehour: true, //Define the 12 Hour Clock
    });
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


// Define the errors for the contact page


function defineErrors() {
    errors["404 Not Found"] = "The " + object + " has not been found and therefore has not been deleted";
}

// Define the values of the form

function defineValues(nameSchedule, stateSchedule, descriptionSchedule, startDay, closeDay, startTime, closeTime) {
    formValues["nameSchedule"] = nameSchedule;
    formValues["stateSchedule"] = stateSchedule;
    formValues["descriptionSchedule"] = descriptionSchedule;
    formValues["startDay"] = startDay;
    formValues["closeDay"] = closeDay;
    formValues["startTime"] = startTime;
    formValues["closeTime"] = closeTime;
}

// Ask and then clean the inputs of the form

function cleanForm(type) {
    if (type == 1) { //Ask to clean the form if the user press reset
        askCleanForm();
    } else {
        cleanTheForm();
    }
}


// Ask to clean the form 


function askCleanForm() {
    swal({
        title: 'Are you sure?',
        text: "Once reset, you will not be able to recover the data",
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, reset it!'
    }).then((result) => {
        swal("Form reseted!", "The form was reset sucessfully", "success");
        cleanTheForm();
    }, function (dismiss) {
        if (dismiss === 'cancel' || dismiss === 'close') {
            swal("Form not reseted!", "The form hasn't been reseted!", "info");
        }
    })
}


// Clean the inputs of the form


function cleanTheForm() {
    document.getElementById("createScheduleForm").reset();
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


// Save the contact of the form

function saveSchedule() {
    errorsValidation.validate(); //Validate the form
    scheduleCreatedId = 0;
    if (errorsValidation.valid() == true) {
        defineValues($('#nameSchedule').val(), $('#stateSchedule').val(), $('#descriptionSchedule').val(), $('#startDay').val(), $('#closeDay').val(), $('#startTime').val(), $('#closeTime').val());

        // Save the schedule  with Django REST Framework
        // Interact with the API endpoint to create a schedule
        var action = ["schedule", "create"]
        var params = {
            name: formValues["nameSchedule"] ,
            startTime: formValues["startTime"],
            closeTime: formValues["closeTime"],
            startDay: formValues["startDay"],
            closeDay: formValues["closeDay"],
            description: formValues["descriptionSchedule"],
            state: formValues["stateSchedule"],
        }
        client.action(schema, action, params).then(function (result) {
            // Return value is in 'result'
            scheduleCreatedId = result.id

            // Interact with the API endpoint to read the print and get the paper types
            // When we get the paper type we add the new id to the array with push 
            var action = ["printObject", "read"]
            var params = {
                id: printObjectId,
            }
            client.action(schema, action, params).then(function (result) {
                var schedulesIds = result.schedules;
                schedulesIds.push(scheduleCreatedId);

                var action = ["printObject", "partial_update"]
                var params = {
                    id: printObjectId,
                    schedules: schedulesIds,
                }
                client.action(schema, action, params).then(function (result) {
                    // Return value is in 'result'
                    swal("Schedule created!", "The " + object + " was created successfully", "success");
                    cleanForm(0);
                }).catch(function (error) {
                    // Handle error case where eg. user provides incorrect credentials.
                    swal("Schedule not created!", errors[error.message], "error");
                })
            }).catch(function (error) {
                swal("Schedule not created!", errors[error.message], "error");
                // Handle error case where eg. user provides incorrect credentials.
            })
        }).catch(function (error) {
            swal("Schedule not created!", errors[error.message], "error");
            // Handle error case where eg. user provides incorrect credentials.
        })
    }
}