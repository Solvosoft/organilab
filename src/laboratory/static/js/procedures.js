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

function get_procedure(pk){
    $.ajax({
        url: document.getProcedure,
        type:'POST',
        data:{'pk':pk},
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        success: function({data}){
            $('#procedure_title').text(data.title);
            $('#procedure').val(data.pk);
        }

    })
}
function add_object(){
  form= new FormData(document.getElementById('object_form'));
    $.ajax({
        url: document.save_object,
        type: 'POST',
        data: form,
        processData: false,
        contentType: false,
        success: function({data, status, msg}) {
            generate_table(JSON.parse(data));
            if(!status){
            Swal.fire({
                icon: 'error',
                text: msg,
            })
            }
        }
        });
  }

function generate_table(data){
    let tbody=document.querySelector('#object_list');
    tbody.innerHTML='';

    data.forEach((item)=>{
    tbody.innerHTML+=`<tr>
        <td>${item.obj}</td>
        <td>${item.amount} ${item.unit}</td>
        <td><a class="btn btn-md btn-danger" onclick="delete_object(${item.id},'${item.obj}')"><i class="fa fa-trash"></i> Eliminar</a>
              </td>
        </tr>`;
    });
}

function add_observation(){
    form= new FormData(document.getElementById('observation_form'));
    $.ajax({
        url: document.save_observation,
        type: 'POST',
        data: form,
        processData: false,
        contentType: false,
        success: function({data}) {
        document.getElementById('observation_form').reset();
            generate_observation_table(JSON.parse(data))
        }
    });
}

function generate_observation_table(data){

    let tbody=document.querySelector('#observation_list');
    tbody.innerHTML='';

    data.forEach((item)=>{
        tbody.innerHTML+=`<tr>
            <td>${item.description}</td>
             <td><a class="btn btn-md btn-danger" onclick="delete_observation(${item.id})"><i class="fa fa-trash"></i> Eliminar</a></td>
            </tr>`

    });
 }


function delete_procedure(pk,procedure_name){
    open_alert(pk, document.message.confirmprocedure+` ${procedure_name}?`,
    `${procedure_name} `+ document.message.deletemsg,
    document.remove_procedure,0);
}

function delete_step(pk,step_name){
    open_alert(pk, document.message.confirmstep+ ` ${step_name}?`,
    document.message.step+` ${step_name} `+ document.message.deletemsg,
    document.remove_step,0);
}

function delete_observation(pk){
    open_alert(pk, document.message.confirmobs,
    document.message.deleteobs,
    document.remove_observation,2);
}

function delete_object(pk,obj_name){
    open_alert(pk, document.message.confirmobj+ ` ${obj_name}?`,
    document.message.object+` ${obj_name} `+document.message.deletemsg,
    document.remove_object,1);
}

function sendrequest(element,url,action){
     $.ajax({
        url: url,
        type:'POST',
        data: {'pk':element},
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        success: function ({data}) {

          if(action==0){
               if(data){
                location.reload();
               }
           }else if(action==1){
               generate_table(JSON.parse(data));
           }else{
               generate_observation_table(JSON.parse(data))

           }
      }
      });

}
function open_alert(pk, in_msg,out_msg,url,action){
const swalWithBootstrapButtons = Swal.mixin({
  customClass: {
    confirmButton: 'btn btn-success',
    cancelButton: 'btn btn-danger'
  },
  buttonsStyling: false
})

swalWithBootstrapButtons.fire({
  title: in_msg,
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
      out_msg,
      'success'
    )
     sendrequest(pk,url,action);


  } else if (
    result.dismiss === Swal.DismissReason.cancel
  ) {
    swalWithBootstrapButtons.fire(
      'Cancelado',
      'El procedimiento no fue eliminado',
      'error'
    )
  }
})
}

function add_reservation(){
  form= new FormData(document.getElementById('reservation_form'));
    $.ajax({
        url: document.reservation,
        type: 'POST',
        data: form,
        processData: false,
        contentType: false,
        success: function({state, errors}) {
            if(state){
            Swal.fire(
                    '',
                    gettext("Reserved"),
                    'success'
            )
            }else{
                let list=""
                errors.forEach(element =>
                                    list += `<li class="list-group-item">${element}</li>`
                );
                document.querySelector("#list_errors").innerHTML=list;
                $("#error_reserved").modal('show')
            }
        }
        });
  }
