function editForm() {
    Swal.fire({
        title: translations_form['update_title'],
        text: translations_form['update_text'],
        input: 'text',
        showCancelButton: true, 
        confirmButtonText: translations_form['btn_update'],

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
                        translations_form['update_success_title'],
                        translations_form['update_success_text'],
                        'success'
                        )       
                },
                error: function () {
                    Swal.fire(
                    'Error!',
                    translations_form['update_error_text'],
                    'error'
                    )
                }
            });
        }
    });
}

function redirectSave() {
    Swal.fire({
        title: translations_form['return_title'],
        text: translations_form['return_text'],
        icon: 'warning',
        confirmButtonText: translations_form['return_save'],
        denyButtonText: translations_form['return_discard'],
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
                        translations_form['return_success_title'],
                        translations_form['return_success_text'],
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