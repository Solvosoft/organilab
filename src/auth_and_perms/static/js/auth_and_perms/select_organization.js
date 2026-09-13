function create_object_table(){

const object_table_layout = {
    topStart: 'buttons',
    topEnd: 'pageLength',
    bottomStart: 'info',
    bottomEnd: 'paging'
};


objectdatatable=createDataTable('#objecttable', searchshelfobjectorg_api_url, {
language: {"url": datatables_lang },
 columns: [
        {data: "name", name: "name", title: gettext("Shelf Object"), type: "string", visible: true},
        {data: "shelf_name", name: "shelf_name", title: gettext("Shelf"), type: "string", visible: true},
        {data: "quantity", name: "quantity", title: gettext("Quantity"), type: "string", visible: true},
        {data: "laboratory_name", name: "laboratory_name", title: gettext("Laboratory"), type: "string", visible: true}
      ],
 ajax: {
    url: searchshelfobjectorg_api_url,
    type: 'GET',
    data: function(dataTableParams, settings) {
        var data= formatDataTableParams(dataTableParams, settings);
        data['organization'] = $('#id_organization').val();
        data['object'] = $('#id_object').val();
        return data;
    }
},
layout: object_table_layout
}, addfilter=false);
}

$("#id_organization, #id_object").on("change", function(){
    if($('#id_object').val() && $('#id_organization').val()){
        if($("#objecttable").html()){
            objectdatatable.ajax.reload();
        }else{
            create_object_table();
        }
        $("#objecttable_wrapper").show();
    }
});

$("#id_organization").on("change", function(){
    var organization = $(this).val();
    if(organization){
        $.ajax({
            url: organization_buttons_api_url,
            type: 'GET',
            dataType: 'json',
            data: {'organization': organization},
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            success: function(data){
                $("#orginfo").html(data.result);
            }
        });
        $("#searchobjdiv").show();
    }
    $("#id_object").val("").trigger("change");
    $("#objecttable_wrapper").hide();
});
