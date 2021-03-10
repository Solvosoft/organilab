let canvas;
let option="";

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
         enableControls();
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

function templateList(data){
    let templates=document.querySelector('#id_templates')
    templates.innerHTML='';
    let y= JSON.parse(data);

    if(y.length>0){
    y.forEach(e=>{
       templates.innerHTML+=`<option value=${e.id}>${e.name}</option>`;
    });
    }
}

function initElements(){

   $("#text-font-size").on("change",function(){
      if(option.type=='textbox'){
         let aux=getCanvas(option.text);
         canvas.canv_obj.getObjects()[aux].fontSize=$(this).val();
         canvas.canv_obj.renderAll();
       }
      });

    $('#textalign').on("change",function(){
      if(option.type=='textbox'){
         let aux=getCanvas(option.text);
         canvas.canv_obj.getObjects()[aux].textAlign=$(this).val();
         canvas.canv_obj.renderAll();
       }
      });

    $('#fontfamily').on("change",function(){
       if(option.type=='textbox' || option.type=='i-text'){
          let aux=getCanvas(option.text);
          canvas.canv_obj.getObjects()[aux].fontFamily=$(this).val();
          canvas.canv_obj.renderAll();
       }
      });

     $('#colorstroke').on("change",function(){
       if(option.type=='textbox' || option.type=='i-text'){
          let aux=getCanvas(option.text);
          canvas.canv_obj.getObjects()[aux].borderColor=$(this).val();
          canvas.canv_obj.renderAll();
      }
     });

     $('#colorfill').on("change",function(){
       if(option.type=='textbox' || option.type=='i-text'){
          let aux=getCanvas(option.text);
          canvas.canv_obj.getObjects()[aux].fill=$(this).val();
          canvas.canv_obj.renderAll();
        }
       });

     $('#text-bg-color').on("change",function(){
       if(option.type=='textbox' || option.type=='i-text'){
           let aux=getCanvas(option.text);
            canvas.canv_obj.getObjects()[aux].backgroundColor=$(this).val();
            canvas.canv_obj.renderAll();
       }
     });
     set_color_value();
     let recipient=$('#id_recipients');
  let pk=$(recipient).find('option:selected');
    if(pk.index()>0){
        $.ajax({
        url: 'sga/getList/',
        type:'POST',
        data: {'pk':pk.val()},
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        success: function (data) {
        templateList(data);
      }
        });
        }

    $('#id_recipients').change(function(){
    let pk=$(this).find('option:selected').val();
     $.ajax({
        url: 'sga/getList/',
        type:'POST',
        data: {pk},
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        success: function (data) {
        templateList(data);
      }
        });
});
}
function set_color_value(){

     $('#colorstroke').val('#ffffff');

     $('#colorfill').val('#000000');

     $('#text-bg-color').val('#ffffff');
}

$(document).ready(function () {
    let formdata = $("#sgaform").serializeArray();

    $(".templatepreview").each(function(index, element){
        $.post(element.dataset.href,formdata,function(data, status){
            let json_object = {};
            let newcanvas = new fabric.Canvas(element.id);
            newcanvas.renderAll();

             canvas = new CanvasHandler(JSON.stringify(newcanvas), newcanvas);

            canvas.canv_obj.renderAll();
              canvasActions(data,element);
          });
    });
    $('#update_form').submit((e)=>{
        $('#representation').val(JSON.stringify(canvas.canv_obj));
    });
});

