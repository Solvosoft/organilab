function platform_users_escape(text) {
    return $("<div>").text(text || "").html();
}

const platform_users_config = {
    datatable_element: "#platform_users_table",
    modal_ids: {destroy: "#delete_user_modal"},
    urls: platform_users_urls,
    add_filter: true,
    datatable_inits: {
        columns: [
            {data: "id", name: "id", title: "ID", type: "string", visible: false},
            {data: "username", name: "username", title: gettext("User name"), type: "string", visible: true},
            {data: "name", name: "first_name", title: gettext("Name"), type: "readonly", visible: true,
                render: data => platform_users_escape(data)},
            {data: "email", name: "email", title: gettext("Email"), type: "string", visible: true},
            {data: "last_login", name: "last_login", title: gettext("Last login"), type: "readonly", visible: true},
            {data: "date_joined", name: "date_joined", title: gettext("Date joined"), type: "readonly", visible: true},
            {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true,
                filterable: false, sortable: false},
        ],
        addfilter: true,
    },
    actions: {
        table_actions: [],
        object_actions: [
            {
                'name': "merge",
                'action': 'merge',
                'in_action_column': true,
                'i_class': 'fa fa-compress fa-lg',
                'title': gettext("Merge another user into this one"),
            }
        ],
        title: gettext('Actions'),
        className: "no-export-col"
    },
    delete_display: data => `${platform_users_escape(data['username'])}<br><span class="text-danger">${gettext("The user is deleted; the information it created is kept and assigned to the system user.")}</span>`,
    icons: {destroy: 'fa fa-trash fa-lg'},
}

const platform_users_crud = ObjectCRUD("platformuserscrudobj", platform_users_config);
let platform_users_target = null;

platform_users_crud.merge = function (data) {
    platform_users_target = data;
    $("#merge_target_name").text(data.username);
    $("#id_source").val(null).trigger("change");
    $("#merge_user_modal").modal("show");
}

$("#merge_user_submit").on("click", function () {
    const source = $("#id_source").val();
    if (!source || !platform_users_target) {
        return;
    }
    Swal.fire({
        icon: 'warning',
        title: gettext("Are you sure?"),
        text: gettext("The selected user will be deleted after moving its information. This cannot be undone."),
        showCancelButton: true,
        confirmButtonText: gettext("Merge"),
        cancelButtonText: gettext("Cancel"),
    }).then(result => {
        if (!result.isConfirmed) {
            return;
        }
        const url = platform_users_urls.merge_url.replace(/\/0\/merge\/$/, '/' + platform_users_target.id + '/merge/');
        $.ajax({
            url: url, type: "POST", data: {source: source},
            headers: {"X-CSRFToken": getCookie('csrftoken')},
            success: function () {
                $("#merge_user_modal").modal("hide");
                platform_users_crud.datatable.ajax.reload();
                Swal.fire({icon: 'success', title: gettext("Users merged"), timer: 2000, showConfirmButton: false});
            },
            error: function (xhr) {
                const detail = (xhr.responseJSON && (xhr.responseJSON.detail || JSON.stringify(xhr.responseJSON))) || gettext("Error");
                Swal.fire({icon: 'error', title: gettext('Error'), text: detail});
            }
        });
    });
});
