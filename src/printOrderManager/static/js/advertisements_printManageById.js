/*

Created by Luis Felipe Castro Sanchez
Universidad Nacional de Costa Rica 
Practica Profesional Supervisada (Julio - Noviembre 2018)
GitHub User luisfelipe7

*/


// GLOBAL VARS

// Django REST Framework
var advertisementToUpdateId = 0;


// Method to show the notification

function updateAndDisplayAdvertisement(advertisementId, advertisementTitle, advertisementDescription, advertisementType, advertisementCreator, printObjectIcon) {
    advertisementToUpdateId = advertisementId;
    var advertisementCreatorText = "";
    if (advertisementCreator != "None") {
        advertisementCreatorText = ". Created by " + advertisementCreator;
    }

    swal.queue([{
        imageUrl: 'http://localhost:8000/media/'+printObjectIcon,
        imageWidth: 90,
        imageHeight: 90,
        title: advertisementTitle,
        confirmButtonText: 'Mark as read it',
        cancelButtonText: 'Close',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        text: advertisementDescription + advertisementCreatorText,
        showLoaderOnConfirm: true,
        preConfirm: () => {
            markAsRead();
        },
    }]).catch(swal.noop);
}


// Method to mark as read it the notification

function markAsRead() {
    var usersNotifiedAdvertisement = new Array();

    // Interact with the API endpoint to get the users notified
    // To update the advertisement 
    var action = ["advertisement", "read"]
    var params = {
        id: advertisementToUpdateId,
    }
    client.action(schema, action, params).then(function(result) {
        // Return value is in 'result'
        usersNotifiedAdvertisement = result.usersNotified;
        usersNotifiedAdvertisement.push(userId);

        // Interact with the API endpoint to update the advertisement
        var action = ["advertisement", "partial_update"]
        var params = {
            id: advertisementToUpdateId,
            usersNotified: usersNotifiedAdvertisement,
        }
        client.action(schema, action, params).then(function(result) {
            location.reload();
        }, function (dismiss) {
            if (dismiss === 'cancel' || dismiss === 'close') {
                // ERROR
            }
        })
    }, function (dismiss) {
        if (dismiss === 'cancel' || dismiss === 'close') {
            // ERROR
        }
    })

}