/*
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 03 oct. 2018
@author: Guillermo Castro Sánchez
@email: guillermoestebancs@gmail.com
*/

// Control label information validation
var errorsValidation = $('.wizard-card form');
/* Control selected card template   
     -1 : No template
      0 : Blank Vertical template
      1 : Blank Horizontal template
      2 : Pre Designed Vertical template
      3 : Pre Designed Horizontal template
*/
var selectedCardTemplate = -1;
// Canvas images for the modals
var canvasImages = [];
/* Canvas in JSON
      0 : Pre Designed Vertical template
      1 : Pre Designed Horizontal template
*/
var canvasJSON = [];

// Testing Canvas
// var jsonPrueba;

// Default to true for browsers, false for node, it enables objectCaching at object level.
fabric.Object.prototype.objectCaching = false;
// Enabled to avoid blurry effects for big scaling
fabric.Object.prototype.noScaleCache = true;
// Improve Canvas perfomance
fabric.Object.prototype.statefullCache = false;
fabric.Object.prototype.needsItsOwnCache = false;

$(document).ready(function () {
    // Blank Templates
    // Blank Template: Vertical
    // Add dark blue border to selected card, change button text and color
    $("#button_blank_template_vertical").on("click", function ($e) {
        $e.preventDefault(); //Stop Web Page scrolling to the top
        if (hasClass(template_card_vertical, 'template_card')) {
            selectedCardTemplate = 0;
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
            selectedCardTemplate = -1;
            noselectedCard("template_card_vertical");
            //Change button text and color
            selectButon("button_blank_template_vertical");
        }
    });
    // Blank Template: Horizontal
    // Add dark blue border to selected card, change button text and color
    $("#button_blank_template_horizontal").on("click", function ($e) {
        $e.preventDefault(); //Stop Web Page scrolling to the top
        if (hasClass(template_card_horizontal, 'template_card')) {
            selectedCardTemplate = 1;
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
            selectedCardTemplate = -1;
            noselectedCard("template_card_horizontal");
            //Change button text and color
            selectButon("button_blank_template_horizontal");
        }
    });
    // Pre Designed Template: Vertical
    // Add dark blue border to selected card, change button text and color
    $("#button_pre_designed_template_vertical").on("click", function ($e) {
        $e.preventDefault(); //Stop Web Page scrolling to the top
        if (hasClass(pre_designed_template_card_vertical, 'template_card')) {
            selectedCardTemplate = 2;
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
            selectedCardTemplate = -1;
            noselectedCard("pre_designed_template_card_vertical");
            //Change button text and color
            selectButon("button_pre_designed_template_vertical");
        }
    });
    // Pre Designed Template: Horizontal
    // Add dark blue border to selected card, change button text and color
    $("#button_pre_designed_template_horizontal").on("click", function ($e) {
        $e.preventDefault(); //Stop Web Page scrolling to the top
        if (hasClass(pre_designed_template_card_horizontal, 'template_card')) {
            selectedCardTemplate = 3;
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
            selectedCardTemplate = -1;
            noselectedCard("pre_designed_template_card_horizontal");
            //Change button text and color
            selectButon("button_pre_designed_template_horizontal");
        }
    });
    // Set canvas editor according to selected template
    $("#Next").click(function () {
        if (hasClass(label_template, 'active')) {
            var canvas_editor;
            switch (selectedCardTemplate) {
                // -1 : No template
                case (-1):
                    swal({
                        type: 'error',
                        title: 'Plantilla requerida',
                        text: 'Por favor, seleccione una plantilla.'
                    })
                    break;
                // 0 : Blank Vertical template
                case (0):
                    //Side menu according to canvas size
                    document.getElementById("addCanvas").classList.remove('col-md-4');
                    document.getElementById("addCanvas").classList.add('col-md-6'); 
                    document.getElementById("addCanvas").classList.remove('col-sm-4');              
                    document.getElementById("addCanvas").classList.add('col-sm-6');
                    //Initialize Fabric.js Vertical canvas using "id"
                    canvas_editor = new fabric.Canvas('canvas_editor');
                    //Clear Canvas
                    canvas_editor.clear();
                    canvas_editor.dispose();
                    //Initialize Fabric.js Vertical canvas using "id"
                    canvas_editor = new fabric.Canvas('canvas_editor');
                    //Size settings
                    canvas_editor.setHeight(600);
                    canvas_editor.setWidth(520);
                    //Selection settings
                    canvas_editor.selectionColor = 'rgba(0, 122, 255, 0.2)';
                    canvas_editor.selectionBorderColor = '#337ab7';
                    canvas_editor.selectionLineWidth = 2;
                    //Canvas background color
                    canvas_editor.backgroundColor = 'rgba(255, 255, 255, 1)';
                    //Save changes in Canvas
                    canvas_editor.renderAll();     
                    break;
                // 1 : Blank Horizontal template
                case (1):
                    //Side menu according to canvas size
                    document.getElementById("addCanvas").classList.remove('col-md-6');
                    document.getElementById("addCanvas").classList.add('col-md-4'); 
                    document.getElementById("addCanvas").classList.remove('col-sm-6');
                    document.getElementById("addCanvas").classList.add('col-sm-4');              
                    //Initialize Fabric.js Horizontal canvas using "id"
                    canvas_editor = new fabric.Canvas('canvas_editor');
                    //Clear Canvas
                    canvas_editor.clear();
                    canvas_editor.dispose();
                    //Initialize Fabric.js Horizontal canvas using "id"
                    canvas_editor = new fabric.Canvas('canvas_editor');
                    //Size settings
                    canvas_editor.setHeight(450);
                    canvas_editor.setWidth(720);
                    //Selection settings
                    canvas_editor.selectionColor = 'rgba(0, 122, 255, 0.2)';
                    canvas_editor.selectionBorderColor = '#337ab7';
                    canvas_editor.selectionLineWidth = 2;
                    //Canvas background color
                    canvas_editor.backgroundColor = 'rgba(255, 255, 255, 1)';
                    //Save changes in Canvas
                    canvas_editor.renderAll();
                    break;
                // 2 : Pre Designed Vertical template
                case (2):
                    //Side menu according to canvas size
                    document.getElementById("addCanvas").classList.remove('col-md-4');
                    document.getElementById("addCanvas").classList.add('col-md-6'); 
                    document.getElementById("addCanvas").classList.remove('col-sm-4');              
                    document.getElementById("addCanvas").classList.add('col-sm-6');
                    //Initialize Fabric.js Vertical canvas using "id"
                    canvas_editor = new fabric.Canvas('canvas_editor');
                    //Clear Canvas
                    canvas_editor.clear();
                    canvas_editor.dispose();
                    //Initialize Fabric.js Vertical canvas using "id"
                    canvas_editor = new fabric.Canvas('canvas_editor');
                    //Size settings
                    canvas_editor.setHeight(600);
                    canvas_editor.setWidth(520);
                    //Selection settings
                    canvas_editor.selectionColor = 'rgba(0, 122, 255, 0.2)';
                    canvas_editor.selectionBorderColor = '#337ab7';
                    canvas_editor.selectionLineWidth = 2;
                    //Canvas background color
                    canvas_editor.backgroundColor = 'rgba(255, 255, 255, 1)';
                    //Save changes in Canvas
                    canvas_editor.renderAll(); 
                    //Load selected template from JSON 
                    canvas_editor.loadFromJSON(canvasJSON[1], function(){canvas_editor.renderAll()}); 
                    break;
                // 3 : Pre Designed Horizontal template
                case (3):
                     //Side menu according to canvas size
                     document.getElementById("addCanvas").classList.remove('col-md-6');
                     document.getElementById("addCanvas").classList.add('col-md-4'); 
                     document.getElementById("addCanvas").classList.remove('col-sm-6');
                     document.getElementById("addCanvas").classList.add('col-sm-4');              
                     //Initialize Fabric.js Horizontal canvas using "id"
                     canvas_editor = new fabric.Canvas('canvas_editor');
                     //Clear Canvas
                     canvas_editor.clear();
                     canvas_editor.dispose();
                     //Initialize Fabric.js Horizontal canvas using "id"
                     canvas_editor = new fabric.Canvas('canvas_editor');
                     //Size settings
                     canvas_editor.setHeight(450);
                     canvas_editor.setWidth(720);
                     //Selection settings
                     canvas_editor.selectionColor = 'rgba(0, 122, 255, 0.2)';
                     canvas_editor.selectionBorderColor = '#337ab7';
                     canvas_editor.selectionLineWidth = 2;
                     //Canvas background color
                     canvas_editor.backgroundColor = 'rgba(255, 255, 255, 1)';
                     //Save changes in Canvas
                     canvas_editor.renderAll();
                     //Load selected template from JSON 
                     canvas_editor.loadFromJSON(canvasJSON[0], function(){canvas_editor.renderAll()}); 
                    break;
                default:
                    break;
            }
            //Control zoom and panning in canvas editor
            canvas_editor.on('mouse:wheel', function (opt) {
                var delta = opt.e.deltaY;
                var zoom = canvas_editor.getZoom();
                zoom = zoom + delta / 200;
                if (zoom > 20) zoom = 20;
                if (zoom < 0.01) zoom = 0.01;
                canvas_editor.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
                opt.e.preventDefault();
                opt.e.stopPropagation();
            });
        }
    });
    //Pre Designed Horizontal Template Modal
    $("#tag_pre_designed_template_horizontal").on('click', function () {
        document.getElementById("modal_pre_designed_template").src = canvasImages[0];
        document.getElementById("modalPreDesignedTemplateTitle").innerHTML = "Pre designed horizontal template";
        document.getElementById("modal_pre_designed_template").style.marginLeft = "0%";
    });
    //Pre Designed Vertical Template Modal
    $("#tag_pre_designed_template_vertical").on('click', function () {
        document.getElementById("modal_pre_designed_template").src = canvasImages[1];
        document.getElementById("modalPreDesignedTemplateTitle").innerHTML = "Pre designed vertical template";
        document.getElementById("modal_pre_designed_template").style.marginLeft = "15%";
    });
});
// Set blank templates images according to recipient size
function set_blank_templates() {
    var label_information = JSON.parse(localStorage.getItem('label_information'));
    //Blank Template: Vertical
    $("#template_card_image_vertical").attr("src", "https://dummyimage.com/300x400/ffffff/0000007c/&text=" + label_information.height + label_information.height_unit + "+x+" + label_information.width + label_information.width_unit);
    //Blank Template: Horizontal
    $("#template_card_image_horizontal").attr("src", "https://dummyimage.com/300x250/ffffff/0000007c/&text=" + label_information.height + label_information.height_unit + "+x+" + label_information.width + label_information.width_unit);
}
// Sleep time expects milliseconds
function sleep(time) {
    return new Promise((resolve) => setTimeout(resolve, time));
}
// Set pre designed templates according to selected substance
function set_pre_designed_templates() {
    //Load label information
    var label_information = JSON.parse(localStorage.getItem('label_information'));
    //Obtain all substance information
    $.ajax({
        url: 'getSubstanceInformation',
        dataType: 'json',
        data: {
            substance_id: label_information.substance_id,
            csrfmiddlewaretoken: '{{ csrf_token }}',
        },
        success: function (substance_information) {
            // Modify danger indications to justified text
            for (var i = 0; i < substance_information.DangerIndications.length; i++) {
                substance_information.DangerIndications[i] = substance_information.DangerIndications[i].replace('  ', ' ');
                substance_information.DangerIndications[i] = substance_information.DangerIndications[i].replace('\r\n', ' ');
                substance_information.DangerIndications[i] = substance_information.DangerIndications[i].replace('\r', ' ');
                substance_information.DangerIndications[i] = substance_information.DangerIndications[i].replace('\n', ' ');
            }
            // Modify prudence advices to justified text
            for (var i = 0; i < substance_information.PrudenceAdvices.length; i++) {
                substance_information.PrudenceAdvices[i] = substance_information.PrudenceAdvices[i].replace('  ', ' ');
                substance_information.PrudenceAdvices[i] = substance_information.PrudenceAdvices[i].replace('\r\n', ' ');
                substance_information.PrudenceAdvices[i] = substance_information.PrudenceAdvices[i].replace('\r', ' ');
                substance_information.PrudenceAdvices[i] = substance_information.PrudenceAdvices[i].replace('\n', ' ');
            }
            // Pre Designed Horizontal and Vertical Template
            preDesignedHorizontalVerticalTemplate(label_information, substance_information);
        }
    });
}
// Add dark blue color to selected card
function selectedCard(card_id) {
    card = document.getElementById(card_id);
    card.classList.remove("template_card");
    card.classList.add("template_card_selected");
}
// Add light blue color to card
function noselectedCard(card_id) {
    card = document.getElementById(card_id);
    card.classList.remove("template_card_selected");
    card.classList.add("template_card");
}
// Change button value
function changeButtonValue(button_id, button_value) {
    button = document.getElementById(button_id);
    button.innerText = button_value;
}
// Selected button
function selectedButon(button_id) {
    changeButtonValue(button_id, "Selected");
    document.getElementById(button_id).classList.add("button_border_selected");
}
// Select button
function selectButon(button_id) {
    changeButtonValue(button_id, "Select");
    document.getElementById(button_id).classList.remove("button_border_selected");
}
// Pre-Designed Horizontal and Vertical Template
function preDesignedHorizontalVerticalTemplate(label_information, substance_information) {
    //Initialize Fabric.js Horizontal canvas using "id"
    var canvas_horizontal = new fabric.Canvas('working_canvas_area_horizontal');
    //Initialize Fabric.js Vertical canvas using "id"
    var canvas_vertical = new fabric.Canvas('working_canvas_area_vertical');
    //Improve Canvas perfomance
    canvas_horizontal.renderOnAddRemove = false;
    canvas_horizontal.selection = false;
    canvas_vertical.renderOnAddRemove = false;
    canvas_vertical.selection = false;
    //Clear Canvas
    canvas_horizontal.clear();
    canvas_horizontal.dispose();
    canvas_vertical.clear();
    canvas_vertical.dispose();
    // Working Canvas Area
    canvas_horizontal = new fabric.Canvas('working_canvas_area_horizontal');
    canvas_vertical = new fabric.Canvas('working_canvas_area_vertical');
    //Size settings
    canvas_horizontal.width = 498;
    canvas_horizontal.height = 264;
    canvas_vertical.width = 400;
    canvas_vertical.height = 550;
    //Selection settings
    canvas_horizontal.selectionColor = 'rgba(0, 122, 255, 0.2)';
    canvas_horizontal.selectionBorderColor = '#337ab7';
    canvas_horizontal.selectionLineWidth = 2;
    canvas_vertical.selectionColor = 'rgba(0, 122, 255, 0.2)';
    canvas_vertical.selectionBorderColor = '#337ab7';
    canvas_vertical.selectionLineWidth = 2;
    //Canvas background color
    canvas_horizontal.backgroundColor = 'rgba(255, 255, 255, 1)';
    canvas_vertical.backgroundColor = 'rgba(255, 255, 255, 1)';
    //Save changes in Canvas
    canvas_horizontal.clear().renderAll();
    canvas_vertical.clear().renderAll();
    //Substance comercial name line
    canvas_horizontal.add(new fabric.Line([100, 400, 400, 400], {
        strokeWidth: 2,
        left: 200,
        top: 50,
        stroke: 'black'
    }));
    canvas_vertical.add(new fabric.Line([100, 460, 460, 460], {
        strokeWidth: 2,
        left: 20,
        top: 50,
        stroke: 'black'
    }));
    //Prudence advices line
    canvas_horizontal.add(new fabric.Line([100, 400, 400, 400], {
        strokeWidth: 2,
        left: 200,
        top: 230,
        stroke: 'black'
    }));
    canvas_vertical.add(new fabric.Line([100, 460, 460, 460], {
        strokeWidth: 2,
        left: 20,
        top: 500,
        stroke: 'black'
    }));
    //Line between supplier information and comercial information
    canvas_horizontal.add(new fabric.Line([200, 100, 200, 200], {
        strokeWidth: 2,
        left: 350,
        top: 230,
        stroke: 'black'
    }));
    canvas_vertical.add(new fabric.Line([200, 100, 200, 200], {
        strokeWidth: 2,
        left: 200,
        top: 500,
        stroke: 'black'
    }));  
    //===========================================================================
    //#1: Name of the product or identifier
    //===========================================================================
    addComercialNameHorizontal(canvas_horizontal, label_information);
    addComercialNameVertical(canvas_vertical, label_information);
    //===========================================================================
    //#2: Signal Word
    //===========================================================================
    addSignalWordHorizontal(canvas_horizontal, substance_information);
    addSignalWordVertical(canvas_vertical, substance_information);
    //===========================================================================
    //#3: Supplier Information
    //===========================================================================
    addSupplierInformationHorizontal(canvas_horizontal, label_information);
    addSupplierInformationVertical(canvas_vertical, label_information);
    //===========================================================================
    //#4: Comercial Information
    //===========================================================================
    if (typeof label_information.commercial_information !== 'undefined') {
        addComercialInformationHorizontal(canvas_horizontal, label_information);
        addComercialInformationVertical(canvas_vertical, label_information);
    }
    //===========================================================================
    //#5: Danger Indications
    //===========================================================================
    addDangerIndicationsHorizontal(canvas_horizontal, substance_information);
    addDangerIndicationsVertical(canvas_vertical, substance_information);
    //===========================================================================
    //#6: Prudence Advices
    //===========================================================================
    if (typeof substance_information.PrudenceAdvices != 'undefined' && substance_information.PrudenceAdvices.length > 0) {
        addPrudenceAdvicesHorizontal(canvas_horizontal, substance_information);
        addPrudenceAdvicesVertical(canvas_vertical, substance_information);
    }    
    //===========================================================================
    //===========================================================================
    //#7: Pictograms
    //===========================================================================
    if (typeof substance_information.Pictograms !== 'undefined' && substance_information.Pictograms.length > 0) {
        addPictogramsHorizontal(canvas_horizontal, substance_information);
        addPictogramsVertical(canvas_vertical, substance_information);
    }
    //=========================================================================== 
    //#8: Cas Numbers
    //===========================================================================
    addCasNumbersHorizontal(canvas_horizontal, substance_information);
    addCasNumbersVertical(canvas_vertical, substance_information);
    //===========================================================================
    // Hide loading message, save canvas images and hide working canvas areas
    sleep(500).then(() => {
        controlLoadingMessage(canvas_horizontal, canvas_vertical);
    });
}
// Add comercial name in Horizontal Canvas
function addComercialNameHorizontal(canvas, label_information) {
    var name_label = label_information.substance_commercial_name;
    var split_substance_input = name_label.split(' : ');
    name_label = split_substance_input[0];
    //Text size <=20
    if (name_label.length <= 20) {
        name_label = new fabric.Textbox(name_label, {
            width: 280,
            height: 5,
            top: 20,
            left: 205,
            fontSize: 25,
            textAlign: 'center',
            fixedWidth: 280,
            fontFamily: 'Helvetica',
            objectCaching: false
        });
    } else {
        //Text size >20
        name_label = new fabric.IText(name_label, {
            width: 280,
            left: 205,
            top: 22,
            fontSize: 25,
            fontFamily: 'Helvetica',
            textAlign: 'center',
            fill: '#000000',
            fixedWidth: 280,
            centeredScaling: true,
            objectCaching: false,
            renderOnAddRemove: false,
        });
    }
    //Capitalize the first letter in each word
    name_label.text = titleCase(name_label.text);
    canvas.add(name_label);
    //Save changes
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(name_label);
}
// Add comercial name in vertical canvas
function addComercialNameVertical(canvas, label_information) {
    var name_label = label_information.substance_commercial_name;
    var split_substance_input = name_label.split(' : ');
    name_label = split_substance_input[0];
    //Text size <=30
    if (name_label.length <= 30) {
        name_label = new fabric.Textbox(name_label, {
            width: 360,
            height: 5,
            top: 20,
            left: 20,
            fontSize: 25,
            textAlign: 'center',
            fixedWidth: 360,
            fontFamily: 'Helvetica',
            objectCaching: false
        });
    } else {
        //Text size >30
        name_label = new fabric.IText(name_label, {
            width: 360,
            left: 20,
            top: 22,
            fontSize: 25,
            fontFamily: 'Helvetica',
            textAlign: 'center',
            fill: '#000000',
            fixedWidth: 360,
            centeredScaling: true,
            objectCaching: false,
            renderOnAddRemove: false,
        });
    }
    //Capitalize the first letter in each word
    name_label.text = titleCase(name_label.text);
    canvas.add(name_label);
    //Save changes
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(name_label);
}
// Add Signal Word in Horizontal Canvas
function addSignalWordHorizontal(canvas, substance_information) {
    //Text size <=10
    if (substance_information.signalWord.length <= 10) {
        signalWord = new fabric.Textbox(substance_information.signalWord, {
            width: 180,
            height: 20,
            top: 20,
            left: 25,
            fontSize: 25,
            fill: '#ff0000',
            textAlign: 'center',
            fixedWidth: 160,
            fontFamily: 'Helvetica',
            objectCaching: false,
            renderOnAddRemove: false,
        });
    } else {
        //Text size >10
        signalWord = new fabric.IText(substance_information.signalWord, {
            width: 150,
            left: 30,
            top: 30,
            fontSize: 25,
            fontFamily: 'Helvetica',
            textAlign: 'center',
            fill: '#ff0000',
            fixedWidth: 150,
            centeredScaling: true,
            objectCaching: false,
            renderOnAddRemove: false,
        });
    }
    //Capitalize the entire word
    signalWord.text = signalWord.text.toUpperCase();
    canvas.add(signalWord);
    //Save changes
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(signalWord);
}
// Add Signal Word in Vertical Canvas
function addSignalWordVertical(canvas, substance_information) {
    //Text size <=30
    if (substance_information.signalWord.length <= 30) {
        signalWord = new fabric.Textbox(substance_information.signalWord, {
            width: 360,
            height: 5,
            top: 150,
            left: 20,
            fontSize: 25,
            fill: '#ff0000',
            textAlign: 'center',
            fixedWidth: 360,
            fontFamily: 'Helvetica',
            objectCaching: false
        });
    } else {
        //Text size >30
        signal_word = new fabric.IText(substance_information.signalWord, {
            width: 360,
            left: 20,
            top: 150,
            fontSize: 25,
            fontFamily: 'Helvetica',
            textAlign: 'center',
            fill: '#ff0000',
            fixedWidth: 360,
            centeredScaling: true,
            objectCaching: false,
            renderOnAddRemove: false,
        });
    }
    //Capitalize the entire word
    signalWord.text = signalWord.text.toUpperCase();
    canvas.add(signalWord);
    //Save changes
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(signalWord);
}
// Add supplier information in Horizontal Canvas
function addSupplierInformationHorizontal(canvas, label_information) {
    //====================================================
    //===============Company Name=========================
    //Text size <=35
    var company_name = label_information.company_name;
    if (company_name.length <= 35) {
        company_name = new fabric.Textbox(company_name, {
            width: 130,
            top: 235,
            left: 355,
            fontSize: 8,
            fixedWidth: 130,
            fontFamily: 'Helvetica',
            objectCaching: false,
        });
    } else {
        //Text size >35
        company_name = new fabric.IText(company_name, {
            width: 130,
            left: 355,
            top: 235,
            fontSize: 8,
            fontFamily: 'Helvetica',
            fill: '#000000',
            fixedWidth: 130,
            centeredScaling: true,
            objectCaching: false,
            renderOnAddRemove: false,
        });
    }
    canvas.add(company_name);
    //====================================================
    //===============Company address======================
    //Text size <=35
    var company_address = label_information.company_address;
    if (company_address.length <= 35) {
        company_address = new fabric.Textbox(company_address, {
            width: 130,
            top: 245,
            left: 355,
            fontSize: 8,
            fixedWidth: 130,
            fontFamily: 'Helvetica',
            objectCaching: false,
        });
    } else {
        //Text size >35
        company_address = new fabric.IText(company_address, {
            width: 130,
            left: 355,
            top: 245,
            fontSize: 8,
            fontFamily: 'Helvetica',
            fill: '#000000',
            fixedWidth: 130,
            centeredScaling: true,
            objectCaching: false,
            renderOnAddRemove: false,
        });
    }
    canvas.add(company_address);
    //====================================================
    //===============Company phone========================
    //Text size <=35
    var company_phone = label_information.company_phone;
    if (company_phone.length <= 35) {
        company_phone = new fabric.Textbox(company_phone, {
            width: 130,
            top: 255,
            left: 355,
            fontSize: 8,
            fixedWidth: 130,
            fontFamily: 'Helvetica',
            objectCaching: false,
        });
    } else {
        //Text size >35
        company_phone = new fabric.IText(company_phone, {
            width: 130,
            left: 355,
            top: 255,
            fontSize: 8,
            fontFamily: 'Helvetica',
            fill: '#000000',
            fixedWidth: 130,
            centeredScaling: true,
            objectCaching: false,
            renderOnAddRemove: false,
        });
    }
    canvas.add(company_phone);
    //Save changes in Canvas
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(company_name);
    controlTextWidth(company_address);
    controlTextWidth(company_phone);
}
// Add supplier information in Vertical Canvas
function addSupplierInformationVertical(canvas, label_information) {
    //====================================================
    //===============Company Name=========================
    company_name = new fabric.IText(label_information.company_name, {
        width: 170,
        left: 205,
        top: 505,
        fontSize: 10,
        fontFamily: 'Helvetica',
        fill: '#000000',
        fixedWidth: 170,
        centeredScaling: true,
        objectCaching: false,
        renderOnAddRemove: false,
    });
    canvas.add(company_name);
    //====================================================
    //===============Company address======================
    company_address = new fabric.IText(label_information.company_address, {
        width: 170,
        left: 205,
        top: 520,
        fontSize: 10,
        fontFamily: 'Helvetica',
        fill: '#000000',
        fixedWidth: 170,
        centeredScaling: true,
        objectCaching: false,
        renderOnAddRemove: false,
    });
    canvas.add(company_address);
    //====================================================
    //===============Company phone========================
    company_phone = new fabric.IText(label_information.company_phone, {
        width: 170,
        left: 205,
        top: 535,
        fontSize: 10,
        fontFamily: 'Helvetica',
        fill: '#000000',
        fixedWidth: 170,
        centeredScaling: true,
        objectCaching: false,
        renderOnAddRemove: false,
    });
    canvas.add(company_phone);
    //Save changes in Canvas
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(company_name);
    controlTextWidth(company_address);
    controlTextWidth(company_phone);
}
// Add comercial information in Horizontal Canvas
function addComercialInformationHorizontal(canvas, label_information) {
    var commercial_information = label_information.commercial_information;
    commercial_information = new fabric.Textbox(commercial_information, {
        width: 140,
        left: 205,
        top: 235,
        fontSize: 8,
        fontFamily: 'Helvetica',
        textAlign: 'justify',
        fill: '#000000',
        fixedWidth: 140,
        fixedHeight: 25,
        objectCaching: false,
        renderOnAddRemove: false,
    });
    canvas.add(commercial_information);
    //Save changes in Canvas
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(commercial_information);
    //Control font size according to height
    controlTextHeightCommercialInformationHorizontal(commercial_information, canvas);
}
// Add comercial information in Vertical Canvas
function addComercialInformationVertical(canvas, label_information) {
    var commercial_information = label_information.commercial_information;
    commercial_information = new fabric.Textbox(commercial_information, {
        width: 175,
        left: 20,
        top: 508,
        fontSize: 8,
        fontFamily: 'Helvetica',
        textAlign: 'justify',
        fill: '#000000',
        fixedWidth: 175,
        fixedHeight: 35,
        objectCaching: false,
        renderOnAddRemove: false,
    });
    canvas.add(commercial_information);
    //Save changes in Canvas
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(commercial_information);
    //Control font size according to height
    controlTextHeightCommercialInformationVertical(commercial_information, canvas);
}
// Control text height in Commercial Information of Horizontal Canvas
function controlTextHeightCommercialInformationHorizontal(text, canvas) {
    //Set max text font size to fixed height
    if (text.height > text.fixedHeight) {
        text.fontSize = 7;
        //Save changes in canvas
        canvas.renderAll();
    }
    //Decrease font size
    while (text.height > text.fixedHeight) {
        text.fontSize -= 1;
        canvas.renderAll();
    }
    text.fontSize += 1;
    //Save changes in canvas
    canvas.renderAll();
    //Increment font size
    while ((text.height < text.fixedHeight)) {
        text.fontSize += 1;
        canvas.renderAll();
    }
    //Decrease font size
    if (text.height > text.fixedHeight) {
        text.fontSize -= 1;
        canvas.renderAll();
    }
}
// Control text height in Commercial Information of Vertical Canvas
function controlTextHeightCommercialInformationVertical(text, canvas) {
    //Set max text font size to fixed height
    if (text.height > text.fixedHeight) {
        text.fontSize = 7;
        //Save changes in canvas
        canvas.renderAll();
    }
    //Decrease font size
    while (text.height > text.fixedHeight) {
        text.fontSize -= 1;
        canvas.renderAll();
    }
    text.fontSize += 1;
    //Save changes in canvas
    canvas.renderAll();
    //Increment font size
    while ((text.height < text.fixedHeight)) {
        text.fontSize += 1;
        canvas.renderAll();
    }
    //Decrease font size
    if (text.height > text.fixedHeight) {
        text.fontSize -= 1;
        canvas.renderAll();
    }
}
// Add Danger indications in Horizontal Canvas
function addDangerIndicationsHorizontal(canvas, substance_information) {
    //Obtain all danger indications separated by a dot
    var dangerIndicationsText = substance_information.DangerIndications.join('. ');
    dangerIndicationsText += '.';
    dangerIndication = new fabric.Textbox(dangerIndicationsText, {
        width: 280,
        left: 205,
        top: 75,
        fontSize: 25,
        fontFamily: 'Helvetica',
        textAlign: 'justify',
        fill: '#000000',
        fixedWidth: 280,
        fixedHeight: 72,
        objectCaching: false,
        renderOnAddRemove: false,
    });
    canvas.add(dangerIndication);
    //Save changes
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(dangerIndication);
    //Control text height in danger indications
    controlTextHeightDangerIndicationsHorizontal(dangerIndication, canvas);
}
// Add Danger indications in Vertical Canvas
function addDangerIndicationsVertical(canvas, substance_information) {
    //Obtain all danger indications separated by a dot
    var dangerIndicationsText = substance_information.DangerIndications.join('. ');
    dangerIndicationsText += '.';
    dangerIndication = new fabric.Textbox(dangerIndicationsText, {
        width: 360,
        left: 20,
        top: 205,
        fontSize: 25,
        fontFamily: 'Helvetica',
        textAlign: 'justify',
        fill: '#000000',
        fixedWidth: 360,
        fixedHeight: 140,
        objectCaching: false,
        renderOnAddRemove: false,
    });
    canvas.add(dangerIndication);
    //Save changes
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(dangerIndication);
    //Control text height in danger indications
    controlTextHeightDangerIndicationsVertical(dangerIndication, canvas);
}
// Control text height in Danger Indications of Horizontal Canvas
function controlTextHeightDangerIndicationsHorizontal(text, canvas) {
    //Set max text font size to fixed height
    if (text.height > text.fixedHeight) {
        text.fontSize = 11;
        //Save changes in canvas
        canvas.renderAll();
    }
    //Decrease font size
    while (text.height > text.fixedHeight) {
        text.fontSize -= 1;
        canvas.renderAll();
    }
    text.fontSize += 1;
    //Save changes in canvas
    canvas.renderAll();
    //Increment font size
    while ((text.height < text.fixedHeight)) {
        text.fontSize += 1;
        canvas.renderAll();
    }
    //Decrease font size
    if (text.height > text.fixedHeight) {
        text.fontSize -= 1;
        canvas.renderAll();
    }
}
// Control text height in Danger Indications of Vertical Canvas
function controlTextHeightDangerIndicationsVertical(text, canvas) {
    //Set max text font size to fixed height
    if (text.height > text.fixedHeight) {
        text.fontSize = 18;
        //Save changes in canvas
        canvas.renderAll();
    }
    //Decrease font size
    while (text.height > text.fixedHeight) {
        text.fontSize -= 1;
        canvas.renderAll();
    }
    text.fontSize += 1;
    //Save changes in canvas
    canvas.renderAll();
    //Increment font size
    while ((text.height < text.fixedHeight)) {
        text.fontSize += 1;
        canvas.renderAll();
    }
    //Decrease font size
    if (text.height > text.fixedHeight) {
        text.fontSize -= 1;
        canvas.renderAll();
    }
}
// Add prudence advices in Horizontal Canvas
function addPrudenceAdvicesHorizontal(canvas, substance_information) {
    //Obtain all prudence advices separated by dot
    var prudenceAdvicesText = substance_information.PrudenceAdvices.join('. ');
    prudenceAdvicesText += '.';
    prudenceAdvice = new fabric.Textbox(prudenceAdvicesText, {
        width: 280,
        left: 205,
        top: 152,
        fontSize: 25,
        fontFamily: 'Helvetica',
        textAlign: 'justify',
        fill: '#000000',
        fixedWidth: 280,
        fixedHeight: 78,
        objectCaching: false,
        renderOnAddRemove: false,
    });
    canvas.add(prudenceAdvice);
    //Save changes in Canvas
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(prudenceAdvice);
    //Control text height in Prudence Advices
    controlTextHeightPrudenceAdvicesHorizontal(prudenceAdvice, canvas);
}
// Add prudence advices in Vertical Canvas
function addPrudenceAdvicesVertical(canvas, substance_information) {
    //Obtain all prudence advices separated by dot
    var prudenceAdvicesText = substance_information.PrudenceAdvices.join('. ');
    prudenceAdvicesText += '.';
    prudenceAdvice = new fabric.Textbox(prudenceAdvicesText, {
        width: 360,
        left: 20,
        top: 355,
        fontSize: 25,
        fontFamily: 'Helvetica',
        textAlign: 'justify',
        fill: '#000000',
        fixedWidth: 360,
        fixedHeight: 150,
        objectCaching: false,
        renderOnAddRemove: false,
    });
    canvas.add(prudenceAdvice);
    //Save changes in Canvas
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(prudenceAdvice);
    //Control text height in Prudence Advices
    controlTextHeightPrudenceAdvicesVertical(prudenceAdvice, canvas);
}
// Control text height in Prudence Advices of Horizontal Canvas
function controlTextHeightPrudenceAdvicesHorizontal(text, canvas) {
    //Set max text font size to fixed height
    if (text.height > text.fixedHeight) {
        text.fontSize = 4;
        //Save changes in canvas
        canvas.renderAll();
    }
    //Decrease font size
    while (text.height > text.fixedHeight) {
        text.fontSize -= 1;
        canvas.renderAll();
    }
    text.fontSize += 1;
    //Save changes in canvas
    canvas.renderAll();
    //Increment font size
    while ((text.height < text.fixedHeight)) {
        text.fontSize += 1;
        canvas.renderAll();
    }
    //Decrease font size
    if (text.height > text.fixedHeight) {
        text.fontSize -= 1;
        canvas.renderAll();
    }
}
// Control text height in Prudence Advices of Vertical Canvas
function controlTextHeightPrudenceAdvicesVertical(text, canvas) {
    //Set max text font size to fixed height
    if (text.height > text.fixedHeight) {
        text.fontSize = 7;
        //Save changes in canvas
        canvas.renderAll();
    }
    //Decrease font size
    while (text.height > text.fixedHeight) {
        text.fontSize -= 1;
        canvas.renderAll();
    }
    text.fontSize += 1;
    //Save changes in canvas
    canvas.renderAll();
    //Increment font size
    while ((text.height < text.fixedHeight)) {
        text.fontSize += 1;
        canvas.renderAll();
    }
    //Decrease font size
    if (text.height > text.fixedHeight) {
        text.fontSize -= 1;
        canvas.renderAll();
    }
}
// Add pictograms in Horizontal Canvas
function addPictogramsHorizontal(canvas, substance_information) {
    var pictogramslength = substance_information.Pictograms.length;
    switch (pictogramslength) {
        // One pictogram
        case 1:
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[0], function (img) {
                img.scaleToWidth(170);
                img.scaleToHeight(170);
                img.set("top", 60);
                img.set("left", 15);
                canvas.add(img);
            });
            break;
        // Two pictograms
        case 2:
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[0], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 90);
                img.set("left", 15);
                canvas.add(img);
            });
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[1], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 90);
                img.set("left", 105);
                canvas.add(img);
            });
            break;
        // Tree pictograms
        case 3:
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[0], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 54);
                img.set("left", 60);
                canvas.add(img);
            });
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[1], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 100);
                img.set("left", 15);
                canvas.add(img);
            });
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[2], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 100);
                img.set("left", 105);
                canvas.add(img);
            });
            break;
        //Four pictograms
        case 4:
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[0], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 54);
                img.set("left", 60);
                canvas.add(img);
            });
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[1], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 146);
                img.set("left", 60);
                canvas.add(img);
            });
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[2], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 100);
                img.set("left", 15);
                canvas.add(img);
            });
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[3], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 100);
                img.set("left", 105);
                canvas.add(img);
            });
            break;
        // Five or more pictograms
        default:
            if (pictogramslength >= 5) {
                fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[0], function (img) {
                    img.scaleToWidth(90);
                    img.scaleToHeight(90);
                    img.set("top", 96);
                    img.set("left", 60);
                    canvas.add(img);
                });
                fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[1], function (img) {
                    img.scaleToWidth(90);
                    img.scaleToHeight(90);
                    img.set("top", 50);
                    img.set("left", 15);
                    canvas.add(img);
                });
                fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[2], function (img) {
                    img.scaleToWidth(90);
                    img.scaleToHeight(90);
                    img.set("top", 50);
                    img.set("left", 105);
                    canvas.add(img);
                });
                fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[3], function (img) {
                    img.scaleToWidth(90);
                    img.scaleToHeight(90);
                    img.set("top", 143);
                    img.set("left", 15);
                    canvas.add(img);
                });
                fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[4], function (img) {
                    img.scaleToWidth(90);
                    img.scaleToHeight(90);
                    img.set("top", 143);
                    img.set("left", 105);
                    canvas.add(img);
                });
            }
            break;
    }
    canvas.renderAll();
}
// Add pictograms in Vertical Canvas
function addPictogramsVertical(canvas, substance_information) {
    var pictogramslength = substance_information.Pictograms.length;
    switch (pictogramslength) {
        //One pictogram
        case 1:
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[0], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 55);
                img.set("left", 20);
                canvas.add(img);
            });
            break;
        //Two pictograms
        case 2:
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[0], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 55);
                img.set("left", 20);
                canvas.add(img);
            });
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[1], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 55);
                img.set("left", 110);
                canvas.add(img);
            });
            break;
        //Tree pictograms
        case 3:
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[0], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 55);
                img.set("left", 20);
                canvas.add(img);
            });
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[1], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 55);
                img.set("left", 110);
                canvas.add(img);
            });
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[2], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 55);
                img.set("left", 200);
                canvas.add(img);
            });
            break;
        //Four pictograms
        case 4:
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[0], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 55);
                img.set("left", 20);
                canvas.add(img);
            });
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[1], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 55);
                img.set("left", 110);
                canvas.add(img);
            });
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[2], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 55);
                img.set("left", 200);
                canvas.add(img);
            });
            fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[3], function (img) {
                img.scaleToWidth(90);
                img.scaleToHeight(90);
                img.set("top", 55);
                img.set("left", 290);
                canvas.add(img);
            });
            break;
        //Five or more pictograms
        default:
            if (pictogramslength >= 5) {
                fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[0], function (img) {
                    img.scaleToWidth(72);
                    img.scaleToHeight(72);
                    img.set("top", 55);
                    img.set("left", 20);
                    canvas.add(img);
                });
                fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[1], function (img) {
                    img.scaleToWidth(72);
                    img.scaleToHeight(72);
                    img.set("top", 55);
                    img.set("left", 92);
                    canvas.add(img);
                });
                fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[2], function (img) {
                    img.scaleToWidth(72);
                    img.scaleToHeight(72);
                    img.set("top", 55);
                    img.set("left", 164);
                    canvas.add(img);
                });
                fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[3], function (img) {
                    img.scaleToWidth(72);
                    img.scaleToHeight(72);
                    img.set("top", 55);
                    img.set("left", 236);
                    canvas.add(img);
                });
                fabric.Image.fromURL('/static/sga/img/pictograms/' + substance_information.Pictograms[4], function (img) {
                    img.scaleToWidth(72);
                    img.scaleToHeight(72);
                    img.set("top", 55);
                    img.set("left", 308);
                    canvas.add(img);
                });
            }
            break;
    }
    canvas.renderAll();
}
// Add cas numbers in Horizontal Canvas
function addCasNumbersHorizontal(canvas, substance_information) {
    //Obtain all cas numbers separated by comma
    var casNumbersText = substance_information.CasNumbers.join(', ');
    //Text size <=20
    if (casNumbersText.length <= 20) {
        casNumbers = new fabric.Textbox(casNumbersText, {
            width: 280,
            height: 5,
            top: 52,
            left: 205,
            fontSize: 22,
            textAlign: 'center',
            fixedWidth: 280,
            fontFamily: 'Helvetica',
            objectCaching: false
        });
    } else {
        //Text size >20
        casNumbers = new fabric.IText(casNumbersText, {
            width: 280,
            left: 205,
            top: 55,
            fontSize: 22,
            fontFamily: 'Helvetica',
            textAlign: 'center',
            fill: '#000000',
            fixedWidth: 280,
            centeredScaling: true,
            objectCaching: false,
            renderOnAddRemove: false,
        });
    }
    canvas.add(casNumbers);
    //Save changes
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(casNumbers);
}
// Add cas numbers in Vertical Canvas
function addCasNumbersVertical(canvas, substance_information) {
    //Obtain all cas numbers separated by comma
    var casNumbersText = substance_information.CasNumbers.join(', ');
    //Text size <=30
    if (casNumbersText.length <= 30) {
        casNumbers = new fabric.Textbox(casNumbersText, {
            width: 360,
            height: 5,
            top: 180,
            left: 20,
            fontSize: 22,
            textAlign: 'center',
            fixedWidth: 360,
            fontFamily: 'Helvetica',
            objectCaching: false
        });
    } else {
        //Text size >30
        casNumbers = new fabric.IText(casNumbersText, {
            width: 360,
            left: 20,
            top: 182,
            fontSize: 22,
            fontFamily: 'Helvetica',
            textAlign: 'center',
            fill: '#000000',
            fixedWidth: 360,
            centeredScaling: true,
            objectCaching: false,
            renderOnAddRemove: false,
        });
    }
    canvas.add(casNumbers);
    //Save changes
    canvas.renderAll();
    //Control font size according to width
    controlTextWidth(casNumbers);
}
// Control text width in label
function controlTextWidth(text) {
    if (text.width > text.fixedWidth) {
        text.fontSize *= text.fixedWidth / (text.width + 1);
        text.width = text.fixedWidth;
    }
}
//Capitalize the first letter in each word
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
// Resize canvas and objects to specified width and height
function zoomCanvas(factorX, factorY, canvas) {
    canvas.setHeight(canvas.getHeight() * factorY);
    canvas.setWidth(canvas.getWidth() * factorX);
    if (canvas.backgroundImage) {
        // Need to scale background images as well
        var bi = canvas.backgroundImage;
        bi.width = bi.width * factorX; bi.height = bi.height * factorY;
    }
    var objects = canvas.getObjects();
    for (var i in objects) {
        var scaleX = objects[i].scaleX;
        var scaleY = objects[i].scaleY;
        var left = objects[i].left;
        var top = objects[i].top;
        var tempScaleX = scaleX * factorX;
        var tempScaleY = scaleY * factorY;
        var tempLeft = left * factorX;
        var tempTop = top * factorY;
        objects[i].scaleX = tempScaleX;
        objects[i].scaleY = tempScaleY;
        objects[i].left = tempLeft;
        objects[i].top = tempTop;
        objects[i].setCoords();
    }
    canvas.renderAll();
    canvas.calcOffset();
}
// Hide loading message, save canvas images and hide working canvas areas
function controlLoadingMessage(canvas_horizontal, canvas_vertical) {
    // Pre Designed Horizontal Template Modal
    var factorX = 1000 / canvas_horizontal.getWidth();
    var factorY = 650 / canvas_horizontal.getHeight();
    zoomCanvas(factorX, factorY, canvas_horizontal);
    // Save Canvas image in array for the pre Designed Horizontal Template Modal
    canvasImages[0] = canvas_horizontal.toDataURL('png');
    // Pre Designed Vertical Template Modal
    var factorX = 400 / canvas_vertical.getWidth();
    var factorY = 550 / canvas_vertical.getHeight();
    zoomCanvas(factorX, factorY, canvas_vertical);
    // Save Canvas image in array for the pre Designed Vertical Template Modal
    canvasImages[1] = canvas_vertical.toDataURL('png');
    // Pre Designed Horizontal Template
    var factorX = 300 / canvas_horizontal.getWidth();
    var factorY = 250 / canvas_horizontal.getHeight();
    zoomCanvas(factorX, factorY, canvas_horizontal);
    document.getElementById("pre_designed_template_horizontal").src = canvas_horizontal.toDataURL('png');
    // Pre Designed Vertical Template
    var factorX = 300 / canvas_vertical.getWidth();
    var factorY = 400 / canvas_vertical.getHeight();
    zoomCanvas(factorX, factorY, canvas_vertical);
    document.getElementById("pre_designed_template_vertical").src = canvas_vertical.toDataURL('png');
    // Save pre designed templates in JSON
    // Pre Designed Horizontal Template
    var factorX = 720 / canvas_horizontal.getWidth();
    var factorY = 450 / canvas_horizontal.getHeight();
    zoomCanvas(factorX, factorY, canvas_horizontal);
    // Save Canvas JSON in array for the pre Designed Horizontal Template
    canvasJSON[0] = JSON.stringify(canvas_horizontal);
    // Pre Designed Vertical Template
    var factorX = 520 / canvas_vertical.getWidth();
    var factorY = 600 / canvas_vertical.getHeight();
    zoomCanvas(factorX, factorY, canvas_vertical);
    // Save Canvas JSON in array for the pre Designed Vertical Template
    canvasJSON[1] = JSON.stringify(canvas_vertical);
    // Hide working canvas area horizontal
    var factorX = 0 / canvas_horizontal.getWidth();
    var factorY = 0 / canvas_horizontal.getHeight();
    zoomCanvas(factorX, factorY, canvas_horizontal);
    canvas_horizontal.clear();
    canvas_horizontal.dispose();
    $('#working_canvas_area_horizontal').hide();
    // Hide working canvas area vertical
    var factorX = 0 / canvas_vertical.getWidth();
    var factorY = 0 / canvas_vertical.getHeight();
    zoomCanvas(factorX, factorY, canvas_vertical);
    canvas_vertical.clear();
    canvas_vertical.dispose();
    $('#working_canvas_area_vertical').hide();
    // Hide loading message
    $('#loadingMessage').modal("hide");
}
/*
// Testing Canvas
$('#testing_canvas').click( function() {     
    console.log(canvasJSON[2]);
    var canvas2 = new fabric.Canvas('working_canvas_area2');
    canvas2.loadFromJSON(canvasJSON[2], function(){canvas2.renderAll()}); 
});
*/