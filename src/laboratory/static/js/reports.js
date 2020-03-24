$(document).ready(function () {
    //Search sustance with autocomplete
    $("#hcode").autocomplete({
        source: "filter_autocomplete_hcode",
        //Start predicting at character #1
        minLength: 1,
        //Show important substance information and save id
        select: function (event, ui) {
            console.log(ui.item.value);
            $('#hcode_id').val(ui.item.value); // save selected id to hidden input
            $('#hcode_id').data("name", ui.item.label); // save the selected text to hidden input
            $('#hcode').val(ui.item.label); // display the selected text
            return false;
        }
    });
});