/*
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 03 oct. 2018
@author: Guillermo Castro Sánchez
@email: guillermoestebancs@gmail.com
*/


// Control label information validation
var errorsValidation = $('.wizard-card form');
// Control selected card template
var selectedCardTemplate = false;


$(document).ready(function () {
    // Blank Templates
    // Blank Template: Vertical
    // Add green border to selected card, change button text and color
    $("#button_blank_template_vertical").on("click", function ($e) {
        $e.preventDefault(); //Stop Web Page scrolling to the top
        if (hasClass(template_card_vertical, 'template_card')) {
            selectedCardTemplate = true;
            selectedCard("template_card_vertical");
            noselectedCard("template_card_horizontal");
            noselectedCard("pre_designed_template_card_horizontal");
            noselectedCard("pre_designed_template_card_vertical");
            //Change button text and color
            selectedButon("button_blank_template_vertical");
            selectButon("button_blank_template_horizontal");
            selectButon("button_pre_designed_template_vertical");
            selectButon("button_pre_designed_template_horizontal");
        } else {
            selectedCardTemplate = false;
            noselectedCard("template_card_vertical");
            //Change button text and color
            selectButon("button_blank_template_vertical");
        }
    });
    // Blank Template: Horizontal
    // Add green border to selected card, change button text and color
    $("#button_blank_template_horizontal").on("click", function ($e) {
        $e.preventDefault(); //Stop Web Page scrolling to the top
        if (hasClass(template_card_horizontal, 'template_card')) {
            selectedCardTemplate = true;
            selectedCard("template_card_horizontal");
            noselectedCard("template_card_vertical");
            noselectedCard("pre_designed_template_card_horizontal");
            noselectedCard("pre_designed_template_card_vertical");
            //Change button text and color
            selectedButon("button_blank_template_horizontal");
            selectButon("button_blank_template_vertical");
            selectButon("button_pre_designed_template_vertical");
            selectButon("button_pre_designed_template_horizontal");
        } else {
            selectedCardTemplate = false;
            noselectedCard("template_card_horizontal");
            //Change button text and color
            selectButon("button_blank_template_horizontal");
        }
    });
    // Pre Designed Template: Vertical
    // Add green border to selected card, change button text and color
    $("#button_pre_designed_template_vertical").on("click", function ($e) {
        $e.preventDefault(); //Stop Web Page scrolling to the top
        if (hasClass(pre_designed_template_card_vertical, 'template_card')) {
            selectedCardTemplate = true;
            selectedCard("pre_designed_template_card_vertical");
            noselectedCard("pre_designed_template_card_horizontal");
            noselectedCard("template_card_vertical");
            noselectedCard("template_card_horizontal");
            //Change button text and color
            selectedButon("button_pre_designed_template_vertical");
            selectButon("button_pre_designed_template_horizontal");
            selectButon("button_blank_template_horizontal");
            selectButon("button_blank_template_vertical");
        } else {
            selectedCardTemplate = false;
            noselectedCard("pre_designed_template_card_vertical");
            //Change button text and color
            selectButon("button_pre_designed_template_vertical");
        }
    });
    // Pre Designed Template: Horizontal
    // Add green border to selected card, change button text and color
    $("#button_pre_designed_template_horizontal").on("click", function ($e) {
        $e.preventDefault(); //Stop Web Page scrolling to the top
        if (hasClass(pre_designed_template_card_horizontal, 'template_card')) {
            selectedCardTemplate = true;
            selectedCard("pre_designed_template_card_horizontal");
            noselectedCard("pre_designed_template_card_vertical");
            noselectedCard("template_card_vertical");
            noselectedCard("template_card_horizontal");
            //Change button text and color
            selectedButon("button_pre_designed_template_horizontal");
            selectButon("button_pre_designed_template_vertical");
            selectButon("button_blank_template_vertical");
            selectButon("button_blank_template_horizontal");
        } else {
            selectedCardTemplate = false;
            noselectedCard("pre_designed_template_card_horizontal");
            //Change button text and color
            selectButon("button_pre_designed_template_horizontal");
        }
    });
    // Code for the Validator
    errorsValidation.validate({
        rules: {
            label_selected: {
                required: true
            }
        }
    });
    $("#Next").click(function () {
        if (hasClass(label_template, 'active')) {
            if (!selectedCardTemplate) {
                swal({
                    type: 'error',
                    title: 'Plantilla requerida',
                    text: 'Por favor, seleccione una plantilla.'
                })
            }
        }
    });

});



/* Set blank templates images according to recipient size */
function set_template_image() {

    // Show loading message
    waitingDialog.show('Loading...');

    var label_information = JSON.parse(localStorage.getItem('label_storage'));
    //Blank Template: Vertical
    $("#template_card_image_vertical").attr("src", "https://dummyimage.com/300x400/ededed/0000007c/&text=" + label_information.height + label_information.height_unit + "+x+" + label_information.width + label_information.width_unit);
    //Blank Template: Horizontal
    $("#template_card_image_horizontal").attr("src", "https://dummyimage.com/300x250/ededed/0000007c/&text=" + label_information.height + label_information.height_unit + "+x+" + label_information.width + label_information.width_unit);

    // Hide loading message after few miliseconds
    setTimeout(function () { waitingDialog.hide() }, 1000);
}

/* Add green color to selected card */
function selectedCard(card_id) {
    card = document.getElementById(card_id);
    card.classList.remove("template_card");
    card.classList.add("template_card_selected");
}

/* Add light blue color to card */
function noselectedCard(card_id) {
    card = document.getElementById(card_id);
    card.classList.remove("template_card_selected");
    card.classList.add("template_card");
}

/* Change button value */
function changeButtonValue(button_id, button_value) {
    button = document.getElementById(button_id);
    button.innerText = button_value;
}

/* Selected button */
function selectedButon(button_id) {
    changeButtonValue(button_id, "Selected");
    document.getElementById(button_id).classList.add("button_border_selected");
}

/* Select button */
function selectButon(button_id) {
    changeButtonValue(button_id, "Select");
    document.getElementById(button_id).classList.remove("button_border_selected");
}