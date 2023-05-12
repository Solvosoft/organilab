
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
            {data: "object_name", name: "object_name", title: gettext("Name"), type: "string", visible: true},
            {data: "quantity", name: "quantity", title: gettext("Quantity"), type: "string", visible: true },
            {data: "unit", name: "unit", title: gettext("Unit"), type: "string", visible: true},
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
                titleAttr: gettext('Transfer in'),
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