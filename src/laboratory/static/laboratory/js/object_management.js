// from html: object_urls

const OPTIONS = [
    ["True", gettext("Yes")],
    ["False", gettext("No")],
]

datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "number", visible: false},
        {data: "code", name: "code", title: gettext("Code"), type: "string", visible: true},
        {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
        {
            data: "capacity",
            name: "capacity",
            title: gettext("Capacity"),
            type: "string",
            visible: true
        },
        {
            data: "capacity_measurement_unit",
            name: "capacity_measurement_unit",
            title: gettext("Measurement Unit"),
            render: selectobjprint({display_name: 'text'}),
            type: "string",
            visible: true,

        },
        {
            data: "description",
            name: "description",
            title: gettext("Description"),
            type: "string",
            render: truncateTextRenderer(),
            visible: true
        },
        {
            data: "features",
            name: "features",
            title: gettext("Object Features"),
            type: "string", visible: true,
            render: gt_print_list_object("text"),
        },
        {
            data: "is_container",
            name: "is_container",
            title: gettext("Is Container?"),
            type: "select",
            choices: OPTIONS,
            render: yesnoprint,
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
    destroy: "#delete_obj_modal",
    update: "#update_obj_modal",
}

if (has_perm_add_object) {
    modalids.create = "#create_obj_modal";
}

const actions = {
    table_actions: [],
    object_actions: [],
    title: 'Actions',
    className: "no-export-col"
}

icons = {
    create: '<i class="fa fa-plus" aria-hidden="true"></i>',
    clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
    detail: 'fa fa-eye fa-lg',
    update: 'fa fa-edit fa-lg',
    destroy: 'fa fa-trash fa-lg',
}

const objconfig = {
    datatable_element: "#table",
    modal_ids: modalids,
    actions: actions,
    datatable_inits: datatable_inits,
    add_filter: true,
    relation_render: {'field_autocomplete': 'text'},
    delete_display: data => data['name'],
    create: "btn-success",
    icons: icons,
    urls: object_urls,
    gt_form_modals: {
        'create': {"parentdiv": 'p'},
        'update': {"parentdiv": 'p'},
        'detail': {},
        'destroy': {}
    }
}

const ocrud = ObjectCRUD("crudobj", objconfig)
ocrud.init();
