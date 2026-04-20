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
            title: gettext("CAS number"),
            type: "string",
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
            data: "quantity_box",
            name: "quantity_box",
            title: gettext("Boxes"),
            type: "number",
            visible: true,
            render: function(data, type, row) {
                if (row.is_box) return data;
                return "-";
            },
            filterable: false,
            sortable: false,
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

    if (data.is_box) {
        modal.find('#id_increase-measurement_unit').closest('.form-group').hide();
        modal.find('#reactive_increase_box_warning').remove();
        var expirationDate = data.reactive_expiration_date || '';
        if (expirationDate) {
            modal.find('.modal-body').append(
                '<div id="reactive_increase_box_warning" class="alert alert-warning text-center" role="alert">' +
                gettext("If you wish to add a new box, please note that it will be subject to the expiration date of") +
                ' ' + expirationDate + '.</div>'
            );
        }
    } else {
        modal.find('#id_increase-measurement_unit').closest('.form-group').show();
        modal.find('#reactive_increase_box_warning').remove();
    }

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

    var $boxContainer = modal.find('#reactive_decrease_box_selection_container');
    if (data.is_box) {
        if (!$boxContainer.length) {
            modal.find('.modal-body form').prepend(
                '<div id="reactive_decrease_box_selection_container" class="form-group row mb-3">' +
                '<label class="col-sm-2 control-label">' + gettext("Select box") + '</label>' +
                '<div class="col-sm-10"><select id="reactive_decrease_box_select" class="form-control"></select></div>' +
                '</div>'
            );
            $boxContainer = modal.find('#reactive_decrease_box_selection_container');
            $(document).on('change', '#reactive_decrease_box_select', function () {
                modal.find('input[name$="-box_index"]').val($(this).val());
            });
        }
        var quantityUnits = data.box_units || [];
        var $select = $boxContainer.find('#reactive_decrease_box_select');
        $select.empty();
        quantityUnits.forEach(function (box, idx) {
            $select.append($('<option>', {
                value: idx,
                text: box.code + ' (' + box.units + ' ' + gettext("unit(s)") + ')'
            }));
        });
        $boxContainer.removeClass('d-none');
        modal.find('input[name$="-box_index"]').val($select.val());
        modal.find('[name$="-measurement_unit"]').closest('.form-group').addClass('d-none');
    } else {
        if ($boxContainer.length) $boxContainer.addClass('d-none');
        modal.find('[name$="-measurement_unit"]').closest('.form-group').removeClass('d-none');
        modal.find('input[name$="-box_index"]').val('');
    }

    form_modals[modalid].showmodal();
    return false;
}

ocrud.init();
