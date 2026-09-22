/** Muestra solo el campo de umbral que usa el disparador elegido. */
function toggle_threshold(prefix) {
    const trigger = $("#id_" + prefix + "trigger option:selected").text().trim();
    Object.entries(threshold_fields).forEach(function ([description, field]) {
        $("#id_" + prefix + field).closest(".gtformfield").toggle(description === trigger);
    });
}

["create-", "update-"].forEach(function (prefix) {
    $("#id_" + prefix + "trigger").on("change", () => toggle_threshold(prefix));
    toggle_threshold(prefix);
});

const modalids = {update: "#update_obj_modal", destroy: "#delete_obj_modal"};
if (has_perm.create) {
    modalids.create = "#create_obj_modal";
}

const rules = ObjectCRUD("platform_alertrule", {
    datatable_element: "#table-alertrule",
    modal_ids: modalids,
    actions: {table_actions: [], object_actions: [], title: gettext("Actions"), className: "no-export-col"},
    datatable_inits: {
        columns: [
            {data: "id", name: "id", title: "ID", type: "string", visible: false},
            {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
            {data: "process", name: "process", title: gettext("Process"), type: "readonly", render: gt_print_list_object("text"), visible: true},
            {data: "trigger", name: "trigger", title: gettext("Trigger"), type: "readonly", render: gt_print_list_object("text"), visible: true},
            {data: "threshold_display", name: "threshold", title: gettext("Threshold"), type: "readonly", visible: true, sortable: false},
            {data: "level", name: "level", title: gettext("Level"), type: "readonly", render: gt_print_list_object("text"), visible: true},
            {data: "is_active", name: "is_active", title: gettext("Active"), type: "readonly", render: objShowBool, visible: true},
            {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true, filterable: false, sortable: false},
        ],
        addfilter: true,
    },
    add_filter: true,
    relation_render: {},
    delete_display: data => data["name"],
    create: "btn-success",
    icons: {
        create: '<i class="fa fa-plus" aria-hidden="true"></i>',
        update: "fa fa-edit me-1 fa-lg",
        destroy: "fa fa-trash fa-lg",
        clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
    },
    urls: object_urls,
    events: {
        update_data: function (data) {
            setTimeout(() => toggle_threshold("update-"), 0);
            return data;
        }
    },
    gt_form_modals: {create: {}, update: {}, detail: {}, destroy: {}},
});
rules.init();

const events = ObjectCRUD("platform_alertevent", {
    datatable_element: "#table-alertevent",
    modal_ids: {},
    actions: {table_actions: [], object_actions: [], title: gettext("Actions"), className: "no-export-col"},
    datatable_inits: {
        columns: [
            {data: "id", name: "id", title: "ID", type: "string", visible: false},
            {data: "creation_date", name: "creation_date", title: gettext("Date"), type: "readonly", visible: true},
            {data: "rule", name: "rule", title: gettext("Alert rule"), type: "readonly", render: gt_print_list_object("text"), visible: true},
            {data: "level", name: "level", title: gettext("Level"), type: "readonly", visible: true},
            {data: "message", name: "message", title: gettext("Message"), type: "string", visible: true},
            {data: "link", name: "link", title: gettext("Link"), type: "readonly", render: showlink, visible: true, sortable: false},
        ],
        addfilter: false,
    },
    add_filter: false,
    relation_render: {},
    urls: event_urls,
    gt_form_modals: {create: {}, update: {}, detail: {}, destroy: {}},
});
events.init();
