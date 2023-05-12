
window.onload = function () {
    Formio.builder($('#formio')[0], saved, {
        noDefaultSubmitButton: true,
        builder: {
            advanced: false,
            data: false,
            premium: false,
            custom: {
                title: 'API Fields',
                weight: 10,
                components: {
                    customSelect: {
                        title: 'Select using APIs',
                        type: 'custom_select',
                        key: 'custom_select',
                        icon: 'terminal',
                        schema: {
                            label: 'Select using APIs',
                            type: 'custom_select',
                            key: 'custom_select',
                            input: true
                        },


                    }
                }
            }
        },


    }).then(function (new_form) {
        form = new_form.form;
        new_form.on('change', function () {
            form = new_form.form;
        });
        collapse_show();
        sizesing_buttons();
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
function collapse_show(){
   let collapses = document.querySelectorAll('.builder-group-button');
   let target =document.querySelectorAll('.collapse.show')[0]
   collapses.forEach(e =>
   e.addEventListener('click',()=>{
      close_collapse(collapses,e.getAttribute('data-target'));
    }));
}

function close_collapse(collapses,target){
   let new_target=""
   for (var i = 0; i < collapses.length; i++) {
        new_target=collapses[i].getAttribute('data-target')
        if(new_target != target){
            document.querySelector(collapses[i].getAttribute('data-target')).classList='collapse'
        }else if(new_target==target && document.querySelector(target).className=="collapse show" ){
            document.querySelector(target).classList='collapse';
        }else{
            document.querySelector(target).classList='collapse show';

        }

    }
}
function sizesing_buttons(){
    document.querySelectorAll('.no-drop').forEach(e=>{
      e.classList.add('d-grid');
    })
   document.querySelectorAll('.builder-group-button').forEach(e=>{
      e.parentNode.classList.add('d-grid');
    })
}