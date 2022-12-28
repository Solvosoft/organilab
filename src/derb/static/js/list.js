var table_data;

function loadDataTable() {
    table_data = $('#form_table').DataTable();
}

function deleteForm() {
    var id = $(this).attr('form_id');
    var name = $(this).attr('form_name');
    var url = $(this).data('url');

    Swal.fire({
        title: translations['delete_title'] + name + '?',
        text: translations['delete_text'],
        icon: 'warning',
        showCloseButton: true,
        showCancelButton: true,
        confirmButtonText: translations['btn_delete']

        }).then((result) => {
        if (result.isConfirmed) {
            
            $.ajax({
                type: 'POST', 
                url: url,
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
                        translations['delete_success_title'],
                        translations['delete_success_text'],
                        'success'
                        )
                    }
                },
                error: function () {
                    Swal.fire(
                    'Error!',
                    translations['delete_error_text'],
                    'error'
                    )
                }
            });
            
        }
        })
}

function createForm() {
    Swal.fire({
        title: translations['create_title'],
        text: translations['create_text'],
        input: 'text',
        showCancelButton: true, 
        showCloseButton: true,
        confirmButtonText: translations['btn_create'],
        cancelButtonText: translations['btn_cancel'],

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
    var url = $(this).data('url');
    location.href = url;
}
