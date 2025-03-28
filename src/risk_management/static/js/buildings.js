
datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "string", visible: false},
        {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
        {data: "phone", name: "phone", title: gettext("Phone"), type: "string", visible: true},
        {data: "geolocation", name: "geolocation", title: gettext("Geolocation"), type: "readonly", visible: true},
        {data: "manager", name: "manager", title: gettext("Manager"),render: selectobjprint({display_name: "text"}), visible: true},
        {data: "regents",
        name: "regents",
        title: gettext("Regent Associated"),
        visible: true,
        render:gt_print_list_object("text")},
        {data: "nearby_buildings", name: "nearby_buildings", title: gettext("Nearby buildings"),
        render:gt_print_list_object("text"), visible: true},
        {data: "laboratories", name: "laboratories", title: "Laboratories",visible: true, render:gt_print_list_object("text")},
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

    destroy: "#delete_obj_modal",
}

const actions = {
    table_actions: [],
    object_actions: [
            {
            name: "update_building",
            action: 'update_building',
            in_action_column: true,
            i_class: 'fa fa-edit',
            method: 'GET',
            title: gettext("Update"),
            data_fn: function (data) {
                return data;
            }
    }],
    title: 'Actions',
    className: "no-export-col"
}

icons = {
    clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
    destroy: 'fa fa-trash fa-lg',
}

const objconfig = {
    datatable_element: "#table-building",
    modal_ids: modalids,
    actions: actions,
    datatable_inits: datatable_inits,
    add_filter: true,
    relation_render: {'field_autocomplete': 'text'},
    delete_display: data => data['name'],
    create: "btn-success",
    icons: icons,
    urls: object_urls,
    gt_form_modals: {
        'destroy': {}
    }
}

const crud = ObjectCRUD("buildings_crud", objconfig);
crud.update_building = function (data) {
    let updateUrl = update_url.replace("/0/", "/" + data.id + "/");
    window.location.href = updateUrl;
}

crud.init();



