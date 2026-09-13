$(document).ready(function() {

    let buttons = []
    if (has_perm) {
        buttons.push({
            action: function ( e, dt, button, config ) {
                window.location = document.urls['create_procedure'];
                },
            text: '<i class="fa fa-plus" aria-hidden="true"></i> '+gettext('Create procedure template'),
            className: 'btn-sm btn-success',
            });
    }

procedure_table = createDataTable('#procedure', document.urls['get_procedures'], {
        columns: [
            {data: "title", name: "title", title: gettext("Title"), type: "string", visible: true, width:"20%",className: 'dt-center'},
            {data: "description", name: "status", title: gettext("Description"), type: "string", visible: true},
            {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true, filterable: false, sortable: false, width:"20%",className: 'dt-center'}
        ],
          layout: {
              topStart: 'pageLength',
              top: 'buttons',
              topEnd: 'search',
              bottomStart: 'info',
              bottomEnd: 'paging'
          },
           buttons: buttons,
        ajax: {
           url: document.urls['get_procedures'],
           type: 'GET',
           data: function(dataTableParams, settings) {
               var data= formatDataTableParams(dataTableParams, settings);
               return data;
           }
       }
    },
    addfilter=false);
})
