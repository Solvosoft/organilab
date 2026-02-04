const object_urls = window.object_urls
var datatableelement = null;
datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "number", visible: false},
        {
            data: "object",
            name: "object_name",
            title: gettext("Name"),
            render: selectobjprint({display_name: "text"}),
            visible: true,
            type: "string",
        },
        {
            data: "cas_code",
            name: "cas_code",
            title: gettext("Nº CAS"),
            type: "readonly",
            visible: true
        },
        {
            data: "labroom",
            name: "labroom_name",
            title: gettext("Labroom"),
            type: "string",
            visible: true
        },
        {
            data: "furniture",
            name: "furniture_name",
            title: gettext("Furniture"),
            type: "string",
            visible: true
        },
        {
            data: "shelf",
            name: "shelf_name",
            title: gettext("Shelf"),
            render: selectobjprint({display_name: "text"}),
            type: "string",
            visible: true,
        },
        {
            data: "container",
            name: "container_name",
            title: gettext("Container"),
            type: "string",
            visible: true,
        },
        {
            data: "quantity",
            name: "quantity",
            title: gettext("Quantity"),
            type: "number",
            visible: true,
        },
        {
            data: "measurement_unit",
            name: "measurement_description",
            title: gettext("Measurement Unit"),
            render: selectobjprint({display_name: "text"}),
            type: "string",
            visible: true,
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

const modalids = {}

const actions = {
    table_actions: [],
    object_actions: [
        {
            'name': "increase",
            'action': 'increase',
            'in_action_column': true,
            'i_class': 'fa fa-plus text-success',
            'method': 'POST',
            'title': gettext("Add"),
            data_fn: function (data) {
                return data;
            },
        },
        {
            'name': "decrease",
            'action': 'decrease',
            'in_action_column': true,
            'i_class': 'fa fa-minus text-danger',
            'method': 'POST',
            'title': gettext("Decrease"),
            data_fn: function (data) {
                return data;
            },
        }
    ],
    title: 'Actions',
    className: "no-export-col"
}

icons = {
    clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
}

const objconfig = {
    datatable_element: "#table",
    modal_ids: modalids,
    actions: actions,
    datatable_inits: datatable_inits,
    add_filter: true,
    relation_render: {'field_autocomplete': 'text'},
    create: "btn-success",
    icons: icons,
    urls: object_urls
}

const ocrud = ObjectCRUD("crudobj", objconfig)

$(document).ready(function() {
    datatableelement = $('#table').DataTable();
});

ocrud.increase = function (data) {
    var modalid = "#increasesomodal";
    var modal = $(modalid);

    modal.find('#id_increase-shelf').val(data.shelf.id);
    modal.find('#id_increase-shelfobject').val(data.id);
    modal.find('#id_increase-laboratory').val(data.in_where_laboratory.id);
    modal.find('#id_increase-organization').val(org_pk);

    if(!form_modals.hasOwnProperty(modalid)) {
        var formmodal = BaseFormModal(modalid, {
            shelf_object: data.id,
            shelf: data.shelf.id
        });

        formmodal.url = object_urls.increase_url;
        formmodal.init();

        formmodal.success = function(instance, response) {
            modal.find(':focus').blur();
            modal.modal('hide');
        };

        form_modals[modalid] = formmodal;
    }

    form_modals[modalid].showmodal();
    return false;
}

ocrud.decrease = function (data) {
    var modalid = "#decreasesomodal";
    var modal = $(modalid);

    modal.find('#id_decrease-shelf').val(data.shelf.id);
    modal.find('#id_decrease-shelfobject').val(data.id);
    modal.find('#id_decrease-laboratory').val(data.in_where_laboratory.id);
    modal.find('#id_decrease-organization').val(org_pk);

    if(!form_modals.hasOwnProperty(modalid)) {
        var formmodal = BaseFormModal(modalid, {
            shelf_object: data.id,
            shelf: data.shelf.id
        });

        formmodal.url = object_urls.decrease_url;
        formmodal.init();

        formmodal.success = function(instance, response) {
            modal.find(':focus').blur();
            modal.modal('hide');
        };

        form_modals[modalid] = formmodal;
    }

    form_modals[modalid].showmodal();
    return false;
}

ocrud.init();
