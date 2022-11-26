function update_resolution(width, height){
    var value = 37.795280352; //CM VALUE IN PIXELES
    svgEditor.svgCanvas.setResolution(Math.round(width*value), Math.round(height*value), 1);
    svgEditor.updateCanvas();
    svgEditor.svgCanvas.selectAllInCurrentLayer();
}


$(window).ready(function(){

    var svg_content = $("#id_json_representation").val();

    if(svg_content){
        svgEditor.svgCanvas.clear();
        try {
            svgEditor.loadSvgString(svg_content);
            load_canvas_editor_template($("#id_recipient_size").val());
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


function load_canvas_editor_template(id){

    var url = document.url_get_recipient_size;
    if(id){
        url = url+id;
    }

    $.ajax({
        url: url,
        type: 'GET',
        success: function(result) {
          if(result){
            update_resolution(result.width, result.height);
          }
        },
        error: function(xhr, resp, text) {
            console.log(xhr, resp, text);
        }
    });
}


$("#id_recipient_size").on("change", function(){
    load_canvas_editor_template($(this).val());
});


$("#savesgalabel").on('click', function(){
    load_data_form("personal");
    $("#sgaform").submit();
});


