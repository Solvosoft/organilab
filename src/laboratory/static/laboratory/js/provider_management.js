// from html: object_urls

datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "number", visible: false},
        {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
        {data: "phone_number", name: "phone_number", title: gettext("Phone"), type: "string", visible: true},
        {data: "email", name: "email", title: gettext("Email"), type: "string", visible: true},
        {data: "legal_identity", name: "legal_identity", title: gettext("Legal Identity"), type: "string", visible: true},
        {data: "laboratory", name: "laboratory", title: gettext("Laboratory"), type: "string", render: selectobjprint({display_name: 'text'}), visible: false},

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
    urls: object_urls
}

const ocrud = ObjectCRUD("crudobj", objconfig)
ocrud.init();