function canvasActions(data,element){
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
            canvas.canv_obj.loadFromJSON(data.object, function() {
                let view= $(".canvas-container-preview");


                updateTop();
                setTop();
                enableControls();

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
                canvas.canv_obj.on('mouse:up', function (e) {
                     canvas.canv_obj['panning'] = false;
                    if(e.target!=undefined&&e.target.type!='rect'&&e.target.type!='image'){
                     $('#text-font-size').val(e.target.fontSize)
                        option=e.target;
                     }else{
                     $('#text-font-size').val('20');
                     }
                 });
                   initElements();

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

                canvas.canv_obj.on('object:selected', function (e) {

                     canvas.canv_obj['onselected'] = true;
                 });

                canvas.canv_obj.on('before:selection:cleared', function () {
                     canvas.canv_obj['onselected'] = false;
                 });

                canvas.canv_obj.on('object:modified', function (e) {
                     if (e.target.type=='textbox') {
                         e.target.scaleX=1;
                        }
                       save(element.id);
                 });

                canvas.canv_obj.on('object:scaling', function(e) {
                     if (e.target.type=='textbox') {
                         let index=getCanvas(e.target.text);
                         e.target.fontSize*=e.target.scaleX;
                         $('#text-font-size').val(e.target.fontSize)
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

}
function enableControls(){

    canvas.canv_obj.getObjects().forEach((element,i)=>{
        element.setControlsVisibility({
    bl: true,br: true, tl: true, tr: true, mt: false,mb: false,
});
    });
}

function getPositionX(data){
    let aux=[];
    canvas.canv_obj.getObjects().forEach((item,i)=>{
         if(data.left+data.width<item.left&&(data.top<item.top||data.top-30<item.top)){
           aux.push(item.left);
           }
    });

    let x=aux.sort((a,b) => a-b);
    return x;
}

function getPositionY(data){
    let aux=[];
    canvas.canv_obj.getObjects().forEach((item,i)=>{
         if(Math.abs(data.left-item.left)<20&&
         (data.top<item.top)&&
         (data.top+data.height)>item.top){
           aux.push(item.top);

           }
    });

    let x=aux.sort((a,b) => a-b);
    return x;
}

// Aumenta el ancho
function upWidth(){
       canvas.canv_obj.getObjects().forEach((item,i)=>{
               if(item.type=='textbox'){
                   if(item.left<700){
                       let position=getPositionX(item);
                       canvas.canv_obj.getObjects()[i].width=position!=undefined?position[0]:item.width;
                     }else{
                       canvas.canv_obj.getObjects()[i].width+=(1400-(item.left+item.width));

                       }
                }
       });
	}
function updateTop(){
       canvas.canv_obj.getObjects().forEach((item,i)=>{
        if(item.top+item.height>=1300 && item.type=='textbox'){
            let aux=1300-item.top;
            canvas.canv_obj.getObjects()[i].fontSize*=aux/1300;
            canvas.canv_obj.getObjects()[i].height=aux;

        }
        });
}
function setTop(){
       canvas.canv_obj.getObjects().forEach((item,i)=>{
               if(item.type=='textbox'){
                       let position=getPositionY(item);
                        if(position[0]!=undefined){
                        let res=canvas.canv_obj.getObjects()[i];
                        let aux=(res.top+res.height)-position[0];
                        aux=(aux*2<position[0])?(res.top+res.height-aux)*0.8:aux*0.7
                        canvas.canv_obj.getObjects()[i].fontSize*=aux/position[0];
            }

                }
       });
	}


function getCanvas(text){
    let position=-1;
       canvas.canv_obj.getObjects().forEach((item,i)=>{
        if(item.type=="textbox" || item.type=="i-text"){
              if(text==item.text){
            position=i
            }
        }
        });
        return position;
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
             width: 180,
             height: 20,
             left: get_position_x(e),
             top: get_position_y(e),
             fontSize: $("#text-font-size").val(),
             fill: $('#colorfill').val(),
             textAlign: $('#textalign').val(),
             fixedWidth: 160,
             fontFamily: $('#fontfamily').val(),
             lineHeight:1,
             backgroundColor:$('#text-bg-color').val()!='#ffffff'?$('#text-bg-color').val():'transparent',
             borderColor:$('#colorstroke').val(),
             objectCaching: false,
             renderOnAddRemove: false,
         });
            name_label.setControlsVisibility({
            bl: true,br: true, tl: true, tr: true, mt: false,mb: false,
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
             borderColor:$('#colorstroke').val(),
             backgroundColor:$('#text-bg-color').val(),
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



function get_as_pdf(pk){
    const json_data = JSON.stringify(canvas.canv_obj);

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

//

$('#personal').submit((e)=>{
    $('#json_representation').attr('value',JSON.stringify(canvas.canv_obj));
    $('#sizes').attr('value',$('#id_recipients').val());
})

$('#id_prudence_advice').change(function(){

    let pk=$(this).find('option:selected').val();
    $.ajax({
        url: 'sga/prudence/',
        type:'POST',
        data: {pk},
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        success: function (message) {
        if($('.prudence_message').length==0){
        $("#id_prudence_advice").parent().append(create_container(message,'prudence_message'));
        }else{
        $('.prudence_message').find('p').text(message);
        }
      }
        });
        });

$('#id_danger_indication').change(function(){
    let pk=$(this).find('option:selected').val();
    $.ajax({
        url: 'sga/get_danger_indication/',
        type:'POST',
        data: {pk},
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        success: function (message) {
        if($('.danger_message').length==0){
        $("#id_danger_indication").parent().append(create_container(message,'danger_message'));
        }else{
        $('.danger_message').find('p').text(message);
        }
      }
        });
        });
function create_container(message,classname){
    let div= document.createElement('div')
    div.innerHTML=`<span class="delete_message">x</span>`;
    div.classList.add(classname);
    div.append(create_message(message));

    return div;
 }
 function create_message(message){
    let textbox= document.createElement('p');
    textbox.classList.add('selects');
    textbox.textContent=message;
    textbox.setAttribute('draggable', 'True');
    textbox.setAttribute('data-ftype',"textbox")
    textbox.setAttribute('title',message);
    textbox.addEventListener('dragstart', handleDragStart, false);
    textbox.addEventListener('dragend', handleDragEnd, false);
 return textbox;
 }

 $(document).on('click','.delete_message',function(){
    $(this).parent().remove();

});