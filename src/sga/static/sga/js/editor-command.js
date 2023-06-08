$("#editor_save").on('click', function(e){
    const event = new CustomEvent("serializeall", { detail: $("#id_json_representation")[0] });
    const savepngevent = new CustomEvent("savepng", { detail:
           {callback: data =>{ $("#id_preview").val(data); $("#formeditor").submit();} ,
           width: 6,
           height: 8
          }
    });
    let canvas = $("#editoriframe").contents().find("#canvas")[0];
    canvas.dispatchEvent(event);
    canvas.dispatchEvent(savepngevent);
});

$("#editoriframe").ready(function(){
    let canvas = $("#editoriframe").contents().find("#canvas")[0];
    if(json_representation !== undefined && json_representation.length > 0){
    const event = new CustomEvent("loadjson", { detail: {data: JSON.parse(json_representation), dontClear: false}});
    canvas.dispatchEvent(event);
    }

});
