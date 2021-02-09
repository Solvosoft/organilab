let canvas;
let op;

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

function handleDragStart(e) {

       e.dataTransfer.setData("text", e.target.id);
       e.dataTransfer.setData("type", $(e.target).data('ftype'));

      if(e.target.title){
         e.dataTransfer.setData("label", e.target.title);
      }else{
        e.dataTransfer.setData("label", "{{"+e.target.id+"}}");
      }
}
function handleDragEnd(e) {
    console.log('handleDragEnd');
}
function save(index_local){
    canvas.redo = [];
    $('#redo').prop('disabled', true);
    if (canvas.state){
        canvas.undo.push(canvas.state);
        $('#undo').prop('disabled', false);
    }
    canvas.state = JSON.stringify(canvas.canv_obj);
    if ( window.localStorage.getItem(index_local)){
        window.localStorage.removeItem(index_local)
        window.localStorage.setItem(index_local, canvas.canv_obj)
    }
    else{
        window.localStorage.setItem(index_local, canvas.canv_obj)
    }

}
function replay(playStack, saveStack, buttonsOn, buttonsOff, index){
    if(saveStack =='redo'){
        canvas.redo.push(canvas.state);
        if(canvas.undo.length >= 2)
        {
            canvas.state = canvas.undo.pop();
        }

    }
    else if (saveStack == 'undo'){
        canvas.undo.push(canvas.state);
        if(canvas.redo.length >= 1)
        {
            canvas.state = canvas.redo.pop();
        }
    }
    let on = $(buttonsOn);
    let off = $(buttonsOff);
    on.prop('disabled', true);
    off.prop('disabled', true);

    canvas.canv_obj.clear();
    canvas.canv_obj.loadFromJSON(JSON.parse(canvas.state), function(){
        canvas.canv_obj.renderAll();
        on.prop('disabled', false);
        if(playStack == 'undo'){
            if (canvas.undo.length>=1){
                off.prop('disabled',false);
            }
        }
        else{
            if (canvas.redo.length>=1){
                off.prop('disabled',false);
            }
        }
    });

}

$(document).ready(function () {
    let formdata = $("#sgaform").serializeArray();

    $(".templatepreview").each(function(index, element){
        $.post(element.dataset.href,formdata,function(data, status){
            let json_object = {};
            let newcanvas = new fabric.Canvas(element.id);
            op=newcanvas;
            newcanvas.renderAll();

             canvas = new CanvasHandler(JSON.stringify(newcanvas), newcanvas);

            $(".img").each((i,e)=>{
             fabric.Image.fromURL(e.value, function (img) {
             img.scaleToWidth(100);
             img.scaleToHeight(100);
             img.set("top", 0);
             img.set("left", 0);
             img.set("centeredScaling", true);
             canvas.canv_obj.add(img)
         });
         });
            canvas.canv_obj.renderAll();

       $(".genericitem").each(function (i, obj) {
         obj.addEventListener('dragstart', handleDragStart, false);
         obj.addEventListener('dragend', handleDragEnd, false);
       });
        let container = document.querySelector(".canvas-container-preview");

       container.addEventListener('dragenter', handleDragEnter, false);
       container.addEventListener('dragover', handleDragOver, false);
       container.addEventListener('dragleave', handleDragLeave, false);
       container.addEventListener('drop', handleDrop, false);

            json_object = data.object;
        //    data.object.objects.forEach((e,i)=>{
          //      console.log(e)
           // })
            canvas.canv_obj.loadFromJSON(data.object, function() {
                let view= $(".canvas-container-preview");
                upWidth();
                //setTop();
                updateTop();
             //   setWidth()
                canvas.canv_obj.item(0).selectable = false;
                canvas.canv_obj['panning'] = false;
                canvas.canv_obj['onselected'] = false;
                canvas.canv_obj.on('mouse:wheel', function (opt) {
                    let delta = opt.e.deltaY;
                    let zoom = canvas.canv_obj.getZoom();
                    zoom = zoom + delta / 200;
                    if (zoom > 20) zoom = 20;
                    if (zoom < 0.01) zoom = 0.01;
                    canvas.canv_obj.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
                    opt.e.preventDefault();
                    opt.e.stopPropagation();
                 });
                canvas.canv_obj.on('mouse:up', function () {
                     canvas.canv_obj['panning'] = false;
                 });
                canvas.canv_obj.on('mouse:dblclick', function () {
                     if (!canvas.canv_obj['onselected']) {
                         canvas.canv_obj['panning'] = true;
                     }
                 });
                canvas.canv_obj.on('mouse:move', function (e) {
                     if (canvas.canv_obj['panning'] && e && e.e && !canvas.canv_obj['onselected']) {
                             var delta = new fabric.Point(e.e.movementX, e.e.movementY);
                             canvas.canv_obj.relativePan(delta);
                     }
                 });
                canvas.canv_obj.on('object:selected', function () {
                     canvas.canv_obj['onselected'] = true;
                 });
                canvas.canv_obj.on('before:selection:cleared', function () {
                     canvas.canv_obj['onselected'] = false;
                 });
                canvas.canv_obj.on('object:modified', function (e) {
                       save(element.id);
                 });
                canvas.canv_obj.on('object:scaling', function(e) {
                    if (e.target.type=='textbox') {
                         let index=getCanvas(e.target.text);
                         let item=canvas.canv_obj.getObjects()[index];
                         canvas.canv_obj.getObjects()[index].fontSize=(e.target.fontSize*e.target.scaleX).toFixed(0x);

                    }
                   });
                let height = view.height();
                if (height < 400){
                    height = 400;
                }
                let width = view.width();
                if(width < 400 ){
                    width = 400;
                }
                canvas.canv_obj.setWidth(width);
                canvas.canv_obj.setHeight(height);
                canvas.canv_obj.renderAll();

                save(element.id);
            });
          });
    });
});

