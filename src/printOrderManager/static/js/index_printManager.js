// This functions is called when the document is ready
$(document).ready(function () {
    // Get each element from a li with the id=messages
    $("#messages li").each(function (index) {
        swal("Print registered!", $(this).text(), "success");
    });
});

// 2A. Define the method for the onclick (myFunction())
function deletePrint(printName, printId) {
    swal({
            title: "Are you sure?",
            text: "Once deleted, you will not be able to recover the print: " + printName,
            icon: "warning",
            buttons: true,
            dangerMode: true,
        })
        .then((willDelete) => {
            // 3A. With an ajax function we call a .py method for delete the print
            // with a method in views.py
            if (willDelete) {
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
                            updateTable();
                        } else {
                            if (json.status == 1) {
                                swal("Print Undeleted!", json.msg, "info");
                                updateTable();
                            } else {
                                swal("Print Undeleted!", json.msg, "error");
                            }
                        }
                    },
                    error: function (xhr, errmsg, err) { //If the result is an error return an error message
                        console.log(xhr.status + ": " + xhr.responseText); // Provide a bit more info about the error to the console
                    }
                });
            } else {
                swal("Print Undeleted!", "The print " + printName + " hasn't been deleted!", "error");
            }
        });
}