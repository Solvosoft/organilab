let _canvases;


class CanvasHandler
{
    constructor(state, canv_obj)
    {
        this.canv_obj = canv_obj;
        this.state = state;
        this.undo = [];
        this.redo = [];
    }
}

function save(index_temp, index_local){
    _canvases.redo = [];
    $('#redo').prop('disabled', true);
    if (_canvases.state){
        _canvases.undo.push(_canvases.state);
        $('#undo').prop('disabled', false);
    }
    _canvases.state = JSON.stringify(_canvases.canv_obj);
    if ( window.localStorage.getItem(index_local)){
        window.localStorage.removeItem(index_local)
        window.localStorage.setItem(index_local, _canvases.canv_obj)
    }
    else{
        window.localStorage.setItem(index_local, _canvases.canv_obj)
    }

}
function replay(playStack, saveStack, buttonsOn, buttonsOff, index){
    if(saveStack =='redo'){
        _canvases.redo.push(_canvases.state);
        if(_canvases.undo.length >= 2)
        {
            _canvases.state = _canvases.undo.pop();
        }

    }
    else if (saveStack == 'undo'){
        _canvases.undo.push(_canvases.state);
        if(_canvases.redo.length >= 1)
        {
            _canvases.state = _canvases.redo.pop();
        }
    }
    let on = $(buttonsOn);
    let off = $(buttonsOff);
    on.prop('disabled', true);
    off.prop('disabled', true);

    _canvases.canv_obj.clear();
    _canvases.canv_obj.loadFromJSON(JSON.parse(_canvases.state), function(){
        _canvases.canv_obj.renderAll();
        on.prop('disabled', false);
        if(playStack == 'undo'){
            if (_canvases.undo.length>=1){
                off.prop('disabled',false);
            }
        }
        else{
            if (_canvases.redo.length>=1){
                off.prop('disabled',false);
            }
        }
    });

}
(function( ) {
    let formdata = $("#sgaform").serializeArray();

    $(".templatepreview").each(function(index, element){
        $.post(element.dataset.href,formdata,function(data, status){
            let json_object = {};
            let newcanvas = new fabric.Canvas(element.id);
            $(".img").each((i,e)=>{
            fabric.Image.fromURL(e.value, function (img) {
             img.scaleToWidth(100);
             img.scaleToHeight(100);
             img.set("top", 0);
             img.set("left", 0);
             img.set("centeredScaling", true);
             newcanvas.add(img);
         });
         });
            newcanvas.renderAll();
            let handler = new CanvasHandler(JSON.stringify(newcanvas), newcanvas);

            _canvases=handler;
            let index_temp = _canvases.length - 1;
           /* if( window.localStorage.getItem(element.id)){
                temp = window.localStorage.getItem(element.id);
                json_object = JSON.parse(temp)
            }
            else{*/
            json_object = data.object;
           // }
            _canvases.canv_obj.loadFromJSON(data.object, function() {
                _canvases.canv_obj.item(0).selectable = false;
                _canvases.canv_obj['panning'] = false;
                _canvases.canv_obj['onselected'] = false;
                _canvases.canv_obj.on('mouse:wheel', function (opt) {
                    let delta = opt.e.deltaY;
                    let zoom = _canvases.canv_obj.getZoom();
                    zoom = zoom + delta / 200;
                    if (zoom > 20) zoom = 20;
                    if (zoom < 0.01) zoom = 0.01;
                    _canvases.canv_obj.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
                    opt.e.preventDefault();
                    opt.e.stopPropagation();
                 });
                _canvases.canv_obj.on('mouse:up', function () {
                     _canvases.canv_obj['panning'] = false;
                 });
                _canvases.canv_obj.on('mouse:dblclick', function () {
                     if (!_canvases.canv_obj['onselected']) {
                         _canvases.canv_obj['panning'] = true;
                     }
                 });
                _canvases.canv_obj.on('mouse:move', function (e) {
                     if (_canvases.canv_obj['panning'] && e && e.e && !_canvases.canv_obj['onselected']) {
                             var delta = new fabric.Point(e.e.movementX, e.e.movementY);
                             _canvases.canv_obj.relativePan(delta);
                     }
                 });
                _canvases.canv_obj.on('object:selected', function () {
                     _canvases.canv_obj['onselected'] = true;
                 });
                _canvases.canv_obj.on('before:selection:cleared', function () {
                     _canvases.canv_obj['onselected'] = false;
                 });
                _canvases.canv_obj.on('object:modified', function (e) {
                       save(index_temp,element.id);
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
                _canvases.canv_obj.setWidth(width);
                _canvases.canv_obj.setHeight(height);
                _canvases.canv_obj.renderAll();

                save(index_temp,element.id);
            });
          });
    });
})();

function undoFunction(ele){
    replay('undo','redo','#redo','#undo', ele.dataset.order);
}

function redoFunction(ele){
    replay('redo','undo','#undo','#redo', ele.dataset.order );
}

$(document).ready(function(){
    $(".canvaspng").on('click', function(){
         let canvas =  _canvases;
         this.href=canvas.toDataURL({ format: 'png', quality: 0.8});
    });
});

function get_canvas(pk){
        let id = _canvases.canv_obj.lowerCanvasEl.id;
        if (id === "preview_" + pk.toString())
            return _canvases.canv_obj;
     }


function get_as_pdf(pk){
    const canvas = get_canvas(pk);
    const json_data = JSON.stringify(canvas);

    $('#json_data').attr('value',json_data);
    $('#template_sga_pk').attr('value',pk)

    document.download_pdf.submit();
}

