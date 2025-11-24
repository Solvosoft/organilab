var is_container_create = document.querySelector('#id_create-is_container');
var is_container_update = document.querySelector('#id_update-is_container');
function reset_is_container_elements(is_container, id_capacity, id_unit) {
    let object_type = document.querySelector('#id_create-type');
    let object_type_2 = document.querySelector('#id_update-type');

    if (object_type.value == '1' || object_type_2.value == '1') {
        if (is_container.checked) {
            $(id_capacity).parent().parent().show();
            $(id_capacity).attr("required", true);

            $(id_unit).parent().parent().show();
            $(id_unit).attr("required", true);
        } else {
            $(id_capacity).parent().parent().hide();
            $(id_unit).parent().parent().hide();

            $(id_capacity).attr("required", false);
            $(id_unit).attr("required", false);
        }
    }
}

reset_is_container_elements(
    is_container_create,
    "#id_create-capacity",
    "#id_create-capacity_measurement_unit"
);
reset_is_container_elements(
    is_container_update,
    "#id_update-capacity",
    "#id_update-capacity_measurement_unit"
);
if (is_container_create) {
    is_container_create.onchange = function () {
        reset_is_container_elements(
            is_container_create,
            "#id_create-capacity",
            "#id_create-capacity_measurement_unit"
        );
    };
}

if (is_container_update) {
    is_container_update.onchange = function () {
        reset_is_container_elements(
            is_container_update,
            "#id_update-capacity",
            "#id_update-capacity_measurement_unit"
        );
    };
}

