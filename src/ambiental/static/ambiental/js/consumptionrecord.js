/**
 * Registro de consumos por edificio.
 *
 * El edificio elegido en la cabecera filtra la tabla y el autocomplete de puntos.
 * Al elegir un punto, el recurso decide la unidad por defecto y qué campos aplican
 * (campos extra y datos de residuo); el servidor vuelve a validarlo igual.
 */
const EXTRA_FIELD_NAMES = ["vehicle_plate", "fuel_type", "paper_type", "waste_code", "manifest_number"];

function ambiental_toggle_resource_fields(prefix, info) {
    const extra = info ? info.extra_fields : [];
    EXTRA_FIELD_NAMES.forEach(function (name) {
        $("#id_" + prefix + name).closest(".gtformfield").toggle(extra.indexOf(name) >= 0);
    });
    ["treatment", "waste_manager"].forEach(function (name) {
        $("#id_" + prefix + name).closest(".gtformfield").toggle(Boolean(info && info.is_waste));
    });
}

function ambiental_bind_point(prefix) {
    const point = $("#id_" + prefix + "point");
    // Los autocompletes leen sus filtros de los data-s2filter-*: en la pantalla de
    // residuos solo se ofrecen puntos de residuos, y en la de consumos los demás.
    point.data("s2filterWaste", "#waste_flag");
    point.on("select2:select", function (event) {
        const info = event.params.data.resource_info;
        ambiental_toggle_resource_fields(prefix, info);
        if (info && info.unit) {
            $("#id_" + prefix + "unit").val(info.unit.id).trigger("change");
        }
    });
    ambiental_toggle_resource_fields(prefix, null);
}

ambiental_bind_point("create-");
ambiental_bind_point("update-");

const ocrud = ambiental_crud("ambiental_consumptionrecord", "#table-consumptionrecord", [
    {data: "id", name: "id", title: "ID", type: "string", visible: false},
    {
        data: "building", name: "point__building", title: gettext("Building"),
        type: "readonly", render: gt_print_list_object("text"), visible: true
    },
    {
        data: "point", name: "point", title: gettext("Measurement point"),
        type: "select2", url: selects2_url.point_url,
        render: gt_print_list_object("text"), visible: true
    },
    {
        data: "resource_type", name: "point__resource_type", title: gettext("Resource type"),
        type: "readonly", render: gt_print_list_object("text"), visible: true
    },
    {data: "period_start", name: "period_start", title: gettext("Period start"), type: "readonly", visible: true,
    "dateformat":  document.date_format},
    {data: "period_end", name: "period_end", title: gettext("Period end"), type: "date", visible: true,
						"dateformat":  document.date_format},
    {data: "quantity", name: "quantity", title: gettext("Quantity"), type: "readonly", visible: true},
    {
        data: "unit", name: "unit", title: gettext("Unit"),
        type: "readonly", render: gt_print_list_object("text"), visible: true
    },
    {data: "total_cost", name: "total_cost", title: gettext("Total cost"), type: "readonly", visible: true},
    {data: "document", name: "document", title: gettext("Document"), type: "readonly",
        render: (data) => data ? '<a href="' + data.url + '" target="_blank">' + gettext("Download") + '</a>' : "---",
        visible: true, sortable: false},
], {
    delete_display: data => data["point"]["text"] + " (" + data["period_start"] + " - " + data["period_end"] + ")",
    datatable_events: {
        filter: function (data) {
            const building = $("#id_building").val();
            if (building) {
                data["point__building"] = building;
            }
            data["is_waste"] = $("#waste_flag").val() === "1" ? "true" : "false";
            return data;
        }
    },
    events: {
        update_data: function (data) {
            ambiental_toggle_resource_fields("update-", data.resource_info);
            return data;
        }
    },
});

$("#id_building").on("change", function () {
    ocrud.datatable.ajax.reload();
});
