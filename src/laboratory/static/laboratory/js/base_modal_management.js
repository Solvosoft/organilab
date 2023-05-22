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
    let prefix=form.find(".form_prefix").val();
        if(prefix.length !== 0){
            prefix = prefix+"-"
        }
    return {
        "instance": modal,
        "reloadtable": true,
        "form": form,
        "url": form[0].action,
        "prefix": prefix,
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
                    headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': "application/json"},
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
                            form_field_errors(form, errors, instance.prefix);
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
        "showShelfInfo": function(div, id_shelf){
            $.ajax({
                url: document.urls.shelf_availability_information,
                type: 'GET',
                data: {'shelf': id_shelf},
                headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': "application/json"},
                success: function(data){
                    div.append(data.shelf_info);
                },
                error: function(xhr, resp, text){
                    Swal.fire({
                        icon: 'error',
                        title: gettext('Error'),
                        text: gettext('There was a problem performing your request. Please try again later or contact the administrator.')
                    });
                }
            });
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
                clear_action_form(instance.form);
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
    var modalid= $(instance).data('modalid');

    if(!form_modals.hasOwnProperty(modalid) ){
        var formmodal= BaseFormModal("#"+modalid);
        formmodal.init(instance);
        form_modals[modalid]=formmodal;
    }
    form_modals[modalid].showmodal(instance);
    return false;
}