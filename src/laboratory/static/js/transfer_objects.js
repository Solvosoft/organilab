function init_add_object(id, object, object_name,lab_received){
    $('#transfer_obj').val(id)
    get_shelfs({'lab':lab_received})
}

function get_shelfs(lab){
     $.ajax({
            url: document.get_shelfs,
            type: 'POST',
            data: lab,
            headers: {'X-CSRFToken': getCookie('csrftoken') },
            success: function({data}) {

            let shelfs=JSON.parse(data);
            let selector=document.querySelector('#shelf_list');
            selector.innerHTML='';
            shelfs.forEach(e => selector.innerHTML+=`<option value=${e.id}>${e.shelf}</option>`);

            }
            });
 }

function get_form_data(form) {
    const formAttributes = {};
    input_fields = $(form).find(':input');
    for (const input of input_fields) {
        name = input.name;
        value = input.value;
        formAttributes[`${name}`] = value;
    }
    return formAttributes;
}

function send_form(){
    form_modal = $('#transfer_form');
    data = get_form_data(form_modal);
    $.ajax({
            url: document.update_shelf,
            type: 'POST',
            data: data,
            success: function({msg}) {
                location.reload()
            }
            });

}

function delete_transfer(id){
    $.ajax({
            url: document.delete_transfer,
            type: 'POST',
            data: {'id':id},
            headers: {'X-CSRFToken': getCookie('csrftoken') },
            success: function({msg}) {
                location.reload()
            }
            });

}

function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

const sendrequest=(element=>{

     $.ajax({
        url: document.remove_transfer,
        type:'POST',
        data: {'id':element},
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        success: function ({data}) {
        location.reload()
      }
        });

});
function delete_transfer(element){

const swalWithBootstrapButtons = Swal.mixin({
  customClass: {
    confirmButton: 'btn btn-success',
    cancelButton: 'btn btn-danger'
  },
  buttonsStyling: false
})

swalWithBootstrapButtons.fire({
  title: 'Esta seguro de eLiminar la transferencia?',
  text: "Estas a tiempo de revertir esta acción!",
  icon: 'warning',
  showCancelButton: true,
  confirmButtonText: 'Si',
  cancelButtonText: 'No',
  reverseButtons: true
}).then((result) => {
  if (result.isConfirmed) {
    swalWithBootstrapButtons.fire(
      'Eliminado!',
      'La Transferencia ha sido eliminada.',
      'success'
    )
        sendrequest(element);

  } else if (
    result.dismiss === Swal.DismissReason.cancel
  ) {
    swalWithBootstrapButtons.fire(
      'Cancelado',
      'El dato no fue eliminado :)',
      'error'
    )
  }
})
}
