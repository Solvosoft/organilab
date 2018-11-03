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
const object = "advertisement";


// Values required to register a contact

var formValues = new Array();


// Define the errors validation of the form

var errorsValidation = $('.createAdvertisement-card form');

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
            titleAdvertisement: {
                required: true,
                maxlength: 255,
            },
            descriptionAdvertisement: {
                required: true,
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


// Define the errors for the advertisement page


function defineErrors() {
    errors["404 Not Found"] = "The " + object + " has not been found and therefore has not been deleted";
}

// Define the values of the form

function defineValues(titleAdvertisement, typeAdvertisement, descriptionAdvertisement,stateAdvertisement) {
    formValues["titleAdvertisement"] = titleAdvertisement;
    formValues["typeAdvertisement"] = typeAdvertisement;
    formValues["descriptionAdvertisement"] = descriptionAdvertisement;
    formValues["idCreator"] = null;
    formValues["stateAdvertisement"] = stateAdvertisement;
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
    document.getElementById("createAdvertisementForm").reset();
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


// Save the advertisement of the form

function saveAdvertisement() {
    console.log($('#checkCreator').value);
    if ($('#checkCreator').is(":checked")){
        console.log("Checkeado ");
    }
    var advertisementCreatedId = 0 // Save the id of the advertisement created
    if (errorsValidation.valid() == true) {
        var usersNotifiedArray = new Array();
        usersNotifiedArray.push(userId);
        defineValues($('#titleAdvertisement').val(), $('#typeAdvertisement').val(), $('#descriptionAdvertisement').val(),$('#stateAdvertisement').val());
        if ($('#checkCreator').is(":checked")){
            formValues["idCreator"]= userId;
        }

        // Save the advertisement with Django REST Framework
        // Interact with the API endpoint to create an advertisement
        var action = ["advertisement", "create"]
        var params = {
            title: formValues["titleAdvertisement"],
            description: formValues["descriptionAdvertisement"],
            typeOfAdvertisement: formValues["typeAdvertisement"],
            state: formValues["stateAdvertisement"],
            usersNotified: usersNotifiedArray,
            creator: formValues["idCreator"],
        }
        client.action(schema, action, params).then(function(result) {
            // Return value is in 'result'
            advertisementCreatedId=result.id;

            // Interact with the API endpoint to read the print and get the paper types
            // When we get the advertisements we add the new id to the array with push 
            var action = ["printObject", "read"]
            var params = {
                id: printObjectId,
            }
            client.action(schema, action, params).then(function(result) {
                var scheduleIds = result.advertisements;
                scheduleIds.push(advertisementCreatedId);
                
                var action = ["printObject", "partial_update"]
                var params = {
                    id: printObjectId,
                    advertisements: scheduleIds,
                }
                client.action(schema, action, params).then(function(result) {
                    // Return value is in 'result'
                    swal("Advertisement created!", "The " + object + " was created successfully", "success");
                    cleanForm(0);
                }).catch(function (error) {
                    // Handle error case where eg. user provides incorrect credentials.
                    swal("Advertisement not created!", errors[error.message], "error");
                })
            }).catch(function (error) {
                swal("Advertisement not created!", errors[error.message], "error");
                // Handle error case where eg. user provides incorrect credentials.
            })
        }).catch(function (error) {
            swal("Advertisement not created!", errors[error.message], "error");
            // Handle error case where eg. user provides incorrect credentials.
        })
    }
}


// Method to update the advertisement and show a message

function updateAndDisplayAdvertisement(advertisementId,advertisementTitle,advertisementDescription,advertisementType){

}