function printns(){
    canvas.canv_obj.getObjects().forEach((item,i)=>{
        console.log(item.top);
    });
}

// Aumenta el ancho
function upWidth(){
let w=0;
       canvas.canv_obj.getObjects().forEach((item,i)=>{
         canvas.canv_obj.getObjects().forEach((other,e)=>{
               if(item.type=='textbox'&&i!=e){
               if(item.left>700&&w==0){
                        canvas.canv_obj.getObjects()[i].width*=1.5;
                        w++;
                        }
                }
       });
       });
	}
function updateTop(){
       canvas.canv_obj.getObjects().forEach((item,i)=>{
        if(item.top+item.height>=1500 && item.type=='textbox'){
            let aux=(item.top+item.height)-1400

            canvas.canv_obj.getObjects()[i].scaleY=aux/1400;
            canvas.canv_obj.getObjects()[i].fontSize=item.fontSize*(aux/1400);
            console.log(aux/1500)
        }
        });
}
function getCanvas(text){
    let position=-1;
       canvas.canv_obj.getObjects().forEach((item,i)=>{
        if(item.type=="textbox"){
              if(text=item.text){
            position=i
            }
        }
        });
        return position;
}

function setWidth(){
        let canva=canvas.canv_obj.getObjects();
        let res=canvas.canv_obj.getObjects();
       for(let x in canvas.canv_obj.getObjects()){
         for(let y in canvas.canv_obj.getObjects()){
            if(canvas[x].type!='images'){
            if((canva[x].left+canva[x].width)<res[y].left&&
            Math.abs(canva[x].left-res[y].left)<500&&
            canva[x].top<(res[y].top+res[y].height)&&
            x!=y){
               // console.log(canva[x].text,' ',i)
               }
               }

     	}
     	i++;
	}
	}

function discard(){
       for(let x in canvas.canv_obj.getObjects()){
        let a=canvas.canv_obj.getObjects()[x];
         for(let y in canvas.canv_obj.getObjects()){
            let b=canvas.canv_obj.getObjects()[y];
             if(a.type=="textbox" && x!=y && a.width+a.left>b.left && b.top+b.height>a.top&& (a.width+a.left<1200)){
                canvas.canv_obj.getObjects()[x].width*=0.9;
        }
        }
}
}

function setTop(){

    let x=0;
    canvas.canv_obj.getObjects().forEach((item,i)=>{
        canvas.canv_obj.getObjects().forEach((other,e)=>{
        if(item.top+item.height> other.top &&
        item.top<other.top &&
        item.type!='image'&&
        other.type!='image'&&
        Math.abs(item.top-other.top)>20&&
        Math.abs(item.left-other.left)<200&&
        i!=e){
        canvas.canv_obj.getObjects()[x].top-=item.top>0?50:0;
     }
     });
     x++;
    });
}


