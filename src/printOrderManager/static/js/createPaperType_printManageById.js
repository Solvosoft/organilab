/*

Created by Luis Felipe Castro Sanchez
Universidad Nacional de Costa Rica 
Practica Profesional Supervisada (Julio - Noviembre 2018)
GitHub User luisfelipe7

*/

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
const object = "paper type";


// Values required to register a contact

var formValues = new Array();


// Define the errors validation of the form

var errorsValidation = $('.createPaperType-card form');

// This functions is called when the document is ready


$(document).ready(function () {
    defineErrors();
    defineValues("", 0, "", "", 0, 0, 0);
    defineValidations();
});


// This function define the validations

function defineValidations() {
    errorsValidation.validate({
        rules: {
            namePaperType: {
                required: true,
                maxlength: 255,
            },
            gramsPaperType: {
                required: true,
                maxlength: 10,
                number: true,
            },
            availablePaper: {
                required: true,
                maxlength: 15,
            },
            descriptionPaperType: {
                required: true,
                maxlength: 255,
            },
            unitSize: {
                required: true,
                maxlength: 25,
            },
            longSize: {
                required: true,
                maxlength: 10,
                number: true,
            },
            widthSize: {
                required: true,
                maxlength: 10,
                number: true,
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

function defineValues(name, grams, availability, description, unitSize, longSize, widthSize) {
    formValues["name"] = name;
    formValues["grams"] = grams;
    formValues["availability"] = availability;
    formValues["description"] = description;
    formValues["unitSize"] = unitSize;
    formValues["longSize"] = longSize;
    formValues["widthSize"] = widthSize;
}

// Ask and then clean the inputs of the form

function cleanForm(type) {
    if(type == 1){ //Ask to clean the form if the user press reset
        askCleanForm();
    }else{
        cleanTheForm();
    }
}


// Ask to clean the form 


function askCleanForm(){
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


function cleanTheForm(){
    document.getElementById("createPaperTypeForm").reset();
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

function savePaperType() {
    errorsValidation.validate(); //Validate the form
    var paperTypeCreatedId = 0 // Save the id of the papaer type created
    if (errorsValidation.valid() == true) {
        defineValues($('#namePaperType').val(), $('#gramsPaperType').val(), $('#availablePaper').val(), $('#descriptionPaperType').val(), $('#unitSize').val(), $('#longSize').val(), $('#widthSize').val());

        // Save the paper type with Django REST Framework
        // Interact with the API endpoint to create a paper type
        var action = ["paperType", "create"]
        var params = {
            unit_size: formValues["unitSize"],
            widthSize: formValues["widthSize"],
            longSize: formValues["longSize"],
            name: formValues["name"],
            grams: formValues["grams"],
            available: formValues["availability"],
            description: formValues["description"],
        }
        client.action(schema, action, params).then(function (result) {
            // Return value is in 'result'
            paperTypeCreatedId = result.id

            // Interact with the API endpoint to read the print and get the paper types
            // When we get the paper type we add the new id to the array with push 
            var action = ["printObject", "read"]
            var params = {
                id: printObjectId,
            }
            client.action(schema, action, params).then(function(result) {
                var paperTypesIds = result.paperType;
                paperTypesIds.push(paperTypeCreatedId);
                
                var action = ["printObject", "partial_update"]
                var params = {
                    id: printObjectId,
                    paperType: paperTypesIds,
                }
                client.action(schema, action, params).then(function(result) {
                    // Return value is in 'result'
                    swal("Paper Type created!", "The " + object + " was created successfully", "success");
                    cleanForm(0);
                }).catch(function (error) {
                    // Handle error case where eg. user provides incorrect credentials.
                    swal("Paper Type not created!", errors[error.message], "error");
                })
            }).catch(function (error) {
                swal("Paper Type not created!", errors[error.message], "error");
                // Handle error case where eg. user provides incorrect credentials.
            })
        }).catch(function (error) {
            swal("Paper Type not created!", errors[error.message], "error");
            // Handle error case where eg. user provides incorrect credentials.
        })
    }
}