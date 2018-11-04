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
const tableId = "paperTypes";
var table = undefined;

// Values required to update a contact
var formValues = new Array();


// Define the errors validation of the form

var errorsValidation = $('.updatePaperType-card form');


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
                "url": '/printOrderManager/listPaperTypesByPrint',
                "data": { //Parameters send it in a POST
                    "pk": printObjectId,
                }
            }, // Data sent with the delete request
            responsive: true,
            "fixedHeader": true,
            "language": {
                "url": "/get_dataset_translation"
            }
            /*"scrollY": 200,
            "scrollX": true*/
        });
    } else {
        table.ajax.reload(null, false);
    }
}


// Function to delete a contact from a printObject


function deletePaperType(idPaperType, namePaperType) {
    swal({
        title: 'Are you sure?',
        text: "Once deleted, you will not be able to recover the " + object + " with the name: " + namePaperType,
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        // Interact with the API endpoint to delete the paper type
        var action = ["paperType", "delete"]
        var params = {
            id: idPaperType,
        }
        client.action(schema, action, params).then(function (result) {
            // Return value is in 'result'
            loadTable();
            swal("Paper Type Deleted!", "The " + object + " with the name " + namePaperType + " was deleted successfully", "success");
        }).catch(function (error) {
            swal("Paper Type Undeleted!", errors[error.message], "error");
            // Handle error case where eg. user provides incorrect credentials.
        })
    }, function (dismiss) {
        if (dismiss === 'cancel' || dismiss === 'close') {
            swal("Paper Type Undeleted!", "The " + object + " with the name " + namePaperType + " hasn't been deleted!", "info");
        }
    })
}

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


// Clean the inputs of the form

function cleanForm() {
    document.getElementById("updatePaperTypeForm").reset();
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


// Define the values of the form

function defineValues(id, name, grams, availability, description, unitSize, longSize, widthSize) {
    formValues["id"] = id;
    formValues["name"] = name;
    formValues["grams"] = grams;
    formValues["availability"] = availability;
    formValues["description"] = description;
    formValues["unitSize"] = unitSize;
    formValues["longSize"] = longSize;
    formValues["widthSize"] = widthSize;
}


// Set the values to the form


function defineValuesForm(id, name, grams, availability, description, unitSize, longSize, widthSize) {
    cleanForm();
    defineValues(id, name, grams, availability, description, unitSize, longSize, widthSize);
    $('#namePaperType').val(formValues["name"]);
    $('#gramsPaperType').val(formValues["grams"]);
    $('#availablePaper').val(formValues["availability"]);
    $('#descriptionPaperType').val(formValues["description"]);
    $('#unitSize').val(formValues["unitSize"]);
    $('#longSize').val(formValues["longSize"]);
    $('#widthSize').val(formValues["widthSize"]);
}


// Update the paper type


function updatePaperType() {
    errorsValidation.validate(); //Validate the form
    if (errorsValidation.valid() == true) {
        //Reload the values
        formValues["name"] = $('#namePaperType').val();
        formValues["grams"] = $('#gramsPaperType').val();
        formValues["availability"] = $('#availablePaper').val();
        formValues["description"] = $('#descriptionPaperType').val();
        formValues["unitSize"] = $('#unitSize').val();
        formValues["longSize"] = $('#longSize').val();
        formValues["widthSize"] = $('#widthSize').val();

        // Partial Update the paper type with Django REST Framework
        // Interact with the API endpoint to update the paper type
        var action = ["paperType", "partial_update"]
        var params = {
            id: formValues["id"],
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
            swal("Paper type updated!", "The " + object + " with the name  " + formValues["name"] + " was updated successfully", "success");
            loadTable();
        }).catch(function (error) {
            swal("Paper type not updated!", errors[error.message], "error");
            // Handle error case where eg. user provides incorrect credentials.
        })
        $("#closeModal").click(); //Close Modal
    }
}