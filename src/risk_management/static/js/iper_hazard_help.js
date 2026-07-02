(function () {
    var CATEGORY_HELP = window.IPER_CATEGORY_HELP || {};
    var PROBABILITY_HELP = window.IPER_PROBABILITY_HELP || {};
    var CONSEQUENCE_HELP = window.IPER_CONSEQUENCE_HELP || {};

    function makePanel(id) {
        var panel = document.createElement("div");
        panel.id = id;
        panel.style.display = "none";
        panel.className = "mt-2 mb-1";
        panel.innerHTML =
            "<div class='px-3 py-2 rounded border small' style='background:#f8f9fa;'>"
            + "<div class='d-flex justify-content-between align-items-start'>"
            + "<div class='panel-body'></div>"
            + "<button type='button' class='btn-close ms-3 flex-shrink-0' aria-label='" + gettext("Close") + "'></button>"
            + "</div></div>";
        panel.querySelector(".btn-close").addEventListener("click", function () {
            panel.style.display = "none";
        });
        return panel;
    }

    function insertAfterField(fieldEl, panel) {
        var row = fieldEl.closest(".gtformfield") || fieldEl.closest("p") || fieldEl.parentElement;
        if (row && row.parentNode) {
            row.parentNode.insertBefore(panel, row.nextSibling);
        }
    }

    function addHelpBtn(forId, title, onClick) {
        var labelEl = document.querySelector("label[for='" + forId + "']");
        if (!labelEl) return;
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-link btn-sm p-0 ms-1 align-baseline";
        btn.title = title;
        btn.innerHTML = "<i class='fa fa-question-circle text-secondary'></i>";
        btn.addEventListener("click", onClick);
        labelEl.appendChild(btn);
    }

    // Bind change event compatible with Select2 (jQuery) and plain selects
    function onSelectChange(selectId, callback) {
        if (window.jQuery) {
            jQuery(document).on("change", "#" + selectId, callback);
            jQuery(document).on("select2:select select2:unselect", "#" + selectId, callback);
        } else {
            var el = document.getElementById(selectId);
            if (el) el.addEventListener("change", callback);
        }
    }

    function getSelectText(selectEl) {
        var opt = selectEl.options[selectEl.selectedIndex];
        return opt ? opt.text.trim() : "";
    }

    function init() {
        var categorySelect = document.getElementById("id_category");
        var descriptionField = document.getElementById("id_description");
        var probabilitySelect = document.getElementById("id_probability");
        var consequenceSelect = document.getElementById("id_consequence");

        if (!categorySelect) return;

        // --- Panel 1: clasificaciones ---
        var catPanel = makePanel("hazard-category-help-panel");
        var catHtml = "";
        Object.keys(CATEGORY_HELP).forEach(function (key) {
            var d = CATEGORY_HELP[key];
            catHtml += "<div class='mb-1'><strong>" + d.emoji + " " + key + "</strong>"
                + " — <span class='text-muted'>" + d.description + "</span></div>";
        });
        catPanel.querySelector(".panel-body").innerHTML = catHtml;
        insertAfterField(categorySelect, catPanel);
        addHelpBtn("id_category", gettext("Help about classifications"), function () {
            catPanel.style.display = catPanel.style.display === "none" ? "block" : "none";
        });

        // --- Panel 2: ejemplos bajo descripción ---
        if (descriptionField) {
            var exPanel = makePanel("hazard-examples-panel");
            insertAfterField(descriptionField, exPanel);
            addHelpBtn("id_description", gettext("View examples by category"), function () {
                if (exPanel.style.display === "none") {
                    refreshExamples();
                    exPanel.style.display = "block";
                } else {
                    exPanel.style.display = "none";
                }
            });

            function refreshExamples() {
                var label = getSelectText(categorySelect);
                var data = CATEGORY_HELP[label];
                var bodyEl = exPanel.querySelector(".panel-body");
                if (!data || !data.examples || !data.examples.length) {
                    bodyEl.innerHTML = "<span class='text-muted'>" + gettext("Select a classification to see examples.") + "</span>";
                    return;
                }
                var html = "<strong>" + data.emoji + " " + gettext("Examples") + " — " + label + "</strong>"
                    + "<ul class='mb-0 mt-1 ps-3'>";
                data.examples.forEach(function (ex) { html += "<li>" + ex + "</li>"; });
                html += "</ul>";
                bodyEl.innerHTML = html;
            }

            onSelectChange("id_category", function () {
                refreshExamples();
                if (exPanel.style.display !== "none") {
                    exPanel.style.display = "block";
                }
            });
        }

        // --- Panel 3: probabilidad ---
        if (probabilitySelect) {
            var probPanel = makePanel("hazard-probability-help-panel");
            var probHtml = "";
            Object.keys(PROBABILITY_HELP).forEach(function (key) {
                probHtml += "<div class='mb-1'><strong>" + key + ":</strong>"
                    + " <span class='text-muted'>" + PROBABILITY_HELP[key] + "</span></div>";
            });
            probPanel.querySelector(".panel-body").innerHTML = probHtml;
            insertAfterField(probabilitySelect, probPanel);
            addHelpBtn("id_probability", gettext("Help about probability"), function () {
                probPanel.style.display = probPanel.style.display === "none" ? "block" : "none";
            });
        }

        // --- Panel 4: consecuencia ---
        if (consequenceSelect) {
            var consPanel = makePanel("hazard-consequence-help-panel");
            var consHtml = "";
            Object.keys(CONSEQUENCE_HELP).forEach(function (key) {
                consHtml += "<div class='mb-1'><strong>" + key + ":</strong>"
                    + " <span class='text-muted'>" + CONSEQUENCE_HELP[key] + "</span></div>";
            });
            consPanel.querySelector(".panel-body").innerHTML = consHtml;
            insertAfterField(consequenceSelect, consPanel);
            addHelpBtn("id_consequence", gettext("Help about consequence"), function () {
                consPanel.style.display = consPanel.style.display === "none" ? "block" : "none";
            });
        }

        // --- Matriz: highlight celda activa ---
        if (probabilitySelect && consequenceSelect) {
            function highlightMatrix() {
                var probLabel = getSelectText(probabilitySelect);
                var consLabel = getSelectText(consequenceSelect);
                var cells = document.querySelectorAll("#risk-matrix-table td[data-prob]");
                cells.forEach(function (cell) {
                    var isActive = cell.dataset.prob === probLabel && cell.dataset.cons === consLabel;
                    cell.style.outline = isActive ? "3px solid #000" : "";
                    cell.style.opacity = (!probLabel && !consLabel) ? "1" : (isActive ? "1" : "0.35");
                    cell.style.fontWeight = isActive ? "bold" : "";
                });
            }

            onSelectChange("id_probability", highlightMatrix);
            onSelectChange("id_consequence", highlightMatrix);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();