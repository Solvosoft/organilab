

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
            data: "workday",
            name: "workday",
            title: gettext("Workday"),
            type: "string",
            visible: true,
            render: gt_print_list_object( "text"),
        },
        {
            data: "num_workers",
            name: "num_workers",
            title: gettext("Number of workers"),
            type: "string",
            visible: true
        },
        {
            data: "start_time",
            name: "start_time",
            title: gettext("Start Time"),
            type: "string",
            visible: true
        },
        {
            data: "end_time",
            name: "end_time",
            title: gettext("End Time"),
            type: "string",
            visible: true
        },
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
    addfilter: false,
}

const modalids = {
    destroy: "#delete_obj_modal",
    update: "#update_obj_modal",
}

if (has_create_perm){
    modalids.create = "#create_obj_modal";
}

const actions = {
    table_actions: [],
    object_actions: [],
    title: 'Actions',
    className: "no-export-col"
}

icons = {
    create: '<i class="fa fa-plus" aria-hidden="true"></i>',
    update: 'fa fa-edit me-1 fa-lg',
    clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
    detail: 'fa fa-eye fa-lg',
    destroy: 'fa fa-trash fa-lg',
}

const objconfig = {
    datatable_element: "#table-workday",
    modal_ids: modalids,
    actions: actions,
    datatable_inits: datatable_inits,
    add_filter: true,
    relation_render: {'field_autocomplete': 'text'},
    delete_display: data => data['workday'],
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

const ocrud = ObjectCRUD("workdays_crud", objconfig);

ocrud.init();



