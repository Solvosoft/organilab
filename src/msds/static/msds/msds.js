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
            data: "hcodes",
            name: "hcodes",
            title: gettext("H-codes"),
            type: "readonly",
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
                    return `<a class="validate_sds" data-sds="${row.id}" data-verified="true" title=${gettext("Verified")}><i class="fa fa-square-o text-success" title="${gettext("Verified")}"></i></a>
                    <a class="get_sustance_characteristics_info" data-sds="${row.id}" title=${gettext("Get Substance Characteristics")}><i class="fa fa-info-circle text-secondary" title=${gettext("Get Substance Information")}></i></a>`;
                } else {
                    return `<a class="validate_sds" data-sds="${row.id}" data-verified="false" title=${gettext("Unverified")}><i class="fa fa-check-square-o text-success"></i></a>
                    <a class="get_sustance_characteristics_info" data-sds="${row.id}" title=${gettext("Get Substance Characteristics")}><i class="fa fa-info-circle text-secondary" title=${gettext("Get Substance Information")}></i></a>`;
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
        title: verified ? gettext("Verify FDS") : gettext("Unverify FDS"),
        text: verified ? gettext("Do you want to mark this FDS as verified?"): gettext("Do you want to mark this FDS as unverified?"),
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
                        text: response.detail || gettext('FDS marked was updated'),
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

$(document).on('click', '.get_sustance_characteristics_info', function(){
    let sds = $(this).data('sds');
    let url = verified_urls.get_sustance_characteristics_info_url;
    console.log(url);
    $.ajax({
        url: url,
        type: "GET",
        dataType: "json",
        data: {pk: sds},
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
        },
        success: function(response) {
            $('#object_title').html(gettext('Information from ' ) + ' ' + response.obj_name);
            add_single_data("obj_name", response.obj_name);
            add_single_data("cas", response.cas_id_number);
            add_single_data("molecular", response.molecular_formula);
            add_single_data("precursor", response.is_precursor);
            add_multiple_data("white_organ", response.white_organ_list);
            add_multiple_data("h_code", response.h_code_list);
            add_multiple_data("ue_code", response.ue_code_list);
            add_multiple_data("storage_class", response.storage_class_list);
            $('#fds_modal').modal('show');
        },
        error: function(request, status, error) {
            Swal.fire({
                icon: 'error',
                title: gettext('Error'),
                text: gettext('An error has occurred'),
            });
        }
    });
});

function add_single_data(id, data){
    $('#'+id).empty();
    $('#'+id).html("<p>"+data+"</p>");
}
function add_multiple_data(id, data){
    result= ""
    $('#'+id).empty();
    data.forEach(function(item){
        result+= "<li>"+item+"</li>";

    }
    );
    $('#'+id).html(result);
}
