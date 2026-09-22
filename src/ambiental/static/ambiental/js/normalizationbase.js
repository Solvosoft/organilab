let ocrud = null;

function ambiental_preload_bases() {
    Swal.fire({
        title: gettext("Preload bases"),
        text: gettext("Square meters come from each building and people from the workdays of its risk zones. Values entered manually are kept."),
        input: "number",
        inputValue: new Date().getFullYear(),
        inputLabel: gettext("Year"),
        showCancelButton: true,
        confirmButtonText: gettext("Preload"),
        cancelButtonText: gettext("Cancel"),
    }).then(function (result) {
        if (!result.isConfirmed) {
            return;
        }
        fetch(object_urls.preload_url, {
            method: "POST",
            body: JSON.stringify({year: result.value}),
            headers: {"X-CSRFToken": getCookie("csrftoken"), "Content-Type": "application/json"}
        }).then(response => response.json().then(data => ({ok: response.ok, data: data})))
            .then(function (response) {
                const text = response.data.detail || Object.values(response.data).join(" ");
                Swal.fire({icon: response.ok ? "success" : "error", text: text});
                ocrud.datatable.ajax.reload();
            });
    });
}

const table_actions = [];
if (has_perm.preload) {
    table_actions.push({
        action: ambiental_preload_bases,
        text: '<i class="fa fa-magic" aria-hidden="true"></i>',
        className: "btn btn-sm btn-outline-primary",
        titleAttr: gettext("Preload bases"),
    });
}

ocrud = ambiental_crud("ambiental_normalizationbase", "#table-normalizationbase", [
    {data: "id", name: "id", title: "ID", type: "string", visible: false},
    {data: "year", name: "year", title: gettext("Year"), type: "string", visible: true},
    {
        data: "building", name: "building", title: gettext("Building"),
        type: "select2", url: selects2_url.building_url,
        render: gt_print_list_object("text"), visible: true
    },
    {
        data: "normalizer", name: "normalizer", title: gettext("Normalizer"),
        type: "readonly", render: gt_print_list_object("text"), visible: true
    },
    {data: "value", name: "value", title: gettext("Value"), type: "readonly", visible: true},
    {data: "origin", name: "is_manual", title: gettext("Origin"), type: "readonly", visible: true, sortable: false},
], {
    table_actions: table_actions,
    delete_display: data => data["building"]["text"] + " " + data["year"],
});
