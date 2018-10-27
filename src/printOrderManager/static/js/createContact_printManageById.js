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
const tableId = "users";



// Values required to register a contact

var formValues = new Array();


// This functions is called when the document is ready


$(document).ready(function () {
    loadTable();
    defineErrors();
    defineFormValues(0, 0, "", "");

    $('.tooltip-demo').tooltip({
        selector: "[data-toggle=tooltip]",
        container: "body"
    })

    $("[data-toggle=popover]")
        .popover()
});

// Define the errors for the contact page


function defineErrors() {
    errors["404 Not Found"] = "The " + object + " has not been found and therefore has not been deleted";
}

// Define the values of the form

function defineFormValues(printId, userId, userName, userFullName) {
    formValues["printId"] = printId;
    formValues["userId"] = userId;
    formValues["userName"] = userName;
    formValues["userFullName"] = userFullName;
    formValues["contactPhoneNumber"] = 0;
    formValues["contactState"] = 0;
}

// Load the table


function loadTable() {
    $('#' + tableId).DataTable({
        "ajax": {
            "url": '/printOrderManager/list_usersNotRelatedToPrint',
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

// Set the values to the form

function defineValuesForm(printId, userId, userName, userFullName) {
    defineFormValues(printId, userId, userName, userFullName);
    if (userFullName != " ") {
        $('#userId').text(userName + " : " + userFullName);
    } else {
        $('#userId').text(userName);
    }
    //$('#userPhoneNumber').val('FFFFFF');
}

// Save the contact of the form

function saveContact() {
    var idSavedContact = 0;
    if (true) {
        //Reload the values
        formValues["contactPhoneNumber"] = $('#userPhoneNumber').val();
        formValues["contactState"] = $('#stateContact').val();

        //Save the contact with Django REST Framework
        // Interact with the API endpoint to create a contact
        var action = ["contacts", "create"]
        var params = {
            phone: formValues["contactPhoneNumber"],
            assigned_user: formValues["userId"],
            state: formValues["contactState"],
        }
        client.action(schema, action, params).then(function (result) {
            // Return value is in 'result'
            idSavedContact = result.id;

            //Read the print object with Django REST Framework
            // Interact with the API endpoint to read the contacts of the print
            var action = ["printObject", "read"]
            var params = {
                id: formValues["printId"],
            }
            client.action(schema, action, params).then(function (result) {
                // Return value is in 'result'
                var printContacts = result.contacts;
                printContacts.push(idSavedContact);

                //Partial update the print object with Django REST Framework
                // Interact with the API endpoint to partial update the contact
                var action = ["printObject", "partial_update"]
                var params = {
                    id: formValues["printId"],
                    contacts: printContacts,
                }
                client.action(schema, action, params).then(function (result) {
                    swal("Contact added!", "The " + object + " with the user  " + formValues["userName"] + " was added successfully", "success");
                    loadTable();
                })

            }).catch(function (error) {
                swal("Contact not added!", errors[error.message], "error");
                // Handle error case where eg. user provides incorrect credentials.
            })

        }).catch(function (error) {
            swal("Contact not added!", errors[error.message], "error");
            // Handle error case where eg. user provides incorrect credentials.
        })
        $("#closeModal").click(); //Close Modal
    }
}