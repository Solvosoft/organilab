
datatable_inits = {
				columns: [
						{data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
						{data: "substance", name: "substance", title: gettext("Substance"), type: "string", visible: true,
						render: selectobjprint({display_name: "text"})},
						{data: "total", name: "total", title: gettext("Total"), type: "string", visible: true},
						{data: "break_threshold", name: "break_threshold", title: gettext("Break threshold"), type: "string",
						visible: true},
						{data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: false}
			],


			addfilter: false
	}

	var process_modalids = {}

	var process_actions = {
			table_actions: [],  //table_actions
			object_actions: [],
			title: gettext('Actions'),
			className:  "no-export-col"
	}

	icons= {
					clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
	}

	let objconfig={
		urls: report_urls,
		datatable_element: "#table_3",
		modal_ids: process_modalids,
		actions: process_actions,
		datatable_inits: datatable_inits,
		add_filter: true,
		relation_render: {'field_autocomplete': 'text' },
		delete_display: data => data['pk'],
		create: "btn-success",
		icons: icons
	}


	let ocrud=ObjectCRUD("table_3", objconfig)
	ocrud.init();


datatable_inits_quarter = {
				columns: [
						{data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
						{data: "substance", name: "substance", title: gettext("Substance"), type: "string", visible: true,
						render: selectobjprint({display_name: "text"})},
						{data: "total", name: "total", title: gettext("Total"), type: "string", visible: true},
						{data: "danger_category", name: "danger_category", title: gettext("Danger category"), type: "string"},
						{data: "break_threshold", name: "break_threshold", title: gettext("Break threshold"), type: "string",
						visible: true},
						{data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: false}
			],


			addfilter: false
	}


	icons_quarter= {
					clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
	}
		var process_modalids_quarter = {}

	var process_actions_quarter = {
			table_actions: [],  //table_actions
			object_actions: [],
			title: gettext('Actions'),
			className:  "no-export-col"
	}

	let objconfig_quarter={
		urls: report_quarter_urls,
		datatable_element: "#table_4",
		modal_ids: process_modalids_quarter,
		actions: process_actions_quarter,
		datatable_inits: datatable_inits_quarter,
		add_filter: true,
		relation_render: {'field_autocomplete': 'text' },
		delete_display: data => data['pk'],
		create: "btn-success",
		icons: icons_quarter
	}


	let ocrud_quarter=ObjectCRUD("table_4", objconfig_quarter)
	ocrud_quarter.init();
