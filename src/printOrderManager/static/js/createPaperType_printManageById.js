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
    defineValues("",0,"","",0,0,0);
    defineValidations();
});


// This function define the validations

function defineValidations() {
    /**
     * Custom validator for phone number
     */

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


// Save the contact of the form

function savePaperType() {
    errorsValidation.validate(); //Validate the form
    if (errorsValidation.valid() == true) {

    }
}