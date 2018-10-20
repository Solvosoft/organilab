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
// Canvas images for the modals
var canvasImages = []

/* Testing Canvas */
/*
var jsonPrueba;
*/

// Default to true for browsers, false for node, it enables objectCaching at object level.
fabric.Object.prototype.objectCaching = false;
// Enabled to avoid blurry effects for big scaling
fabric.Object.prototype.noScaleCache = true;

$(document).ready(function () {
    //Hide Working Canvas Area
    $('#working_canvas_area').hide();
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
    // Pre Designed Horizontal Template Modal
    $("#tag_pre_designed_template_horizontal").on('click', function () {
        document.getElementById("modal_pre_designed_template").src = canvasImages[0];
    });
});


/* Set blank templates images according to recipient size */
function set_blank_templates() {

    // Show loading message
    //waitingDialog.show('Loading...');
    waitingDialog.show("<span class='glyphicon glyphicon-time'></span> Loading...", { dialogSize: 'sm', progressType: 'primary' });
    var label_information = JSON.parse(localStorage.getItem('label_information'));
    // console.log(JSON.parse(localStorage.getItem('label_information')));
    //Blank Template: Vertical
    $("#template_card_image_vertical").attr("src", "https://dummyimage.com/300x400/ffffff/0000007c/&text=" + label_information.height + label_information.height_unit + "+x+" + label_information.width + label_information.width_unit);
    //Blank Template: Horizontal
    $("#template_card_image_horizontal").attr("src", "https://dummyimage.com/300x250/ffffff/0000007c/&text=" + label_information.height + label_information.height_unit + "+x+" + label_information.width + label_information.width_unit);

    // Hide loading message after few miliseconds
    setTimeout(function () { waitingDialog.hide() }, 1000);
}

