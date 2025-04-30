var choices = [
    ["physical", gettext("Physical")],
    ["health",gettext("Health")],
    ["environment",gettext("Environment")],
    ]

datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "string", visible: false},
        {
            data: "danger_category",
            name: "danger_category",
            title: gettext("Danger Category"),
            type: "select",
            choices: choices,
            visible: true
         },
        {
            data: "h_code",
            name: "h_code",
            title: gettext("H Codes"),
            render: gt_print_list_object( "text"),
            url: selects2_url['h_code_url'],
             type: "select2",
            visible: true
        },
        {
            data: "actions",
            name: "actions",
            title: gettext("Actions"),
            type: "string",
            visible: true,
            filterable: false,
            sortable: false
        },
    ],
    addfilter: true,
}

const modalids = {
    create: "#create_obj_modal",
    destroy: "#delete_obj_modal",
    update: "#update_obj_modal",
}

const actions = {
    table_actions: [],
    object_actions: [],
    title: 'Actions',
    className: "no-export-col"
}

icons = {
    create: '<i class="fa fa-plus" aria-hidden="true"></i>',
    update: 'fa fa-edit me-1 fa-lg',
    clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
    detail: 'fa fa-eye fa-lg',
    destroy: 'fa fa-trash fa-lg',
}

const objconfig = {
    datatable_element: "#table-category",
    modal_ids: modalids,
    actions: actions,
    datatable_inits: datatable_inits,
    add_filter: true,
    relation_render: {'field_autocomplete': 'text'},
    delete_display: data => data['id'],
    create: "btn-success",
    icons: icons,
    urls: object_urls,
    gt_form_modals: {
        'create': {"parentdiv": '.asgrid'},
        'update': {"parentdiv": '.asgrid'},
        'detail': {},
        'destroy': {}
    }
}

const ocrud = ObjectCRUD("category_crud", objconfig);

ocrud.init();



