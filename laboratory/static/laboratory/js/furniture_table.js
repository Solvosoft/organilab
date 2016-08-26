var numberCol = 2,
	    numberRow = 2;

	function addRow() {
		sk=$("<tr> </tr>");
		$('#mytab tr:last td').each(function(i, e){
			sk.append(
				"<td>"+$("#addshelfproto").html()+"</td>"
			);
					numberCol++;
		});
		
		$('#mytab tr').last().after(sk);
		numberRow++;
	}

	function addColumn() {
		$('#mytab tr').each(function(i, e){
			$(e).append(
				"<td>"+$("#addshelfproto").html()+"</td>"
			);
					numberCol++;
		});
	}


	function deleteRows() {
			$('#mytab tr').last().remove();
	}

	// delete table columns with index greater then 0
	function deleteColumns() {
		$('#mytab tr').each(function(i, e){
			$(e).find("td:last").remove();
			
		});

	}

	function processResponse(data) {
		$('#shelves').html(data);
	}