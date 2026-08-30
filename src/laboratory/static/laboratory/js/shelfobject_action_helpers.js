/* Ayudantes de las acciones de un objeto en un estante.
 *
 * Estaban dentro de laboratory.js, que mezcla dos cosas: el cableado del
 * arbol y la tabla de la vista antigua, y estos ayudantes, que solo abren y
 * rellenan los modales de accion. Al vivir en su propio archivo los cargan
 * las dos pantallas -- la antigua y el labview -- y las acciones de objeto no
 * hay que reescribirlas.
 */


const tableObject={
    clearFilters: function ( e, dt, node, config ) {clearDataTableFilters(dt, id)},
    addObjectOk: function(data){
         datatableelement.ajax.reload();
    },
    addObjectResponse: function(datarequest){
            let id=""
            let modalid=""
            let prefix_id=""
            discard= document.shelf_discard.toLowerCase()==='true';
            if(objecttype==0){
                modalid="reactive_modal";
                  id='#id_rf-';
                  prefix_id = "rf-"
                if(discard){
                  modalid="reactive_refuse_modal";
                    id='#id_rff-';
                    prefix_id="rff-"
                }
                update_selects(id+"recipient",{})
                show_hide_container_selects("#"+modalid,"none", prefix=prefix_id)
            }else if(objecttype==1){
                    modalid="material_modal";
                    id='#id_mf-';
                    if(discard){
                        modalid="material_refuse_modal";
                        id='#id_mff-';
                   }
            }else{
                    modalid="equipment_modal";
                    id='#id_ef-';
                if(discard){
                    modalid="equipment_refuse_modal";
                    id='#id_erf-';
                }
            }
            document.prefix=id;
            shelf_action_modals(modalid, datarequest['shelf'], objecttype)
            $(document.prefix+"without_limit").prop('checked', true);
            if(!discard){
                $(document.prefix+"marked_as_discard").prop('checked', false);
            }

    },
    addObject: function( e, dt, node, config ){
        let activeshelf=tableObject.get_active_shelf();
        if (activeshelf == undefined){
            return 1;
        }
        objecttype=e.currentTarget.dataset.type;
        datarequest ={'shelf':activeshelf,
               'objecttype': objecttype
               }
       tableObject.addObjectResponse(datarequest)
    },
    showTransfers: function(data){
        if (tableObject.get_active_shelf() != undefined){
            // make sure to get the latest data on the table before opening the modal
            $('#transfer-list-datatable').DataTable().ajax.reload();
            $("#transfer-list-modal").modal('show');
        }
    },
    redirectContainer: function(data){
        if (tableObject.get_active_shelf() != undefined){
            window.location.href=document.url_container_list+"?shelf="+tableObject.get_active_shelf()
        }
    },
    get_active_shelf: function(show_alert=true){
         let radio = $('input[name="shelfselected"]:checked');
         let value = radio.val();
         if (value !== undefined) {
            document.shelf_discard = radio.data('refuse');
         } else if ($('input[name="shelfselected"]').length === 0) {
            // El labview no dibuja radios: el estante elegido vive en #id_shelf
            // y su marca de descarte la publica la propia vista.
            value = $("#id_shelf").val() || undefined;
         }
         if(value == undefined && show_alert){
            Swal.fire({
                icon: 'info',
                title: gettext('No shelf selected'),
                text: gettext('You need to select a shelf before performing this action.'),
            });
         }else{
            $("#id_shelf").val(value)
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
    message = `${message} "${transfer_data.object.name}"?`
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
                    body: JSON.stringify({'transfer_object': transfer_data.id, 'shelf': tableObject.get_active_shelf()})})
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
                            if(data['errors'] && data.errors['transfer_object']){
                                error_msg = data.errors['transfer_object'][0];  // specific api validation errors
                            }else if(data['detail']){
                                error_msg = data['detail'];
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

function transferInObjectApprove(btn, event){
    let transferListDataTable = $('#transfer-list-datatable').DataTable()
    let transfer_data = transferListDataTable.row($(btn).closest('tr')).data();
    let shelfObjectDataTable = datatableelement;
    if(transfer_data.object.type === '0'&& !transfer_data.is_box){  // type - Reactive
        show_hide_container_selects("#transfer_in_approve_with_container_form", 'none');
        $("#transfer_in_approve_with_container_form #id_transfer_object").val(transfer_data.id);
        $("#transfer_in_approve_with_container_form #id_shelf").val(tableObject.get_active_shelf());
        $("#transfer-list-modal").modal('hide');
        show_me_modal(btn, event);
        form_modals[$(btn).data('modalid')].hidemodal = function(){  // it is called also after the form is submitted
            this.instance.modal('hide');
            transferListDataTable.ajax.reload();
            $("#transfer-list-modal").modal('show');
        }
    }else{
        $.ajax({
            type: "POST",
            headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'},
            url: document.urls.transfer_in_approve,
            data: JSON.stringify({'transfer_object': transfer_data.id, 'shelf': tableObject.get_active_shelf()}),
            success: function(data){
                Swal.fire({ title: gettext('Success'), text: data['detail'], icon: 'success', timer: 1500 });
                transferListDataTable.ajax.reload();
                shelfObjectDataTable.ajax.reload();
            },
            error: function(data){
                let error_msg = gettext('There was a problem performing your request. Please try again later or contact the administrator.');  // any other error
                if(data.responseJSON.errors && data.responseJSON.errors.transfer_object){
                    error_msg = data.responseJSON.errors.transfer_object.join(" ");  // specific api validation errors
                }else if(data.responseJSON.detail){
                    error_msg = data.responseJSON.detail;
                }
                Swal.fire({ title: gettext('Error'), text: error_msg, icon: 'error' });
            }
        });
    }
}

/* La tabla de transferencias entrantes y los botones de la tabla de objetos.
 *
 * Estaban dentro del `$(document).ready` de laboratory.js, que solo corre en la
 * vista antigua. Como funciones las usan las dos pantallas y ninguna de las dos
 * reimplementa "crear objeto", "contenedores" ni "transferencias entrantes".
 */
function init_transfer_list_table(){
    function objShowBool(data, type, row, meta){ return data ? '<i class="fa fa-check-circle" title="' + data + '">': '<i class="fa fa-times-circle" title="' +  data + '">'; };
    createDataTable('#transfer-list-datatable', document.urls.transfer_list, {
        columns: [
            {data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
            {data: "object.name", name: "object__object__name", title: gettext("Object"), type: "string", visible: true},
            {data: "quantity", name: "quantity", title: gettext("Quantity"), type: "string", visible: true},
            {data: "laboratory_send", name: "laboratory_send__name", title: gettext("Laboratory Send"), type: "string", visible: true },
            {data: "mark_as_discard", name: "mark_as_discard", title: gettext("Mark as Discard"), type: "boolean", render: objShowBool, visible: true },
            {data: "update_time", name: "update_time", title: gettext("Date"), type: "date", render: DataTable.render.datetime(), visible: true},
            {data: null, title: gettext('Actions'), sortable: false, filterable: false,
             defaultContent: `<a onclick="transferInObjectApprove(this, event);" data-modalid="transfer_in_approve_with_container_id_modal" class='btn btn-sm btn-outline-success' title='` + gettext('Approve') + `'><i class="fa fa-check-circle"></i></a>
                              <a onclick="transferInObjectDeny(this);" class='btn btn-sm btn-outline-danger' title='` + gettext('Deny') + `'><i class="fa fa-times-circle"></i></a>`
            }
        ],
        paging: true,
        buttons: [],
        deferLoading: true,
        layout: {
            topStart: 'pageLength',
            topEnd: 'search',
            bottomStart: 'info',
            bottomEnd: 'paging'
        },
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
}

function get_shelfobject_table_buttons(){
    var buttons = [];
    if (typeof can_add_shelfobject !== 'undefined' && can_add_shelfobject) {
        buttons.push(
            {
                action: tableObject.addObject,
                text: '<i class="fa fa-desktop" aria-hidden="true"></i>',
                titleAttr: gettext('Create Equipment'),
                className: 'btn-sm btn-success ml-4',
                attr: {'data-type': '2'}
            },
            {
                action: tableObject.addObject,
                text: '<i class="fa fa-battery-quarter" aria-hidden="true"></i>',
                titleAttr: gettext('Create Material'),
                className: 'btn-sm btn-success ml-4',
                attr: {'data-type': '1'}
            },
            {
                action: tableObject.addObject,
                text: '<i class="fa fa-flask" aria-hidden="true"></i>',
                titleAttr: gettext('Create Substance'),
                className: 'btn-sm btn-success ml-4',
                attr: {'data-type': '0'}
            },
            {
                action: tableObject.redirectContainer,
                text: '<i class="fa fa-cubes" aria-hidden="true"></i>',
                titleAttr: gettext('Containers'),
                className: 'btn-sm btn-success ml-4'
            }
        );
    }
    if (typeof has_perm !== 'undefined' && has_perm.transfer) {
        buttons.push({
            action: tableObject.showTransfers,
            text: '<i class="fa fa-exchange" aria-hidden="true"></i>',
            titleAttr: gettext('Transfer In'),
            className: 'btn-sm btn-success ml-4'
        });
    }
    return buttons;
}

var objecttype= "";
document.shelf_discard = undefined;
document.prefix="";

function shelf_action_modals(modalid, shelf, objecttype){
    var label_a = document.createElement("a");
    label_a.setAttribute("data-modalid", modalid);
    label_a.setAttribute("data-shelf", shelf);
    label_a.setAttribute("data-add_creation_help", true);
    label_a.setAttribute("data-objecttype", objecttype);
    show_me_modal(label_a, null);
    form_modals[modalid].data_extras['shelf']=$("#id_shelf").val();
    show_hide_limits($(`${document.prefix}without_limit`), document.prefix);
    return false;
}

// El enlace "+ Nuevo estado" lo inyecta el help_text de nueve formularios de
// objeto; su manejador estaba solo en laboratory.js, de modo que en cualquier
// pantalla que no cargara ese archivo el enlace aparecía y no hacía nada.
$(".add_status").click(function(){
    add_status(document.url_status)
});

$(".check_limit").on('change', function(event){
    show_hide_limits(this,document.prefix)
})


function show_hide_limits(e,prefix){
    if($(e).is(":checked")){
        $(prefix+'minimum_limit').val(0).parent().parent().hide();
        $(prefix+'maximum_limit').val(0).parent().parent().hide();
        $(prefix+'expiration_date').parent().parent().parent().hide();
    }else{
        $(prefix+'minimum_limit').parent().parent().show();
        $(prefix+'maximum_limit').parent().parent().show();
        $(prefix+'expiration_date').parent().parent().parent().show();
    }
}

function reset_container_selects(form_id,select_id){
    $(form_id).find(select_id+" option:selected").prop("selected", false);
    $(form_id).find(select_id).val(null).trigger('change');
}
function show_hide_container_selects(form_id, selected_value, prefix=""){
    // they are hidden for the other options, so hide them by default and just display one if required
    $(form_id).find("#id_"+prefix+"available_container").parents(".form-group").hide();
    $(form_id).find("#id_"+prefix+"container_for_cloning").parents(".form-group").hide();
    if(selected_value === 'available'){
        $(form_id).find("#id_"+prefix+"available_container").parents('.form-group').show();
        reset_container_selects(form_id,"#id_"+prefix+"container_for_cloning")
    }else if(selected_value === 'clone'){
        $(form_id).find("#id_"+prefix+"container_for_cloning").parents('.form-group').show();
        reset_container_selects(form_id,"#id_"+prefix+"available_container")
    }else{
        reset_container_selects(form_id,"#id_"+prefix+"container_for_cloning")
        reset_container_selects(form_id,"#id_"+prefix+"available_container")
   }
}

$("#transfer_in_approve_with_container_form #id_container_select_option").on('change', function(event){
    show_hide_container_selects("#transfer_in_approve_with_container_form", event.target.value);
});

$("#reactive_refuse_form #id_rff-container_select_option").on('change', function(event){
    show_hide_container_selects("#reactive_refuse_form", event.target.value, prefix="rff-");

});

$("#reactive_form #id_rf-container_select_option").on('change', function(event){
    show_hide_container_selects("#reactive_form", event.target.value, prefix="rf-");
});


$("#movesocontainerform #id_movewithcontainer-container_select_option").on('change', function(event){
    show_hide_container_selects("#movesocontainerform", event.target.value, prefix="movewithcontainer-");
});

$('#movesocontainermodal').on('show.bs.modal', function (e) {
    var row = "<div class='form-group row my-3' id='div_separator_container' style='border-bottom: 1px solid #dee2e6;'></div>";
    if($("#movesocontainerform #div_separator_container").length == 0){
        $("#id_movewithcontainer-container_select_option").parents(".form-group").before(row);
    }
    show_hide_container_selects("#movesocontainerform", "none", prefix="movewithcontainer-");
});


function ContainerUpdateForm(elementid, shelfobject, container, containername){
    let obj={
        "elementid": elementid,
        "element": $("#"+elementid),
        "shelfobject": shelfobject,
        "container": container,
        'radio_action_id': 'input[name="mc-container_select_option"]',
        'select_shelfobject_c': 'select[name="mc-available_container"]',
        'select_object_c': 'select[name="mc-container_for_cloning"]',
        "init": function(){
             $(this.radio_action_id).on('change', (function(instance){ return (event)=>{instance.onchange_event(event)};})(this));
        },
        'onchange_event': function(event){
            if($(event.target).prop('checked')){
                show_hide_container_selects('#managecontainermodal', $(event.target).val(), prefix="mc-");
            }
        },
        'set_shelfobject': function(shelfobject, container, containername){
            this.shelfobject=shelfobject;
            this.container=container;
            $("#id_container").val(container);
            if(container != "" && container != undefined){
                var newOption = new Option(containername, container, true, true);
                $(this.select_shelfobject_c).append(newOption);
                $(this.select_shelfobject_c).trigger('change');

            }
            this.update_shelfobject_filters();
        },
        'update_shelfobject_filters': function(){
            if(this.container == "" || this.container == undefined){
                $(this.radio_action_id+'[value=clone]').prop('checked', true);
                $(this.radio_action_id).trigger('change');
            }else{
                $(this.radio_action_id+'[value=available]').prop('checked', true);
                $(this.radio_action_id).trigger('change');
            }
        }

    }
    obj.init();
    obj.set_shelfobject(shelfobject, container, containername);
    return obj;
}

function updateContainerOfShelfObject(instance, event){
    var modalid= $(instance).data('modalid');
    let is_created = form_modals.hasOwnProperty(modalid);
    show_me_modal(instance, event);
    if(!is_created){
        form_modals[modalid].containermanagement=ContainerUpdateForm
        (modalid, $(instance).data('shelfobject'), $(instance).data('container'),  $(instance).data('containername'));
    }else{
        form_modals[modalid].containermanagement.set_shelfobject(
        $(instance).data('shelfobject'), $(instance).data('container'),  $(instance).data('containername'));
    }
    $('input[name="mc-shelf"]').val($('#id_shelf').val());
}


function editBoxShelfObject(instance, event) {
    var modalid = $(instance).data('modalid');
    var form = $(instance).data('form');
    var shelfobjectPk = $(instance).data('shelfobject');
    var updateUrl = document.urls["update_box_shelfobject"].replace('0', shelfobjectPk);

    document.getElementById(form).action = updateUrl;

    if (form_modals.hasOwnProperty(modalid)) {
        delete form_modals[modalid];
        $("#edit_box_modal").find('.formadd').off('click');
    }
    show_me_modal(instance, event);
    form_modals[modalid].type = 'PUT';

    // Pre-populate form fields from current box data
    var dataUrl = document.urls["get_box_edit_data"].replace('0', shelfobjectPk);
    $.ajax({
        url: dataUrl,
        type: "GET",
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function (data) {
            // Plain inputs
            $('#id_ubf-description').val(data.description);
            $('#id_ubf-batch').val(data.batch);
            $('#id_ubf-reactive_expiration_date').val(data.reactive_expiration_date).trigger('change');
            $('#id_ubf-quantity').val(data.quantity);
            $('#id_ubf-concentration').val(data.concentration);
            $('#id_ubf-units_per_box').val(data.units_per_box);
            $('#id_ubf-quantity_box').val(data.quantity_box);

            // Regular select
            $('#id_ubf-physical_status').val(data.physical_status).trigger('change');

            // Select2 AJAX fields: create Option with text so it renders correctly
            function setSelect2(selector, item) {
                if (!item) return;
                var $el = $(selector);
                $el.find('option[value="' + item.id + '"]').remove();
                $el.append(new Option(item.text, item.id, true, true)).trigger('change');
            }
            setSelect2('#id_ubf-object', data.object);
            setSelect2('#id_ubf-status', data.status);
            setSelect2('#id_ubf-measurement_unit', data.measurement_unit);
            setSelect2('#id_ubf-type_budget', data.type_budget);

            // Checkbox was_donated
            if (data.was_donated) {
                $('#id_ubf-was_donated').prop('checked', true).trigger('change');
            } else {
                $('#id_ubf-was_donated').prop('checked', false).trigger('change');
            }
        }
    });
}

function editReactiveShelfObject(instance, event){
    var modalid= $(instance).data('modalid');
    form = $(instance).data('form');
    let is_created = form_modals.hasOwnProperty(modalid);
    edit_shelfobject_url = document.urls["edit_shelfobject"].replace('0',$(instance).data('shelfobject'))
    document.getElementById(form).action = edit_shelfobject_url;
    if(form_modals.hasOwnProperty(modalid)){
        delete form_modals[modalid]
        $("#edit_reactive_modal").find('.formadd').off('click');
    }
    show_me_modal(instance, event);
    form_modals[modalid].type='PUT';
    get_shelfobject_data($(instance).data('shelfobject'));

}

$(".lock_limits").on('change', function(event){

    show_hide_limits(this,"#"+this.dataset.prefix)

})

function get_shelfobject_data(shelfobject){
    edit_shelfobject_url = document.urls["get_shelfobject_data"].replace('0',shelfobject)
    $.ajax({
        url: edit_shelfobject_url,
        type: "GET",
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'},
        success: function(data){
            document.querySelector("#id_edit-minimum_limit").value = data.minimum_limit;
            document.querySelector("#id_edit-maximum_limit").value = data.maximum_limit;
            document.querySelector("#id_edit-description").value = data.description;
            document.querySelector("#id_edit-batch").value = data.batch;
            $('#id_edit-reactive_expiration_date').val(data.reactive_expiration_date).trigger('change');
            $('#id_edit-physical_status').val(data.physical_status).trigger('change');
            $('#id_edit-status').val(data.status).trigger('change');
            if(data.type_budget){
                $('#id_edit-type_budget').val(data.type_budget.id).trigger('change');
            }
            document.querySelector("#id_edit-shelfobject_code").value = data.shelfobject_code;
            $('#id_edit-container_entry_date').val(data.container_entry_date).trigger('change');
            $('#id_edit-container_open_date').val(data.container_open_date).trigger('change');
            if(data.was_donated) {
                $('#id_edit-was_donated').prop('checked', true).trigger('change');
            }
        $('#id_edit-without_limit')
            .prop('checked', data.minimum_limit == 0 && data.maximum_limit == 0)
            .trigger('change');

            $('#id_edit-pictograms').val(null).trigger('change');
              if (data.pictograms.length > 0) {
                  if (Array.isArray(data.pictograms)) {
                        for (var x = 0; x < data.pictograms.length; x++) {
                            $('#id_edit-pictograms option[value="' + data.pictograms[x]['id'] + '"]').remove();
                            var newOption = new Option(data.pictograms[x]["text"], data.pictograms[x]['id'], true, true);
                            $('#id_edit-pictograms').append(newOption);
                        }
                    }
                    $('#id_edit-pictograms').trigger('change')
                }

         show_hide_limits($(".lock_limits"),"#id_edit-");


        }
    });
}

function editMaterialShelfObject(instance, event){
    var modalid= $(instance).data('modalid');
    form = $(instance).data('form');
    let is_created = form_modals.hasOwnProperty(modalid);
    edit_shelfobject_url = document.urls["edit_material_shelfobject"].replace('0',$(instance).data('shelfobject'))
    document.getElementById(form).action = edit_shelfobject_url;
    if(form_modals.hasOwnProperty(modalid)){
        delete form_modals[modalid]
        $("#edit_material_modal").find('.formadd').off('click');

    }
    show_me_modal(instance, event);
    form_modals[modalid].type='PUT';
    form_modals[modalid].action = edit_shelfobject_url;
    get_material_shelfobject_data($(instance).data('shelfobject'));

}

function get_material_shelfobject_data(shelfobject){
    edit_shelfobject_url = document.urls["get_shelfobject_limits"].replace('0',shelfobject)
    $.ajax({
        url: edit_shelfobject_url,
        type: "GET",
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'},
        success: function(data){
        document.querySelector("#id_edit_material-description").value = data.description;
        document.querySelector("#id_edit_material-minimum_limit").value = data.minimum_limit;
        document.querySelector("#id_edit_material-maximum_limit").value = data.maximum_limit;
        document.querySelector("#id_edit_material-expiration_date").value = data.expiration_date;
        document.querySelector("#id_edit_material-batch").value = data.batch;
        document.querySelector("#id_edit_material-shelfobject_code").value = data.shelfobject_code;
        $('#id_edit_material-status').val(data.status).trigger('change');
        if(data.was_donated) {
            $('#id_edit_material-was_donated').prop('checked', true).trigger('change');
        }
        $('#id_edit_material-without_limit')
            .prop('checked', data.minimum_limit == 0 && data.maximum_limit == 0)
            .trigger('change');
         show_hide_limits($(".lock_limits"),"#id_edit_material-");
        }
    });
    }


function displayShelfobjectLabels(data) {
     if ($.fn.DataTable.isDataTable('#recipient_datatable')) {
      $('#recipient_datatable').DataTable().destroy();
      $('#recipient_datatable').empty(); // Limpia el thead/tbody generado
  }
  let reagent_id = $(data).data('object');
  createDataTable('#recipient_datatable', $(data).data('url'), {
        columns: [
            {data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
            {data: "name", name: "name", title: gettext("Object"), type: "string", visible: true},
            {data: "height", name: "height", title: gettext("Height"), type: "string", visible: true},
            {data: "width", name: "width", title: gettext("Width"), type: "string", visible: true},
            {data: "unit", name: "unit", title: gettext("Unit"), type: "string", visible: true},
            {data: null, title: gettext('Actions'), sortable: false, filterable: false,
             render: function(rowData, type, row) {
                 let url = $(data).data('recipient').replace('0', row.id);
                 let buttons_actions= `<a class='btn btn-sm btn-outline-success' download href='${url}' title='${gettext('Download')}'><i class="fa fa-download"></i></a>`;
                 if(has_perm.remove){
                         buttons_actions+=`<a class='btn btn-sm btn-outline-danger delete_recipient' title='${gettext('Delete')}'><i class="fa fa-trash"></i></a>`;
                 }
                 return buttons_actions;
             }
            }
        ],
        paging: true,
        buttons: [],
        deferLoading: true,
        layout: {
            topStart: 'pageLength',
            topEnd: 'search',
            bottomStart: 'info',
            bottomEnd: 'paging'
        },
        ajax: {
           url: $(data).data('url'),
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
    setTimeout(function(){
        $('#recipient_datatable').DataTable().ajax.reload();
                 $('#recipient_modal').modal('show')

    }
    , 100);

}
$(document).on('click', '.add_recipient', function(e) {
    e.preventDefault();
    let formId = $(this).data('form');
    let form = $('#' + formId);
    let url = form.attr('action');
    let formData = form.serialize();
    formData = convertToStringJson(form, "recipient-")

    $.ajax({
        url: url,
        type: 'POST',
        data: formData,
        contentType: 'application/json',
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function(response) {
            Swal.fire({
                icon: 'success',
                title: gettext('Success'),
                text: response.detail || gettext('Recipient size was created successfully.'),
                timer: 1500
            });
            form[0].reset();
            $('#recipient_datatable').DataTable().ajax.reload();
            $('#recipient_modal_tab1_btn').tab('show');
        },
        error: function(xhr) {
            let errorMsg = gettext('There was a problem performing your request.');
            if (xhr.responseJSON && xhr.responseJSON.errors) {
                let errors = xhr.responseJSON.errors;
                let errorList = [];
                for (let field in errors) {
                    errorList.push(field + ': ' + errors[field].join(', '));
                }
                errorMsg = errorList.join('\n');
            }
            Swal.fire({
                icon: 'error',
                title: gettext('Error'),
                text: errorMsg
            });
        }
    });
});

$(document).on('click', '.delete_recipient', function(e) {
    e.preventDefault();
    let btn = $(this);
    let row = $('#recipient_datatable').DataTable().row(btn.closest('tr'));
    let rowData = row.data();
    let recipient_url = document.delete_recipient_url.replace("/0/", "/"+rowData.id+"/")
    Swal.fire({
        icon: 'warning',
        title: gettext('Are you sure?'),
        text: gettext('Are you sure you want to delete this recipient size?'),
        confirmButtonText: gettext('Confirm'),
        showCloseButton: true,
        denyButtonText: gettext('Cancel'),
        showDenyButton: true,
    }).then(function(result) {
        if (result.isConfirmed) {
            $.ajax({
                url: recipient_url,
                type: 'DELETE',
                data: JSON.stringify({recipient_size: rowData.id}),
                contentType: 'application/json',
                headers: {'X-CSRFToken': getCookie('csrftoken')},
                success: function(response) {
                    Swal.fire({
                        icon: 'success',
                        title: gettext('Success'),
                        text: response.detail || gettext('Recipient size was deleted successfully.'),
                        timer: 1500
                    });
                    $('#recipient_datatable').DataTable().ajax.reload();
                },
                error: function(xhr) {
                    let errorMsg = gettext('There was a problem performing your request.');
                    if (xhr.responseJSON && xhr.responseJSON.errors) {
                        let errors = xhr.responseJSON.errors;
                        let errorList = [];
                        for (let field in errors) {
                            errorList.push(errors[field].join(', '));
                        }
                        errorMsg = errorList.join('\n');
                    } else if (xhr.responseJSON && xhr.responseJSON.detail) {
                        errorMsg = xhr.responseJSON.detail;
                    }
                    Swal.fire({
                        icon: 'error',
                        title: gettext('Error'),
                        text: errorMsg
                    });
                }
            });
        }
    });
});

