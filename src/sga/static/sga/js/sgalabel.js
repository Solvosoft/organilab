function select_values(element, data){
    if(data){
        data.forEach( function(item, i){
            var newOption = new Option(item.name, item.id, true, true);
            $(element).append(newOption);
        });
    }
}

function update_complement_form(data, container, selectsimple=null){
    if(selectsimple){
        selectsimple.forEach(function(item, i){
            if(data.hasOwnProperty($(this)[0].name)){
                $("#id_"+item).val(data[item]).change();
            }
        });
    }

    $(container).find("select[data-widget='AutocompleteSelectMultiple']").each(function(item, i){
        if(data.hasOwnProperty($(this)[0].name)){
            select_values("#id_"+$(this)[0].name, data[$(this)[0].name]);
        }
    });

    $(container).find("textarea").each(function(i){
        if(data.hasOwnProperty($(this)[0].name)){
            $(this).val(data[$(this)[0].name]);
        }
    });

    $(container).find("input").each(function(i){
        if(data.hasOwnProperty($(this)[0].name)){
            $(this).val(data[$(this)[0].name]);
        }
    });
}



function clean_complementform(container, selectsimple=null){
    if(selectsimple){
        selectsimple.forEach(function(item, i){
            $("#id_"+item).val('').change();
        });
    }
    $(container+" select[data-widget='AutocompleteSelectMultiple'] option").remove();
    $(container+" textarea").val('');
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
              clean_complementform("#complementcontainer", ['warningword', 'pictograms']);
              if(result){
                update_complement_form(result, "#complementcontainer", ['warningword', 'pictograms']);
              }
            },
            error: function(xhr, resp, text) {
                console.log(xhr, resp, text);
            }
        });

    }
});

$("#id_company").on('change', function(){
    var id = $(this).val();
    if(id){
        var url = document.url_get_company;
        url = url.replace('0', id);

        $.ajax({
            url: url,
            type: 'GET',
            success: function(result) {
              clean_complementform("#companycontainer")
              if(result){
                update_complement_form(result, "#companycontainer");
              }
            },
            error: function(xhr, resp, text) {
                console.log(xhr, resp, text);
            }
        });

    }
});