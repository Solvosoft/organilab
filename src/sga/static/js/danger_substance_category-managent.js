const object_urls = window.object_urls

datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "number", visible: false},
        {
            data: "h_code",
            name: "h_code",
            title: gettext("H Code"),
            render: selectobjprint({display_name: "text"}),
            type: "string",
            visible: true,
        },
        {
            data: "category",
            name: "category",
            title: gettext("Category"),
            type: "string",
            visible: true,
            render: selectobjprint({display_name: "text"}),
        },
        {
            data: "section",
            name: "section",
            title: gettext("Section"),
            type: "string",
            visible: true
        },
        {
            data: "process_condition",
            name: "process_condition__description",
            title: gettext("Process Condition"),
            render: selectobjprint({display_name: "text"}),
            type: "string",
            visible: true
        },
        {
            data: "note",
            name: "note",
            title: gettext("Note"),
            type: "string",
            visible: true,
        },
        {
            data: "threshold",
            name: "threshold",
            title: gettext("Threshold"),
            type: "string",
            visible: true,
        },
        {
            data: "measurement_unit",
            name: "measurement_unit",
            title: gettext("Measurement Unit"),
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
    delete_display: data => `${gettext("Are you sure you want to delete this Danger substance category? <br> This action will delete all data related.")}`,

    create: "btn-success",
    icons: icons,
    urls: object_urls
}

const ocrud = ObjectCRUD("crudobj", objconfig)
ocrud.init();
