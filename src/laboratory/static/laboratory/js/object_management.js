// from html: object_urls

const OPTIONS = [
    ["True", gettext("Yes")],
    ["False", gettext("No")],
]

datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "number", visible: false},
        {data: "code", name: "code", title: gettext("Code"), type: "string", visible: true},
        {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
        {
            data: "capacity",
            name: "capacity",
            title: gettext("Capacity"),
            type: "string",
            visible: true
        },
        {
            data: "capacity_measurement_unit",
            name: "capacity_measurement_unit",
            title: gettext("Measurement Unit"),
            render: selectobjprint({display_name: 'text'}),
            type: "string",
            visible: true,

        },
        {
            data: "description",
            name: "description",
            title: gettext("Description"),
            type: "string",
            render: truncateTextRenderer(),
            visible: true
        },
        {
            data: "features",
            name: "features",
            title: gettext("Object Features"),
            type: "string", visible: true,
            render: gt_print_list_object("text"),
        },
        {
            data: "is_container",
            name: "is_container",
            title: gettext("Is Container?"),
            type: "select",
            choices: OPTIONS,
            render: yesnoprint,
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
    destroy: "#delete_obj_modal",
    update: "#update_obj_modal",
}

if (has_perm_add_object) {
    modalids.create = "#create_obj_modal";
}

const actions = {
    table_actions: [],
    object_actions: [
        {
            'name': 'view_detail',
            'action': 'view_detail',
            'title': gettext('View Detail'),
            'in_action_column': true,
            'i_class': 'fa fa-eye',
        }
    ],
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
    delete_display: data => data['name'],
    create: "btn-success",
    icons: icons,
    urls: object_urls,
    gt_form_modals: {
        'create': {"parentdiv": 'p'},
        'update': {"parentdiv": 'p'},
    }
}

const ocrud = ObjectCRUD("crudobj", objconfig)
ocrud.view_detail = function(obj, action) {
    let detail_url = object_urls.detail_url.replace('/0/', '/' + obj.id + '/');
    fetch(detail_url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        buildObjectDetailModal(data);
        $('#object_detail_modal').modal('show');
    })
    .catch(error => {
        console.error('Error fetching object detail:', error);
    });
}

function buildObjectDetailModal(data) {
    const modalBody = document.querySelector('#object_detail_modal .modal-body');
    modalBody.innerHTML = '';

    const modalLabel = document.getElementById('object_detail_modal_title');
    modalLabel.textContent = data.name || gettext('Material Detail');

    let html = '<div class="container-fluid">';
    html += '<div class="row">';

    // Columna izquierda - Datos del Object
    html += '<div class="col-md-6">';
    html += '<h5 class="border-bottom pb-2 mb-3">' + gettext('General Information') + '</h5>';
    html += '<table class="table table-sm table-striped">';
    html += '<tbody>';
    html += buildTableRow(gettext('Code'), data.code);
    html += buildTableRow(gettext('Name'), data.name);
    html += buildTableRow(gettext('Synonym'), data.synonym);
    html += buildTableRow(gettext('Description'), data.description);
    html += buildTableRow(gettext('Model'), data.model);
    html += buildTableRow(gettext('Serie'), data.serie);
    html += buildTableRow(gettext('Plaque'), data.plaque);
    html += buildTableRow(gettext('Organization'), data.organization_name);
    html += buildTableRow(gettext('Is Container'), data.is_container ? gettext('Yes') : gettext('No'));
    html += '</tbody></table>';

    // Features
    if (data.features && data.features.length > 0) {
        html += '<h6 class="mt-3">' + gettext('Features') + '</h6>';
        html += '<ul class="list-group list-group-flush">';
        data.features.forEach(function(feature) {
            html += '<li class="list-group-item py-1">' + feature.name + '</li>';
        });
        html += '</ul>';
    }
    html += '</div>';

    // Columna derecha - Material Capacity
    html += '<div class="col-md-6">';
    html += '<h5 class="border-bottom pb-2 mb-3">' + gettext('Container Detail') + '</h5>';

    if (data.material_capacity) {
        const mc = data.material_capacity;
        html += '<table class="table table-sm table-striped">';
        html += '<tbody>';
        html += buildTableRow(gettext('Capacity'), mc.capacity);
        if (mc.capacity_measurement_unit) {
            html += buildTableRow(gettext('Measurement Unit'), mc.capacity_measurement_unit.description);
        }
        html += '</tbody></table>';
    } else {
        html += '<p class="text-muted">' + gettext('No material capacity defined') + '</p>';
    }

    html += '</div>';
    html += '</div>';
    html += '</div>';

    modalBody.innerHTML = html;
}

function buildTableRow(label, value) {
    return '<tr><td class="fw-bold" style="width: 40%;">' + label + '</td><td>' + (value || '-') + '</td></tr>';
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
ocrud.init();
