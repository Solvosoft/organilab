function convertFormToJSON(form, prefix="") {
  const re = new RegExp("^"+prefix);
  return form
    .serializeArray()
    .reduce(function (json, { name, value }) {
      json[name.replace(re, "")] = value;
      return json;
    }, {});
}

function convertToStringJson(form, prefix="", extras={}){
    var formjson =convertFormToJSON(form, prefix=prefix);
    formjson=Object.assign({}, formjson, extras)
    return JSON.stringify(formjson);
}

function load_errors(error_list, obj){
    ul_obj = "<ul class='errorlist form_errors d-flex justify-content-center'>";
    error_list.forEach((item)=>{
        ul_obj += "<li>"+item+"</li>";
    });
    ul_obj += "</ul>"
    $(obj).parents('.form-group').prepend(ul_obj);
    return ul_obj;
}

function form_field_errors(target_form, form_errors, prefix){
    var item = "";
    for (const [key, value] of Object.entries(form_errors)) {
        item = " #id_" +prefix+key;
        if(target_form.find(item).length > 0){
            load_errors(form_errors[key], item);
        }
    }
}

function clear_action_form(form){
    // clear switchery before the form reset so the check status doesn't get changed before the validation
    $(form).find("input[data-switchery=true]").each(function() {
        if($(this).prop("checked")){  // only reset it if it is checked
            $(this).trigger("click").prop("checked", false);
        }
    });

    $(form).trigger('reset');
    $(form).find("select option:selected").prop("selected", false);
    $(form).find("select").val(null).trigger('change');
    $(form).find("ul.form_errors").remove();
}

var form_modals = {}
function BaseFormModal(modalid,  data_extras={})  {
    var modal = $(modalid);
    var form = modal.find('form');
    return {
        "instance": $(modalid),
        "form": form,
        "url": form[0].action,
        "prefix": form.find(".form_prefix").val(),
        "type": "POST",
        "data_extras": data_extras,
        "init": function(btninstance){
            var myModalEl = this.instance[0];
            myModalEl.addEventListener('hidden.bs.modal', this.hidemodalevent(this))
            this.instance.find('.formadd').on('click', this.addBtnForm(this));
        },
        "addBtnForm": function(instance){
            return function(event){
                $.ajax({
                url: instance.url,
                type: instance.type,
                data: convertToStringJson(instance.form, prefix=instance.prefix, extras=instance.data_extras),
                headers: {'X-CSRFToken': getCookie('csrftoken')},
                success: function(data){
                    datatableelement.ajax.reload();
                    instance.hidemodal();
                    Swal.fire({
                        icon: 'success',
                        title: gettext('Success'),
                        text: data.detail,
                        timer: 1500
                    });
                    instance.success(instance, data);
                },
                error: function(xhr, resp, text) {
                    var errors = xhr.responseJSON.errors;
                    if(errors){  // form errors
                        form.find('ul.form_errors').remove();
                        let prefix=instance.prefix;
                        if(prefix.length !== 0){
                            prefix = prefix+"-"
                        }
                        form_field_errors(form, errors, prefix);
                    }else{ // any other error
                        Swal.fire({
                            icon: 'error',
                            title: gettext('Error'),
                            text: gettext('There was a problem performing your request. Please try again later or contact the administrator.')
                        });
                    }
                    instance.error(instance, xhr, resp, text);
                }
            });
            }
        },
        "success": function(instance, data){
        },
        "error": function(instance, xhr, resp, text){
        },
        "hidemodal": function(){
            this.instance.modal('hide');
        },
        "hidemodalevent": function(instance){
            return function(event){
                clear_action_form(instance.instance);
                instance.hidemodal();
                if(instance.data_extras.hasOwnProperty('shelf_object')){
                    delete instance.data_extras.shelf_object;
                }
            }
        },
        "showmodal": function(btninstance){
            var shelf_object = $(btninstance).data('shelfobject');
            if (shelf_object != undefined){
                this.data_extras['shelf_object'] = shelf_object;
            }
            this.instance.modal('show');
        }

    }
}

function show_me_modal(instance, event){
    var modalid = $(instance).data('modalid');

    if(form_modals.hasOwnProperty(modalid) ){
        form_modals[modalid].showmodal(instance);
    }else{
        var formmodal=BaseFormModal("#"+modalid);
         formmodal.init(instance);
         form_modals[modalid].showmodal(instance);
         form_modals[modalid]=formmodal;
    }
}


