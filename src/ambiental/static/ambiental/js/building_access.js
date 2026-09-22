ambiental_crud("ambiental_buildingaccess", "#table-buildingaccess", [
    {data: "id", name: "id", title: "ID", type: "string", visible: false},
    {
        data: "building", name: "building", title: gettext("Building"),
        type: "select2", url: selects2_url.building_url,
        render: gt_print_list_object("text"), visible: true
    },
    {
        data: "user", name: "user", title: gettext("User"),
        type: "select2", url: selects2_url.user_url,
        render: gt_print_list_object("text"), visible: true
    },
    {
        data: "rol", name: "rol", title: gettext("Roles"),
        type: "readonly", render: gt_print_list_object("text"), visible: true, sortable: false
    },
], {
    delete_display: data => data["user"]["text"] + " - " + data["building"]["text"],
});
