let _canvases = [];
let state;
let undo = [];
let redo = [];

function save(index){
    redo = [];
    $('#redo').prop('disabled', true);
    if (state){
        undo.push(state);
        $('#undo').prop('disabled', false);
    }
    state = JSON.stringify(_canvases[index]);

}
function replay(playStack, saveStack, buttonsOn, buttonsOff, index){
    saveStack.push(state);
    state = playStack.pop();
    var on = $(buttonsOn);
    var off = $(buttonsOff);
    on.prop('disabled', true);
    off.prop('disabled', true);
    _canvases[index].clear();
    _canvases[index].loadFromJSON(state, function(){
        _canvases.renderAll();
        on.prop('disabled', false);
        if (playStack.length){
            off.prop('disabled',false);
        }
    });

}
(function( ) {
    let formdata = $("#sgaform").serializeArray();
    $(".templatepreview").each(function(index, element){
        $.post(element.dataset.href,formdata,function(data, status){
            let newcanvas = canvas_editor = new fabric.Canvas(element.id);

            let idUndo = "undo" + index;
            let idRedo = "redo" +  index;
            $(idUndo).click(function(){
                let index = $(idUndo).val();
                console.log(index);
                replay(undo,redo,'#redo',this, index);
            });
            $(idRedo).click(function(){
                console.log("redo");
                let index = $(idRedo).val();
                console.log(index);
                replay(redo,undo,'#undo',this, index);
            });
            _canvases.push(newcanvas);
            save( (index -1));
            newcanvas.loadFromJSON(data.object, function() {
                newcanvas.item(0).selectable = false;
                newcanvas['panning'] = false;
                newcanvas['onselected'] = false;
                newcanvas.on('mouse:wheel', function (opt) {
                     let delta = opt.e.deltaY;
                     let zoom = newcanvas.getZoom();
                     zoom = zoom + delta / 200;
                     if (zoom > 20) zoom = 20;
                     if (zoom < 0.01) zoom = 0.01;
                     newcanvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
                     opt.e.preventDefault();
                     opt.e.stopPropagation();
                 });
                newcanvas.on('mouse:up', function () {
                     newcanvas['panning'] = false;
                 });
                newcanvas.on('mouse:dblclick', function () {
                     if (!newcanvas['onselected']) {
                         newcanvas['panning'] = true;
                     }
                 });
                newcanvas.on('mouse:move', function (e) {
                     if (newcanvas['panning'] && e && e.e && !newcanvas['onselected']) {
                             var delta = new fabric.Point(e.e.movementX, e.e.movementY);
                             newcanvas.relativePan(delta);
                     }
                 });
                newcanvas.on('object:selected', function () {
                     newcanvas['onselected'] = true;
                     save(index);
                 });
                newcanvas.on('before:selection:cleared', function () {
                     newcanvas['onselected'] = false;
                 });
                newcanvas.on('object:modified', function () {
                    console.log("objeto modificado : " +  (index -1));
                     save(index);
                 });

                let canvas_container_preview = $(".canvas-container-preview");
                let height = canvas_container_preview.height();
                if (height < 400){
                height = 400;
                }
                let width = canvas_container_preview.width();
                if(width < 400 ){
                width = 400;
                }
         /*      newcanvas.setZoom(parseFloat(data.preview));*/
                newcanvas.setWidth(width);
                newcanvas.setHeight(height);
                newcanvas.renderAll();
                save(index);
            });
          });
    });
})();

$(document).ready(function(){
    $(".canvaspng").on('click', function(){
         let canvas =  _canvases[this.dataset.order];
         this.href=canvas.toDataURL({ format: 'png', quality: 0.8});

    });
    for (let x=0; x<_canvases.length; x++){
        let idUndo = "undo" + x;
        let idRedo = "redo" + x;
        console.log(idUndo, idRedo);
        $(idUndo).click(function(){
            let index = $(idUndo).val();
            console.log(index);
            replay(undo,redo,'#redo',this, index);
        });
        $(idRedo).click(function(){
            console.log("redo");
            let index = $(idRedo).val();
            console.log(index);
            replay(redo,undo,'#undo',this, index);
        });
    }
});

function get_canvas(pk){
    for(let canvas of _canvases){
        let id = canvas.lowerCanvasEl.id;
        if (id === "preview_" + pk.toString())
            return canvas;
     }
}

function get_as_pdf(pk){
    const canvas = get_canvas(pk);
    const json_data = JSON.stringify(canvas);
    $('#json_data').attr('value',json_data);
    document.download_pdf.submit();
}

