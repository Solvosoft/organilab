var pks = [];
var shelfs_pk= []

function do_sortable(){
	  $("ul.sortableself").sortable({group: 'nested',
	        //cancel: ".ui-state-disabled",
	        items: "li:not(.ui-state-disabled)"
	  });
}

function addRow() {
	sk=$("<tr> </tr>");
	if($('#mytab tr:last td').length>0){
		$('#mytab tr:last td').each(function(i, e){
			var inp = "<td>"+$("#addshelfproto").html()+"</td>";
			inp=inp.replace(/ROW/g, ""+document.numberRow);
			inp=inp.replace(/COL/g, ""+i);
			sk.append(inp);
		});
	} else {
		var inp = "<td>"+$("#addshelfproto").html()+"</td>";
		inp=inp.replace(/ROW/g, ""+document.numberRow);
		inp=inp.replace(/COL/g, ""+document.numberCol);	
		sk.append(inp);
		document.numberCol++;
	}
	$('#mytab').append(sk);
	document.numberRow++;
	do_sortable();
}

function addColumn() {
	if($('#mytab tr').length>0){
		$('#mytab tr').each(function(i, e){
			var inp = "<td>"+$("#addshelfproto").html()+"</td>";
			inp=inp.replace(/ROW/g, ""+i);
			inp=inp.replace(/COL/g, ""+document.numberCol);	
			$(e).append(inp);
		});			
	}else{
		var inp = "<td>"+$("#addshelfproto").html()+"</td>";
		inp=inp.replace(/ROW/g, ""+document.numberRow);
		inp=inp.replace(/COL/g, ""+document.numberCol);		
		$('#mytab').append("<tr>"+inp+"</tr>");	
		document.numberRow++;	
	}
	document.numberCol++;
	do_sortable();
}



function closeModal(){
	$("#createshelfmodal").modal("hide");
}

function refresh_description(){

    try {
        const editor = tinymce.get('id_shelf--description')
        tinymce.remove(editor);

    } catch (e) {
         console.log(e)
    };

    setTimeout(function () {
        show_refuse_elements();
        gt_find_initialize($("#shelfmodalbody"));
    }, 1000);

}
function processResponse(data) {
	$("#modal_shelf--type_id").remove();
	$("#id_shelf--description").remove()
	$("#shelfmodalbody").html(data);
	gt_find_initialize($("#shelfmodalbody"));
	activemodal = $("#createshelfmodal").modal('show');
	show_refuse_elements();

}


function createconfigdata(){
  var dev = '[';
  var trs =$("#mytab tr");
  for (var x=0; x<trs.length; x++){
    dev += '[';
    var tds = $(trs[x]).find('td');
    for (var y=0; y<tds.length; y++){
      dev+='[';
      var inp = $(tds[y]).find("li.shelfitem");
      for (var z=0; z<inp.length; z++){
        dev += $(inp[z]).data('id');
        if(!(z+1==inp.length)) dev+=',';
      }
      dev+=']';
       if(!(y+1==tds.length)) dev+=',';
    }
    dev += ']';
    if(!(x+1==trs.length)) dev+=',';
  }
  return dev+']';
}

function save_form(){
	$('form').submit(function(event){
        $("#id_dataconfig").val(createconfigdata());
    });
}

function delete_shelf(id, url){
    var delete_id = id;
    var delete_url = url;

    Swal.fire({
      title: translations_shelf_modal['title'],
      showDenyButton: false,
      showCancelButton: true,
      confirmButtonText: translations_shelf_modal['yes'],
      cancelButtonText: translations_shelf_modal['cancel'],
    }).then((result) => {
      if (result.isConfirmed) {
            ajaxPost(delete_url, {}, function(response){
                $(delete_id).remove();
            });
      }
    })
}
function show_refuse_elements(){
     if($('#id_shelf--discard').is(':checked')){
        $('#id_shelf--description').parent().parent().show();
     }else{
        $('#id_shelf--description').parent().parent().hide();

      }
}


function removeShelf(){
    $('#id_shelfs').val(JSON.stringify(shelfs_pk))
	$("#wbody").empty()
	$("#warningobjects").modal('hide')
	pks=[]


}
function cancelRemoveShelfs(){
    shelfs_pk = shelfs_pk.filter(e => !pks.includes(e))
    pks=[]
    $("#wbody").empty()

}

function deleteColumn(){
	$('#mytab tr').each(function(i, e){
		$(e).find("td:last").remove();

		});
		document.numberCol--;
		do_sortable();
        removeShelf()


}

function deleteRow() {
	$('#mytab tr').last().remove();
	document.numberRow--;
	do_sortable();
	removeShelf()
}

function deleteRows() {
	  $('#mytab tr:last').find(".shelfitem").each(function(x, o){
    	pks.push(o.dataset.id)
    	})
    	if(pks.length>0){
        send_shelf_request('deleteRow();')
        }else{
        deleteRow()
        }
}

function deleteColumns() {

	$('#mytab tr').each(function(i, e){
	    $($(e).find("td:last .shelfitem")).each(function(x, o){pks.push(o.dataset.id)});
	 });

    if(pks.length>0){
        send_shelf_request('deleteColumn();')
    }else{
        deleteColumn()
    }

}

function send_shelf_request(action_click){
    $.ajax({
            url: shelfs_url,
            type: "POST",
            dataType: "json",
            contentType: 'application/json',
            data: JSON.stringify({'shelfs': pks}),
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
            },
            success: ({data}) => {
                shelfs_pk = Array.from(new Set([...shelfs_pk, ...pks]));
                $("#wbody").empty();
                $("#wbody").html(data);
                $("#remove_shelf").attr('onClick', action_click);
                $("#warningobjects").modal('show');
            },
        });
}

save_form();
do_sortable();

$(document).on('ifChanged','#id_shelf--discard', function(event){
    show_refuse_elements('#id_shelf--discard');
});

$(document).on('click','#cancel_modal', function(event){
    cancelRemoveShelfs()
});