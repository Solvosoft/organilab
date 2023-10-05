var is_container = document.querySelector('#id_is_container');
function reset_is_container_elements(id_capacity,id_unit){
    let object_type = document.querySelector('#id_type');
    if(object_type.value=='1'){
        if(is_container.checked){
            $(id_capacity).parent().parent().show()
            $(id_capacity).attr("required", true);
            $(id_unit).parent().parent().show()
            $(id_unit).attr("required", true);
        }else{
            $(id_capacity).parent().parent().hide()
            $(id_unit).parent().parent().hide()
            $(id_capacity).attr("required", false);
            $(id_unit).attr("required", false);
        }
    }
}
reset_is_container_elements("#id_capacity","#id_capacity_measurement_unit");
if(is_container){
is_container.onchange = function(){
	reset_is_container_elements("#id_capacity","#id_capacity_measurement_unit");
}
}
