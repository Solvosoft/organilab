function trash_escape(text) {
    return $("<div>").text(text || "").html();
}

const trash_datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "string", visible: false},
        {
            data: "created_at", name: "created_at", title: gettext("Deleted date"),
            type: "date", dateformat: document.datetime_format, visible: true
        },
        {
            data: "deleted_by", name: "deleted_by", title: gettext("Deleted by"),
            type: "readonly", visible: true, render: data => trash_escape(data)
        },
        {
            data: "object_repr", name: "object_repr", title: gettext("Description"),
            type: "readonly", visible: true, render: data => trash_escape(data)
        },
        {
            data: "model_name", name: "content_type__model", title: gettext("Model"),
            type: "readonly", visible: true, render: data => trash_escape(data)
        },
        {
            data: "actions", name: "actions", title: gettext("Actions"),
            type: "string", visible: true, filterable: false, sortable: false
        },
    ],
    addfilter: false,
}

const trash_actions = {
    table_actions: [],
    object_actions: [
        {
            'name': "restore",
            'action': 'restore',
            'in_action_column': true,
            'i_class': 'fa fa-undo',
            'method': 'POST',
            'title': gettext("Restore"),
            data_fn: function (data) {
                return data;
            }
        }
    ],
    title: gettext('Actions'),
    className: "no-export-col"
}

const trash_config = {
    datatable_element: "#trash_table",
    modal_ids: {destroy: "#delete_trash_modal"},
    actions: trash_actions,
    datatable_inits: trash_datatable_inits,
    add_filter: false,
    delete_display: data => {
        return `${trash_escape(data['object_repr'])} <br> ${gettext('Model')}: ${trash_escape(data['model_name'])} <br> <span class="text-danger">${gettext("This action will permanently delete the register, as well as all related data.")}</span>`;
    },
    icons: {
        detail: 'fa fa-eye fa-lg',
        update: 'fa fa-edit fa-lg',
        destroy: 'fa fa-trash fa-lg',
    },
    urls: trash_urls,
}

const trash_crud = ObjectCRUD("trashcrudobj", trash_config);

trash_crud.restore = function (data) {
    // Solo se sustituye el placeholder del pk (".../0/restore/"), nunca el
    // org_pk del prefijo.
    const url = trash_urls.restore_url.replace(/\/0\/restore\/$/, '/' + data.id + '/restore/');

    $.ajax({
        url: url, type: "POST", data: {}, headers: {
            "X-CSRFToken": getCookie('csrftoken'),
        }, success: function (response) {
            if (response.result) {
                Swal.fire({
                    icon: 'success',
                    title: gettext('Success'),
                    text: response.detail,
                    confirmButtonText: gettext('Accept'),
                })
                trash_crud.datatable.ajax.reload()
            } else {
                window.location.reload();
            }
        }, error: function (xhr, status, error) {
            // La API contesta JSON en todos los errores que controla
            // ({result, detail} o {detail} de DRF: 404 restaurado en otra
            // pestaña, 403 sin permiso, 410 huérfano); se muestra esa razón.
            const detail = xhr.responseJSON && xhr.responseJSON.detail;
            Swal.fire({
                icon: 'error',
                title: gettext('Error'),
                text: detail || gettext("Sorry, an error occurred."),
                confirmButtonText: gettext('Accept'),
            })
        }
    });
}

trash_crud.init();