const tableObject={
    clearFilters: function ( e, dt, node, config ) {clearDataTableFilters(dt, id)},
    addObjectOk: function(data){
         datatableelement.ajax.reload();

    },
    addObjectResponse: function(dat){
            $('#shelfobjectCreate').html(dat);
            $("#object_create").modal('show');
    },
    addObject: function( e, dt, node, config ){
        let activeshelf=tableObject.get_active_shelf();
        if (activeshelf == undefined){
            return 1;
        }
        ajaxGet(document.urls['shelfobject_create'], {'shelf': activeshelf }, tableObject.addObjectResponse);
    },
    get_active_shelf: function(){
         let value= $('input[name="shelfselected"]:checked').val();
         if(value == undefined){

            Swal.fire({
                  position: 'top',
                  icon: 'info',
                  height: 100,
                  title: gettext('No shelf selected'),
                  text: gettext('You need to select a shelf before do this action'),
                  showConfirmButton: false,
                  timer: 2500
                })
         }
         return value;
    },
    update_object: function(obj){
        datatableelement.rows( function ( idx, data, node ) {
                                return data.pk == obj.pk;
                            } ).data(obj).draw();
    }

};

$(document).ready(function(){
    const searchLaboratory={
        init: function(){
            this.init_box();
        },
        init_box: function(){
            var toggler = document.getElementsByClassName("box");
            var i;

            for (i = 0; i < toggler.length; i++) {
              toggler[i].addEventListener("click", function() {
                this.parentElement.querySelector(".nested").classList.toggle("active");
                this.classList.toggle("check-box");
              });
            }
        }
    };


    searchLaboratory.init();

    datatableelement=createDataTable('#shelfobjecttable', document.url_shelfobject, {
     columns: [
            {data: "pk", name: "pk", title: gettext("Id"), type: "string", visible: false},
            {data: "object_type", name: "object_type", title: gettext("Type"), type: "string", visible: true},
            {data: "object_name", name: "object_name", title: gettext("Name"), type: "string", visible: true},
            {data: "quantity", name: "quantity", title: gettext("Quantity"), type: "string", visible: true },
            {data: "unit", name: "unit", title: gettext("Unit"), type: "string", visible: true},
            {data: "container", name: "container", title: gettext("Container"), type: "string", visible: true},
            {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true},
        ],
    buttons: [
            {
                action: tableObject.clearFilters,
                text: '<i class="fa fa-eraser" aria-hidden="true"></i>',
                titleAttr: gettext('Clear Filters'),
                className: 'btn-sm mr-4'
            },
            {
                action: tableObject.addObject,
                text: '<i class="fa fa-desktop" aria-hidden="true"></i>',
                titleAttr: gettext('Create Equipment'),
                className: 'btn-sm btn-success ml-4'
            },
            {
                action: tableObject.addObject,
                text: '<i class="fa fa-battery-quarter" aria-hidden="true"></i>',
                titleAttr: gettext('Create Material'),
                className: 'btn-sm btn-success ml-4'
            },
            {
                action: tableObject.addObject,
                text: '<i class="fa fa-flask" aria-hidden="true"></i>',
                titleAttr: gettext('Create Substance'),
                className: 'btn-sm btn-success ml-4'
            },
            {
                action: tableObject.addObject,
                text: '<i class="fa fa-exchange" aria-hidden="true"></i>',
                titleAttr: gettext('Transfer In'),
                className: 'btn-sm btn-success ml-4'
            },
        ],
     ajax: {
        url: document.url_shelfobject,
        type: 'GET',
        data: function(dataTableParams, settings) {
            var data= formatDataTableParams(dataTableParams, settings);
            data['organization'] = $('#id_organization').val();
            data['laboratory'] = $('#id_laboratory').val();
            data['shelf'] = tableObject.get_active_shelf;
            return data;
        }
    }
    }, addfilter=false);
    //shelfselected

$('input[name="shelfselected"]').change(function(){
    datatableelement.ajax.reload();
});

});

$(document).ready(function(){
    var $input = $('input[name=tags-search]')
        .tagify({
                whitelist : [
                    {"id":1, "value":"some string"}
                ]
            })
            .on('add', function(e, tagName){
                console.log('JQEURY EVENT: ', 'added', tagName)
            })
            .on("invalid", function(e, tagName) {
                console.log('JQEURY EVENT: ',"invalid", e, ' ', tagName);
            });

    // get the Tagify instance assigned for this jQuery input object so its methods could be accessed
    var jqTagify = $input.data('tagify');
});





