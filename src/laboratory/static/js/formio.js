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
                        "",
                        saved,
                        "success"
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
                        '',
                        saved,
                        'success'
                        )
                    location.href =urls['list'];
                },
            });

        } else if (result.isDenied){
        }
        })
}


function save_comment(){
    Swal.fire({
    title: add_translation['title'],
    input: 'textarea'
    }).then(function(result) {
    if (result.value) {
    $.ajax({
            url: urls['add_comment'],
            type: "POST",
            dataType: "json",
            data: {'comment':result.value,'inform':inform},
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            success: (success) => {
                Swal.fire(
                    '',
                    add_translation['successfull'],
                    "success"
                    )
                    document.querySelector('#listado').innerHTML=success.data;
            },
        });
    }
    })
}


function edit_comment(pk){
    localStorage.setItem('comment', pk);
    let url = urls['get_comment']+pk;
    $.ajax({
    url: url,
        type: "GET",
        dataType: "json",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        success: (success) => {
            Swal.fire({
                title: update_translation['title'],
                input: 'textarea',
                confirmButtonText: update_translation['accept'],
                denyButtonText: update_translation['deny'],
                showDenyButton: true,
                showCloseButton: true,
                inputValue:success.comment
            }).then(function(result) {
                if (result.isConfirmed) {
                    update_comment(result.value)
                }
            })
        }
    });
}
function update_comment(comment){
     let url = urls['delete_update_comment'].replace('0',localStorage.getItem('comment'));
     localStorage.removeItem('comment');
     $.ajax({
            url: url,
            type: "PUT",
            dataType: "json",
            data: {'comment':comment},
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            success: (success) => {
                Swal.fire(
                    '',
                    update_translation['successfull'],
                    'success'
                    )
                 document.querySelector('#listado').innerHTML=success.data;
            },
        });
}
function delete_comment(comment){
    let url = urls['delete_update_comment'].replace('0',comment);
    Swal.fire({
    title: remove_translation["title"],
    text: remove_translation['text'],
    icon: "error",
    confirmButtonText: remove_translation['accept'],
    denyButtonText: remove_translation['deny'],
    showDenyButton: true,
    showCloseButton: true
    }).then((result) => {
    if (result.isConfirmed) {
        $.ajax({
            url: url,
            type: "DELETE",
            dataType: "json",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            success: (success) => {
                document.querySelector('#listado').innerHTML=success.data;
                Swal.fire(
                   remove_translation['successfull'],
                    )
            },
        });
    }
    });
}

function get_comments(pk){
    $.ajax({
        url: urls['add_comment']+'?inform='+pk,
        type: "GET",
        dataType: "json",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken"),
       },
       success: (success) => {
        document.querySelector('#listado').innerHTML=success.data;
        },
        });
 }