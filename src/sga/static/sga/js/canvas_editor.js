$(window).load(function(){
    var urlParams = new URLSearchParams(window.location.search);
    var instance = urlParams.get('instance');
    var svgContent = $("#id_json_representation").val();

    if(instance && svgContent){
        svgEditor.svgCanvas.clear();
        try {
            svgEditor.loadSvgString(svgContent);
        } catch (err) {
        if (err.name !== 'AbortError') {
            console.log(err);
        }
      }
    }else{
        if(document.clean_canvas_editor){
            svgEditor.svgCanvas.clear();
        }
    }
    svgEditor.updateCanvas();
});


$("#editor_save").on('click', function(){
    var svgText = svgEditor.svgCanvas.getSvgString();
    $("#id_json_representation").val(svgText);

    var svgElement = document.getElementById('svgcontent');
    var svgString = new XMLSerializer().serializeToString(svgElement);
    var decoded = unescape(encodeURIComponent(svgString));
    var base64 = btoa(decoded);
     $("#id_preview").val(base64);

     $("#sgaform").submit();
});