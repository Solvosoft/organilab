function remove_company(element){
let company = element.getAttribute('data-company')
let url = element.getAttribute('data-url')
Swal.fire({
        title: messages['title'],
        text: messages['text']+ " "+company,
        icon: 'success',
        confirmButtonText: messages['yes'],
        denyButtonText: 'No',
        showDenyButton: true,
        showCloseButton: true

        }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: url,
                type: "GET",
                dataType: "json",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                success: ({msg, status}) => {
                    icon= 'error';
                    if(status){
                        icon='success';
                        Swal.fire(
                            '',
                            msg,
                            'success'
                        )
                        location.reload();
                    }

                },
            });

        }
        });
}