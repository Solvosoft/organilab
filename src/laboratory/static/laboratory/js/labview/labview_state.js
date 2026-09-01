/* Estado del labview: qué sala, mueble, estante y objeto está mirando el
 * usuario, y su reflejo en la barra de direcciones.
 *
 * El deep-link `?labroom=&furniture=&shelf=&shelfobject=` es un contrato, no
 * un detalle de implementación: lo llevan impresos los QR pegados en los
 * muebles y los enlaces del mapa de peligros. Por eso el estado se escribe en
 * la URL con esos nombres exactos, y al abrir la página se lee tanto del query
 * string (que el servidor ya resolvió) como del fragmento `#labroom=...`, que
 * es lo que generaron algunos QR antiguos y nunca llega al servidor.
 */

const LabviewState = {
    tree: null,
    permissions: {},
    riskEnabled: false,
    selection: {labroom: null, furniture: null, shelf: null, shelfobject: null},
    listeners: [],

    subscribe(listener) {
        this.listeners.push(listener);
    },

    notify(reason) {
        this.listeners.forEach((listener) => listener(this.selection, reason));
    },

    can(capability) {
        return this.permissions[capability] === true;
    },

    /* -- lectura inicial --------------------------------------------------- */

    // El servidor ya resolvió el query string hacia arriba (dado un estante
    // sabe su mueble y su sala), así que aquí solo se aplana.
    fromServer(searchByUrl) {
        const first = (value) => (Array.isArray(value) && value.length ? value[0] : null);
        const selection = {labroom: null, furniture: null, shelf: null, shelfobject: null};
        if (!searchByUrl) { return selection; }
        selection.labroom = first(searchByUrl.labroom);
        if (searchByUrl.furniture) {
            selection.furniture = first(searchByUrl.furniture.furniture);
        }
        if (searchByUrl.shelf) { selection.shelf = first(searchByUrl.shelf.shelf); }
        if (searchByUrl.shelfobject) {
            selection.shelfobject = first(searchByUrl.shelfobject.shelfobject);
        }
        return selection;
    },

    // Los QR que generó LabroomCreate llevan `#labroom=...`: el fragmento no
    // viaja al servidor, así que se rescata aquí.
    fromFragment() {
        const selection = {};
        const raw = window.location.hash.replace(/^#/, '');
        if (!raw) { return selection; }
        new URLSearchParams(raw).forEach((value, key) => {
            if (['labroom', 'furniture', 'shelf', 'shelfobject'].includes(key)) {
                const parsed = parseInt(value, 10);
                if (!isNaN(parsed)) { selection[key] = parsed; }
            }
        });
        return selection;
    },

    init(searchByUrl) {
        this.selection = Object.assign(
            this.fromServer(searchByUrl), this.fromFragment()
        );
    },

    /* -- escritura --------------------------------------------------------- */

    select(partial, reason) {
        // Seleccionar hacia arriba limpia lo de abajo: elegir otra sala no
        // puede dejar seleccionado un estante que ya no se ve.
        const next = Object.assign({}, this.selection, partial);
        if (partial.labroom !== undefined && partial.furniture === undefined) {
            next.furniture = null; next.shelf = null; next.shelfobject = null;
        }
        if (partial.furniture !== undefined && partial.shelf === undefined) {
            next.shelf = null; next.shelfobject = null;
        }
        if (partial.shelf !== undefined && partial.shelfobject === undefined) {
            next.shelfobject = null;
        }
        this.selection = next;
        this.pushUrl();
        this.notify(reason || 'select');
    },

    queryString() {
        const params = [];
        ['labroom', 'furniture', 'shelf', 'shelfobject'].forEach((key) => {
            if (this.selection[key]) { params.push(key + '=' + this.selection[key]); }
        });
        return params.length ? '?' + params.join('&') : window.location.pathname;
    },

    pushUrl() {
        const url = window.location.pathname + (
            this.queryString().startsWith('?') ? this.queryString() : ''
        );
        window.history.replaceState(this.selection, '', url);
    },

    /* -- consultas sobre el árbol ------------------------------------------ */

    setTree(tree) {
        this.tree = tree;
        this.permissions = tree.permissions || {};
        this.riskEnabled = !!tree.risk_enabled;
    },

    eachFurniture(callback) {
        (this.tree ? this.tree.rooms : []).forEach((room) => {
            room.furniture.forEach((furniture) => callback(furniture, room));
        });
    },

    findFurniture(id) {
        let found = null;
        this.eachFurniture((furniture) => {
            if (furniture.id === id) { found = furniture; }
        });
        return found;
    },

    findShelf(id) {
        let found = null;
        this.eachFurniture((furniture, room) => {
            const shelf = furniture.shelves[String(id)];
            if (shelf) { found = {shelf: shelf, furniture: furniture, room: room}; }
        });
        return found;
    }
};
