// from html: object_urls, has_perm_create

const datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "number", visible: false},
        {data: "name", name: "name", title: gettext("Name"), type: "readonly", visible: true},
        {data: "entity_type_display", name: "entity_type_display", title: gettext("Type"), type: "readonly", visible: true},
        {data: "status_display", name: "status_display", title: gettext("Status"), type: "readonly", visible: true},
        {data: "requested_by", name: "requested_by", title: gettext("Requested by"), type: "readonly", render:selectobjprint({display_name: "text"}), visible: true},
        {data: "requested_at", name: "requested_at", title: gettext("Date"), type: "readonly", visible: true},
        {data: "review_notes", name: "review_notes", title: gettext("Notes"), type: "readonly", render: truncateTextRenderer(), visible: true},
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
    events: {
        filter: function (data) {
            var el = document.getElementById('id_filter-status');
            if (el) data['status'] = el.value || 'pending';
            return data;
        }
    }
}

const modalids = {
    destroy: "#delete_obj_modal",
    create: "#create_obj_modal",
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
    update: 'fa fa-edit me-1 fa-lg',
    destroy: 'fa fa-trash fa-lg',
}

const objconfig = {
    datatable_element: "#table",
    modal_ids: modalids,
    actions: actions,
    datatable_inits: datatable_inits,
    add_filter: true,
    delete_display: data => data['name'],
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

const ocrud = ObjectCRUD("crudobj", objconfig)
ocrud.init();

document.getElementById("id_filter-status").addEventListener('change', function () {
    ocrud.datatable.ajax.reload();
})