function danger_color(data){
   let result=$('#colorfill').val();
    if(data==='Peligro' || data==="{{warningword}}"||data==="atención"){
       result="red";
       }
    return result;
}
 function get_position_x(e){
     return e.layerX;
 }
 function get_position_y(e){
     return e.layerY;
 }

 function get_fabric_element(e){
     let data = e.dataTransfer.getData("label");
     let ftype = e.dataTransfer.getData('type');
     if(ftype == "textbox"){
         let name_label = new fabric.Textbox(data, {
             id:'op',
             width: 180,
             height: 20,
             left: get_position_x(e),
             top: get_position_y(e),
             fontSize: $("#text-font-size").val(),
             fill: $('#colorfill').val(),
             textAlign: $('#textalign').val(),
             fixedWidth: 160,
             fontFamily: 'Helvetica',
             objectCaching: false,
             renderOnAddRemove: false,
         });
         canvas.canv_obj.add(name_label);
     }else if (ftype == "itext"){
        let danger_count=getList(data);
         let name_label = new fabric.IText(data, {
             width: 280,
             left: get_position_x(e),
             top: get_position_y(e),
             fontSize: $("#text-font-size").val(),
             fontFamily: $('#fontfamily').val(),
             textAlign: $('#textalign').val(),
             fill: danger_color(data),
             fixedWidth: 280,
             objectCaching: false,
             renderOnAddRemove: false,
         });
         canvas.canv_obj.add(name_label);

     }else if(ftype == "image") {
         fabric.Image.fromURL(data, function (img) {
             img.scaleToWidth(100);
             img.scaleToHeight(100);
             img.set("top", get_position_x(e));
             img.set("left", get_position_y(e));
             img.set("centeredScaling", true);
             canvas.canv_obj.add(img);
         });
      }else if (ftype == "danger-itext"){
        let danger=getList(data);
         if(danger.peligro==0 && danger.atencion==0){
         let name_label = new fabric.IText(data, {
             width: 280,
             left: get_position_x(e),
             top: get_position_y(e),
             fontSize: $("#text-font-size").val(),
             fontFamily: $('#fontfamily').val(),
             textAlign: $('#textalign').val(),
             fill: danger_color(data),
             fixedWidth: 280,
             objectCaching: false,
             renderOnAddRemove: false,
         });
         canvas.canv_obj.add(name_label);
        }else{
              $("#messages").css('display','block');
           setTimeout(function() {
              $("#messages").css('display','none');
              }, 4000);
        }
     }
 }


 function handleDragOver(e) {
     if (e.preventDefault) {
         e.preventDefault();
     }
      e.dataTransfer.dropEffect = 'copy';
     return false;
 }

 function handleDragEnter(e) {
     this.classList.add('over');
 }

 function handleDragLeave(e) {
     this.classList.remove('over');
 }

 function handleDrop(e) {
     e = e || window.event;
     if (e.preventDefault) {
       e.preventDefault();
     }
     if (e.stopPropagation) {
         e.stopPropagation();
     }
     get_fabric_element(e);
     return false;
}


function undoFunction(ele){
    replay('undo','redo','#redo','#undo', ele.dataset.order);
}

function redoFunction(ele){
    replay('redo','undo','#undo','#redo', ele.dataset.order );
}

$(document).ready(function(){
    $(".canvaspng").on('click', function(){
         let canva =  canvas;
         this.href=canva.toDataURL({ format: 'png', quality: 0.8});
    });
});

function get_canvas(pk){
        let id = canvas.canv_obj.lowerCanvasEl.id;
        if (id === "preview_" + pk.toString())
            return canvas.canv_obj;
     }


function get_as_pdf(pk){
    const canvas = get_canvas(pk);
    const json_data = JSON.stringify(canvas);

    $('#json_data').attr('value',json_data);
    $('#template_sga_pk').attr('value',pk)

    document.download_pdf.submit();
}

function deleteSelectedObj(){
    canvas.canv_obj.remove(canvas.canv_obj.getActiveObject());
}

function getList(data){
   let x= canvas.canv_obj.getObjects();
   let p=0;
   let a=0;
   x.forEach( function(item,i){
        if(item.text=='Peligro'){
            p++;
           }
        if(item.text=="atención"){
            a++;
        }
   });
   return {"peligro":p,"atencion":a};
}