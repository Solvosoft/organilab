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

function load_errors(error_list, obj, display_on_top=false){
    ul_obj = "<ul class='errorlist form_errors d-flex justify-content-center'>";
    error_list.forEach((item)=>{
        ul_obj += "<li>"+item+"</li>";
    });
    ul_obj += "</ul>"
    var obj_to_prepend = display_on_top ? $(obj) : $(obj).parents(".form-group");
    obj_to_prepend.prepend(ul_obj);
    return ul_obj;
}

function form_field_errors(target_form, form_errors, prefix){
    var item = "";
    for (const [key, value] of Object.entries(form_errors)) {
        item = " #id_" +prefix+key;
        if(target_form.find(item).length > 0){
            if(target_form.find(item).attr("type") == "hidden"){
                // for hidden elements the errors are displayed at the top of the form
                load_errors(form_errors[key], target_form, display_on_top=true);
            }else{
               load_errors(form_errors[key], item);
            }
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

    // reset iCheck elements
    $(form).find("input[type='radio']").prop('checked', false);
    $(form).find("input[type='radio']").iCheck('update');

    // reset everything else
    $(form).trigger('reset');
    $(form).find("select option:selected").prop("selected", false);
    $(form).find("select").val(null).trigger('change');
    $(form).find("ul.form_errors").remove();
}


function get_creation_help(){
    return [
        [gettext("Status"), gettext("It is a feature related to the physical properties of this element, some examples "+
        "could be volatile, fragile, poor state, good condition.")],
        [gettext("Measurement Unit"), gettext("It is filtered by the shelf's measurement unit.")],
        [gettext("Quantity"), gettext("There is no limit if the shelf has infinite quantity setup, in any other "+
         "case the capacity is restricted.")]
    ]
}


function add_creation_help_func(div, objecttype){
    if(div.find('div.shelfinfocontainer').length){
        var creation_help_list = get_creation_help();
        var title = "<label>"+gettext("General Information")+"</label>";
        var creation_help = "<div class='container px-3 pt-3 creation_help'>"+title+"<div class='card card-body'>";
        var creation_length = creation_help_list.length - 1;

        $.each(creation_help_list, function(value) {
            var div_class = 'row';
            if(value < creation_length) {
                div_class += ' mb-3';
            }
            creation_help += "<div class='"+div_class+"'><div class='col-sm-4'>";
            creation_help += "<label><b>"+creation_help_list[value][0]+":</b><label></div>";
            creation_help += "<div class='col-sm-8'>"+creation_help_list[value][1]+"</div></div>";

        });

        if(!objecttype){

            var div_class = 'row mt-3';
            creation_help += "<div class='"+div_class+"'><div class='col-sm-4'>";
            creation_help += "<label><b>"+gettext("Container")+":</b><label></div>";
            creation_help += "<div class='col-sm-8'>" + gettext("This field represents a material object like a box, "+
            "a bottle, a tank, or a tin that will be responsible for containing a substance.  As a requirement, the "+
            "container object needs to be registered on this laboratory as a material.") +"</div></div>";

        }

         creation_help += "</div></div>";
        $(div).append(creation_help);
    }else{
        setTimeout(function(){
            add_creation_help_func(div, objecttype);
        }, 10);
    }
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
                        }else{
                            let error_msg = gettext('There was a problem performing your request. Please try again later or contact the administrator.');  // any other error
                            if(xhr.responseJSON.detail){
                                error_msg = xhr.responseJSON.detail;
                            }
                            Swal.fire({
                                icon: 'error',
                                title: gettext('Error'),
                                text: error_msg
                            });
                        }
                        instance.error(instance, xhr, resp, text);
                    }
                });
            }
        },
        "showShelfInfo": function(div, id_shelf, position='top'){
            $.ajax({
                url: document.urls.shelf_availability_information,
                type: 'GET',
                data: {'shelf': id_shelf, 'position': position},
                headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': "application/json"},
                success: function(data){
                    if(div.find('div.shelfinfocontainer').length){
                        div.find('div.shelfinfocontainer').remove();
                    }
                    div.prepend(data.shelf_info);
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
            var shelf = $(btninstance).data('shelf');
            var add_creation_help = $(btninstance).data('add_creation_help');
            var objecttype = $(btninstance).data('objecttype');

            if (shelf_object != undefined){
                this.data_extras['shelf_object'] = shelf_object;
                $("#id_shelfobject").val(shelf_object);
            }

            var info_shelf = this.instance.find('div.info_shelf');
            var position = this.instance.find('input[name="position"]');

            if (info_shelf != undefined && shelf != undefined && position != undefined){
                this.showShelfInfo($(info_shelf[0]), shelf, position=$(position[0]).val());
                if(add_creation_help && !$(info_shelf[0]).find("div.creation_help").length){
                   add_creation_help_func($(info_shelf[0]), objecttype);
                }
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

function show_update_status_modal(instance, event){
    var modalid= $(instance).data('modalid');

    if(!form_modals.hasOwnProperty(modalid) ){
        var formmodal= BaseFormModal("#"+modalid);
        formmodal.init(instance);
        form_modals[modalid]=formmodal;
    }
    form_modals[modalid].showmodal(instance);
    form_modals[modalid].type='PUT';
    form_modals[modalid].success=function(instance,data){
        $("#shelfobject_status").text(data['shelfobject_status'])

    }

    return false;
}

$('#id_move-lab_room').on('change', function(){
    $('#id_move-furniture').val(null).trigger('change');
});

$('#id_move-furniture').on('change', function(){
    $('#id_move-shelf').val(null).trigger('change');
});
