function step_inline_escape(text) {
    return $("<div>").text(text || "").html();
}

const reqobj_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "string", visible: false},
        {
            data: "object", name: "object", title: gettext("Name"),
            type: "string", visible: true, render: data => step_inline_escape(data)
        },
        {
            data: "quantity", name: "quantity", title: gettext("Amount"),
            type: "string", visible: true
        },
        {
            data: "measurement_unit", name: "measurement_unit", title: gettext("Unit"),
            type: "string", visible: true, sortable: false,
            render: data => step_inline_escape(data)
        },
        {
            data: "actions", name: "actions", title: gettext("Actions"),
            type: "string", visible: true, filterable: false, sortable: false
        },
    ],
    addfilter: false,
}

const reqobj_modalids = {
    destroy: "#delete_object_modal",
}
if (step_inline_perms.reqobj_create) {
    reqobj_modalids.create = "#object_modal";
}

const reqobj_crud = ObjectCRUD("reqobj_crud", {
    datatable_element: "#table-reqobj",
    modal_ids: reqobj_modalids,
    datatable_inits: reqobj_inits,
    btn_class: {
        create: "btn-success create-reqobj-btn",
        clear_filters: "btn-outline-secondary",
    },
    delete_display: data => step_inline_escape(data.object),
    urls: reqobj_urls,
});
reqobj_crud.init();

const obs_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "string", visible: false},
        {
            data: "description", name: "description", title: gettext("Description"),
            type: "string", visible: true, render: data => step_inline_escape(data)
        },
        {
            data: "actions", name: "actions", title: gettext("Actions"),
            type: "string", visible: true, filterable: false, sortable: false
        },
    ],
    addfilter: false,
}

const obs_modalids = {
    destroy: "#delete_observation_modal",
}
if (step_inline_perms.obs_create) {
    obs_modalids.create = "#observation_modal";
}

const obs_crud = ObjectCRUD("obs_crud", {
    datatable_element: "#table-obs",
    modal_ids: obs_modalids,
    datatable_inits: obs_inits,
    btn_class: {
        create: "btn-success create-obs-btn",
        clear_filters: "btn-outline-secondary",
    },
    delete_display: data => step_inline_escape(data.description),
    urls: obs_urls,
});
obs_crud.init();
