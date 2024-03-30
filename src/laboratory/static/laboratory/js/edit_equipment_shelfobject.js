
gtformequipment=GTBaseFormModal("#editequipmentcollapse", {},  {reload_table: false, type: "PUT"});
gtformequipment.hide_modal = function(){
    $(gtformequipment.form).find("ul.form_errors").remove();
};
gtformequipment.show_modal = function(){};
gtformequipment.init();
