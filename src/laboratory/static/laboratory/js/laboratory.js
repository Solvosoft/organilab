var objecttype= ""
document.shelf_discard= undefined;
const tableObject={
    clearFilters: function ( e, dt, node, config ) {clearDataTableFilters(dt, id)},
    addObjectOk: function(data){
         datatableelement.ajax.reload();

    },
    addObjectResponse: function(datarequest){
            /**Se va a mejorar**/
            let id=""
            if(objecttype==0){
                if(document.shelf_discard){
                    $("#reactive_refuse_form").modal('show');
                    id='#id_rff-';
                }else{
                    $("#reactive_form").modal('show');
                    id='#id_rf-';
                }
            }else if(objecttype==1){
                if(document.shelf_discard){
                    $("#material_refuse_form").modal('show');
                    id='#id_mff-';
                }else{
                $("#material_form").modal('show');
                    id='#id_mf-';
                }

            }else{
                if(document.shelf_discard){
                    $("#equipment_refuse_form").modal('show');
                    id='#id_erf-';
                }else{
                    $("#equipment_form").modal('show');
                    id='#id_ef-';

                }
            }
            update_selects(id+"object",datarequest)
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
    get_active_shelf: function(){
         let value= $('input[name="shelfselected"]:checked').val();
         document.shelf_discard= $('input[name="shelfselected"]:checked').data('refuse');
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


$('.actionshelfobjmodal').on('show.bs.modal', function (e) {
    var shelfobject = $(this).find("form input[name='shelf_object']")[0];
    $(shelfobject).val(e.relatedTarget.dataset.shelfobject);
    $(this).find("button.actionshelfobjectsave").attr('data-modal', "#"+this.id);
});


function load_errors(error_list, obj){
    ul_obj = "<ul class='errorlist shelf_form_errors'>";
    error_list.forEach((item)=>{
        ul_obj += "<li>"+item+"</li>";
    });
    ul_obj += "</ul>"
    $(obj).before(ul_obj);
    return ul_obj;
}

function form_field_errors(target_form, form_errors){
    var item = "";
    for (const [key, value] of Object.entries(form_errors)) {
        item = " #id_" +key;
        if(target_form.find(item).length > 0){
            load_errors(form_errors[key], item);
        }
    }
}

$(".actionshelfobjectsave").on('click', function(){
    var modal = $(this).data('modal');
    var form = $(modal + " form");

    $.ajax({
        url: $(form)[0].action,
        type:'POST',
        data: $(form).serialize(),
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        success: function(data){
            datatableelement.ajax.reload();
            $(modal).modal('hide');
            Swal.fire({
                icon: 'success',
                title: data.detail,
                showConfirmButton: true,
                timer: 1500
            });     
        },
        error: function(xhr, resp, text) {
            var errors = xhr.responseJSON.errors;
            if(errors){  // form errors
                form.find('ul.shelf_form_errors').remove();
                form_field_errors(form, errors);  
            }else{ // any other error
                Swal.fire({
                    icon: 'error',
                    title: text,
                    text: gettext('There was a problem performing your request. Please try again later or contact the administrator.')
                });
            }
        }
    });
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

function clear_action_form(form){
    $(form).trigger('reset');
    $(form).find("select option:selected").prop("selected", false);
    $(form).find("select").val(null).trigger('change');
}


$('.actionshelfobjmodal').on('hidden.bs.modal', function () {
    clear_action_form($(this).find('form'));
})

