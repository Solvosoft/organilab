function update_resolution(width, height){
    var value = 37.795275591; //CM VALUE IN PIXELES
    svgEditor.svgCanvas.setResolution(width*value, height*value, 1);
    svgEditor.updateCanvas();
    svgEditor.svgCanvas.selectAllInCurrentLayer();
}

$(window).load(function(){

    let elem = document.querySelector('#canvas_editor');
    let rect = elem.getBoundingClientRect();

    var urlParams = new URLSearchParams(window.location.search);
    var instance = urlParams.get('instance');
    var svg_content = $("#id_json_representation").val();

    if(instance && svg_content){
        svgEditor.svgCanvas.clear();
        try {
            svgEditor.loadSvgString(svg_content);
            update_resolution(document.width, document.height);
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


$("#editor_save").on('click', function(){
    var svg_text = svgEditor.svgCanvas.getSvgString();
    $("#id_json_representation").val(svg_text);

    var svg_element = document.getElementById('svgcontent');
    var svg_string = new XMLSerializer().serializeToString(svg_element);
    var decoded = unescape(encodeURIComponent(svg_string));
    var base64 = btoa(decoded);
     $("#id_preview").val(base64);

     $("#sgaform").submit();
});



$("#id_recipient_size").on("change", function(){
    var id = $(this).val();
    var url = document.url_get_recipient_size;
    if(id){
        url = url.replace('0', id);
    }

    $.ajax({
        url: url,
        type: 'GET',
        success: function(result) {
          if(result.size){
            update_resolution(result.size.width, result.size.height);
          }
        },
        error: function(xhr, resp, text) {
            console.log(xhr, resp, text);
        }

    });

});