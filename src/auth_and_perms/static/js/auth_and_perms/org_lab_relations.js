// from html: object_urls

const datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "number", visible: false},
        {data: "laboratory_name", name: "laboratory_name", title: gettext("Laboratory"), type: "string", visible: true},
        {
            data: "actions",
            name: "actions",
            title: gettext("Actions"),
            type: "string",
            visible: true,
        },
    ],
    addfilter: true,
}

const modalids = {
    destroy: "#delete_relation_modal",
}

const actions = {
    table_actions: [],
    object_actions: [],
    title: 'Actions',
    className: "no-export-col"
}

const icons = {
    destroy: 'fa fa-trash fa-lg',
    clear: '<i class="fa fa-eraser" aria-hidden="true"></i>'
}

const objconfig = {
    datatable_element: "#lab_relations_table",
    modal_ids: modalids,
    actions: actions,
    datatable_inits: datatable_inits,
    add_filter: false,
    delete_display: data => data['laboratory_name'],
    icons: icons,
    urls: object_urls,
    gt_form_modals: {
        'destroy': {}
    }
}

const ocrud = ObjectCRUD("labrelcrud", objconfig);
ocrud.init();
