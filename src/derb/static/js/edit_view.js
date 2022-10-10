function editForm() {
    Swal.fire({
        title: "Update Form Name",
        text: "Form name:",
        input: 'text',
        showCancelButton: true, 
        confirmButtonText: 'Update',  

        preConfirm: (value) => {
            if (!value) {
              Swal.showValidationMessage(
                '<i class="fa fa-info-circle"></i> The form name is required'
              )
            }
          }

    }).then((result) => {
        if (result.value) {
            var name = result.value;
            var status = 'admin';
            $.ajax({
                type: 'POST', 
                url: 'update/', 
                data: { 'name' : name, 'status': status}, 
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                success: function() {
                    document.getElementById("form_name").textContent = name;
                    Swal.fire(
                        'Updated!',
                        'The form name has been updated.',
                        'success'
                        )       
                },
                error: function () {
                    Swal.fire(
                    'Error!',
                    'The form could not be created.',
                    'error'
                    )
                }
            });
        }
    });
}

function redirectSave() {
    Swal.fire({
        title: 'Save or discard your changes to proceed',
        text: "Discarding cannot be undone.",
        icon: 'warning',
        confirmButtonText: 'Save',
        denyButtonText: `Discard`,
        showDenyButton: true, 
        showCloseButton: true

        }).then((result) => {
        if (result.isConfirmed) {
            json_schema = JSON.stringify(form);
            $.ajax({
                url: window.urls['editview'],
                type: "POST",
                dataType: "json",
                data: json_schema,
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                success: (success) => {
                    Swal.fire(
                        'Saved!',
                        'The form name has been saved.',
                        'success'
                        )     
                    location.href = window.urls['formlist'];
                },   
            });   

        } else if (result.isDenied){
            location.href = window.urls['formlist'];
        }
        })
}