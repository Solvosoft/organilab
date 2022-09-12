window.onload = function () {
    Formio.builder($('#formio')[0], saved, {
        noDefaultSubmitButton: true,
        builder: {
            derb_layout: {
                title: 'Layout',
                weight: 0
            },
            advanced: false,
            data: false,
            premium: false
        }
    }).then(function (new_form) {
        form = new_form.form;
        new_form.on('change', function () {
            form = new_form.form;
        });
    });
};

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function save_form_schema() {
    console.log(JSON.stringify(form, undefined, 2));
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
            result = JSON.parse(success).result;
            if (result) {
                Swal.fire({
                    icon: 'success',
                    title: 'Your form has been saved',
                    showConfirmButton: false,
                    timer: 1500
                })
            }
        },
        error: (error) => {
            Swal.fire({
                icon: 'error',
                title: 'Something went wrong while saving your form',
                showConfirmButton: false,
                timer: 1500
            })
        }
    });
}