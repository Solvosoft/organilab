// GLOBAL VARS
const tableId = "printObjects";

// This functions is called when the document is ready
$(document).ready(function () {
    // Get each element from a li with the id=messages
    loadTable();
    $("#messages li").each(function (index) {
        swal("Print registered!", $(this).text(), "success");
    });
});


function loadTable() {
    $('#' + tableId).DataTable({
        "ajax": '/printOrderManager/list_printObject',
        "destroy": true, // Allow reload table
        responsive: true,
        "fixedHeader": true,
        "language": {
            "url": "/get_dataset_translation"
        }
    });
    //table.buttons().container().appendTo($('.col-sm-6:eq(0)', table.table().container()));
}

// 2A. Define the method for the onclick (myFunction())
function deletePrint(printName, printId) {
    swal({
        title: 'Are you sure?',
        text: "Once deleted, you will not be able to recover the print: " + printName,
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        $.ajax({
            url: "printDelete", // Name of the method in views.py (the endpoint)
            data: { //Parameters send it in a POST
                pk: printId,
                nombre: printName,
                csrfmiddlewaretoken: getCookie('csrftoken'),
            }, // Data sent with the delete request
            success: function (json) { //If the result is success return a JSON value
                if (json.status == 0) {
                    swal("Print Deleted!", json.msg, "success");
                    loadTable();
                } else {
                    if (json.status == 1) {
                        swal("Print Undeleted!", json.msg, "info");
                        loadTable();
                    } else {
                        swal("Print Undeleted!", json.msg, "error");
                    }
                }
            },
            error: function (xhr, errmsg, err) { //If the result is an error return an error message
                console.log(xhr.status + ": " + xhr.responseText); // Provide a bit more info about the error to the console
            }
        });
    }, function (dismiss) {
        if (dismiss === 'cancel' || dismiss === 'close') {
            swal("Print Undeleted!", "The print " + printName + " hasn't been deleted!", "info");
        }
    })
}