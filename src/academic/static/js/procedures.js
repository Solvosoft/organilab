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

function get_procedure(element){
   $('.form_errors').remove();
   $("#reservation_form").trigger('reset');
    let url = $(element).data('url')
    $.ajax({
        url: url,
        type:'GET',
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
function delete_procedure(pk,procedure_name){
    open_alert(pk, gettext('Are you sure to delete the procedure')+` ${procedure_name}?`,
    `${procedure_name} `+ gettext('has been deleted'),
    document.urls["remove_procedure"],0, gettext('The procedure was not removed'));
}

function delete_step(pk,step_name){
    open_alert(pk, gettext('Are you sure to delete the step')+ ` ${step_name}?`,
    gettext('Step')+` ${step_name} `+ gettext('has been deleted'),
    document.urls["remove_step"],0, gettext('The procedure step was not removed'));
}

function sendrequest(element,url,action, msg, swal){
     $.ajax({
        url: url,
        type:'POST',
        data: {'pk':element},
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        success: function ({data}) {
          if(data){
            swal.fire({
                title:gettext('Deleted!'),
                text:msg,
                type:'success'
          }).then(function(){
          if(data){
                location.reload();
           }
           });
           }else{
               swal.fire({
                     title:gettext("Don't have permissions"),
                     type:'error'
              })
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
     sendrequest(pk,url,action,out_msg,swalWithBootstrapButtons);
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
        url: document.urls["add_reservation"],
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
                if(errors){
                let list=""
                errors.forEach(element =>
                                    list += `<li class="list-group-item">${element}</li>`
                );
                document.querySelector("#list_errors").innerHTML=list;
                $("#reservation_modal").modal("hide")

                $("#error_reserved").modal('show')
                }else{
                    alert(gettext("Don't have permissions"))
                }
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
   var modal_target =$(this).data('bsTarget')
   var form= $(modal_target).find('form')
   if(form){
        $(form).trigger("reset");
        $('select').prop('selectedIndex', 0).change();
   }
})
$("#save_step").click(function(e){
   $("#form_step").submit();

})

