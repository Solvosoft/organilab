
datatable_inits = {
    columns: [
        {
            data: "id",
            name: "id",
            title: "ID",
            type: "string",
            visible: false
         },
        {
            data: "name",
            name: "name",
            title: gettext("Name"),
            type: "string",
            visible: true
         },
         {
            data: "type_structure",
            name: "type_structure",
            title: gettext("Type"),
            render: selectobjprint({display_name: "text"}),
            type: "select2",
            url: selects2_url['structure_url'],
            visible: true
            },
        {
            data: "manager",
            name: "manager",
            title: gettext("Manager"),
            render: selectobjprint({display_name: "text"}),
            url: selects2_url['manager_url'],
            type: "select2",
            visible: true
            },
        {
            data: "buildings",
            name: "buildings",
            title: gettext("Buildings"),
            render:gt_print_list_object("text"),
            url: selects2_url['buildings_url'],
            type: "select2",
            visible: true},
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
}

const modalids = {
    destroy: "#delete_obj_modal",
}

const actions = {
    table_actions: [
            {
            action: function (data) {
               window.location.href = add_structure_url;
            },
            text: '<i class="fa fa-plus" aria-hidden="true"></i>',
            className: "btn btn-sm btn-outline-success",
            titleAttr: gettext("Add Structure"),
    }],
    object_actions: [
            {
            name: "update_structure",
            action: 'update_structure',
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
    datatable_element: "#table-structure",
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

const crud = ObjectCRUD("structure_crud", objconfig);
crud.update_structure = function (data) {
    let updateUrl = update_url.replace("/0/", "/" + data.id + "/");
    window.location.href = updateUrl;
}

crud.init();



