// from html: object_urls

datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "number", visible: false},
        {
            data: "object",
            name: "object",
            title: gettext("Object"),
            type: "readonly",
            render: selectobjprint({display_name: 'text'}),
            visible: true
        },
        {
            data: "measurement_unit",
            name: "measurement_unit",
            title: gettext("Measurement Unit"),
            type: "readonly",
            render: selectobjprint({display_name: 'text'}),
            visible: true
        },
        {data: "quantity", name: "quantity", title: gettext("Quantity"), type: "readonly", visible: true},
        {data: "previous_balance", name: "previous_balance", title: gettext("Previous Balance"), type: "readonly", visible: true},
        {data: "new_income", name: "new_income", title: gettext("New Income"), type: "readonly", visible: true},
        {data: "bills", name: "bills", title: gettext("Bills"), type: "readonly", visible: true},
        {data: "providers", name: "providers", title: gettext("Providers"), type: "readonly", visible: true},
        {data: "stock", name: "stock", title: gettext("Stock"), type: "readonly", visible: true},
        {data: "month_expense", name: "month_expense", title: gettext("Month Expense"), type: "readonly", visible: true},
        {data: "final_balance", name: "final_balance", title: gettext("Final Balance"), type: "readonly", visible: true},
        {data: "reason_to_spend", name: "reason_to_spend", title: gettext("Reason to Spend"), type: "readonly", visible: true},
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
    update: "#update_obj_modal",
}

if (has_perm_create) {
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
    clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
    detail: 'fa fa-eye fa-lg',
    update: 'fa fa-edit fa-lg',
    destroy: 'fa fa-trash fa-lg',
}

const objconfig = {
    datatable_element: "#table",
    modal_ids: modalids,
    actions: actions,
    datatable_inits: datatable_inits,
    add_filter: true,
    relation_render: {'field_autocomplete': 'text'},
    delete_display: data => data['object']['text'],
    create: "btn-success",
    icons: icons,
    urls: object_urls,
    gt_form_modals: {
        'create': {"parentdiv": 'as_grid'},
        'update': {"parentdiv": 'as_grid'},
        'detail': {},
        'destroy': {}
    }
}

const ocrud = ObjectCRUD("crudobj", objconfig)
ocrud.init();
