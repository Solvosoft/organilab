datatable_inits = {
    columns: [
        {data: "id", name: "id", title: gettext("Id"), type: "string", visible: false},
        {
            data: "created_by", name: "created_by", title: gettext("Created by"), type: "readonly", visible: true,
            render: selectobjprint({display_name: "text"})
        },
        {data: "description", name: "description", title: gettext("Description"), type: "readonly", visible: true},
        {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true}
    ],


    addfilter: false
}

var process_modalids = {
    destroy: "#delete_obj_modal",
    update: "#update_obj_modal"
}

if (has_perm) {
    process_modalids.create = "#create_obj_modal";
}

var process_actions = {
    table_actions: [],  //table_actions
    object_actions: [],
    title: gettext('Actions'),
    className: "no-export-col"
}

icons = {
    create: '<i class="fa fa-plus" aria-hidden="true"></i>',
    clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
    detail: 'fa fa-eye',
    update: 'fa fa-edit me-1 fa-lg',
    destroy: 'fa fa-trash fa-lg'
}

let objconfig = {
    urls: object_urls,
    datatable_element: "#process_table",
    modal_ids: process_modalids,
    actions: process_actions,
    datatable_inits: datatable_inits,
    add_filter: true,
    relation_render: {'field_autocomplete': 'text'},
    delete_display: data => data['pk'],
    create: "btn-success",
    icons: icons
}


let ocrud = ObjectCRUD("processcrudobj", objconfig)
ocrud.init();
