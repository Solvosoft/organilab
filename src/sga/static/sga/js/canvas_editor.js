function update_resolution(width, height){
    var value = 37.795280352; //CM VALUE IN PIXELES
    svgEditor.svgCanvas.setResolution(Math.round(width*value), Math.round(height*value), 1);
    svgEditor.updateCanvas();
    svgEditor.svgCanvas.selectAllInCurrentLayer();
}

function load_data_sga_label_form(urlParams){

    var label_name = urlParams.get('name');
    var substance = urlParams.get('substance');
    var template = urlParams.get('template');

    if(label_name){
        $("#id_name").val(label_name);
    }
    if(substance){
        $("#id_substance").val(substance);
        $("#id_substance").change();
    }
    if(template){
        var url = document.url_get_recipient_size;
        url = url.replace('0', '1');
        url = url+template;
        load_canvas_editor_template(url);
        $("#id_template").val(template);
    }

}


$(window).ready(function(){

    let elem = document.querySelector('#canvas_editor');
    let rect = elem.getBoundingClientRect();

    var urlParams = new URLSearchParams(window.location.search);
    load_data_sga_label_form(urlParams);
    var instance = urlParams.get('instance');

    var svg_content = $("#id_json_representation").val();

    if(instance || svg_content){
        svgEditor.svgCanvas.clear();
        try {
            svgEditor.loadSvgString(svg_content);
            if(document.canvas_size){
                update_resolution(document.canvas_size.width, document.canvas_size.height);
            }
        } catch (err) {
        if (err.name !== 'AbortError') {
            console.log(err);
        }
      }
    }else{
        if(document.clean_canvas_editor){
            svgEditor.svgCanvas.clear();
            svgEditor.svgCanvas.setResolution(640, 480, 1);
            svgEditor.updateCanvas();
        }
    }

});



function load_data_form(idform){
    var svg_text = svgEditor.svgCanvas.getSvgString();
    $("#id_json_representation").val(svg_text);
    var svg_element = document.getElementById('svgcontent');
    var svg_string = new XMLSerializer().serializeToString(svg_element);
    var decoded = unescape(encodeURIComponent(svg_string));
    var base64 = btoa(decoded);
    $("#id_preview").val(base64);
}


$("#editor_save").on('click', function(){
     load_data_form("sgaform");
     $("#sgaform").submit();
});


function load_canvas_editor_template(url){

    $.ajax({
        url: url,
        type: 'GET',
        success: function(result) {
          if(result.svg_content){
            svgEditor.loadSvgString(result.svg_content);
          }

          if(result.size){
            update_resolution(result.size.width, result.size.height);
          }
        },
        error: function(xhr, resp, text) {
            console.log(xhr, resp, text);
        }
    });
}


$("#id_recipient_size").on("change", function(){
    var id = $(this).val();
    var url = document.url_get_recipient_size;
    if(id){
        url = url+id;
    }
    load_canvas_editor_template(url);
});


$("#savesgalabel").on('click', function(){
    load_data_form("personal");
    $("#sgaform").submit();
});