/* Set pre designed templates according to selected substance */
function set_pre_designed_templates() {
    //Load label information
    var label_information = JSON.parse(localStorage.getItem('label_information'));

    // Obtain all substance information
    $.ajax({
        url: 'getSubstanceInformation',
        dataType: 'json',
        data: {
            substance_id: label_information.substance_id,
            csrfmiddlewaretoken: '{{ csrf_token }}',
        },
        success: function (substance_information) {
            // Pre Designed Horizontal Template
            preDesignedHorizontalTemplate(label_information, substance_information);
        }
    });

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

/* Pre-Designed Horizontal Template */
function preDesignedHorizontalTemplate(label_information, substance_information) {
    //Initialize Fabric.js canvas using "id"
    var canvas = new fabric.Canvas('working_canvas_area');

    //Clear Canvas
    canvas.clear();
    canvas.dispose();

    canvas = new fabric.Canvas('working_canvas_area');

    // console.log(canvas.getObjects().length);

    //Size settings
    canvas.width = 498;
    canvas.height = 264;

    //Selection settings
    canvas.selectionColor = 'rgba(0,255,0,0.3)';
    canvas.selectionBorderColor = '#fe7f00';
    canvas.selectionLineWidth = 2;

    //Canvas background color
    canvas.backgroundColor = 'rgba(242,242,242,1)';

    //Save changes in Canvas
    canvas.clear().renderAll();

    //Sustance Name Line
    canvas.add(new fabric.Line([100, 400, 400, 400], {
        strokeWidth: 2,
        left: 200,
        top: 50,
        stroke: 'black'
    }));

    //---------------------------------------------------------------------------
    //#1: Name of the product or identifier
    //---------------------------------------------------------------------------
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
            objectCaching: false
        });
    }
    name_label.text = titleCase(name_label.text);
    controlTextWidth(name_label, canvas);
    canvas.add(name_label);
    //Save changes in Canvas
    canvas.renderAll();
    //---------------------------------------------------------------------------
    //#2: Signal Word
    //---------------------------------------------------------------------------
    //Text size <=10
    if (substance_information.signalWord.length <= 10) {
        signalWord = new fabric.Textbox(substance_information.signalWord, {
            width: 180,
            height: 20,
            top: 20,
            left: 5,
            fontSize: 25,
            textAlign: 'center',
            fixedWidth: 180,
            fontFamily: 'Helvetica',
            objectCaching: false
        });
    } else {
        //Text size >10
        signalWord = new fabric.IText(substance_information.signalWord, {
            width: 150,
            left: 4,
            top: 22,
            fontSize: 25,
            fontFamily: 'Helvetica',
            textAlign: 'center',
            fill: '#000000',
            fixedWidth: 150,
            centeredScaling: true,
            objectCaching: false
        });
    }
    signalWord.text = signalWord.text.toUpperCase();
    controlTextWidth(signalWord, canvas);
    canvas.add(signalWord);
    //Save changes in Canvas
    canvas.renderAll();
    //---------------------------------------------------------------------------
    //#3: Danger Indications
    //---------------------------------------------------------------------------
    dangerIndication = new fabric.Textbox('La banca tendrá que asumir el impuesto de las hipotecas. El Supremo libra al cliente de abonar un tributo clave en la compra de vivienda. La sentencia no aclara si afecta a préstamos nuevos o también a miles ya firmados.', {
        width: 280,
        height: 100,
        left: 205,
        top: 50,
        fontSize: 30,
        fontFamily: 'Helvetica',
        textAlign: 'justify',
        fill: '#000000',
        fixedWidth: 280,
        fixedHeight: 100,
        objectCaching: false
    });
    controlTextWidth(dangerIndication, canvas);
    //controlTextHeight(dangerIndication, canvas);
    canvas.add(dangerIndication);
    //Save changes in Canvas
    canvas.renderAll();

    /*
    //---------------------------------------------------------------------------
    //-------------------------------Prueba--------------------------------------

    //Save changes in Canvas
    canvas.renderAll();
    //---------------------------------------------------------------------------
    jsonPrueba = JSON.stringify(canvas);
    */


    // Pre Designed Horizontal Template Modal
    var factorX = 700 / canvas.getWidth();
    var factorY = 350 / canvas.getHeight();
    zoomCanvas(factorX, factorY, canvas);
    // Save Canvas image in array for the pre Designed Horizontal Template Modal
    canvasImages[0] = canvas.toDataURL('png');

    // Pre Designed Horizontal Template
    var factorX = 300 / canvas.getWidth();
    var factorY = 250 / canvas.getHeight();
    zoomCanvas(factorX, factorY, canvas);
    document.getElementById("pre_designed_template_horizontal").src = canvas.toDataURL('png');


    
    var factorX = 0 / canvas.getWidth();
    var factorY = 0 / canvas.getHeight();
    zoomCanvas(factorX, factorY, canvas);
    canvas.clear();
    canvas.dispose();
    $('#working_canvas_area').hide();
    

}

/* Control text width in label */
function controlTextWidth(text, canvas) {
    if (text.width > text.fixedWidth) {
        text.fontSize *= text.fixedWidth / (text.width + 1);
        text.width = text.fixedWidth;
    }
    canvas.on('text:changed', function (opt) {
        var text = opt.target;
        if (text.width > text.fixedWidth) {
            text.fontSize *= text.fixedWidth / (text.width + 1);
            text.width = text.fixedWidth;
        }
    });
}

/* Control text height in label */
function controlTextHeight(text, canvas) {
    if (text.height > text.fixedHeight) {
        text.fontSize *= (text.fixedHeight / (text.height+1));
        text.height = text.fixedHeight;
    }
    canvas.on('text:changed', function (opt) {
        var text = opt.target;
        if (text.height > text.fixedHeight) {
            text.fontSize *= text.fixedHeight / (text.height + 1);
            text.height = text.fixedHeight;
        }
    });
}

/* Capitalize each letter in a word */
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

/* Resize canvas and objects to specified width and height */
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

/* Testing Canvas */
/*
$('#testing_canvas').click( function() {     
    console.log(jsonPrueba);
    var canvas2 = new fabric.Canvas('working_canvas_area2');
    canvas2.loadFromJSON(jsonPrueba, function(){canvas2.renderAll()}); 
});
*/