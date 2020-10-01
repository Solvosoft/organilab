$(document).ready(function () {
    function hide_show_precursor_type(){
         var checkBox=document.getElementById("id_is_precursor");
         if (checkBox.checked == true){
            $("#id_precursor_type").closest('.form-group').show()
         }else{
            $("#id_precursor_type").closest('.form-group').hide()
         }
    }

    $("input[name='is_precursor']").change(hide_show_precursor_type);
    hide_show_precursor_type();


});