datatable_inits = {
				columns: [
								{data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
								{data: "object", name: "object", title: gettext("Object"), type: "String", visible: true,
								render: selectobjprint({display_name: "text"})},
								{data: "cas_code", name: "cas_code", title: gettext("CAS Code"), type: "String", visible: true},
								{data: "labroom", name: "labroom", title: gettext("Labroom"), type: "String", visible: true},
								{data: "furniture", name: "furniture", title: gettext("Furniture"), type: "String", visible: true},
								{data: "shelf", name: "shelf", title: gettext("Shelf"), type: "String", visible: true},
								{data: "h_code", name: "h_code", title: gettext("H Code"), type: "String", visible: true},
								{data: "flashpoint", name: "flashpoint", title: gettext("Flashpoint"), type: "String", visible: true,
								render: selectobjprint({display_name: "text"})},
								{data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true}
			],


			addfilter: false
	}

	var process_modalids = {
	    update: "#update_obj_modal"
	}

	var process_actions = {
			table_actions: [],  //table_actions
			object_actions: [],
			title: gettext('Actions'),
			className:  "no-export-col"
	}

	icons= {
					clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
					update: 'fa fa-edit me-1 fa-lg',
	}

	let objconfig={
		urls: object_urls,
		datatable_element: "#tableshelfobject",
		modal_ids: process_modalids,
		actions: process_actions,
		datatable_inits: datatable_inits,
		add_filter: true,
		relation_render: {'field_autocomplete': 'text' },
		delete_display: data => data['pk'],
		create: "btn-success",
		icons: icons
	}


	let ocrud=ObjectCRUD("hcodecrud", objconfig)
	ocrud.init();
