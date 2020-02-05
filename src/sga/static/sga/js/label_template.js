let _canvases = [];


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
    _canvases[index_temp].redo = [];
    $('#redo').prop('disabled', true);
    if (_canvases[index_temp].state){
        _canvases[index_temp].undo.push(_canvases[index_temp].state);
        $('#undo').prop('disabled', false);
    }
    _canvases[index_temp].state = JSON.stringify(_canvases[index_temp].canv_obj);
    if ( window.localStorage.getItem(index_local)){
        window.localStorage.removeItem(index_local)
        window.localStorage.setItem(index_local, _canvases[index_temp].canv_obj)
    }
    else{
        window.localStorage.setItem(index_local, _canvases[index_temp].canv_obj)
    }

}
function replay(playStack, saveStack, buttonsOn, buttonsOff, index){
    if(saveStack =='redo'){
        _canvases[index].redo.push(_canvases[index].state);
        if(_canvases[index].undo.length >= 2)
        {
            _canvases[index].state = _canvases[index].undo.pop();
        }

    }
    else if (saveStack == 'undo'){
        _canvases[index].undo.push(_canvases[index].state);
        if(_canvases[index].redo.length >= 1)
        {
            _canvases[index].state = _canvases[index].redo.pop();
        }
    }
    let on = $(buttonsOn);
    let off = $(buttonsOff);
    on.prop('disabled', true);
    off.prop('disabled', true);

    _canvases[index].canv_obj.clear();
    _canvases[index].canv_obj.loadFromJSON(JSON.parse(_canvases[index].state), function(){
        _canvases[index].canv_obj.renderAll();
        on.prop('disabled', false);
        if(playStack == 'undo'){
            if (_canvases[index].undo.length>=1){
                off.prop('disabled',false);
            }
        }
        else{
            if (_canvases[index].redo.length>=1){
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
            let handler = new CanvasHandler(JSON.stringify(newcanvas), newcanvas);
            _canvases.push(handler);
            let index_temp = _canvases.length - 1;
           /* if( window.localStorage.getItem(element.id)){
                temp = window.localStorage.getItem(element.id);
                json_object = JSON.parse(temp)
            }
            else{*/
            json_object = data.object;
           // }
           console.log(data.object);
           console.log('--------------------');
            _canvases[index_temp].canv_obj.loadFromJSON(data.object, function() {
                _canvases[index_temp].canv_obj.item(0).selectable = false;
                _canvases[index_temp].canv_obj['panning'] = false;
                _canvases[index_temp].canv_obj['onselected'] = false;
                _canvases[index_temp].canv_obj.on('mouse:wheel', function (opt) {
                    let delta = opt.e.deltaY;
                    let zoom = _canvases[index_temp].canv_obj.getZoom();
                    zoom = zoom + delta / 200;
                    if (zoom > 20) zoom = 20;
                    if (zoom < 0.01) zoom = 0.01;
                    _canvases[index_temp].canv_obj.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
                    opt.e.preventDefault();
                    opt.e.stopPropagation();
                 });
                _canvases[index_temp].canv_obj.on('mouse:up', function () {
                     _canvases[index_temp].canv_obj['panning'] = false;
                 });
                _canvases[index_temp].canv_obj.on('mouse:dblclick', function () {
                     if (!_canvases[index_temp].canv_obj['onselected']) {
                         _canvases[index_temp].canv_obj['panning'] = true;
                     }
                 });
                _canvases[index_temp].canv_obj.on('mouse:move', function (e) {
                     if (_canvases[index_temp].canv_obj['panning'] && e && e.e && !_canvases[index_temp].canv_obj['onselected']) {
                             var delta = new fabric.Point(e.e.movementX, e.e.movementY);
                             _canvases[index_temp].canv_obj.relativePan(delta);
                     }
                 });
                _canvases[index_temp].canv_obj.on('object:selected', function () {
                     _canvases[index_temp].canv_obj['onselected'] = true;
                 });
                _canvases[index_temp].canv_obj.on('before:selection:cleared', function () {
                     _canvases[index_temp].canv_obj['onselected'] = false;
                 });
                _canvases[index_temp].canv_obj.on('object:modified', function () {
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
                _canvases[index_temp].canv_obj.setWidth(width);
                _canvases[index_temp].canv_obj.setHeight(height);
                _canvases[index_temp].canv_obj.renderAll();
                save(index_temp,element.id);
            });
          });
    });
})();

function undoFunction(ele){
    replay('undo','redo','#redo','#undo', ele.dataset.pk - 1);
}

function redoFunction(ele){
    replay('redo','undo','#undo','#redo', ele.dataset.pk - 1);
}

$(document).ready(function(){
    $(".canvaspng").on('click', function(){
         let canvas =  _canvases[this.dataset.order];
         this.href=canvas.toDataURL({ format: 'png', quality: 0.8});
    });
});

function get_canvas(pk){
    for(let canvas of _canvases){
        let id = canvas.canv_obj.lowerCanvasEl.id;
        if (id === "preview_" + pk.toString())
            return canvas.canv_obj;
     }
}

function get_as_pdf(pk){
    const canvas = get_canvas(pk);
    const json_data = JSON.stringify(canvas);
    $('#json_data').attr('value',json_data);
    document.download_pdf.submit();
}

