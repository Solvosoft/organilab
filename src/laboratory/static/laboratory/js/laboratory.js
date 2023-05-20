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
        "instance": modal,
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
    showTransfers: function(data){
        if (tableObject.get_active_shelf() != undefined){
            // make sure to get the latest data on the table before opening the modal
            $('#transfer-list-datatable').DataTable().ajax.reload();
            $("#transfer-list-modal").modal('show');
        }
    },
    get_active_shelf: function(show_alert=true){
         let value= $('input[name="shelfselected"]:checked').val();
         if(value == undefined && show_alert){
            Swal.fire({
                icon: 'info',
                title: gettext('No shelf selected'),
                text: gettext('You need to select a shelf before performing this action.'),
            });
         }
         return value;
    },
    update_object: function(obj){
        datatableelement.rows( function ( idx, data, node ) {
                                return data.pk == obj.pk;
                            } ).data(obj).draw();
    }

};

// transfer delete (option inside transfer in table)
function transferInObjectDeny(btn) {
    let transferListDataTable = $('#transfer-list-datatable').DataTable()
    let transfer_data = transferListDataTable.row($(btn).closest('tr')).data();
    let message = gettext("Are you sure you want to deny the transfer of")
    message = `${message} "${transfer_data.object}"?`
    Swal.fire({ //Confirmation for delete
        icon: "warning",
        title: gettext("Are you sure?"),
        text: message,
        confirmButtonText: gettext("Confirm"),
        showCloseButton: true,
        denyButtonText: gettext('Cancel'),
        showDenyButton: true,
        })
        .then(function(result) {
            if (result.isConfirmed) {
                fetch(document.urls.transfer_in_deny, {
                    method: "delete",
                    headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'},
                    body: JSON.stringify({'transfer_object': transfer_data.id})})
                    .then(response => {
                        if(response.ok){ return response.json(); }
                        return Promise.reject(response);  // then it will go to the catch if it is an error code
                    })
                    .then(data => {
                        Swal.fire({
                            title: gettext('Success'),
                            text: data['detail'],
                            icon: 'success',
                            timer: 1500
                        });
                        transferListDataTable.ajax.reload();
                    })
                    .catch(response => {
                        let error_msg = gettext('There was a problem performing your request. Please try again later or contact the administrator.');  // any other error
                        response.json().then(data => {  // there was something in the response from the API regarding validation
                            if(data['transfer_object']){
                                error_msg = data['transfer_object'][0];  // specific api validation errors
                            }
                        })
                        .finally(() => {
                            Swal.fire({
                                title: gettext('Error'),
                                text: error_msg,
                                icon: 'error'
                            });
                        });
                    });
            }
    })
}

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
            {data: "object_type", name: "object__type", title: gettext("Type"), type: "string", visible: true},
            {data: "object_name", name: "object__name", title: gettext("Name"), type: "string", visible: true},
            {data: "quantity", name: "quantity", title: gettext("Quantity"), type: "string", visible: true },
            {data: "unit", name: "measurement_unit__description", title: gettext("Unit"), type: "string", visible: true},
            {data: "container", name: "shelfobjectcontainer__container__name", title: gettext("Container"), type: "string", visible: true},
            {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true, filterable: false, sortable: false},
        ],
        buttons: [
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
                action: tableObject.showTransfers,
                text: '<i class="fa fa-exchange" aria-hidden="true"></i>',
                titleAttr: gettext('Transfer In'),
                className: 'btn-sm btn-success ml-4'
            },
        ],
        dom: "<'d-flex justify-content-between'<'m-2'l>" +
        "<'m-2'B><'m-2 d-flex justify-content-start'f>>" +
        "<'row'tr><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7 m-auto'p>>",
        ajax: {
            url: document.url_shelfobject,
            type: 'GET',
            data: function(dataTableParams, settings) {
                var data= formatDataTableParams(dataTableParams, settings);
                data['organization'] = $('#id_organization').val();
                data['laboratory'] = $('#id_laboratory').val();
                data['shelf'] = tableObject.get_active_shelf(show_alert=false);
                return data;
            }
        }
    }, addfilter=false);

    function objShowBool(data, type, row, meta){ return data ? '<i class="fa fa-check-circle" title="' + data + '">': '<i class="fa fa-times-circle" title="' +  data + '">'; };
    createDataTable('#transfer-list-datatable', document.urls.transfer_list, {
        columns: [
            {data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
            {data: "object", name: "object__object__name", title: gettext("Object"), type: "string", visible: true},
            {data: "quantity", name: "quantity", title: gettext("Quantity"), type: "string", visible: true},
            {data: "laboratory_send", name: "laboratory_send__name", title: gettext("Laboratory Send"), type: "string", visible: true },
            {data: "mark_as_discard", name: "mark_as_discard", title: gettext("Mark as Discard"), type: "boolean", render: objShowBool, visible: true },
            {data: "update_time", name: "update_time", title: gettext("Date"), type: "date", render: DataTable.render.datetime(), visible: true},
            {data: null, title: gettext('Actions'), sortable: false, filterable: false,
             defaultContent: `<a href="#" class='btn btn-sm btn-outline-success' title='Approve'><i class="fa fa-check-circle"></i></a>
                              <a onclick="transferInObjectDeny(this);" class='btn btn-sm btn-outline-danger' title='Deny'><i class="fa fa-times-circle"></i></a>`
            }
        ],
        paging: true,
        buttons: [],
        deferLoading: true,
        dom: "<'row'<'col-sm-4 col-md-4 d-flex justify-content-start'l>" +
        "<'col-sm-7 col-md-7 mt-1 d-flex justify-content-end'f>>" +
        "<'row'<'col-sm-12'tr>><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7 m-auto'p>>",
        ajax: {
           url: document.urls.transfer_list,
           type: 'GET',
           data: function(dataTableParams, settings) {
               var data= formatDataTableParams(dataTableParams, settings);
               data['organization'] = $('#id_organization').val();
               data['laboratory'] = $('#id_laboratory').val();
               return data;
           }
       }
    }, 
    addfilter=false);

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
                console.log('JQUERY EVENT: ', 'added', tagName)
            })
            .on("invalid", function(e, tagName) {
                console.log('JQUERY EVENT: ',"invalid", e, ' ', tagName);
            });

    // get the Tagify instance assigned for this jQuery input object so its methods could be accessed
    var jqTagify = $input.data('tagify');
});





