datatableelement=createDataTable('#observationTable', document.urls.observation_table , {
responsive: true,
paging:true,
columns: [
    {data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
    {data: "creation_date", name: "creation_date", title: gettext("Creation Date"), type: "date", render: DataTable.render.datetime(), visible: true},
    {data: "creator_name", name: "creator_name", title: gettext("Creator"), type: "string", visible: true},
    {data: "action_taken", name: "action_taken", title: gettext("Action Taken"), type: "string", visible: true},
    {data: "description", name: "description", title: gettext("Description"), type: "string", visible: true},

],
ordering: false,
dom: "<'row'<'col-sm-4 col-md-4 d-flex justify-content-start'l>" +
"<'col-sm-7 col-md-7 mt-1 d-flex justify-content-end'f>>" +
"<'row'<'col-sm-12'tr>><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7 m-auto'p>>",
ajax: {
url: document.urls.observation_table,
type: 'GET',
data: function(dataTableParams, settings) {
        return formatDataTableParams(dataTableParams, settings);
      }
}
}, addfilter=false);

$(".add_status").click(function(){
    add_status(document.urls.change_status)
});
