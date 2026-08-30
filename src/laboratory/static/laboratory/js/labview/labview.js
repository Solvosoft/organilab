/* Arranque del labview: estado, mapa, buscador, tabla y editor.
 *
 * El orden importa poco salvo en un punto: el estado se inicializa antes de
 * pedir el arbol, porque el deep-link decide que sala hay que desplegar y hasta
 * que estante hay que desplazarse en cuanto llegan los datos.
 */

$(document).ready(function () {
    LabviewState.init(document.search_by_url);

    LabviewSearch.init(document.querySelector('input[name=tags-search]'));
    LabviewTable.init();
    LabviewEditor.init(document.getElementById('labview_map'));

    LabviewMap.init(document.getElementById('labview_map')).then(function () {
        // El breadcrumb del tema estaba vacio; aqui se llena y a partir de
        // ahora lo mueve la navegacion, no una recarga.
        LabviewBreadcrumb.init();
        LabviewBreadcrumb.update(LabviewState.selection);
        LabviewState.subscribe(function (selection) {
            LabviewBreadcrumb.update(selection);
        });
        // La seleccion que venia en la URL tiene que llegar a la tabla igual
        // que si el usuario hubiera pulsado el estante.
        if (LabviewState.selection.shelf) {
            LabviewTable.onSelection(LabviewState.selection);
        }
    });

    var collapse = document.getElementById('labview_collapse_all');
    if (collapse) {
        collapse.addEventListener('click', function () { LabviewMap.collapseAll(); });
    }

    var risk = document.getElementById('labview_risk_toggle');
    if (risk) {
        risk.addEventListener('change', function () {
            // El riesgo es opcional por parametro: la navegacion normal no lo
            // paga, y activarlo es una decision explicita del usuario.
            LabviewMap.load(this.checked);
        });
    }

    $("#hide_alert").on('click', function () {
        $("#alert_msg").html("");
        $("div.alert").removeClass("show");
    });
});

const LabviewBreadcrumb = {
    nav: null,

    init() {
        var element = document.getElementById('gt-breadcrumb');
        if (!element || typeof BreadcrumbNav === 'undefined') { return; }
        this.nav = new BreadcrumbNav(element, {
            levels: [],
            autoTruncate: false,
            onNavigate: (level) => {
                if (level.kind === 'laboratory') {
                    LabviewState.select({labroom: null}, 'breadcrumb');
                } else if (level.kind === 'labroom') {
                    LabviewState.select({labroom: level.pk}, 'breadcrumb');
                } else if (level.kind === 'furniture') {
                    LabviewState.select(
                        {labroom: level.labroom, furniture: level.pk}, 'breadcrumb');
                }
                LabviewMap.highlight(LabviewState.selection);
            }
        });
    },

    update(selection) {
        if (!this.nav || !LabviewState.tree) { return; }
        var levels = [{
            kind: 'laboratory', label: LabviewState.tree.laboratory.name
        }];
        var room = (LabviewState.tree.rooms || []).find(
            (candidate) => candidate.id === selection.labroom);
        if (room) {
            levels.push({kind: 'labroom', pk: room.id, label: room.name});
        }
        if (selection.furniture) {
            var furniture = LabviewState.findFurniture(selection.furniture);
            if (furniture) {
                levels.push({kind: 'furniture', pk: furniture.id,
                             labroom: furniture.labroom, label: furniture.name});
            }
        }
        if (selection.shelf) {
            var found = LabviewState.findShelf(selection.shelf);
            if (found) {
                levels.push({kind: 'shelf', pk: found.shelf.id,
                             label: found.shelf.name});
            }
        }
        this.nav.set(levels);
    }
};
