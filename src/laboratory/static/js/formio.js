function saveForm(state) {
    Swal.fire({
        title: message['title'],
        text: message['text'],
        icon: message['icon'],
        confirmButtonText: message['confirm'],
        denyButtonText: message['deny'],
        showDenyButton: true,
        showCloseButton: true

        }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: urls['edit'],
                type: "POST",
                dataType: "json",
                data: $('#inform_form').serialize()+"&status="+state,
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                success: (success) => {
                    Swal.fire(
                        result['title'],
                        result['text'],
                        result['icon']
                        )
                    location.href =urls['list'];
                },
            });

        } else if (result.isDenied){
        }
        })
}

function Delete_Inform(id) {
    Swal.fire({
        title: message['title'],
        text: message['text'],
        icon: message['icon'],
        confirmButtonText: message['confirm'],
        denyButtonText: message['deny'],
        showDenyButton: true,
        showCloseButton: true

        }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: urls['edit'],
                type: "POST",
                dataType: "json",
                data: {'id':id},
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                success: (success) => {
                    Swal.fire(
                        result['title'],
                        result['text'],
                        result['icon']
                        )
                    location.href =urls['list'];
                },
            });

        } else if (result.isDenied){
        }
        })
}
