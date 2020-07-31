$(document).ready(function () {
    //Search sustance with autocomplete
    $('select[name="features"]').select2();
    $('select[name="laboratory"]').select2();
    $('select[name="h_code"]').select2();
    $('select[name="white_organ"]').select2();
    $('select[name="iarc"]').select2();
    $('select[name="imdg"]').select2();

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