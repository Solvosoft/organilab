/* El mapa: salas plegables, muebles con su cuadrícula real y el panel del
 * estante seleccionado.
 *
 * Un solo fetch al árbol trae todo lo que la pantalla necesita, incluidos el
 * QR y el enlace directo de cada nodo, de modo que ninguna de esas funciones
 * dependa ya de dónde esté renderizada.
 *
 * La cuadrícula la dibuja PositionsGrid, que es genérico: aquí solo se decide
 * el aspecto de un estante con `renderItem`. Las filas pueden tener distinto
 * número de celdas porque la forma la define el usuario según cómo sea su
 * laboratorio.
 */

const LabviewMap = {
    grids: {},
    container: null,

    init(container) {
        this.container = container;
        LabviewState.subscribe((selection, reason) => {
            if (reason !== 'map') { this.highlight(selection); }
        });
        return this.load();
    },

    url(risk) {
        return document.labview_urls.tree + (risk ? '?risk=1' : '');
    },

    load(risk) {
        const useRisk = risk === undefined ? LabviewState.riskEnabled : risk;
        return fetch(this.url(useRisk), {headers: {'X-CSRFToken': getCookie('csrftoken')}})
            .then((response) => response.json())
            .then((tree) => {
                LabviewState.setTree(tree);
                this.render();
                this.highlight(LabviewState.selection);
                return tree;
            });
    },

    /* -- render ------------------------------------------------------------ */

    render() {
        this.grids = {};
        this.container.innerHTML = LabviewState.tree.rooms
            .map((room) => this.renderRoom(room)).join('') || this.renderEmpty();
        LabviewState.tree.rooms.forEach((room) => {
            room.furniture.forEach((furniture) => this.mountGrid(furniture));
        });
        this.bind();
    },

    renderEmpty() {
        return '<p class="text-muted">' +
               gettext('This laboratory has no rooms yet.') + '</p>';
    },

    renderRoom(room) {
        const counts = room.counts;
        const summary = interpolate(
            gettext('%(furniture)s furniture · %(shelves)s shelves · %(objects)s objects'),
            {furniture: counts.furniture, shelves: counts.shelves,
             objects: counts.shelfobjects}, true);
        const open = LabviewState.selection.labroom === room.id;
        return `
<div class="card mb-3 labview-room" data-room="${room.id}">
  <div class="card-header d-flex align-items-center gap-2">
    <button class="btn btn-sm btn-link p-0 labview-room-toggle" type="button"
            data-room="${room.id}" aria-expanded="${open}">
      <i class="fa fa-chevron-${open ? 'down' : 'right'}"></i>
    </button>
    <strong class="flex-grow-1">${escapeHtml(room.name)}</strong>
    ${this.renderRiskBadge(room.risk)}
    ${this.renderQr(room.qr, room.name)}
    <a href="${room.deep_link}" target="_blank" class="ms-1"
       title="${gettext('Open in another tab')}"><i class="fa fa-tags"></i></a>
  </div>
  <div class="card-body labview-room-body ${open ? '' : 'd-none'}">
    <p class="text-muted small mb-3">${summary}</p>
    ${room.furniture.map((f) => this.renderFurniture(f)).join('') ||
      '<p class="text-muted">' + gettext('No furniture in this room.') + '</p>'}
  </div>
</div>`;
    },

    renderFurniture(furniture) {
        const canEdit = LabviewState.can('change_furniture');
        return `
<div class="labview-furniture mb-4" data-furniture="${furniture.id}">
  <div class="d-flex align-items-center gap-2 mb-2">
    <span class="labview-furniture-dot" style="background:${furniture.color}"></span>
    <strong>${escapeHtml(furniture.name)}</strong>
    <small class="text-muted">${escapeHtml(furniture.type_name)} ·
      ${furniture.counts.shelves} ${gettext('shelves')}</small>
    ${this.renderQr(furniture.qr, furniture.name)}
    ${LabviewState.can('do_report')
      ? `<a href="${furniture.report_url}" target="_blank" class="ms-1"
            title="${gettext('Report')}"><i class="fa fa-file-pdf-o"></i></a>` : ''}
    ${canEdit
      ? `<button type="button" class="btn btn-sm btn-outline-secondary ms-auto labview-edit"
                 data-furniture="${furniture.id}">
           <i class="fa fa-pencil"></i> ${gettext('Edit furniture')}</button>` : ''}
  </div>
  <div class="labview-grid" id="labview_grid_${furniture.id}"></div>
  ${this.renderUnplaced(furniture)}
</div>`;
    },

    // Un estante que existe pero no ocupa ninguna celda no puede desaparecer
    // del mapa: si desapareciera, no habría forma de volver a colocarlo.
    renderUnplaced(furniture) {
        if (!furniture.unplaced.length) { return ''; }
        const names = furniture.unplaced
            .map((pk) => escapeHtml(furniture.shelves[String(pk)].name)).join(', ');
        return `<p class="small text-warning mb-0">
                  <i class="fa fa-exclamation-triangle"></i>
                  ${gettext('Shelves without a position:')} ${names}</p>`;
    },

    renderQr(qr, name) {
        if (!qr) { return ''; }
        return `<a class="imgqr ms-1" href="data:image/svg+xml;base64,${qr}"
                   target="_blank" download="${escapeHtml(name)}.svg"
                   title="${gettext('QR code')}"><i class="fa fa-qrcode"></i></a>`;
    },

    renderRiskBadge(risk) {
        if (!risk || !risk.alerts) { return ''; }
        return `<span class="badge bg-danger" title="${gettext('Incompatibilities')}">
                  ${risk.alerts} ${gettext('alerts')}</span>`;
    },

    /* -- cuadrícula --------------------------------------------------------- */

    mountGrid(furniture) {
        const element = document.getElementById('labview_grid_' + furniture.id);
        if (!element) { return; }
        const grid = new PositionsGrid(element, {
            data: furniture.grid,
            items: furniture.shelves,
            editable: false,
            renderItem: (shelf) => this.renderShelf(shelf),
            renderEmptyCell: () =>
                `<span class="text-muted small">${gettext('empty')}</span>`
        });
        element.addEventListener('pg:item-click', (event) => {
            LabviewState.select({
                labroom: furniture.labroom,
                furniture: furniture.id,
                shelf: event.detail.id
            }, 'map');
            this.highlight(LabviewState.selection);
        });
        this.grids[furniture.id] = grid;
    },

    renderShelf(shelf) {
        // El color del estante es el suyo; el del riesgo se superpone como
        // borde cuando el overlay esta activo, para que no se pisen.
        const risk = shelf.risk;
        const border = risk && risk.color
            ? `border-left:6px solid ${risk.color};` : '';
        const occupancy = shelf.occupancy_percent === null
            ? '<span class="text-muted">—</span>'
            : `${shelf.occupancy_percent}%`;
        // La descripcion la escribe el usuario y la tarjeta antigua la pintaba
        // con `|safe`; aqui llega como HTML del servidor por el mismo motivo.
        const description = shelf.description
            ? `<div class="labview-shelf-desc small">${shelf.description}</div>` : '';
        return `
<div class="labview-shelf" style="${border}">
  <div class="d-flex align-items-center gap-1">
    <span class="labview-shelf-dot" style="background:${shelf.color}"></span>
    <strong class="flex-grow-1">${shelf.id}: ${escapeHtml(shelf.name)}</strong>
    ${shelf.discard ? '<i class="fa fa-trash text-muted" title="' +
      gettext('Disposal') + '"></i>' : ''}
    ${this.renderQr(shelf.qr, shelf.name)}
    <a href="${shelf.deep_link}" target="_blank" title="${gettext('Direct link')}"
       ><i class="fa fa-tags"></i></a>
  </div>
  ${description}
  <small class="text-muted">${occupancy} · ${escapeHtml(shelf.measurement_unit)}
    · ${shelf.counts.shelfobjects} ${gettext('objects')}</small>
</div>`;
    },

    /* -- selección ---------------------------------------------------------- */

    highlight(selection) {
        if (!selection.labroom) { return; }
        const room = this.container.querySelector(
            `.labview-room[data-room="${selection.labroom}"] .labview-room-body`);
        if (room) { room.classList.remove('d-none'); }
        Object.values(this.grids).forEach((grid) => grid.highlight(null));
        if (!selection.shelf) { return; }
        const found = LabviewState.findShelf(selection.shelf);
        if (!found) { return; }
        const grid = this.grids[found.furniture.id];
        if (grid) { grid.highlight(selection.shelf); grid.scrollToItem(selection.shelf); }
        const node = this.container.querySelector(
            `.labview-furniture[data-furniture="${found.furniture.id}"]`);
        if (node) { node.scrollIntoView({block: 'nearest', behavior: 'smooth'}); }
    },

    collapseAll() {
        this.container.querySelectorAll('.labview-room-body').forEach(
            (body) => body.classList.add('d-none'));
        this.container.querySelectorAll('.labview-room-toggle').forEach((button) => {
            button.setAttribute('aria-expanded', 'false');
            button.querySelector('i').className = 'fa fa-chevron-right';
        });
    },

    // La búsqueda navega a la coincidencia más profunda, pero una consulta con
    // varias etiquetas puede casar en varios estantes: marcarlos todos es lo
    // que la vista antigua conseguía filtrando el árbol.
    highlightMatches(shelfIds) {
        this.container.querySelectorAll('.pg-item.labview-match').forEach(
            (node) => node.classList.remove('labview-match'));
        (shelfIds || []).forEach((id) => {
            const found = LabviewState.findShelf(id);
            if (!found) { return; }
            const room = this.container.querySelector(
                `.labview-room[data-room="${found.room.id}"] .labview-room-body`);
            if (room) { room.classList.remove('d-none'); }
            const node = this.container.querySelector(
                `[data-pg-item="${id}"]`);
            if (node) { node.classList.add('labview-match'); }
        });
    },

    bind() {
        this.container.querySelectorAll('.labview-room-toggle').forEach((button) => {
            button.addEventListener('click', () => {
                const card = button.closest('.labview-room');
                const body = card.querySelector('.labview-room-body');
                const open = body.classList.toggle('d-none') === false;
                button.setAttribute('aria-expanded', open);
                button.querySelector('i').className =
                    'fa fa-chevron-' + (open ? 'down' : 'right');
            });
        });
    }
};

function escapeHtml(value) {
    return String(value === null || value === undefined ? '' : value)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
