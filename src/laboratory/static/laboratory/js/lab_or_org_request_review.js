// from html: object_urls

const datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "number", visible: false},
        {data: "name", name: "name", title: gettext("Name"), type: "readonly", visible: true},
        {
            data: "entity_type_display",
            name: "entity_type_display",
            title: gettext("Type"),
            type: "readonly",
            visible: true
        },
        {data: "status_display", name: "status_display", title: gettext("Status"), type: "readonly", visible: true},
        {
            data: "requested_by",
            name: "requested_by",
            title: gettext("Requested by"),
            type: "readonly",
            render: selectobjprint({display_name: "text"}),
            visible: true
        },
        {data: "requested_at", name: "requested_at", title: gettext("Date"), type: "readonly", visible: true},
        {data: "review_notes", name: "review_notes", title: gettext("Notes"), type: "readonly", render: truncateTextRenderer(), visible: true},
        {
            data: "actions",
            name: "actions",
            title: gettext("Actions"),
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

const actions = {
    table_actions: [],
    object_actions: [
        {
            name: "approve",
            title: gettext('Approve'),
            i_class: 'fa fa-check fa-lg text-success',
            url_fn: function (data) { return object_urls.approve_url.replace('/0/', '/' + data.id + '/'); },
            method: 'POST',
        },
        {
            name: "reject",
            title: gettext('Reject'),
            i_class: 'fa fa-times fa-lg text-danger',
            url_fn: function (data) { return object_urls.reject_url.replace('/0/', '/' + data.id + '/'); },
            method: 'POST',
        },
        {
            name: "destroy",
            title: gettext('Delete'),
            i_class: 'fa fa-trash fa-lg text-secondary',
            url_fn: function (data) { return object_urls.destroy_url.replace('/0/', '/' + data.id + '/'); },
            method: 'DELETE',
        },
    ],
    title: 'Actions',
    className: "no-export-col"
}

icons = {
    clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
}

const modalids = {
    destroy: "#delete_obj_modal",
}

const objconfig = {
    datatable_element: "#table",
    modal_ids: modalids,
    actions: actions,
    datatable_inits: datatable_inits,
    add_filter: true,
    delete_display: data => data['name'],
    icons: icons,
    urls: object_urls,
    gt_form_modals: {}
}

const ocrud = ObjectCRUD("crudobj", objconfig)
ocrud.init();

document.getElementById("id_filter-status").addEventListener('change', function () {
    ocrud.datatable.ajax.reload();
})
