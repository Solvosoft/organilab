
(function($){
    $.fn.formulaname = function(){
        var $this = $(this);

        $this.on('change', function(){
                var name=$this.val();
                if (name != ''){
                        name = btoa($this.val())
                        $.ajax({
                        url: molecular_name_url+'?name='+name, // url where to submit the request
                        type : "GET", // type of action POST || GET
                        dataType : 'json', // data type
                        success : function(result) {
                            $(".moleculename").remove();
                            $this.after('<p class="text-success moleculename">'+result['name']+'</p>');
                        },
                        error: function(xhr, resp, text) {
                            if(xhr.status == 400 ){

                                $(".moleculename").remove();
                                $this.after('<p class="text-warning moleculename">'+xhr.responseJSON.name+'</p>');
                            }
                        }
                    });
            }
        });
    }
})(jQuery)

$(document).ready(function () {
    $('#id_type').change(update_form);
    update_form();
    $("#id_molecular_formula").formulaname()
});

function update_form() {
    var select_widget = $('#id_type');
    var selected_option = select_widget.find('option:selected').val();
    if(!selected_option) {
        selected_option = select_widget.val();
    }
    var form = $('#objectview_form');

    if (selected_option == '0') {
        show_reactive_options();
    } else {
        hide_reactive_options();
    }
}

var ids = [
    "id_molecular_formula",
    "id_cas_id_number",
    "id_security_sheet",
    "id_h_code",
    "id_is_precursor"
];

function show_reactive_options() {
    for (var i = 0; i < ids.length; i++) {
        $('#' + ids[i]).parents('.form-group').show();
    }
}

function hide_reactive_options() {
    for (var i = 0; i < ids.length; i++) {
        $('#' + ids[i]).parents('.form-group').hide();
        document.getElementById(ids[i]).required = false;
    }
}
