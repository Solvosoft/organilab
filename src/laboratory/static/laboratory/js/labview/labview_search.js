/* Buscar por etiquetas y **navegar** hasta lo encontrado.
 *
 * El endpoint no cambia: `api-search-labview-get` ya devuelve la cadena
 * jerárquica completa (sala, mueble, estante, objeto) de cada coincidencia.
 * Lo que cambia es qué se hace con ella. La vista antigua escondía nodos de un
 * árbol ya renderizado; aquí se despliega la sala, se desplaza hasta el mueble,
 * se resalta el estante y se filtra la tabla. Buscar deja de ser un filtro
 * visual y pasa a ser navegación.
 */

const LabviewSearch = {
    tagify: null,

    init(input) {
        if (!input) { return; }
        this.tagify = new Tagify(input, {
            delimiters: null,
            enforceWhitelist: true,
            whitelist: document.suggestions_tag || [],
            placeholder: gettext('Search a room, furniture, shelf or object'),
            templates: {
                tag: (tagData) => `
<tag title='${tagData.value}' contenteditable='false' spellcheck='false'
     tabIndex="-1" class='tagify__tag' style='--tag-bg: ${tagData.color}'>
  <x title='' class='tagify__tag__removeBtn'></x>
  <div><span class='tagify__tag-text'>${tagData.value}</span></div>
</tag>`,
                dropdownItem: (tagData) => `
<div class='tagify__dropdown__item'>
  <span class='fs-6' style='background-color: ${tagData.color}; color: black;'>
    ${tagData.value}</span>
</div>`
            }
        });

        this.tagify.on('add', () => this.search());
        this.tagify.on('remove', () => {
            if (this.tagify.value.length) { this.search(); }
        });

        this.tagify.on('remove', () => {
            if (!this.tagify.value.length) { this.reset(); }
        });

        const clear = document.getElementById('labview_clear_tags');
        if (clear) {
            clear.addEventListener('click', () => {
                this.tagify.removeAllTags();
                this.reset();
            });
        }
    },

    reset() {
        LabviewMap.highlightMatches([]);
        if (LabviewTable.table) { LabviewTable.table.search('').draw(); }
        const alert = document.getElementById('alert_msg');
        if (alert) { alert.innerHTML = ''; }
        document.querySelectorAll('div.alert').forEach(
            (node) => node.classList.remove('show'));
    },

    query() {
        return this.tagify.value.map((tag) => {
            // El endpoint espera `labroom`, no `laboratoryroom`.
            const key = tag.objtype === 'laboratoryroom' ? 'labroom' : tag.objtype;
            return key + '=' + tag.pk;
        }).join('&');
    },

    search() {
        const query = this.query();
        if (!query) { return; }
        fetch(document.labview_urls.search_labview + '?' + query,
              {headers: {'X-CSRFToken': getCookie('csrftoken')}})
            .then((response) => response.json())
            .then((payload) => this.navigate(payload.search_list));
    },

    // La respuesta trae varias listas; se toma la coincidencia más profunda,
    // que es la que el usuario quiere ver, y el resto de la cadena viene con
    // ella.
    navigate(searchList) {
        if (!searchList) { return; }
        const first = (value) => (Array.isArray(value) && value.length ? value[0] : null);
        const selection = {};

        if (searchList.labroom) { selection.labroom = first(searchList.labroom); }
        if (searchList.furniture && searchList.furniture.furniture) {
            selection.furniture = first(searchList.furniture.furniture);
            selection.labroom = first(searchList.furniture.labroom) || selection.labroom;
        }
        if (searchList.shelf && searchList.shelf.shelf) {
            selection.shelf = first(searchList.shelf.shelf);
            selection.furniture = first(searchList.shelf.furniture) || selection.furniture;
            selection.labroom = first(searchList.shelf.labroom) || selection.labroom;
        }
        if (searchList.shelfobject && searchList.shelfobject.shelfobject) {
            selection.shelfobject = first(searchList.shelfobject.shelfobject);
            selection.shelf = first(searchList.shelfobject.shelf) || selection.shelf;
            selection.furniture =
                first(searchList.shelfobject.furniture) || selection.furniture;
            selection.labroom = first(searchList.shelfobject.labroom) || selection.labroom;
        }
        if (searchList.object && searchList.object.shelf) {
            const shelf = searchList.object.shelf;
            selection.shelf = first(shelf.shelf) || selection.shelf;
            selection.furniture = first(shelf.furniture) || selection.furniture;
            selection.labroom = first(shelf.labroom) || selection.labroom;
        }

        if (!Object.keys(selection).length) { return; }
        LabviewState.select(selection, 'search');
        LabviewMap.highlight(LabviewState.selection);
        this.filterTable(searchList, selection);
        this.reportMatches(searchList);
        this.markMatches(searchList);
    },

    // Todos los estantes que casan, no solo aquel al que se navega.
    markMatches(searchList) {
        const shelves = [];
        const collect = (block) => {
            if (block && Array.isArray(block.shelf)) { shelves.push(...block.shelf); }
        };
        collect(searchList.shelf);
        collect(searchList.shelfobject);
        collect(searchList.object && searchList.object.shelf);
        LabviewMap.highlightMatches(shelves);
    },

    // Buscar un objeto concreto tiene que dejar la tabla mostrandolo, no solo
    // llevar al estante que lo contiene. Es lo que hacia la vista antigua
    // escribiendo en el buscador de la tabla, y el endpoint entiende el
    // convenio `pk=<n>`.
    filterTable(searchList, selection) {
        if (!LabviewTable.table) { return; }
        let term = null;
        if (searchList.shelfobject && searchList.shelfobject.shelfobject &&
            searchList.shelfobject.shelfobject.length) {
            term = 'pk=' + searchList.shelfobject.shelfobject.slice(-1)[0];
        } else if (searchList.object && searchList.object.object &&
                   searchList.object.object.length) {
            term = searchList.object.object[0];
        }
        if (term === null) { return; }
        LabviewTable.table.search(term).draw();
    },

    // Una busqueda por objeto puede coincidir en varios estantes y solo se
    // muestra el primero: decirlo es informacion que el usuario tenia.
    reportMatches(searchList) {
        const alert = document.getElementById('alert_msg');
        if (!alert) { return; }
        if (!searchList.object || !searchList.object.shelf ||
            !Array.isArray(searchList.object.shelf.shelf) ||
            searchList.object.shelf.shelf.length < 2) {
            return;
        }
        alert.innerHTML = '<b>' + interpolate(
            gettext('Showing the first result out of %s matched shelves'),
            [searchList.object.shelf.shelf.length]) + '</b>';
        document.querySelectorAll('div.alert').forEach(
            (node) => node.classList.add('show'));
    }
};
