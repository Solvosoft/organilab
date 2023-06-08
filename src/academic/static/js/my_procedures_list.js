$(document).ready(function() {
    $('#my_procedures').DataTable();
});

function delete_my_procedure(pk){
    let url = document.removeProcedure.replace('0', pk);
    Swal.fire({
    title: gettext("Delete procedure"),
    text: gettext("Do you want to remove the procedure?"),
    icon: "error",
    confirmButtonText: gettext("Yes"),
    denyButtonText: gettext("No"),
    showDenyButton: true,
    showCloseButton: true
    }).then((result) => {
    if (result.isConfirmed) {
        $.ajax({
            url: url,
            type: "POST",
            data: {},
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            success: (success) => {
                Swal.fire(
                   gettext("Successfully deleted"),
                ).then(function(result) {
                    location.reload();
                })
            },
        });
    }
    });
}