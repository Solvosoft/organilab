const type_regent_choices = [
        ["chemical", gettext("Chemical")],
        ["chemical_engineer", gettext("Chemical Engineer")],
        ["veterinarian", gettext("Veterinarian")]
    ]

datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "string", visible: false},
        {
            data: "user",
            name: "user",
            title: gettext("Regent"),
            render: selectobjprint({display_name: "text"}),
            url: selects2_url['user_url'],
            type: "select2",
            visible: true
        },
        {
            data: "type_regent",
            name: "type_regent",
            title: gettext("Type Regent"),
            type: "select",
            choices: type_regent_choices,
            render: gt_print_list_object( "text"),
            visible: true
        },
        {
            data: "laboratories",
            name: "laboratories",
            title: gettext("Laboratories"),
            render: gt_print_list_object( "text"),
             url: selects2_url['laboratory_url'],
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
    datatable_element: "#table-regent",
    modal_ids: modalids,
    actions: actions,
    datatable_inits: datatable_inits,
    add_filter: true,
    relation_render: {'field_autocomplete': 'text'},
    delete_display: data => data['username'],
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

const ocrud = ObjectCRUD("buildings_crud", objconfig);

ocrud.init();



