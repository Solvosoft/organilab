function select_values(element, data){
    if(data){
        data.forEach( function(item, i){
            var newOption = new Option(item.name, item.id, true, true);
            $(element).append(newOption);
        });
    }
}

function update_complement_form(data){
    $("#id_warningword").val(data.warningword).change();
    $("#id_other_dangers").val(data.other_dangers);
    $("#id_pictograms").val(data.pictograms).change();
    select_values("#id_prudence_advice", data.prudence_advice);
    select_values("#id_danger_indication", data.danger_indication);
}



function clean_complementform(){
    $("#id_pictograms").val('').change();
    $("#id_prudence_advice option").remove();
    $("#id_danger_indication option").remove();
    $("#id_warningword").val('').change();
    $("#id_other_dangers").val('');
}

$("#id_substance").on('change', function(){
    var id = $(this).val();
    if(id){
        var url = document.url_get_sgacomponent;
        url = url.replace('0', id);

        $.ajax({
            url: url,
            type: 'GET',
            success: function(result) {
              clean_complementform();
              if(result){
                update_complement_form(result);
              }
            },
            error: function(xhr, resp, text) {
                console.log(xhr, resp, text);
            }
        });

    }
});