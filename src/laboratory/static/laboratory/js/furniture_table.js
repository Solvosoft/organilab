
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


function deleteRows() {
	$('#mytab tr').last().remove();
	document.numberRow--;
	do_sortable();
}

// delete table columns with index greater then 0
function deleteColumns() {
	$('#mytab tr').each(function(i, e){
		$(e).find("td:last").remove();
			
		});
		document.numberCol--;
		do_sortable();
}

function closeModal(){
	$("#createshelfmodal").modal("hide");
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
      title: 'Do you want to delete this shelf?',
      showDenyButton: false,
      showCancelButton: true,
      confirmButtonText: 'Yes, delete it',
      cancelButtonText: 'Cancel',
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
        $('#id_shelf--quantity').parent().parent().show();
        $('#id_shelf--measurement_unit').parent().parent().show();
        $('#id_shelf--description').parent().parent().show();
     }else{
        $('#id_shelf--quantity').parent().parent().hide();
        $('#id_shelf--measurement_unit').parent().parent().hide();
        $('#id_shelf--description').parent().parent().hide();

      }
}




save_form();
do_sortable();

$(document).on('ifChanged','#id_shelf--discard', function(event){
    show_refuse_elements('#id_shelf--discard');
});