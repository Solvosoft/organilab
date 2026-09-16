ambiental_crud("ambiental_measurementpoint", "#table-measurementpoint", [
    {data: "id", name: "id", title: "ID", type: "string", visible: false},
    {data: "code", name: "code", title: gettext("Code"), type: "string", visible: true},
    {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
    {
        data: "resource_type", name: "resource_type", title: gettext("Resource type"),
        type: "readonly", render: gt_print_list_object("text"), visible: true
    },
    {
        data: "point_type", name: "point_type", title: gettext("Point type"),
        type: "readonly", render: gt_print_list_object("text"), visible: true
    },
    {
        data: "building", name: "building", title: gettext("Building"),
        type: "select2", url: selects2_url.building_url,
        render: gt_print_list_object("text"), visible: true
    },
    {
        data: "laboratories", name: "laboratories", title: gettext("Laboratories"),
        type: "select2", url: selects2_url.laboratory_url,
        render: gt_print_list_object("text"), visible: true
    },
    {data: "meters_count", name: "meters_count", title: gettext("Number of meters"), type: "readonly", visible: true},
], {
    delete_display: data => data["code"] + " - " + data["name"],
});
