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
            if(!$(document.prefix+"without_limit").parent().hasClass('checked')){
                $(document.prefix+"without_limit").parent().addClass('checked')
            }
            if($(document.prefix+"marked_as_discard").parent().hasClass('checked') && !discard){
                $(document.prefix+"marked_as_discard").parent().removeClass('checked')
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
         let value= $('input[name="shelfselected"]:checked').val();
         document.shelf_discard= $('input[name="shelfselected"]:checked').data('refuse');
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
    let shelfObjectDataTable = $("#shelfobjecttable").DataTable();
    if(transfer_data.object.type === '0'){  // type - Reactive
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
            {data: "pk", name: "pk", title: gettext("Id"), type: "string", visible: true},
            {data: "object_type", name: "object__type", title: gettext("Type"), type: "string", visible: true},
            {data: "object_name", name: "object__name", title: gettext("Name"), type: "string", visible: true},
            {data: "quantity", name: "quantity", title: gettext("Quantity"), type: "string", visible: true },
            {data: "unit", name: "measurement_unit__description", title: gettext("Unit"), type: "string", visible: true},
            {data: "container", name: "container__object__name", title: gettext("Container"), type: "string", visible: true},
            {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true, filterable: false, sortable: false},
        ],
        buttons: [
            {
                action: tableObject.addObject,
                text: '<i class="fa fa-desktop" aria-hidden="true"></i>',
                titleAttr: gettext('Create Equipment'),
                className: 'btn-sm btn-success ml-4',
                attr :{
                    'data-type':'2'

                },
            },
            {
                action: tableObject.addObject,
                text: '<i class="fa fa-battery-quarter" aria-hidden="true"></i>',
                titleAttr: gettext('Create Material'),
                className: 'btn-sm btn-success ml-4',
                attr :{
                    'data-type':'1'
                }
            },
            {
                action: tableObject.addObject,
                text: '<i class="fa fa-flask" aria-hidden="true"></i>',
                titleAttr: gettext('Create Substance'),
                className: 'btn-sm btn-success ml-4',
                attr :{
                    'data-type':'0'
                }

            },
            {
                action: tableObject.redirectContainer,
                text: '<i class="fa fa-cubes" aria-hidden="true"></i>',
                titleAttr: gettext('Containers'),
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

    $('#shelfobjecttable').on( 'init.dt', function () {
        if(document.search_by_url){
            labviewSearch.select_objs(document.search_by_url);
        }
    });
});

var inputElm = document.querySelector('input[name=tags-search]');



const tagify = new Tagify(inputElm, {
    templates : {
        tag : function(tagData){
            try{
                return `<tag title='${tagData.value}' objtype='${tagData.objtype}' pk='${tagData.pk}' style='--tag-bg: ${tagData.color}' contenteditable='false' spellcheck="false" class='tagify__tag ${tagData.class ? tagData.class : ""}' ${this.getAttributes(tagData)}>
                        <x title='remove tag' class='tagify__tag__removeBtn'></x>
                        <div>
                            <span class='tagify__tag-text fs-6'>${tagData.value}</span>
                        </div>
                    </tag>`
            }
            catch(err){}
        },
        dropdownItem : function(tagData){
            try{
                return `<div ${this.getAttributes(tagData)} class='tagify__dropdown__item ${tagData.class ? tagData.class : ""}' >

                            <span class='fs-6' style='background-color: ${tagData.color}; color: black;'>${tagData.value}</span>
                        </div>`
            }
            catch(err){ console.error(err)}
        }
    },
    enforceWhitelist: true,
    whitelist: document.suggestions_tag,
    placeholder: gettext("Search")
});

$("#btnremovealltags").on('click', function(){
    tagify.removeAllTags();
    labviewSearch.restart_objs();
});

tagify.on('add', function(e){
        labviewSearch.search(e.detail.tagify.value);
    }).on("invalid", function(e, tagName){
        console.log('JQUERY EVENT: ',"invalid", e, ' ', tagName);
    }).on('remove', function(e){
        var obj_list = e.detail.tagify.value;

        if(obj_list.length){
            labviewSearch.search(obj_list);
        }else{
            labviewSearch.restart_objs();
        }
    });

$(".add_status").click(function(){
    add_status(document.url_status)
});

$(".check_limit").on('ifChanged', function(event){
    show_hide_limits(this,document.prefix)
})


function show_hide_limits(e,prefix){
    if($(e).is(":checked")){
        $(prefix+'minimum_limit').parent().parent().hide();
        $(prefix+'maximum_limit').parent().parent().hide();
        $(prefix+'expiration_date').parent().parent().parent().hide();
    }else{
        $(prefix+'minimum_limit').parent().parent().show();
        $(prefix+'maximum_limit').parent().parent().show();
        $(prefix+'expiration_date').parent().parent().parent().show();
    }
}

const labviewSearch={
    show_deselected_previous_shelfs: function(shelf_list, key, value){
        var active_shelf = tableObject.get_active_shelf(show_alert=false);
        var shelf_obj = $("#"+key+"_"+active_shelf);

        if(active_shelf != undefined && value != active_shelf && shelf_list.hasOwnProperty('furniture')){
            if(shelf_list['furniture'].hasOwnProperty('furniture')){
                var furniture = $(shelf_obj).parents('li').children('span.furnitureroot');
                if($(furniture).length){
                    var furniture_parent = parseInt($(furniture)[0].id.split("_")[1]);
                    if(shelf_list['furniture']['furniture'].includes(furniture_parent)){
                        $(shelf_obj).parents('.shelfrow').children().show();
                    }
                }
            }
        }
    },
    check_objs: function(obj_list, key){
        obj_list.forEach(function(value) {
            span_obj = "#"+key+"_"+value;

            if($(span_obj).length  && !$(span_obj).hasClass('check-box')){
                $(span_obj).parent().show();
                $(span_obj).click();
            }

            if(key === 'labroom'){
                $(span_obj).next().children().show();
            }else{
                $(span_obj).next().children().find('div.input-group').show();
            }

        });
    },
    check_radios: function(shelf_list, obj_list, key, hide_related_shelf=true){
        obj_list.forEach(function(value) {
            var radio_obj = "#"+key+"_"+value;

            if($(radio_obj).length){
                labviewSearch.show_deselected_previous_shelfs(shelf_list, key, value);
                if(hide_related_shelf){
                    $(radio_obj).parents('.shelfrow').children().hide();
                }else{
                    $(radio_obj).removeClass('hideshelves');
                }
                $(radio_obj).parents('.col').show();
                $(radio_obj).iCheck('check');
                $(radio_obj).change();
            }
        });

        if(!hide_related_shelf){
            $(".hideshelves").parents('.col').hide();
        }
    },
    select_labroom: function(labroom_list){
        labviewSearch.check_objs(labroom_list, "labroom");
    },
    select_furniture: function(furniture_list){
        if(furniture_list.hasOwnProperty('furniture')){
            labviewSearch.check_objs(furniture_list['furniture'], "furniture");
        }
        if(furniture_list.hasOwnProperty('labroom')){
            labviewSearch.select_labroom(furniture_list['labroom']);
        }
    },
    select_shelf: function(shelf_list, hide_related_shelf=true){
        if(shelf_list.hasOwnProperty('shelf')){
            labviewSearch.select_furniture(shelf_list['shelf']);

            if(shelf_list['shelf'].hasOwnProperty('shelf')){
                labviewSearch.check_radios(shelf_list, shelf_list['shelf']['shelf'], "shelf", hide_related_shelf=hide_related_shelf);
            }else{
                labviewSearch.check_radios(shelf_list, shelf_list['shelf'], "shelf", hide_related_shelf=hide_related_shelf);
            }
        }
    },
    select_shelfobject: function(shelfobject_list){
        labviewSearch.select_furniture(shelfobject_list);
        labviewSearch.select_shelf(shelfobject_list);
        var table_filter_input = $('div#shelfobjecttable_filter input[type="search"]');
        if(table_filter_input.length){
            table_filter_input.val('pk='+shelfobject_list['shelfobject'].slice(-1)[0]);
            table_filter_input.focus();
            table_filter_input.keyup();
        }
    },
    select_object: function(object_list){
        labviewSearch.select_shelf(object_list, hide_related_shelf=false);
        var table_filter_input = $('div#shelfobjecttable_filter input[type="search"]');
        if(table_filter_input.length){
            table_filter_input.val(object_list['object'][0]);
            table_filter_input.focus();
            table_filter_input.keyup();
        }

        if(object_list.hasOwnProperty('shelf')){
            if(object_list['shelf'].hasOwnProperty('shelf')){
                var shelf_result = object_list['shelf']['shelf'].length;
               $("#alert_msg").html("<b>"+gettext("Showing first result from ")+ shelf_result +gettext(" matched shelves")+"</b>");
               $("div.alert").addClass('show');
            }
        }
    },
    restart_objs: function(){
        $('input[name="shelfselected"]').iCheck('uncheck').change();
        $("span.check-box").click();
        $('div#shelfobjecttable_filter input[type="search"]').val('').keyup();
        $("span.box").parent().show();
        $('input[type="radio"]').parents('.shelfrow').children().show();
        $("div.alert").removeClass('show');
    },
    select_objs: function(search_list){
        labviewSearch.restart_objs();
        if(Object.keys(search_list).length){
            $("span.box").parent().hide();
            if('labroom' in search_list && Object.keys(search_list['labroom']).length){
                labviewSearch.select_labroom(search_list['labroom']);
            }
            if('furniture' in search_list && Object.keys(search_list['furniture']).length){
                labviewSearch.select_furniture(search_list['furniture']);
            }
            if('shelf' in search_list && Object.keys(search_list['shelf']).length){
                labviewSearch.select_shelf(search_list);
            }
            if('shelfobject' in search_list && Object.keys(search_list['shelfobject']).length){
                labviewSearch.select_shelfobject(search_list['shelfobject']);
            }
            if('object' in search_list && Object.keys(search_list['object']).length){
                labviewSearch.select_object(search_list['object']);
            }
        }
    },
    search: function(q){
        var data = "";

        if(q.length){
            q.forEach(function(item) {
                if(item.objtype == 'laboratoryroom'){
                    data += 'labroom=' + item.pk;
                }else{
                    data += item.objtype + "=" + item.pk;
                }
                data += '&';
            });
            data = data.slice(0, -1);
        }

        $.ajax({
            url: document.urls.search_labview,
            type: "GET",
            dataType: "json",
            data: data,
            traditional: true,
            headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': "application/json"},
            success: function(data){
                labviewSearch.select_objs(data.search_list);
            },
            error: function(xhr, resp, text) {
            }
        });
    }
}

$("#hide_alert").on('click', function(){
    $("#alert_msg").html("");
    $("div.alert").removeClass("show");
});

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

$("#transfer_in_approve_with_container_form #id_container_select_option").on('ifChanged', function(event){
    show_hide_container_selects("#transfer_in_approve_with_container_form", event.target.value);
});

$("#reactive_refuse_form #id_rff-container_select_option").on('ifChanged', function(event){
    show_hide_container_selects("#reactive_refuse_form", event.target.value, prefix="rff-");

});

$("#reactive_form #id_rf-container_select_option").on('ifChanged', function(event){
    show_hide_container_selects("#reactive_form", event.target.value, prefix="rf-");
});


$("#movesocontainerform #id_movewithcontainer-container_select_option").on('ifChanged', function(event){
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
             $(this.radio_action_id).on('ifChanged', (function(instance){ return (event)=>{instance.onchange_event(event)};})(this));
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
                $(this.radio_action_id).iCheck('update');
                $(this.radio_action_id).trigger('ifChanged');
            }else{
                $(this.radio_action_id+'[value=available]').prop('checked', true);
                $(this.radio_action_id).iCheck('update');
                $(this.radio_action_id).trigger('ifChanged');
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

