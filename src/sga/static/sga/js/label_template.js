/*
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 27 sept. 2018
@author: Guillermo Castro Sánchez
@email: guillermoestebancs@gmail.com
*/

// Default to true for browsers, false for node, it enables objectCaching at object level.
fabric.Object.prototype.objectCaching = true;
// Enabled to avoid blurry effects for big scaling
fabric.Object.prototype.noScaleCache = true;

$(document).ready(function () {
    /*
    //Check substance information is not empty
    $("#substance").change(function () {
        if (!$("#substance").val()) {
            alert("Please enter substance information");
        } else {
            //Validate information
            //Create a preview label
            previewTemplate1();
            //Create label in database
        }
    });
    */
});

/*----------------------------------------------------------------------------------------------------------------*/
/*----------------------------------------------Saved Canvas Design ----------------------------------------------*/
//Initialize Fabric.js with our canvas using "id"
var canvas = new fabric.StaticCanvas('saved_design_canvas1');

//Selection settings
canvas.selectionColor = 'rgba(0,255,0,0.3)';
canvas.selectionBorderColor = '#fe7f00';
canvas.selectionLineWidth = 2;

//Canvas background color
canvas.backgroundColor = 'rgba(242,242,242,1)';

//Save changes in Canvas
canvas.clear().renderAll();
/*----------------------------------------------------------------------------------------------------------------*/
/*----------------------------------------------Pre-Designed Templates -------------------------------------------*/
//Initialize Fabric.js with our canvas using "id"
var canvas = new fabric.Canvas('pre_design_canvas1');

//Selection settings
canvas.selectionColor = 'rgba(0,255,0,0.3)';
canvas.selectionBorderColor = '#fe7f00';
canvas.selectionLineWidth = 2;

//Canvas background color
canvas.backgroundColor = 'rgba(242,242,242,1)';

//Save changes in Canvas
canvas.clear().renderAll();

//Template #1:
function previewTemplate1() {
    //Clear preview
    //Eemove all objects and re-render
    canvas.clear().renderAll();

    //Sustance Name Line
    canvas.add(new fabric.Line([100, 400, 400, 400], {
        strokeWidth: 2,
        left: 200,
        top: 50,
        stroke: 'black'
    }));
    

    //#1: Name of the product or identifier
    var name_label = document.getElementById("substance").value;
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
            centeredScaling: true
        });
    }
    name_label.text = titleCase(name_label.text);
    controlTextNameSize(name_label);
    canvas.add(name_label);

    //Save changes in Canvas
    canvas.renderAll();
}

//Control text size in label
function controlTextNameSize(text) {
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
/*----------------------------------------------------------------------------------------------------------------*/