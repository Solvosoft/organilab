const ocrud = ObjectCRUD("ambiental_consumptionalert", {
    datatable_element: "#table-consumptionalert",
    modal_ids: {},
    actions: {
        table_actions: [],
        object_actions: [{
            name: "review",
            action: "review",
            in_action_column: true,
            i_class: "fa fa-check-square-o fa-lg",
            title: gettext("Mark as reviewed"),
        }],
        title: gettext("Actions"),
        className: "no-export-col"
    },
    datatable_inits: {
        columns: [
            {data: "id", name: "id", title: "ID", type: "string", visible: false},
            {data: "period", name: "period", title: gettext("Period"), type: "readonly", visible: true},
            {data: "building", name: "point__building", title: gettext("Building"), type: "readonly", render: gt_print_list_object("text"), visible: true},
            {data: "point", name: "point", title: gettext("Measurement point"), type: "readonly", render: gt_print_list_object("text"), visible: true},
            {data: "message", name: "message", title: gettext("Message"), type: "string", visible: true},
            {data: "variation_pct", name: "variation_pct", title: gettext("Variation (%)"), type: "readonly", visible: true},
            {data: "reviewed", name: "reviewed", title: gettext("Reviewed"), type: "boolean", render: objShowBool, visible: true},
            {data: "reviewed_note", name: "reviewed_note", title: gettext("Review note"), type: "readonly", visible: true, sortable: false},
            {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true, filterable: false, sortable: false},
        ],
        addfilter: true,
    },
    add_filter: true,
    relation_render: {},
    urls: object_urls,
    gt_form_modals: {create: {}, update: {}, detail: {}, destroy: {}},
});

ocrud.review = function (data) {
    Swal.fire({
        title: gettext("Mark as reviewed"),
        text: data.message,
        input: "textarea",
        inputLabel: gettext("What explains this alert? (leak, typing error, justified increase...)"),
        inputValidator: value => value ? null : gettext("Write a note."),
        showCancelButton: true,
        confirmButtonText: gettext("Save"),
        cancelButtonText: gettext("Cancel"),
    }).then(function (result) {
        if (!result.isConfirmed) {
            return;
        }
        fetch(review_url.replace("/0/", "/" + data.id + "/"), {
            method: "POST",
            body: JSON.stringify({note: result.value}),
            headers: {"X-CSRFToken": getCookie("csrftoken"), "Content-Type": "application/json"}
        }).then(response => response.json().then(body => ({ok: response.ok, body: body})))
            .then(function (response) {
                Swal.fire({icon: response.ok ? "success" : "error", text: response.body.detail || Object.values(response.body).join(" ")});
                ocrud.datatable.ajax.reload();
            });
    });
};
ocrud.init();
