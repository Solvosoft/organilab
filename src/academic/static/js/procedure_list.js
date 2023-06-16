$(document).ready(function() {
procedure_table = createDataTable('#procedure', document.Procedure, {
        columns: [
            {data: "title", name: "title", title: gettext("Title"), type: "string", visible: true, width:"20%",className: 'dt-center'},
            {data: "description", name: "status", title: gettext("Description"), type: "string", visible: true},
            {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true, filterable: false, sortable: false, width:"20%",className: 'dt-center'}
        ],
     dom: "<'d-flex justify-content-between'<'m-2'l>" +
        "<'m-2 d-flex justify-content-start'f>>" +
        "<'row'tr><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7 m-auto'p>>",
        ajax: {
           url: document.Procedure,
           type: 'GET',
           data: function(dataTableParams, settings) {
               var data= formatDataTableParams(dataTableParams, settings);
               return data;
           }
       }
    },
    addfilter=false);
})
