
const render_file = (data) => {
    if(can_contract){
        if(data){
            return `<a href="${data.url}" title="${data.display_name}" download class="btn btn-outline-success"><i class="fa fa-download"></i> ${gettext("Download")}</a>`
          }
    }else{
        return gettext("You do not have permissions to see or download contract.");
    }
    return data;
}
const render_document = (data) => {
    if(data && data.url){
        return `<a href="${data.url}" title="${data.display_name}" download class="btn btn-sm btn-outline-success"><i class="fa fa-download"></i> ${gettext("Download")}</a>`
    }
    return "";
}
const render_due_status = (data) => {
    if(!data){ return ""; }
    const css = {valid: "bg-success", due_soon: "bg-warning text-dark", expired: "bg-danger", inactive: "bg-secondary"};
    return `<span class="badge ${css[data.code] || 'bg-secondary'}">${data.text}</span>`;
}
const render_bool = (data) => data ? gettext("Yes") : gettext("No");

table_default_layout = {
    topStart: 'search',
    top: 'buttons',
    topEnd: 'pageLength',
    bottomStart: 'info',
    bottomEnd: 'paging'
};

maintenance_datatable_inits = {
				columns: [
						{data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
						{data: "maintenance_date", name:"maintenance_date", title: gettext("Date"), type: "date",
						"dateformat":  document.date_format, visible: true},
						{data: "provider_of_maintenance", name: "provider_of_maintenance", title: gettext("Provider"),
						type: "select2", visible: true, url: selects2_api_urls['providers'], render: selectobjprint({display_name: "text"})},
						{data: "validator", name: "validator", title: gettext("Validator"), type: "select2", visible: true,
						url: selects2_api_urls['profiles'],	render: selectobjprint({display_name: "text"})},
						{data: "maintenance_type_display", name: "maintenance_type", title: gettext("Type"), type: "readonly", visible: true},
						{data: "activities_display", name: "activities", title: gettext("Activities performed"), type: "readonly", visible: true},
						{data: "maintenance_observation", name: "maintenance_observation", title: gettext("Observation"), type: "string", visible: true},
						{data: "report", name: "report", title: gettext("Report"), type: "readonly", visible: true, render: data => render_document(data)},
						{data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true}
						],
		    	addfilter: true,
			    layout: table_default_layout
			    }

var logs_datatable_inits = {
				columns: [
						{data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
						{data: "last_update", name:"last_update", title: gettext("Last Update"), type: "date",
						"dateformat":  document.datetime_format, visible: true},
						{data: "created_by", name: "created_by", title: gettext("Created by"),
						type: "select2", visible: true, url: selects2_api_urls['users'], render: selectobjprint({display_name: "text"})},
					    {data: "description", name: "description", title: gettext("Description"), type: "string", visible: true},
						{data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true}
						],
		    	addfilter: true,
			    layout: table_default_layout
			    }


var calibrate_datatable_inits = {
				columns: [
						{data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
						{data: "calibration_date", name:"calibration_date", title: gettext("Date"), type: "date",
						"dateformat":  document.date_format, visible: true},
						{data: "calibrate_name", name: "calibrate_name", title: gettext("Calibrator"), type: "string", visible: true},
						{data: "provider", name: "provider", title: gettext("Calibration laboratory"), type: "readonly", visible: true},
						{data: "certificate_number", name: "certificate_number", title: gettext("Certificate number"), type: "string", visible: true},
						{data: "certificate", name: "certificate", title: gettext("Certificate"), type: "readonly", visible: true, render: data => render_document(data)},
						{data: "conformity", name: "conformity", title: gettext("Conformity"), type: "readonly", visible: true},
						{data: "next_calibration_date", name: "next_calibration_date", title: gettext("Next calibration"), type: "readonly", visible: true},
						{data: "validator", name: "validator", title: gettext("Validator"),type: "select2", visible: true,
						url: selects2_api_urls['profiles'],	render: selectobjprint({display_name: "text"})},
						{data: "observation", name: "observation", title: gettext("Observation"), type: "string", visible: true},
						{data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true}
						],
		    	addfilter: true,
			    layout: table_default_layout
			    }

var training_datatable_inits = {
				columns: [
						{data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
						{data: "training_initial_date", name:"training_initial_date", title: gettext("Initial date"), type: "date",
						"dateformat":  document.date_format, visible: true},
						{data: "training_final_date", name:"training_final_date", title: gettext("Final date"), type: "date",
						"dateformat":  document.date_format, visible: true},
						{data: "number_of_hours", name:"number_of_hours", title: gettext("Hours"), type: "number", visible: true},
						{data: "place", name:"place", title: gettext("Place"), type: "string", visible: true},
						{data: "intern_people_receive_training", name:"intern_people_receive_training", title: gettext("Internal participants"),
						type: "select2", visible: true,multiple: true, url: selects2_api_urls['profiles'],
						render: gt_print_list_object("text")},
						{data: "observation", name:"observation", title: gettext("Observation"), type: "string", visible: true},
						{data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true}
						],
		    	addfilter: true,
			    layout: table_default_layout
			    }

var guarantee_datatable_inits = {
				columns: [
						{data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
						{data: "guarantee_initial_date", name:"guarantee_initial_date", title: gettext("Initial date"),
						type: "date",  "dateformat":  document.date_format, visible: true},
						{data: "guarantee_final_date", name:"guarantee_final_date", title: gettext("Final date"),
						type: "date", "dateformat":  document.date_format, visible: true},
						{data: "created_by", name: "created_by", title: gettext("Created by"),
						type: "select2", visible: true, url: selects2_api_urls['users'], render: selectobjprint({display_name: "text"})},
						{data: "contract", name:"contract", title: gettext("Contract"), visible: true, type:"readonly", render: data=> render_file(data)},
						{data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true}
						],
		    	addfilter: true,
			    layout: table_default_layout
			    }

var maintenance_modalids = {
    		create: "#create_maintenance_modal",
			destroy: "#delete_maintenance_modal",
			update: "#update_maintenance_modal"
}
var guarantee_modalids = {
    		create: "#create_guarantee_modal",
			destroy: "#delete_guarantee_modal",
			update: "#update_guarantee_modal"
}

var log_modalids = {
    		create: "#create_log_modal",
    		update: "#update_log_modal",
    		destroy: "#delete_log_modal",
    		}

var calibrate_modalids = {
    		create: "#create_calibrate_modal",
    		update: "#update_calibrate_modal",
    		destroy: "#delete_calibrate_modal",
    		}

var training_modalids = {
    		create: "#create_training_modal",
    		update: "#update_training_modal",
    		destroy: "#delete_training_modal",
    		}

var actions_log = {
		    table_actions: [],  //table_actions
			object_actions: [],
			title: gettext('Actions'),
			className:  "no-export-col"
}

var actions = {
		    table_actions: [		    {
		            action:  function(data){
                        window.open(provider_url,"_blank")
                        },
                    text: `<i class="fa fa-building-o" aria-hidden="true"></i>`,
                    titleAttr: gettext('Providers'),
                    className: "btn btn-success"
                    }],  //table_actions
			object_actions: [],
			title: gettext('Actions'),
			className:  "no-export-col"
}
var calibrate_actions = {
		    table_actions: [],  //table_actions
			object_actions: [],
			title: gettext('Actions'),
			className:  "no-export-col"
}

var guarantee_actions = {
		    table_actions: [],  //table_actions
			object_actions: [],
			title: gettext('Actions'),
			className:  "no-export-col"
}

var training_actions = {
		    table_actions: [],
			object_actions: [],
			title: gettext('Actions'),
			className:  "no-export-col"
}


icons= {
        create: '<i class="fa fa-plus" aria-hidden="true"></i>',
		clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
		update: 'fa fa-edit me-1 fa-lg',
		destroy: 'fa fa-trash fa-lg'
}

let maintenance_objconfig={
		urls: object_urls["maintenance"],
		datatable_element: "#maintenance_table",
		modal_ids: maintenance_modalids,
		actions: actions,
		datatable_inits: maintenance_datatable_inits,
		add_filter: true,
		relation_render: {'field_autocomplete': 'text' },
		delete_display: data => data['maintenance_observation'],
		create: "btn-success",
		icons: icons
}


let maintenance_ocrud = ObjectCRUD("maintenancecrudobj", maintenance_objconfig)
maintenance_ocrud.init();


let log_objconfig={
		urls: object_urls["log"],
		datatable_element: "#log_table",
		modal_ids: log_modalids,
		actions: actions_log,
		datatable_inits: logs_datatable_inits,
		add_filter: true,
		relation_render: {'field_autocomplete': 'text' },
		delete_display: data => data['description'],
		create: "btn-success",
		icons: icons
}

let log_ocrud = ObjectCRUD("logcrudobj", log_objconfig)
log_ocrud.init();


let calibrate_objconfig={
		urls: object_urls["calibrate"],
		datatable_element: "#calibrate_table",
		modal_ids: calibrate_modalids,
		actions: calibrate_actions,
		datatable_inits: calibrate_datatable_inits,
		add_filter: true,
		relation_render: {'field_autocomplete': 'text' },
		delete_display: data => data["calibration_date"]+" "+data['calibrate_name'],
		create: "btn-success",
		icons: icons
}

let calibrate_ocrud = ObjectCRUD("calibratecrudobj", calibrate_objconfig)
calibrate_ocrud.init();


let guarantee_objconfig={
		urls: object_urls["guarantee"],
		datatable_element: "#guarantee_table",
		modal_ids: guarantee_modalids,
		actions: guarantee_actions,
		datatable_inits: guarantee_datatable_inits,
		add_filter: true,
		relation_render: {'field_autocomplete': 'text' },
		delete_display: data => data["guarantee_initial_date"]+" - "+data['guarantee_final_date'],
		create: "btn-success",
		icons: icons
}

let guarantee_ocrud = ObjectCRUD("guaranteecrudobj", guarantee_objconfig)
guarantee_ocrud.init();


let training_objconfig={
		urls: object_urls["training"],
		datatable_element: "#training_table",
		modal_ids: training_modalids,
		actions: training_actions,
		datatable_inits: training_datatable_inits,
		add_filter: true,
		relation_render: {'field_autocomplete': 'text' },
		delete_display: data => data["training_initial_date"]+" - "+data['training_final_date'],
		create: "btn-success",
		icons: icons
}

let training_ocrud = ObjectCRUD("trainingcrudobj", training_objconfig)
training_ocrud.init();




// --- Registros ISO/IEC 17025 (laboratory/equipment/api.py) ---

function iso_column(data, title, extra){
    return Object.assign({data: data, name: data, title: title, type: "readonly", visible: true}, extra || {});
}
const id_column = {data: "id", name: "id", title: gettext("Id"), type: "string", visible: false};
const actions_column = {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true};

const iso_tables = {
    plan: {
        columns: [id_column,
            iso_column("activity_kind", gettext("Activity")),
            iso_column("name", gettext("Name")),
            iso_column("interval", gettext("Interval")),
            iso_column("last_done", gettext("Last done")),
            iso_column("next_due", gettext("Next due")),
            iso_column("due_status", gettext("Status"), {render: render_due_status}),
            iso_column("responsible", gettext("Responsible")),
            actions_column],
        delete_display: data => data["activity_kind"] + " " + data["name"],
    },
    verification: {
        columns: [id_column,
            iso_column("verification_date", gettext("Date"), {type: "date", dateformat: document.date_format}),
            iso_column("verification_type", gettext("Verification type")),
            iso_column("result", gettext("Result")),
            iso_column("conformity", gettext("Conformity")),
            iso_column("responsible", gettext("Responsible")),
            iso_column("document", gettext("Record"), {render: render_document}),
            actions_column],
        delete_display: data => data["verification_date"] + " " + data["verification_type"],
    },
    failure: {
        columns: [id_column,
            iso_column("failure_date", gettext("Failure date"), {type: "date", dateformat: document.date_format}),
            iso_column("description", gettext("Description")),
            iso_column("blocked", gettext("Out of service"), {render: render_bool}),
            iso_column("repair_done", gettext("Repair performed")),
            iso_column("provider", gettext("Provider")),
            iso_column("return_to_service_date", gettext("Return to service"), {type: "date", dateformat: document.date_format}),
            iso_column("report", gettext("Report"), {render: render_document}),
            actions_column],
        delete_display: data => data["failure_date"] + " " + data["description"],
    },
    control: {
        columns: [id_column,
            iso_column("name", gettext("Name")),
            iso_column("method", gettext("Control method")),
            iso_column("nominal_value", gettext("Nominal value")),
            iso_column("unit", gettext("Unit")),
            iso_column("correction", gettext("Correction")),
            iso_column("limits", gettext("LCL / CL / UCL")),
            iso_column("last_record", gettext("Last control"), {render: data => data && data.text
                ? (data.alert ? `<span class="badge bg-danger">${data.text}</span>` : data.text) : ""}),
            iso_column("chart_url", gettext("Chart"), {render: url => `<a class="btn btn-sm btn-outline-primary" href="${url}"><i class="fa fa-line-chart"></i> ${gettext("Open")}</a>`}),
            actions_column],
        delete_display: data => data["name"],
    },
    document: {
        columns: [id_column,
            iso_column("document_type", gettext("Document type")),
            iso_column("title", gettext("Title")),
            iso_column("version", gettext("Version")),
            iso_column("valid_from", gettext("Valid from"), {type: "date", dateformat: document.date_format}),
            iso_column("file", gettext("File"), {render: render_document}),
            actions_column],
        delete_display: data => data["title"],
    },
};

for (const [name, table] of Object.entries(iso_tables)) {
    let ocrud = ObjectCRUD(name + "crudobj", {
        urls: object_urls[name],
        datatable_element: "#" + name + "_table",
        modal_ids: {create: "#create_" + name + "_modal", update: "#update_" + name + "_modal", destroy: "#delete_" + name + "_modal"},
        actions: {table_actions: [], object_actions: [], title: gettext('Actions'), className: "no-export-col"},
        datatable_inits: {columns: table.columns, addfilter: false, layout: table_default_layout},
        add_filter: false,
        relation_render: {'field_autocomplete': 'text'},
        delete_display: table.delete_display,
        create: "btn-success",
        icons: icons
    });
    ocrud.init();
}

// Las tablas en pestañas ocultas se dibujan sin ancho: se reajustan al mostrarse.
document.querySelectorAll('#equipment_tabs button[data-bs-toggle="tab"]').forEach(function(tab){
    tab.addEventListener('shown.bs.tab', function(){
        $.fn.dataTable.tables({visible: true, api: true}).columns.adjust();
    });
});
