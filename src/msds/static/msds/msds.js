const is_verified = [
["True", gettext("Yes")],
    ["False", gettext("No")],
]
datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "string", visible: false},
        {
            data: "sustance_characteristics_name",
            name: "sustance_characteristics__obj__name",
            title: gettext("Substance"),
            type: "string",
            visible: true
        },
        {
            data: "sustance_characteristics_cas_id_number",
            name: "sustance_characteristics__cas_id_number",
            title: gettext("CAS"),
            type: "string",
            visible: true
        },
        {
            data: "source",
            name: "source",
            title: gettext("Source"),
            type: "string",
            visible: true
        },
        {
            data: "is_verified",
            name: "is_verified",
            title: gettext("Is Verified"),
            visible: true,
            render: yesnoprint,
            type: "select",
            choices: is_verified,
            render: function(data, type, row) {
                if (data) {
                    return '<span class="badge bg-success">' + gettext("Yes") + '</span>';
                }
                return '<span class="badge bg-secondary">' + gettext("No") + '</span>';
            }
        },
        {
            data: "verified_by_name",
            name: "verified_by",
            title: gettext("Verified By"),
            type: "readonly",
            visible: true
        },

        {data: "verified_date", name: "verified_date", title: gettext("Verified Date"), type: "readonly", visible: true},
        {
            data: "security_sheet_url",
            name: "security_sheet",
            title: gettext("Security Sheet"),
            type: "string",
            visible: true,
            render: function(data, type, row) {
                if (data) {
                    return '<a href="' + data + '" download class="btn btn-sm btn-outline-success">' +
                           '<i class="fa fa-download"></i> ' + gettext("Download") + '</a>';
                }
                return '<p class="text-muted">' + gettext("No file") + '</p>';
            }
        },
        {
            data: "actions",
            name: "actions",
            title: gettext("Actions"),
            visible: true,
            filterable: false,
            sortable: false,
            render: function(data, type, row, meta) {
                if (!data.verified) {
                    return `<a class="validate_sds" data-sds="${row.id}" data-verified="true" title="${gettext("Verified")}"><i class="fa fa-check-square-o text-success" title="${gettext("Verified")}"></i></a>`;
                } else {
                    return `<a class="validate_sds" data-sds="${row.id}" data-verified="false" title="${gettext("Unverified")}"><i class="fa fa-close text-danger"></i></a>`;
                }
            }
        },
    ],
    addfilter: true,
}
const actions = {
    table_actions: [],
    object_actions: [],
    title: gettext('Actions'),
    className: "no-export-col"
}

icons = {
    clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
}

const objconfig = {
    datatable_element: "#sds-traceability-table",
    actions: actions,
    datatable_inits: datatable_inits,
    modal_ids: {},
    add_filter: true,
    icons: icons,
    urls: object_urls,
}

const crud = ObjectCRUD("sds_traceability_crud", objconfig);

crud.init();


$(document).on('click', '.validate_sds', function(){
    let sds = $(this).data('sds');
    let verified = $(this).data('verified');
    Swal.fire({
        title: verified ? gettext("Verify SDS") : gettext("Unverify SDS"),
        text: verified ? gettext("Do you want to mark this SDS as verified?"): gettext("Do you want to mark this SDS as unverified?"),
        icon: "question",
        confirmButtonText: gettext("Yes"),
        denyButtonText: gettext("No"),
        showDenyButton: true,
        showCloseButton: true
    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: verified_urls.verify_url,
                type: "POST",
                dataType: "json",
                data: {id: sds, is_verified: verified},
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                success: function(response) {
                    Swal.fire({
                        icon: 'success',
                        title: gettext('Success'),
                        text: response.detail || gettext('SDS marked was updated'),
                    }).then(function() {
                        crud.datatable.ajax.reload();
                    });
                },
                error: function(request, status, error) {
                    Swal.fire({
                        icon: 'error',
                        title: gettext('Error'),
                        text: gettext('An error has occurred'),
                    });
                }
            });
        }
    });
});
