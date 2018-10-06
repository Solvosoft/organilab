/*
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 26 sept. 2018
@author: Guillermo Castro Sánchez
@email: guillermoestebancs@gmail.com
*/

// Control label information validation
var errorsValidation = $('.wizard-card form');


$(document).ready(function () {
    //Search sustance with autocomplete
    $("#substance").autocomplete({
        source: "search_autocomplete_sustance",
        //Start predicting at character #1
        minLength: 1,
        //Show important substance information and save id
        select: function (event, ui) {
            $('#substance_id').val(ui.item.value); // save selected id to hidden input
            $('#substance').val(ui.item.label); // display the selected text
            return false;
        }
    })
    // View substance label information for a future implementation
    /*
    $("#substanceInformation").click(function () {
        if (!$("#substance").val()) {
            alert("Please enter substance information");
        } else {
            //Validate information
            //Show Modal Popup with tabs

        }
    });
    */
    // Valid substance entered
    $.validator.addMethod("validSubstance", function () {
      if($('#substance_id').val() == ''){
          return false;
      }else{
          return true;
     }
    }, "Por favor, escriba una sustancia válida.");
    // Code for the Validator
    errorsValidation.validate({
        rules: {
            substance: {
                required: true,
                validSubstance: true,
            },
            company_name: {
                required: true,
            },
            company_address: {
                required: true,
            },
            company_phone: {
                required: true,
            },
            recipients: {
                required: true,
            },
            label_selected: {
                required: true
            }

        }
    });
    // Save label information in JSON
    $("#Next").click(function () {
        var label_JSON = {};
        if (hasClass(label_information, 'active')) {
            errorsValidation.validate();
            if(errorsValidation.valid()==false){
                swal({
                    type: 'error',
                    title: 'Información incompleta',
                    text: 'Por favor, revise los datos solicitados.'
                })
            }else{
                //Label properties
                // #1: Substance
                var substance = $('#substance').val();
                var substance_name = substance.split(' : ');
                substance_commercial_name = substance_name[0];
                label_JSON.substance_commercial_name = substance_commercial_name;
                var substance_id = $('#substance_id').val();
                label_JSON.substance_id = substance_id;
                // #2: Supplier Identification
                var company_name = $('#company_name').val();
                label_JSON.company_name = company_name;
                var company_address = $('#company_address').val();
                label_JSON.company_address = company_address;
                var company_phone = $('#company_phone').val();
                label_JSON.company_phone = company_phone;
                // #3: Product Identification
                var commercial_information = $('#commercial_information').val();
                label_JSON.commercial_information = commercial_information;
                // #4: Recipient Size
                var recipient_select_box = document.getElementById("recipients");
                var recipient_name = recipient_select_box.options[recipient_select_box.selectedIndex].getAttribute('data-name');
                label_JSON.recipient_name = recipient_name;
                var height = recipient_select_box.options[recipient_select_box.selectedIndex].getAttribute('data-height');
                label_JSON.height = height;
                var height_unit = recipient_select_box.options[recipient_select_box.selectedIndex].getAttribute('data-height_unit');
                label_JSON.height_unit = height_unit;
                var width = recipient_select_box.options[recipient_select_box.selectedIndex].getAttribute('data-width');
                label_JSON.width = width;
                var width_unit = recipient_select_box.options[recipient_select_box.selectedIndex].getAttribute('data-width_unit');
                label_JSON.width_unit = width_unit;

                var label_JSON_String = JSON.stringify(label_JSON);
                localStorage.setItem('label_storage', label_JSON_String);

                /*var obj = JSON.parse(localStorage.getItem('label_storage'));
                alert(JSON.stringify(obj));*/

                /* Set blank templates images according to recipient size */
                set_template_image();
            }
        }
    });
});

// Select Box Place Holder 
function changePlaceHolder(sel) {
    sel.style.cssText = 'color: #000 !important';
}
// Element contains a class 
function hasClass(element, cls) {
    return (' ' + element.className + ' ').indexOf(' ' + cls + ' ') > -1;
}
//Capitalize each Word
function titleCase(str) {
    var splitStr = str.toString().toLowerCase().split(' ');
    for (var i = 0; i < splitStr.length; i++) {
        // You do not need to check if i is larger than splitStr length, as your for does that for you
        // Assign it back to the array
        splitStr[i] = splitStr[i].charAt(0).toString().toUpperCase() + splitStr[i].substring(1);
    }
    // Directly return the joined string
    return splitStr.join(' ');
}



