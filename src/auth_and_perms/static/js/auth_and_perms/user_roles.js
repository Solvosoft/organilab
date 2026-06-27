datatable_inits = {
    columns: [
	    {data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
		{data: "username", name: "username", title: gettext("User name"), type: "string", visible: true},
		{data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
		{data: "email", name: "email", title: gettext("Email"), type: "string", visible: true},
		{data: "organization", name: "organization", title: gettext("Organization"), type: "readonly", visible: true},
		{data: "laboratory", name: "laboratory", title: gettext("Laboratories"), type: "string", visible: true},
		{data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: false}
		],
		addfilter: true,
	   events: {
		'filter': function(data){
		    data['roles']=$("#id_rol").val();
		    data['organization']=$("#id_organization").val();
			return data
		}
		},
				}

var user_actions = {
    table_actions: [], // table_actions
    object_actions: [],
        title: gettext('Actions'),
        className: "no-export-col"
}
icons = {
    clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
}

let objconfig = {
			urls: object_urls,
			datatable_element: "#user_table",
			modal_ids: {},
			actions: user_actions,
			datatable_inits: datatable_inits,
			add_filter: true,
			relation_render: {'field_autocomplete': 'text'},
			delete_display: data => data['first_name'],
			create: "btn-success",
			icons: icons
		}
let ocrud = ObjectCRUD("user_crudobj", objconfig)
ocrud.init();

function get_roles_in_organization(element){
    var org = $(element).data('org');
    var user = $(element).data('user');
    var url =user_roles_org_url.replace('/0/', '/'+user+'/');
    $.ajax({
        url: url+'?organization='+org,
        type : "GET",
        dataType : 'json',
        success : function(data) {

            var html = '<div class="container"><ul class="list-group">';
            data.roles.forEach(function(item){
                html += '<li>' + item + '</li>';
            });
            html += '</ul></div>';

            $("#user_org_body").html(html);
            $('#user_org_details').modal('show');
        }
    });
}

function get_roles_in_laboratory(element){
    var lab = $(element).data('lab');
    var user = $(element).data('user');
    var url =user_roles_lab_url.replace('/0/', '/'+user+'/');
    $.ajax({
        url: url+'?laboratory='+lab,
        type : "GET",
        dataType : 'json',
        success : function(data) {

        var html = '<div class="container">';
            html += '<div class="row fw-bold border-bottom pb-2 mb-2">';
            html += '<div class="col-6">' + gettext('Organization') + '</div>';
            html += '<div class="col-6">' + gettext('Roles') + '</div>';
            html += '</div>';
            data.data.forEach(function(item){
                html += '<div class="row border-bottom py-2">';
                html += '<div class="col-6">' + item.org_name + '</div>';
                let roles_list = "";
                item.roles.forEach(function(role){
                    roles_list += '<li>'+role+'</li>';
                });
                html += '<div class="col-6"><ul class="list-group">'+roles_list+'</ul></div>';
                html += '</div>';
        });
        html += '</div>';
        $("#user_lab_body").html(html);
        $('#user_lab_details').modal('show');
    }

});
}

$('#id_rol').on('select2:select', function (e) {
    ocrud.datatable.ajax.reload();
})
$('#id_rol').on('select2:unselect', function (e) {
    ocrud.datatable.ajax.reload();
})
$('#id_organization').on('select2:select', function (e) {
    ocrud.datatable.ajax.reload();
})

$('#btn-clear-filters').on('click', function (e) {
$("#formFiltro").trigger("reset");
    ocrud.datatable.ajax.reload();
})
