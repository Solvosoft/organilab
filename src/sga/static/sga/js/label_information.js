/*
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 26 sept. 2018
@author: Guillermo Castro Sánchez
@email: guillermoestebancs@gmail.com
*/

// Control label information validation
var errorsValidation = $('#sgaform');

$(document).ready(function () {
    //Search sustance with autocomplete
    $("#substance").autocomplete({
        source: "search_autocomplete_sustance",
        //Start predicting at character #1
        minLength: 1,
        //Show important substance information and save id
        select: function (event, ui) {
            $('#substance_id').val(ui.item.value); // save selected id to hidden input
            $('#substance_id').data("name", ui.item.label); // save the selected text to hidden input
            $('#substance').val(ui.item.label); // display the selected text
            return false;
        }
    })

    // Valid substance entered
    $.validator.addMethod("validSubstance", function () {
        if ($('#substance_id').data("name") != $('#substance').val() || $('#substance_id').data("name") == 'No results') {
            return false;
        } else {
            return true;
        }
    }, "Por favor, ingrese una sustancia válida.");
    // Code for the Validator
    errorsValidation.validate({
        rules: {
            substance_name: {
                required: true,
                validSubstance: true,
                maxlength: 250
            },
            name: {
                required: true,
                maxlength: 150
            },
            company_name: {
                required: true,
                maxlength: 150
            },
            company_address: {
                required: true,
                maxlength: 100
            },
            company_phone: {
                required: true,
                maxlength: 15
            },
            commercial_information: {
                maxlength: 250
            },
        }
    });
});

function changePlaceHolder(sel) {
    sel.style.cssText = 'color: #000 !important';
}