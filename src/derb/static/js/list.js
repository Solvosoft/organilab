var table_data;

function loadDataTable() {
    table_data = $('#form_table').DataTable();
}

function deleteForm() {
    var id = $(this).attr('form_id');
    var name = $(this).attr('form_name')
    
    Swal.fire({
        title: 'Do you want to delete the form ' + name + '?',
        text: "This action cannot be undone",
        icon: 'warning',
        showCloseButton: true,
        showCancelButton: true,
        confirmButtonText: 'Delete'

        }).then((result) => {
        if (result.isConfirmed) {
            
            $.ajax({
                type: 'POST', 
                url: window.urls['delete'].replace('0', id) ,
                data: id, 
                headers: {'X-CSRFToken': csrftoken},
                mode: 'same-origin', 
                cache: false,
                success: function (response) { 
                    if (response.length == 0) {
                        alert('An error has occurred');
                    } else {
                        $('#tr_' + id).hide(); 
                        Swal.fire(
                        'Deleted!',
                        'The form has been deleted.',
                        'success'
                        )
                    }
                },
                error: function () {
                    Swal.fire(
                    'Error!',
                    'The form could not be deleted.',
                    'error'
                    )
                }
            });
            
        }
        })
}

function createForm() {
    Swal.fire({
        title: "Create Form",
        text: "Form name:",
        input: 'text',
        showCancelButton: true, 
        showCloseButton: true,
        confirmButtonText: 'Create',  

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
                url: window.urls['create'],
                data: { 'name' : name, 'status': status}, 
                headers: {'X-CSRFToken': csrftoken},
                mode: 'same-origin', 
                success: function(data, status, jqxhr) {
                    window.location.href = data['url']
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

function editForm() {
    var id = $(this).attr('form_id'); 
    location.href = window.urls['edit'].replace('0', id);
}
