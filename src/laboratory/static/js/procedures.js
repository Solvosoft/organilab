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
        success: function({title,pk}){
            $('#procedure_title').text(title);
            $('#procedure').val(pk);
            $("#reservation_modal").modal('show');
        },
        error: function(xhr, resp, text) {
               var errors = xhr.responseJSON.msg;
               if(errors){
                     Swal.fire({
                 title: gettext('Error'),
                icon: 'error',
                text: errors,
            })
            }
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
        success: function({data, msg}) {

            generate_table(JSON.parse(data));
            document.getElementById('object_form').reset();
            $('select').prop('selectedIndex', 0).change();
            $('.form_errors').remove();
            $('#object_modal').modal('hide');

        },
        error: function(xhr, resp, text) {
               var errors = xhr.responseJSON.form;
               if(errors){
                  $('.form_errors').remove();
                  form_field_errors(form, errors,".form-group");

               }else{
                           Swal.fire({
                icon: 'error',
                text: xhr.responseJSON.msg,
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
        <td><a class="btn btn-md btn-danger" onclick="delete_object(${item.id},'${item.obj}')"><i class="fa fa-trash"></i> ${gettext("Eliminate")}</a>
              </td>
        </tr>`;
    });
}

function add_observation(){
    var modal = $("#observation_form");
    data= new FormData(document.getElementById('observation_form'));
    var form = modal.find('form');
    $.ajax({
        url: document.save_observation,
        type: 'POST',
        data: data,
        processData: false,
        contentType: false,
        success: function({data}) {
        document.getElementById('observation_form').reset();
            generate_observation_table(JSON.parse(data));
            $("#observation_modal").modal("hide")
        },
        error: function(xhr, resp, text) {
               var errors = xhr.responseJSON.errors;
               if(errors){
                  $('.form_errors').remove();
                  form_field_errors(form, errors,"#observation_form");

               }
            }
        });
        }

function generate_observation_table(data){

    let tbody=document.querySelector('#observation_list');
    tbody.innerHTML='';

    data.forEach((item)=>{
        tbody.innerHTML+=`<tr>
            <td>${item.description}</td>
             <td><a class="btn btn-md btn-danger text-center" onclick="delete_observation(${item.id})"><i class="fa fa-trash"></i> ${gettext("Eliminate")}</a></td>
            </tr>`

    });
 }

function delete_procedure(pk,procedure_name){
    open_alert(pk, gettext('Are you sure to delete the procedure')+` ${procedure_name}?`,
    `${procedure_name} `+ gettext('has been deleted'),
    document.remove_procedure,0, gettext('The procedure was not removed'));
}

function delete_step(pk,step_name){
    open_alert(pk, gettext('Are you sure to delete the step')+ ` ${step_name}?`,
    gettext('Step')+` ${step_name} `+ gettext('has been deleted'),
    document.remove_step,0, gettext('The procedure step was not removed'));
}

function delete_observation(pk){
    open_alert(pk, gettext('Are you sure to delete this observation?'),
    gettext('Observation has been deleted'),
    document.remove_observation,2, gettext('The observation was not removed'));
}

function delete_object(pk,obj_name){
    open_alert(pk, gettext('Are you sure to delete this object')+ ` ${obj_name}?`,
    gettext('Object')+` ${obj_name} `+gettext('has been deleted'),
    document.remove_object,1, gettext('The object was not removed'));
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
function open_alert(pk, in_msg,out_msg,url,action,msg_cancel){
const swalWithBootstrapButtons = Swal.mixin({
  customClass: {
    confirmButton: 'btn btn-success',
    cancelButton: 'btn btn-danger'
  },
  buttonsStyling: false
})

swalWithBootstrapButtons.fire({
  title: in_msg,
  text: gettext("You are in time to reverse this action!"),
  icon: 'warning',
  showCancelButton: true,
  confirmButtonText: gettext('Yes'),
  cancelButtonText: 'No',
  reverseButtons: true
}).then((result) => {
  if (result.isConfirmed) {
    swalWithBootstrapButtons.fire({
      title:gettext('Deleted!'),
      text:out_msg,
      type:'success'
    }).then(function(){
     sendrequest(pk,url,action);
     })


  } else if (
    result.dismiss === Swal.DismissReason.cancel
  ) {
    swalWithBootstrapButtons.fire(
      gettext('Cancelled'),
      msg_cancel,
      'error'
    )
  }
})
}
function load_errors(error_list, obj,klass){
    ul_obj = "<ul class='errorlist form_errors d-flex justify-content-center'>";
    error_list.forEach((item)=>{
        ul_obj += "<li>"+item+"</li>";
    });
    ul_obj += "</ul>"
    $(obj).parents(klass).prepend(ul_obj);
    return ul_obj;
}

function form_field_errors(target_form, form_errors,klass){
    var item = "";
    for (const [key, value] of Object.entries(form_errors)) {
        item = "#id_"+key;
        if($(item).length > 0){
            load_errors(form_errors[key], item,klass);
        }
    }
}

function add_reservation(){
  data= new FormData(document.getElementById('reservation_form'));
    var modal = $("#reservation_form");
    var form = modal.find('form');
    $.ajax({
        url: document.reservation,
        type: 'POST',
        data: data,
        processData: false,
        contentType: false,
        success: function({state, errors}) {
            if(state){
            Swal.fire(
                    '',
                    gettext("Reserved"),
                    'success'
            )
            $("#reservation_modal").modal("hide")

            }else{
                let list=""
                errors.forEach(element =>
                                    list += `<li class="list-group-item">${element}</li>`
                );
                document.querySelector("#list_errors").innerHTML=list;
                $("#error_reserved").modal('show')
            }
            document.getElementById('reservation_form').reset();

        },
        error: function(xhr, resp, text) {
               var errors = xhr.responseJSON.form;
               if(errors){
                  $('.form_errors').remove();
                  form_field_errors(form, errors,".mb-4");

               }else{
                   Swal.fire(
                    xhr.responseJSON.msg,
                    gettext("Error"),
                    'error'
            )

               }
        }
        });
  }
$(".open_modal").click(function(e){
   $('.form_errors').remove();
})