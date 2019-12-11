(function( ) {
    _canvases = [];
    var formdata = $("#sgaform").serializeArray();
    $(".templatepreview").each(function(index, element){
        $.post(element.dataset.href,
          formdata,
          function(data, status){
             var newcanvas = canvas_editor = new fabric.Canvas(element.id);
             _canvases.push(newcanvas);
               newcanvas.loadFromJSON(data.object, function() {
               newcanvas.on('mouse:wheel', function (opt) {
                    var delta = opt.e.deltaY;
                    var zoom = newcanvas.getZoom();
                    zoom = zoom + delta / 200;
                    if (zoom > 20) zoom = 20;
                    if (zoom < 0.01) zoom = 0.01;
                    newcanvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
                    opt.e.preventDefault();
                    opt.e.stopPropagation();
                });

                 var height = $(".canvas-container-preview").height();
                    if (height < 400){
                        height = 400;
                    }
                    var width = $(".canvas-container-preview").width();
                    if(width < 400 ){
                        width = 400;
                    }
         /*      newcanvas.setZoom(parseFloat(data.preview));*/
               newcanvas.setWidth(width);
               newcanvas.setHeight(height);

               newcanvas.renderAll();
            });
          });
    });
})();

function saveImage(canvas) {
    this.href =

    this.download = 'label.png'
}

$(document).ready(function(){
    $(".canvaspng").on('click', function(){
         var canvas =  _canvases[this.dataset.order];
         this.href=canvas.toDataURL({ format: 'png', quality: 0.8});

    });

});