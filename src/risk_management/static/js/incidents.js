
datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "string", visible: false},
        {
            data: "incident_date",
            name: "incident_date",
            title: gettext("Incident Date"),
            type: "date",
            "dateformat":  document.date_format,
            visible: true
        },
        {
            data: "short_description",
            name: "short_description",
            title: gettext("Short Description"),
            type: "readonly",
            visible: true
        },
        {
            data: "laboratories",
            name: "laboratories",
            title: gettext("Laboratories"),
            render: gt_print_list_object("text"),
            url: selects2_url['laboratory_url'],
            type: "select2",
            visible: true
        },
        {
            data: "buildings",
            name: "buildings",
            title: gettext("Buildings"),
            render: gt_print_list_object("text"),
            url: selects2_url['buildings_url'],
            type: "select2",
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
    addfilter: true,
}

const modalids = {
    create: "#create_obj_modal",
    update: "#update_obj_modal",
    destroy: "#delete_obj_modal",
}

const actions = {
    table_actions: [],
    object_actions: [
                {
            name: "download_pdf",
            action: 'download_pdf',
            in_action_column: true,
            i_class: 'fa fa-file-pdf-o',
            method: 'GET',
            title: gettext("Download PDF"),
            data_fn: function (data) {
                return data;
            }
    }],
    title: 'Actions',
    className: "no-export-col"
}

icons = {
    create: '<i class="fa fa-plus" aria-hidden="true"></i>',
    update: 'fa fa-pencil-square-o',
    clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
    detail: 'fa fa-eye fa-lg',
    destroy: 'fa fa-trash fa-lg',
}

const objconfig = {
    datatable_element: "#table-incidents",
    modal_ids: modalids,
    actions: actions,
    datatable_inits: datatable_inits,
    add_filter: true,
    relation_render: {'field_autocomplete': 'text'},
    delete_display: data => data['short_description'],
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

const ocrud = ObjectCRUD("inicident_crud", objconfig);

ocrud.init();



