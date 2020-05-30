$(document).ready(function () {
    //Search sustance with autocomplete
    $('select[name="features"]').select2();
    $('select[name="laboratory"]').select2();
    $('select[name="h_code"]').select2();
    $('select[name="white_organ"]').select2();

    $('#id_features').attr("aria-describedby", "featuresHelp");
    $('#id_laboratory').attr("aria-describedby", "laboratoryHelp")
    $('#id_white_organ').attr("aria-describedby", "white_organHelp");
    $('#id_h_code').attr("aria-describedby", "h_codeHelp")
    $("#id_features").autocomplete({
        source: "search_autocomplete_sustance_features",
        //Start predicting at character #1
        minLength: 1,
        //Show important substance information and save id
        select: function (event, ui) {
            $('#features_id').val(ui.item.value); // save selected id to hidden input
            $('#features_id').data("name", ui.item.label); // save the selected text to hidden input
            $('#id_features').val(ui.item.label); // display the selected text
            return false;
        }
    });
    $("#id_laboratory").autocomplete({
        source: "search_autocomplete_sustance_laboratory",
        //Start predicting at character #1
        minLength: 1,
        //Show important substance information and save id
        select: function (event, ui) {
            $('#laboratory_id').val(ui.item.value); // save selected id to hidden input
            $('#laboratory_id').data("name", ui.item.label); // save the selected text to hidden input
            $('#id_laboratory').val(ui.item.label); // display the selected text
            return false;
        }
    });
    $("#id_white_organ").autocomplete({
        source: "search_autocomplete_sustance_white_organ",
        //Start predicting at character #1
        minLength: 1,
        //Show important substance information and save id
        select: function (event, ui) {
            $('#white_organ_id').val(ui.item.value); // save selected id to hidden input
            $('#white_organ_id').data("name", ui.item.label); // save the selected text to hidden input
            $('#id_white_organ').val(ui.item.label); // display the selected text
            return false;
        }
    });
    $("#id_h_code").autocomplete({
        source: "search_autocomplete_sustance_danger_indication",
        //Start predicting at character #1
        minLength: 1,
        //Show important substance information and save id
        select: function (event, ui) {
            $('#h_code_id').val(ui.item.value); // save selected id to hidden input
            $('#h_code_id').data("name", ui.item.label); // save the selected text to hidden input
            $('#id_h_code').val(ui.item.label); // display the selected text
            return false;
        }
    });
});