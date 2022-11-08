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
        //console.log('load roles');
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


document.contextroletable={
    as_conttentype: false,
    as_user: false,
    as_role: true,
    profile: null,
    contenttypeobj: null,
    user: null
}



$(".applyasrole").on('click', function(e){
    document.contextroletable.as_conttentype=false;
    document.contextroletable.as_user=false;
    document.contextroletable.user=null;
    document.contextroletable.as_role=true;
    document.contextroletable.contenttypeobj=Object.assign({}, e.target.dataset);
    document.contextroletable.profile= e.target.dataset.profile
    $("#modal"+e.target.dataset.org).modal('show');
});
$(".applybycontenttype").on('click', function(e){
    document.contextroletable.as_conttentype=true;
    document.contextroletable.as_user=false;
    document.contextroletable.user=null;
    document.contextroletable.as_role=false;
    document.contextroletable.profile=null;
    document.contextroletable.contenttypeobj=Object.assign({}, e.target.dataset);
    $("#modal"+e.target.dataset.org).modal('show');
});
$(".applybyuser").on('click', function(e){
    document.contextroletable.as_role=false;
    document.contextroletable.as_conttentype=false;
    document.contextroletable.contenttypeobj=null;
    document.contextroletable.as_user=true;
    document.contextroletable.profile=e.target.dataset.user;
    $("#modal"+e.target.dataset.org).modal('show');
});


$(".userbtnadd").on('click', function(e){
    document.contextroletable.as_conttentype=true;
    document.contextroletable.as_user=false;
    document.contextroletable.user=null;
    document.contextroletable.as_role=false;
    document.contextroletable.contenttypeobj=Object.assign({}, e.target.dataset);
    document.contextroletable.profile=null;
    $("#modaluser"+e.target.dataset.id).modal('show');
});

document.profileroleselects={

}


function add_selected_elements_to_select2(rols, data){
    return ()=>{
        for(let x=0; x<data.length; x++){
         if ($(rols).find("option[value='" + data[x].id + "']").length) {
            $(rols).val(data[x].id).trigger('change');
         }else{
            var newOption = new Option(data[x].text, data[x].id, true, true);
            $(rols).append(newOption).trigger('change');
         }
        }
    };

}

function add_data_to_select(rols){
    $(rols).val(null).trigger('change');

    return (data)=>{
        for(let x=0; x<data.results.length; x++){
            if ($(rols).find("option[value='" + data.results[x].id + "']").length) {
                $(rols).val(data.results[x].id).trigger('change');
            }else{
                var newOption = new Option(data.results[x].text, data.results[x].id, data.results[x].selected,
                        data.results[x].selected);
                $(rols).append(newOption)
            }
        }
        $(rols).trigger('change');
    }
}

$(".addprofilerol").on('show.bs.modal', function (e) {


    let modalid=e.target.id;
    var selecttarget = $("#"+modalid+' select');
    var rols = selecttarget;
    var organization = this.dataset.id;
    var url = $(rols).data('url');
    var selecteditems = [];

    if(Object.hasOwnProperty(document.profileroleselects, modalid) ){
        $(rols).select2('destroy');

    }

    $.ajax({
      type: "GET",
      url: url,
      data: document.contextroletable,
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: add_data_to_select(rols),
      dataType: 'json'
    });
    $(rols).select2({theme: 'bootstrap-5',  dropdownParent: $(this)});
/**
    document.profileroleselects[modalid]=$(rols).select2({
        theme: 'bootstrap-5',
        dropdownParent: $(this),
        placeholder: 'Select an element',
        ajax: {
        url: url,
        type: 'GET',
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        dataType: 'json',
        processResults: function (data) {
          // Transforms the top-level key of the response object from 'items' to 'results'
          let results = [];
          var selected = []
          for(let x=0; x<data.results.length; x++){
            if(data.results[x].selected){
                selected.push(data.results[x])
            }
          }
          setTimeout(add_selected_elements_to_select2(rols, selected), 1000)
          return {
            results: data.results
          };
        },
        data: function (params) {
              var dev= {
                term: params.term,
                page: params.page || 1
              };
              dev['organization'] = organization;
              dev['context']=document.contextroletable;
              $(rols).trigger('relautocompletedata', dev);
              return dev;
        },
        }

    });

    $(rols).trigger('change');
**/
});


$(".relatedusermodal").on('show.bs.modal', function (e) {


    let modalid=e.target.id;
    var selecttarget = $("#"+modalid+' select');
    var users = selecttarget;
    var organization = this.dataset.id;
    var url = $(users).data('url');
    var selecteditems = [];


    $(users).val('').trigger('change');

    $.ajax({
      type: "GET",
      url: url,
      data: document.contextroletable,
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: add_data_to_select(users),
      dataType: 'json'
    });
    $(users).select2({theme: 'bootstrap-5',  dropdownParent: $(this)});
});


$(".btnsaverole").on('click', function(e){
    let form = $(e.target).closest('form')[0]
    let url = form.action;
    let dataform = {
        'rols': $(form).find('select[name="rols"]').val(),
        'mergeaction': $(form).find('input[name="mergeaction"]:checked').val(),
        'csrfmiddlewaretoken': $(form).find('input[name="csrfmiddlewaretoken"]').val(),
    }
    let data=Object.assign(dataform, document.contextroletable);


    $.ajax({
      type: "PUT",
      url: url,
      data: JSON.stringify(data),
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: function( data ) {
           window.location.reload();
      },
      dataType: 'json'
    });
});

$(".addOrgStructure").on('click', function(e){
    let parent=this.dataset.parent;
    $('#id_parent').val(parent);
    $("#addOrganizationmodal").modal('show');
});

$(".addOrgStructureEmpty").on('click', function(e){
    $('#id_parent').val('');
    $("#addOrganizationmodal").modal('show');
});