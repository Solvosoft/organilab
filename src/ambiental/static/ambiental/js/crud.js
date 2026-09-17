/**
 * Configuración común de los ObjectCRUD del módulo ambiental.
 *
 * Cada pantalla solo declara sus columnas; los modales, íconos y acciones
 * siguen la misma forma que el resto de Organilab (ver risk_management/js).
 */
function ambiental_crud(name, table_id, columns, options) {
    options = options || {};
    const modalids = {
        update: "#update_obj_modal",
        destroy: "#delete_obj_modal",
    };
    if (has_perm.create) {
        modalids.create = "#create_obj_modal";
    }
    columns.push({
        data: "actions",
        name: "actions",
        title: gettext("Actions"),
        type: "string",
        visible: true,
        filterable: false,
        sortable: false
    });
    const objconfig = {
        datatable_element: table_id,
        modal_ids: modalids,
        actions: {
            table_actions: options.table_actions || [],
            object_actions: options.object_actions || [],
            title: gettext("Actions"),
            className: "no-export-col"
        },
        datatable_inits: {
            columns: columns,
            addfilter: true,
        },
        add_filter: true,
        relation_render: {},
        delete_display: options.delete_display || (data => data["name"]),
        create: "btn-success",
        icons: {
            create: '<i class="fa fa-plus" aria-hidden="true"></i>',
            update: "fa fa-edit me-1 fa-lg",
            clear: '<i class="fa fa-eraser" aria-hidden="true"></i>',
            detail: "fa fa-eye fa-lg",
            destroy: "fa fa-trash fa-lg",
        },
        urls: object_urls,
        gt_form_modals: {
            create: options.create_modal || {},
            update: options.update_modal || {},
            detail: {},
            destroy: {}
        },
    };
    // djgentelella combina estas opciones con $.extend superficial: un `events` vacío
    // reemplazaría sus eventos por defecto (p. ej. `filter`) y la tabla no cargaría.
    if (options.datatable_events) {
        objconfig.datatable_inits.events = options.datatable_events;
    }
    if (options.events) {
        objconfig.events = options.events;
    }
    const ocrud = ObjectCRUD(name, objconfig);
    ocrud.init();
    return ocrud;
}
