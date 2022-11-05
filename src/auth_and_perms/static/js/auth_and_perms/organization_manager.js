const Toast = Swal.mixin({
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true,
                didOpen: (toast) => {
                    toast.addEventListener('mouseenter', Swal.stopTimer)
                    toast.addEventListener('mouseleave', Swal.resumeTimer)
                }
             })

function organization_rol(element){
    const obj=  {
    'is_manager': element.getAttributeNames().find(e => e=="data-addbtn") != undefined,
    'element': element,
    'instance': $(element),
    'init': function(){

        if(this.is_manager){
            this.initialize_buttons();
        }else{
            this.display_rols();
        }

    },
    'display_rols': function(){
        console.log('load roles');
    },
    'initialize_buttons': function(){
         this.instance.find('.rolbtnadd').on('click', this.call_add_btn_click(this));
    },

    'get_add_form_title': function(){
        return this.element.title || "Creating Rol"
    },
    'get_add_form_html': function(){
        return document.getElementById("addrolform").innerHTML;
    },
    'get_add_form_confirmbtntext': function(){
        return this.element.getAttribute('confirmbtntext');
    },
    'add_btn_click': function(){
        const fatherobj=this;
        Swal.fire({
          title: this.get_add_form_title(),
          html: this.get_add_form_html(),
          confirmButtonText: this.get_add_form_confirmbtntext(),
          focusConfirm: false,
          preConfirm: () => {
            const rolname = Swal.getPopup().querySelector('#rolname').value

            if (!rolname) {
              Swal.showValidationMessage(  document.getElementById("addrolform").title )
            }

            return { rolname: rolname }
          }
        }).then((result) => {

          const data = {
            'name': result.value.rolname,
            'rol': fatherobj.element.getAttribute('rol')
          }

          return fetch(document.getElementById("addrolform").getAttribute('url'), {
              method: 'POST', // or 'PUT'
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
              },
              body: JSON.stringify(data),
            })
            }).then(results => {
              return results.json();
            })
            .then(json => {
                 window.location.reload();
            })
            .catch(err => {
              if (err) {
                swal("Oh noes!", "The AJAX request failed!", "error");
              } else {
                swal.stopLoading();
                swal.close();
              }
            });
    },
    // CALLS
    'call_add_btn_click': function(instance){
        return () => { instance.add_btn_click() };
    }
}
    obj.init();
    return obj;
}


document.addEventListener("DOMContentLoaded", function(){
    const collection = document.getElementsByClassName("rolcontainer");
    for (let i = 0; i < collection.length; i++) {
     organization_rol(collection[i]);
    }
});

$(document).ready(function(){
    $("input.checkrol").parent().addClass("checked");
});



$("input[type='checkbox']").on('ifChanged', function(){
    var parent = $(this).parent();
    $.ajax({
        url: $(this).data('url'),
        type:'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        success: function (message) {
            if(message.result == 'ok'){
                Toast.fire({
                    icon: 'success',
                    title: 'Element saved successfully.'
                });
                if(message.removecheck){
                    parent.removeClass("checked");
                }else{
                    parent.addClass("checked");
                }
            }else{
                 Toast.fire({
                    icon: 'error',
                    title: 'Something went wrong while saving this permission rol.'
                });
            }
        }
    });
});


$(".userbtnadd").on('click', function(){
    var id = $(this).data('id');
    var user_list = $(".table"+id+" tbody tr");
    var url = $(this).data('url');
    $("#adduserform").attr('action', url);
    var user_values = [];

    if(user_list){
        Array.from(user_list).forEach((item)=>{
            var user_id = $(item).data('id');
            user_values.push(user_id);
        });
    }

    var selected_values = user_values.join(',');

    $("#id_users").select2({
      theme: 'bootstrap-5',
      dropdownParent: $("#addusermodal"),
      placeholder: 'Select an element',
      ajax: {
        url: '/gtapis/userbase/',
        type: 'GET',
        dataType: 'json',
        data: function (params) {
          var dev= {
            selected: selected_values,
            term: params.term,
            page: params.page || 1
          };
          $("#id_users").trigger('relautocompletedata', dev);
          return dev;
        },
      }

    });

    $("#id_users").trigger('change.select2');
    $("#addusermodal").modal('show');
});



$(".addprofilerol").on('show.bs.modal', function (e) {

    var target = e.relatedTarget;
    var form = $(this).find('form');
    var id = $(this).data('id');
    $(form).attr('action', $(target).data('url'));
    $("#id_org_pk").val(id);
    $("#id_lab_pk").val($(target).data('id'));
    var rols = document.getElementById("id_rols");
    var url = $(rols).data('url');

    $(rols).select2({
      theme: 'bootstrap-5',
      dropdownParent: $(this),
      placeholder: 'Select an element',
      ajax: {
        url: url,
        type: 'GET',
        dataType: 'json',
        data: function (params) {
              var dev= {
                term: params.term,
                page: params.page || 1
              };
              dev['pk'] = id;
              $(rols).trigger('relautocompletedata', dev);
              return dev;
        },
      }

    });

    $(rols).trigger('change.select2');
});


$(".addprofilerol").on('hide.bs.modal', function (e) {
    $("#id_org_pk").val('');
    $("#id_lab_pk").val('');
    $("#id_rols").val('').trigger('change');
});