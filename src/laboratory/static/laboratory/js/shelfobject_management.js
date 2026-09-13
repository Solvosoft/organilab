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
layout: {
    topStart: 'pageLength',
    topEnd: 'search',
    bottomStart: 'info',
    bottomEnd: 'paging'
},
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
