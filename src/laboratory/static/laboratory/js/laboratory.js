var objecttype= ""
document.shelf_discard = undefined;
document.prefix=""

function shelf_action_modals(modalid){
    var label_a = document.createElement("a");
    label_a.setAttribute("data-modalid", modalid)
    show_me_modal(label_a,null)
    form_modals[modalid].data_extras['shelf']=$("#id_shelf").val();
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
            discard= document.shelf_discard.toLowerCase()==='true';
            if(objecttype==0){
                modalid="reactive_modal";
                  id='#id_rf-';
                if(discard){
                  modalid="reactive_refuse_modal";
                    id='#id_rff-';
                }
                update_selects(id+"recipient",{})

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
            shelf_action_modals(modalid)
            update_selects(id+"object",datarequest)
            update_selects(id+"status",datarequest)
            update_selects(id+"measurement_unit",{'shelf':datarequest['shelf']})
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

function update_selects(id,data){
    var select = $(id);
    var url = $(select).data('url');

    $.ajax({
      type: "GET",
      url: url,
      data: data,
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      traditional: true,
      dataType: 'json',
      success: function(data){
                         $(select).find('option').remove();
                        for(let x=0; x<data.results.length; x++){
                            $(select).append(new Option(data.results[x].text, data.results[x].id, data.results[x].selected, data.results[x].selected))
                        }
                    },
           });

    }
$(".add_status").click(function(){
    url = document.url_status;
    Swal.fire({
        title: gettext('Create a new status'),
        input: 'text',
        inputAttributes: {required: 'true'},
        showCancelButton: true,
        CancelButtonText: gettext("Cancel"),
        confirmButtonText: gettext("Send"),
    }).then((result) => {
      if(result.value){
      $.ajax({
      type: "POST",
      url: url,
      data: JSON.stringify({"description":result.value}),
      headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': "application/json"},
      dataType: 'JSON',
      success: function(data){
      Swal.fire({
        text: gettext('Saved the new shelfobject status'),
          icon: 'success',
      })
      },
      error: function(xhr, resp, text) {
       Swal.fire({
        title: text,
          icon: 'error',
    })
      }
    })
    }
});
});

$(".check_limit").on('ifChanged', function(event){
    prefix=document.prefix;
    if($(this).is(":checked")){
        $(prefix+'minimum_limit').parent().parent().hide();
        $(prefix+'maximum_limit').parent().parent().hide();
        $(prefix+'expiration_date').parent().parent().parent().hide();
    }else{
        $(prefix+'minimum_limit').parent().parent().show();
        $(prefix+'maximum_limit').parent().parent().show();
        $(prefix+'expiration_date').parent().parent().parent().show();
    }
})