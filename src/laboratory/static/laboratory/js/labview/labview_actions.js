/* La tabla de objetos del estante seleccionado.
 *
 * Los modales de acción de shelfobject llevan tiempo funcionando contra la API
 * y no se reescriben: esta tabla los abre exactamente igual que la vista
 * antigua, con los mismos `data-*`. Lo único que cambia es quién decide qué
 * botón existe. Antes lo decidía una plantilla de 124 líneas renderizada por
 * fila; ahora llega en el diccionario `actions` de cada fila, y `variants` dice
 * cuál de los cuatro formularios de edición y cuál de los dos de mover
 * corresponden.
 *
 * La interfaz no deduce permisos: pinta lo que el servidor autoriza. Y el
 * servidor vuelve a exigirlos en cada endpoint, así que un cliente manipulado
 * no gana nada.
 */

const LabviewTable = {
    table: null,

    init() {
        LabviewState.subscribe((selection) => this.onSelection(selection));
        this.build();
    },

    url(pk) {
        return document.labview_urls[pk];
    },

    // Hay rutas con barra final (`.../0/details/`) y sin ella
    // (`shelf_objects/0`); sustituir solo `/0/` dejaba estas últimas
    // apuntando al pk 0 en todas las filas.
    withPk(url, pk) {
        if (url.indexOf('/0/') !== -1) { return url.replace('/0/', '/' + pk + '/'); }
        return url.replace(/\/0$/, '/' + pk);
    },

    build() {
        const columns = [
            {data: 'pk', name: 'pk', title: gettext('Id'), type: 'string',
             visible: true},
            {data: 'object_name', name: 'object__name', title: gettext('Object'),
             type: 'string', visible: true},
            {data: 'object_type', name: 'object__type', title: gettext('Type'),
             type: 'string', visible: true},
            {data: 'shelfobject_code', name: 'shelfobject_code',
             title: gettext('Code'), type: 'string', visible: true},
            {data: 'quantity', name: 'quantity', title: gettext('Quantity'),
             type: 'string', visible: true},
            {data: 'unit', name: 'measurement_unit__description',
             title: gettext('Unit'), type: 'string', visible: true,
             render: truncateTextRenderer()},
            {data: 'container', name: 'container__object__name',
             title: gettext('Container'), type: 'string', visible: true},
            {data: null, name: 'actions', title: gettext('Actions'),
             type: 'string',
             render: (row) => this.renderActions(row)}
        ];

        this.table = createDataTable('#labview_shelfobjecttable',
            document.labview_urls.shelfobject_table, {
                columns: columns,
                // Los mismos botones que la vista antigua: crear equipo,
                // material o sustancia, ir a contenedores y transferencias
                // entrantes. Se piden a la funcion compartida para que las dos
                // pantallas no puedan divergir.
                buttons: get_shelfobject_table_buttons(),
                deferLoading: true,
                responsive: true,
                layout: {
                    topStart: 'pageLength', top: 'buttons', topEnd: 'search',
                    bottomStart: 'info', bottomEnd: 'paging'
                },
                ajax: {
                    url: document.labview_urls.shelfobject_table,
                    type: 'GET',
                    data: (dataTableParams, settings) => {
                        const data = formatDataTableParams(dataTableParams, settings);
                        data['shelf'] = LabviewState.selection.shelf || '';
                        return data;
                    }
                }
            }, false);

        // shelfobjectedit.js recarga la tabla por esta global tras borrar o
        // editar; apuntarla aquí es lo que permite reutilizar ese código tal
        // cual.
        window.datatableelement = this.table;
        // El boton "Transfer In" abre esta tabla; sin inicializarla el modal
        // se abriria vacio.
        init_transfer_list_table();
    },

    onSelection(selection) {
        const panel = document.getElementById('labview_shelf_panel');
        if (!selection.shelf) {
            panel.innerHTML = '<p class="text-muted">' +
                gettext('Select a shelf to see its objects.') + '</p>';
            document.getElementById('labview_table_wrapper').classList.add('d-none');
            return;
        }
        document.getElementById('id_shelf').value = selection.shelf;
        const found = LabviewState.findShelf(selection.shelf);
        // `addObjectResponse` lo lee como cadena, igual que el data-refuse del
        // radio de la vista antigua.
        document.shelf_discard = found && found.shelf.discard ? 'True' : 'False';
        this.renderShelfPanel(selection.shelf);
        document.getElementById('labview_table_wrapper').classList.remove('d-none');
        this.table.ajax.reload();
        // En móvil el mapa y la tabla se apilan, así que hay que llevar al
        // usuario hasta la tabla que acaba de pedir.
        if (window.matchMedia('(max-width: 991.98px)').matches) {
            document.getElementById('labview_table_wrapper')
                .scrollIntoView({behavior: 'smooth', block: 'start'});
        }
    },

    renderShelfPanel(shelfPk) {
        const found = LabviewState.findShelf(shelfPk);
        const panel = document.getElementById('labview_shelf_panel');
        if (!found) { panel.innerHTML = ''; return; }
        const shelf = found.shelf;
        const occupancy = shelf.occupancy_percent === null
            ? '—' : shelf.occupancy_percent + '%';
        panel.innerHTML = `
<div class="d-flex align-items-center gap-2 flex-wrap">
  <strong>${escapeHtml(shelf.name)}</strong>
  <small class="text-muted">${escapeHtml(found.furniture.name)} ·
    ${escapeHtml(found.room.name)} · ${occupancy}</small>
  ${LabviewMap.renderQr(shelf.qr, shelf.name)}
  <a href="${shelf.deep_link}" target="_blank" title="${gettext('Direct link')}">
    <i class="fa fa-tags"></i></a>
  <button type="button" class="btn btn-sm btn-link" id="labview_availability"
          data-shelf="${shelf.id}">${gettext('Availability')}</button>
</div>`;
        const availability = document.getElementById('labview_availability');
        availability.addEventListener('click', () => this.showAvailability(shelf.id));
    },

    showAvailability(shelfPk) {
        fetch(this.withPk(document.labview_urls.shelf_detail, shelfPk) + 'availability/',
              {headers: {'X-CSRFToken': getCookie('csrftoken')}})
            .then((response) => response.json())
            .then((data) => {
                const rows = [
                    [gettext('Type'), data.type_name],
                    [gettext('Capacity'), data.infinity_quantity
                        ? gettext('Infinity') : data.quantity],
                    [gettext('Unit'), data.measurement_unit_name],
                    [gettext('Stored'), data.total === null ? '—' : data.total],
                    [gettext('Occupancy'), data.occupancy_percent === null
                        ? '—' : data.occupancy_percent + '%'],
                    [gettext('Disposal'), data.discard ? gettext('Yes') : gettext('No')]
                ];
                Swal.fire({
                    title: data.name,
                    html: '<table class="table table-sm">' + rows.map(
                        (row) => `<tr><th class="text-start">${row[0]}</th>` +
                                 `<td class="text-end">${escapeHtml(row[1])}</td></tr>`
                    ).join('') + '</table>'
                });
            });
    },

    /* -- acciones por fila -------------------------------------------------- */

    renderActions(row) {
        const actions = row.actions || {};
        const variants = row.variants || {};
        const urls = document.labview_urls;
        const shelf = row.shelf;
        const out = [];

        if (actions.detail) {
            out.push(`<a id="shelfobject_view_${row.pk}" class="ms-2"
                data-url="${this.withPk(urls.shelfobject_details, row.pk)}"
                onclick="shelfObjectDetail(this)" title="${gettext('Detail')}"
                ><i class="fa fa-eye text-success"></i></a>`);
        }
        if (actions.labels) {
            out.push(`<a class="ms-2"
                data-url="${this.withPk(urls.recipient_list, row.pk)}"
                onclick="displayShelfobjectLabels(this)"
                data-recipient="${urls.generate_label.replace(
                    '/0/generate_shelfobject_label/',
                    '/' + row.pk + '/generate_shelfobject_label/')}"
                data-object="${row.pk}" title="${gettext('List of Recipients')}"
                ><i class="fa fa-list-alt"></i></a>`);
        }
        if (actions.reserve) {
            out.push(this.modalLink('reservesomodal', row, shelf,
                'fa fa-shopping-basket', gettext('Reservation')));
        }
        if (actions.increase) {
            out.push(`<a class="ms-2" onclick="return show_me_modal(this, event);"
                data-modalid="increasesomodal" title="${gettext('Add')}"
                data-shelfobject="${row.pk}" data-shelf="${shelf}"
                data-box="${row.is_box ? 'True' : 'False'}"
                data-expiration="${row.reactive_expiration_date || 'None'}"
                ><i class="fa fa-plus text-success"></i></a>`);
        }
        if (actions.transfer_out) {
            out.push(`<a class="ms-2" onclick="return show_me_modal(this, event);"
                data-modalid="transfer_out_obj_id_modal"
                title="${gettext('Transfer Out')}" data-shelfobject="${row.pk}"
                data-shelf="${shelf}"
                data-expiration="${row.reactive_expiration_date || 'None'}"
                ><i class="fa fa-window-restore"></i></a>`);
        }
        if (actions.decrease) {
            out.push(`<a class="ms-2" onclick="return show_decrease_modal(this, event);"
                data-modalid="decreasesomodal" title="${gettext('Substract')}"
                data-shelfobject="${row.pk}" data-shelf="${shelf}"
                data-is-box="${row.is_box ? 'true' : 'false'}"
                data-quantity-units='${JSON.stringify(row.quantity_units || [])}'
                ><i class="fa fa-minus text-danger"></i></a>`);
        }
        if (actions.log) {
            out.push(`<a class="ms-2" target="_blank"
                href="${this.withPk(urls.shelfobject_log, row.pk)}"
                title="${gettext('Log')}"><i class="fa fa-file-text-o"></i></a>`);
        }
        if (actions.edit && variants.edit) {
            out.push(this.editLink(variants.edit, row, shelf));
        }
        if (actions.container) {
            out.push(`<a class="ms-2"
                onclick="return updateContainerOfShelfObject(this, event);"
                data-modalid="managecontainermodal"
                title="${gettext('Manage Container')}"
                data-container="${row.container_id || ''}"
                data-containername="${escapeHtml(row.container_display)}"
                data-shelfobject="${row.pk}" data-shelf="${shelf}"
                ><i class="fa fa-hourglass-end"></i></a>`);
        }
        if (actions.move) {
            const modal = variants.move === 'container'
                ? 'movesocontainermodal' : 'movesomodal';
            out.push(this.modalLink(modal, row, shelf, 'fa fa-arrows',
                gettext('Move')));
        }
        if (actions.maintenance) {
            out.push(`<a class="ms-2" target="_blank"
                href="${this.withPk(urls.equipment_detail, row.pk)}"
                title="${gettext('Maintenance')}"><i class="fa fa-archive"></i></a>`);
        }
        if (actions.report) {
            out.push(`<a class="ms-2" target="_blank"
                href="${this.withPk(urls.shelfobject_report, row.pk)}"
                title="${gettext('Download')}"><i class="fa fa-download"></i></a>`);
        }
        if (actions.destroy) {
            const name = String(row.object_raw_name).replace(/'/g, "\\'");
            const container = row.container_id
                ? `true, container_name='${String(row.container_name).replace(/'/g, "\\'")}'`
                : 'false';
            out.push(`<a class="ms-2" title="${gettext('Delete')}"
                onclick="shelfObjectDelete(${row.pk}, '${name}', '${row.type}',
                    container=${container})"
                ><i class="fa fa-close text-danger"></i></a>`);
        }
        return out.join('');
    },

    modalLink(modalid, row, shelf, icon, title) {
        return `<a class="ms-2" onclick="return show_me_modal(this, event);"
            data-modalid="${modalid}" title="${title}"
            data-shelfobject="${row.pk}" data-shelf="${shelf}"
            ><i class="${icon}"></i></a>`;
    },

    editLink(kind, row, shelf) {
        const config = {
            reactive: ['editReactiveShelfObject', 'edit_reactive_modal',
                       'edit_reactive_form'],
            box: ['editBoxShelfObject', 'edit_box_modal', 'edit_box_form'],
            material: ['editMaterialShelfObject', 'edit_material_modal',
                       'edit_material_form']
        }[kind];
        if (!config) { return ''; }
        return `<a class="ms-2" onclick="return ${config[0]}(this, event);"
            data-modalid="${config[1]}" title="${gettext('Edit')}"
            data-shelfobject="${row.pk}" data-shelf="${shelf}"
            data-form="${config[2]}"><i class="fa fa-pencil-square-o"></i></a>`;
    },

    /* -- crear -------------------------------------------------------------- */

    // Crear objetos lo resuelven los botones de cabecera de la tabla
    // (`tableObject.addObject`), que ademas preparan el formulario: prefijo,
    // selects de recipiente y de contenedor, `without_limit` y la variante de
    // residuos cuando el estante es de descarte. Reimplementarlo aqui habria
    // perdido todo eso.
};
