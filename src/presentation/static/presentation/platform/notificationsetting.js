const ocrud = ObjectCRUD("platform_notificationsetting", {
    datatable_element: "#table-notificationsetting",
    modal_ids: {update: "#update_obj_modal"},
    actions: {
        table_actions: [],
        object_actions: [{
            name: "restore",
            action: "restore",
            in_action_column: true,
            i_class: "fa fa-undo fa-lg",
            method: "POST",
            title: gettext("Restore inherited value"),
            url_fn: data => restore_url.replace("/0/", "/" + data.id + "/"),
            data_fn: data => ({}),
        }],
        title: gettext("Actions"),
        className: "no-export-col"
    },
    datatable_inits: {
        columns: [
            {data: "id", name: "id", title: "ID", type: "string", visible: false},
            {data: "code", name: "code", title: gettext("Process"), type: "readonly", visible: true, sortable: false},
            {data: "default_subject", name: "default_subject", title: gettext("Default subject"), type: "readonly", visible: true, sortable: false},
            {data: "is_active", name: "is_active", title: gettext("Active"), type: "readonly", render: objShowBool, visible: true, sortable: false},
            {data: "override_subject", name: "override_subject", title: gettext("Subject"), type: "readonly", visible: true, sortable: false},
            {data: "origin_display", name: "origin", title: gettext("Origin"), type: "readonly", visible: true, sortable: false},
            {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true, filterable: false, sortable: false},
        ],
        addfilter: false,
    },
    add_filter: false,
    relation_render: {},
    delete_display: data => data["code"],
    icons: {update: "fa fa-edit me-1 fa-lg"},
    urls: object_urls,
    gt_form_modals: {update: {}, create: {}, detail: {}, destroy: {}},
});
ocrud.init();
