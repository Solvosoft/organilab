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
}


function deleteRows() {
	$('#mytab tr').last().remove();
	document.numberRow--;
}

// delete table columns with index greater then 0
function deleteColumns() {
	$('#mytab tr').each(function(i, e){
		$(e).find("td:last").remove();
			
		});
		document.numberCol--;
	}

function closeModal(){
	$("#createshelfmodal").modal("hide");
}

function processResponse(data) {
	$("#shelfmodalbody").html(data);
	activemodal = $("#createshelfmodal").modal('show');
}
