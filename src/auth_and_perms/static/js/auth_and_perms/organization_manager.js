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
                 windows.location.ref.reload();
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
    $.ajax({
        url: $(this).data('url'),
        type:'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        success: function (message) {
            if(message.result == 'ok'){
                Swal.fire({
                        icon: 'success',
                        text: "Element saved successfully."
                });
            }
        }
    });
});