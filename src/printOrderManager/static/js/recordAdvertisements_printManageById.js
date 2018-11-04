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
const tableId = "advertisements";
var table = undefined;


// This functions is called when the document is ready


$(document).ready(function () {
    defineErrors();
    loadTable();
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
                "url": '/printOrderManager/list_AdvertisementsByPrint',
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


// Method to view the notification

function viewNotification(title, description, logo, creator) {
    if(creator != "")
        creator = "Created by"+creator;

    swal.queue([{
        imageUrl: 'http://localhost:8000/media/'+logo,
        imageWidth: 90,
        imageHeight: 90,
        title: title,
        confirmButtonText: 'OK',
        cancelButtonText: 'Close',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        text: description +" ."+creator,
        preConfirm: () => {
            swal.close();
        },
    }]).catch(swal.noop);


}











