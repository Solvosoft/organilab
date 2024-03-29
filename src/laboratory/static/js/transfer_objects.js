function init_add_object(id, object, object_name,lab_received, element){
    $('#transfer_obj').val(id)
    get_shelfs({'lab':lab_received,'id':id})
    var url = $(element).data('url');
    $("#savebtn").attr('data-url', url);
}

function get_shelfs(lab){
     $.ajax({
            url: document.get_shelfs,
            type: 'POST',
            data: lab,
            headers: {'X-CSRFToken': getCookie('csrftoken') },
            success: function({data,msg}) {
            $('#obj').text(msg)
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
function replaceLast(obj, search, replace) {
    return obj.replace(new RegExp(search+"([^"+search+"]*)$"), replace+"");
}

function send_form(element){
    var id = $('#shelf_list').val();
    var url = $(element).data('url');
    if(id){
            url = replaceLast(url, '0', id);
        }
    $.ajax({
    url: url,
    type: 'POST',
    headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken"),
        },
    dataType: 'json',
    success: function({status,msg}) {
        if(status){
        location.reload()
        }else{
           error_message('#alert_message',msg)
        }
    }
    });

}
function error_message(id,msg){
  if ($(`${id}`).css('display') != 'block')
      $(`${id}`).css('display', 'block');
      $('#error_message').text(msg);
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
  title: 'Esta seguro de eliminar la transferencia?',
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
      'El dato no fue eliminado',
      'error'
    )
  }
})
}
