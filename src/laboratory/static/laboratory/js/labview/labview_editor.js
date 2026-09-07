/* Modo edición del mueble: persistencia por operación.
 *
 * Cada gesto —crear un estante en una celda, moverlo, quitarlo, añadir o
 * eliminar una fila o una columna— es **una llamada** que muta la cuadrícula en
 * el servidor y devuelve el estado nuevo completo, con el que PositionsGrid se
 * repinta. No hay botón "Guardar" porque no existe un estado intermedio que se
 * pueda perder al cerrar la pestaña, y los índices de fila y columna dejan de
 * ser un dato del DOM: después de crear, se opera siempre por `shelf_pk`.
 *
 * Cada control se ofrece según su capacidad: sin `add_shelf` la celda vacía no
 * ofrece crear, sin `change_shelf` no se puede mover, sin `delete_shelf` no se
 * puede quitar. Nunca se ofrece una acción que el servidor va a rechazar.
 */

const LabviewEditor = {
    active: null,

    init(container) {
        container.addEventListener('click', (event) => {
            const button = event.target.closest('.labview-edit');
            if (!button) { return; }
            this.toggle(parseInt(button.dataset.furniture, 10), button);
        });
    },

    toggle(furniturePk, button) {
        if (this.active === furniturePk) { return this.stop(button); }
        if (this.active !== null) {
            const previous = document.querySelector(
                `.labview-edit[data-furniture="${this.active}"]`);
            if (previous) { this.stop(previous); }
        }
        this.start(furniturePk, button);
    },

    start(furniturePk, button) {
        const grid = LabviewMap.grids[furniturePk];
        if (!grid) { return; }
        this.active = furniturePk;
        button.classList.add('active');
        button.innerHTML = '<i class="fa fa-check"></i> ' + gettext('Done');
        grid.cfg.handlers = this.handlers(furniturePk);
        grid.handlers = grid.cfg.handlers;
        grid.setEditable(true);
        grid.el.addEventListener('pg:error', this.onError);
    },

    stop(button) {
        const grid = LabviewMap.grids[this.active];
        if (grid) {
            grid.el.removeEventListener('pg:error', this.onError);
            grid.handlers = {};
            grid.cfg.handlers = {};
            grid.setEditable(false);
        }
        button.classList.remove('active');
        button.innerHTML = '<i class="fa fa-pencil"></i> ' + gettext('Edit furniture');
        this.active = null;
        // Al salir se recarga el árbol: los conteos por sala y el riesgo
        // pueden haber cambiado con lo que se acaba de editar.
        LabviewMap.load();
    },

    onError(event) {
        if (event.detail.code === 'busy') { return; }
        const error = event.detail.error;
        Swal.fire({
            icon: 'error',
            title: gettext('The operation was refused'),
            text: (error && error.message) || gettext('An error has occurred')
        });
    },

    /* -- llamadas ----------------------------------------------------------- */

    post(url, body) {
        return fetch(url, {
            method: 'POST',
            headers: {'X-CSRFToken': getCookie('csrftoken'),
                      'Content-Type': 'application/json'},
            body: JSON.stringify(body || {})
        }).then((response) => this.unwrap(response));
    },

    unwrap(response) {
        if (response.ok) { return response.json(); }
        return response.json().then((payload) => Promise.reject(
            new Error(payload.detail || gettext('The operation was refused'))));
    },

    furnitureUrl(furniturePk, suffix) {
        return document.labview_urls.furniture_detail
            .replace('/0/', '/' + furniturePk + '/') + suffix;
    },

    // La respuesta del servidor trae `{grid, shelves}`; el widget se repinta
    // con eso y nunca con un estado calculado en el cliente.
    asState(payload) {
        return {data: payload.grid, items: payload.shelves};
    },

    // Crear, mover y quitar cambian la cuadrícula, así que basta con volver a
    // pedir el mueble: recargar el árbol entero rehace el mapa y destruiría la
    // instancia del widget que está en modo edición. Los conteos y el riesgo se
    // refrescan al salir del modo.
    reload(furniturePk) {
        return fetch(document.labview_urls.furniture_detail
                         .replace('/0/', '/' + furniturePk + '/'),
                     {headers: {'X-CSRFToken': getCookie('csrftoken')}})
            .then((response) => this.unwrap(response))
            .then((payload) => this.asState(payload));
    },

    handlers(furniturePk) {
        const handlers = {};
        const can = (capability) => LabviewState.can(capability);

        if (can('change_furniture')) {
            handlers.addRow = () =>
                this.post(this.furnitureUrl(furniturePk, 'grid/row/'))
                    .then((payload) => this.asState(payload));
            handlers.removeRow = (index) =>
                this.post(this.furnitureUrl(furniturePk, 'grid/row/remove/'),
                          {index: index}).then((payload) => this.asState(payload));
            handlers.addCol = () =>
                this.post(this.furnitureUrl(furniturePk, 'grid/col/'))
                    .then((payload) => this.asState(payload));
            handlers.removeCol = (index) =>
                this.post(this.furnitureUrl(furniturePk, 'grid/col/remove/'),
                          {index: index}).then((payload) => this.asState(payload));
        }
        if (can('add_shelf')) {
            handlers.createItem = (row, col) => this.createShelf(furniturePk, row, col);
        }
        if (can('change_shelf')) {
            handlers.moveItem = (id, row, col) =>
                fetch(document.labview_urls.shelf_detail
                          .replace('/0/', '/' + id + '/') + 'move/', {
                    method: 'PUT',
                    headers: {'X-CSRFToken': getCookie('csrftoken'),
                              'Content-Type': 'application/json'},
                    body: JSON.stringify({row: row, col: col})
                }).then((response) => this.unwrap(response))
                  .then(() => this.reload(furniturePk));
        }
        if (can('delete_shelf')) {
            handlers.removeItem = (id) => this.removeShelf(furniturePk, id);
        }
        return handlers;
    },

    createShelf(furniturePk, row, col) {
        const types = document.container_types || [];
        // Shelf.type no acepta nulos: sin catalogo `container_type` el POST
        // solo devolveria un 400 ilegible, asi que se corta antes de pedir
        // datos que no se van a poder guardar.
        if (!types.length) {
            return Swal.fire({
                icon: 'error',
                title: gettext('New shelf'),
                text: gettext('There are no container types configured.')
            }).then(() => null);
        }
        const typeOptions = types.map(
            (t) => `<option value="${t.id}">${escapeHtml(t.description)}</option>`
        ).join('');

        return Swal.fire({
            title: gettext('New shelf'),
            html: `
                <label for="swal-shelf-name" class="swal2-input-label">${gettext('Name')}</label>
                <input type="text" id="swal-shelf-name" class="swal2-input" placeholder="${gettext('Name')}">
                <label for="swal-shelf-type" class="swal2-input-label">${gettext('Type')}</label>
                <select id="swal-shelf-type" class="swal2-select">
                    ${typeOptions}
                </select>
            `,
            showCancelButton: true,
            focusConfirm: false,
            preConfirm: () => {
                const name = document.getElementById('swal-shelf-name').value.trim();
                const type = document.getElementById('swal-shelf-type').value;

                if (!name) {
                    Swal.showValidationMessage(gettext('The name is required'));
                    return false;
                }
                if (!type) {
                    Swal.showValidationMessage(gettext('The type is required'));
                    return false;
                }
                return { name: name, type: parseInt(type, 10) };
            }
        }).then((result) => {
            if (!result.isConfirmed) { return null; }
            return fetch(document.labview_urls.shelf +
                         '?furniture=' + furniturePk, {
                method: 'POST',
                headers: {'X-CSRFToken': getCookie('csrftoken'),
                          'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: result.value.name,
                    type: result.value.type,
                    row: row, col: col,
                    quantity: 0, infinity_quantity: true
                })
            }).then((response) => this.unwrap(response))
              .then(() => this.reload(furniturePk));
        });
    },

    removeShelf(furniturePk, id) {
        return Swal.fire({
            icon: 'warning',
            title: gettext('Are you sure?'),
            text: gettext('The shelf will be removed from the furniture.'),
            showCancelButton: true
        }).then((result) => {
            if (!result.isConfirmed) { return null; }
            return fetch(document.labview_urls.shelf_detail
                             .replace('/0/', '/' + id + '/'), {
                method: 'DELETE',
                headers: {'X-CSRFToken': getCookie('csrftoken')}
            }).then((response) => {
                if (response.status === 204) { return null; }
                return this.unwrap(response);
            }).then(() => this.reload(furniturePk));
        });
    }
};
