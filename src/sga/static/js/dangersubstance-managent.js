const object_urls = window.object_urls

datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "number", visible: false},
        {
            data: "cas_code",
            name: "cas_code",
            title: gettext("Cas Code"),
            type: "string",
            visible: true,
        },
        {
            data: "name",
            name: "name",
            title: gettext("Name"),
            type: "string",
            visible: true
        },
        {
            data: "notes",
            name: "notes",
            title: gettext("Notes"),
            type: "string",
            visible: true
        },
        {
            data: "type_match",
            name: "type_match",
            title: gettext("Type Match"),
            type: "string",
            visible: true
        },
        {
            data: "threshold",
            name: "threshold",
            title: gettext("Threshold"),
            type: "string",
            visible: true,
        },
        {
            data: "patron_name",
            name: "patron_name",
            title: gettext("Patron Name"),
            type: "string",
            visible: true,
        },
        {
            data: "especial_condition",
            name: "especial_condition",
            title: gettext("Especial Condition"),
            type: "string",
            visible: true,
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
    clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
    detail: 'fa fa-eye fa-lg',
    update: 'fa fa-edit fa-lg',
    destroy: 'fa fa-trash fa-lg',
}

const objconfig = {
    datatable_element: "#tableobj",
    modal_ids: modalids,
    actions: actions,
    datatable_inits: datatable_inits,
    add_filter: true,
    relation_render: {'field_autocomplete': 'text'},
    delete_display: data => `<span class="text-danger">${data.name} - ${data.cas_code}</span> <br> ${gettext("Are you sure you want to delete this Danger substance? <br> This action will delete all data related.")}`,

    create: "btn-success",
    icons: icons,
    urls: object_urls
}

const ocrud = ObjectCRUD("customerexonerationobj", objconfig)
ocrud.init();
