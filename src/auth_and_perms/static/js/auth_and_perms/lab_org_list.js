
datatableorgs=createDataTable('#orgtable', org_api_url, {
 columns: [
        {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
        {data: "laboratories", name: "laboratories", title: gettext("Associated laboratories"), type: "string", visible: true},
      ],
 ajax: {
    url: org_api_url,
    type: 'GET',
    data: function(dataTableParams, settings) {
        var data= formatDataTableParams(dataTableParams, settings);
        return data;
    }
}
}, addfilter=false
);

datatablelabs=createDataTable('#labtable', lab_api_url, {
 columns: [
        {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
        {data: "organizations", name: "organizations", title: gettext("Partner organizations"), type: "string", visible: true},
      ],
 ajax: {
    url: lab_api_url,
    type: 'GET',
    data: function(dataTableParams, settings) {
        var data= formatDataTableParams(dataTableParams, settings);
        return data;
    }
}
}, addfilter=false
);

function get_roles(element){
    var org = $(element).data('org');
    var lab = $(element).data('lab');
    var content = $(element).data('content');
    $.ajax({
        url: roles_api_url+'?organization='+org+'&laboratory='+lab+'&content_type='+content,
        type : "GET",
        dataType : 'json',
        success : function(data) {
            var html = '<div class="container">';
            html += '<div class="row fw-bold border-bottom pb-2 mb-2">';
            html += '<div class="col-6">' + gettext('User') + '</div>';
            html += '<div class="col-6">' + gettext('Roles') + '</div>';
            html += '</div>';

            data.forEach(function(item){
                html += '<div class="row border-bottom py-2">';
                html += '<div class="col-6">' + item.user + '</div>';
                roles = item.roles.split(',');
                roles_list=""
                roles.forEach(function(role){
                    roles_list += '- '+role.length > 0 ? role : '<p>'+gettext('No roles assigned')+'</p>' + '<br>';
                });
                html += '<div class="col-6">' + roles_list + '</div>';
                            html += '</div>';

            });

            $("#userroles").html(html);
            $('#rol_details').modal('show');
        }
    });
}
