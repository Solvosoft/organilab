var numberCol = 2,
	    numberRow = 2;

	function addRow() {
		var root = document.getElementById('mytab').getElementsByTagName('tbody')[0];
		var rows = root.getElementsByTagName('tr');
		var clone = cloneEl(rows[rows.length - 1]);
		root.appendChild(clone);
		numberRow++;
	}

	function addColumn() {
		var rows = document.getElementById('mytab').getElementsByTagName('tr'),
		    i = 0,
		    r,
		    c,
		    clone;
		while ( r = rows[i++]) {
			c = r.getElementsByTagName('td');
			clone = cloneEl(c[c.length - 1]);
			c[0].parentNode.appendChild(clone);
		}
		numberCol++;
	}

	function cloneEl(el) {
		var clo = el.cloneNode(true);
		return clo;
	}

	function deleteRows() {
		if (numberRow > 1) {
			var tbl = document.getElementById('mytab'), // table reference
			    lastRow = tbl.rows.length - 1, // set the last row index
			    i;
			// delete rows with index greater then 0
			for ( i = lastRow; i > 0; i++) {
				tbl.deleteRow(i);
			}
			numberRow--;
		}
	}

	// delete table columns with index greater then 0
	function deleteColumns() {
		if (numberCol > 1) {
			var tbl = document.getElementById('mytab'), // table reference
			    lastCol = tbl.rows[0].cells.length - 1, // set the last column index
			    i,
			    j,
			    deleteCol;
			// delete cells with index greater then 0 (for each row)
			for ( i = 0; i < tbl.rows.length; i++) {
				//for ( j = lastCol; j > 0; j--) {
				tbl.rows[i].deleteCell(lastCol);
				//}
			}
			numberCol--;
		}

	}

	function processResponse(data) {
		$('#shelves').html(data);
	}