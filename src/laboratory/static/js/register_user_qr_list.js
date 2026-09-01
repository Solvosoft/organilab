function qr_row_url(template, id) {
    // Las urls llegan con pk=0 al final (".../manage/0/"); solo se sustituye
    // ese último segmento para no tocar org_pk/lab_pk.
    return template.replace(/\/0\/$/, '/' + id + '/');
}

function qr_escape(text) {
    return $("<div>").text(text || "").html();
}

datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "string", visible: false},
        {data: "creation_date", name: "creation_date", title: gettext("Creation date"), type: "string", visible: true},
        {data: "last_update", name: "last_update", title: gettext("Last update"), type: "string", visible: true},
        {
            // name = campo real de BD: el ordenamiento server-side usa column.name.
            data: "created_by", name: "created_by__username", title: gettext("Created by"),
            type: "string", visible: true, render: data => qr_escape(data)
        },
        {
            data: "organization_register", name: "organization_register__name",
            title: gettext("Organization"), type: "string", visible: true,
            render: data => qr_escape(data)
        },
        {data: "id", name: "actions", title: " ", type: "string", visible: true, sortable: false},
    ],
    addfilter: false,
    // columnDefs propio: las acciones son enlaces a páginas (editar, PDF,
    // historial, borrar), el render por defecto de ObjectCRUD no aplica.
    columnDefs: [{
        targets: -1,
        orderable: false,
        searchable: false,
        render: function (data, type, full) {
            return '<a title="' + gettext('Edit') + '" class="btn btn-sm btn-outline-warning" href="' +
                qr_row_url(row_action_urls.edit, full.id) + '"><i class="fa fa-pencil-square-o" aria-hidden="true"></i></a> ' +
                '<a title="' + gettext('Download') + '" class="btn btn-sm btn-outline-info" href="' +
                qr_row_url(row_action_urls.download, full.id) + '"><i class="fa fa-file-pdf-o" aria-hidden="true"></i></a> ' +
                '<a title="' + gettext('History') + '" class="btn btn-sm btn-outline-success" href="' +
                qr_row_url(row_action_urls.logentry, full.id) + '"><i class="fa fa-file-text-o"></i></a> ' +
                '<a title="' + gettext('Delete') + '" class="btn btn-sm btn-outline-danger" href="' +
                qr_row_url(row_action_urls.delete, full.id) + '"><i class="fa fa-trash-o" aria-hidden="true"></i></a>';
        }
    }],
}

const objconfig = {
    datatable_element: "#form_table",
    modal_ids: {},
    datatable_inits: datatable_inits,
    urls: object_urls,
}

const ocrud = ObjectCRUD("register_user_qr_crud", objconfig);

ocrud.init();
