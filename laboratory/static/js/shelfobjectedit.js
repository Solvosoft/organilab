function processResponseshelfobjectCreate(dat) {
	$('#shelfobjectCreate').html(dat);
	// clean the form
	$("#object_create").modal('show');
}

function processResponseshelfobjectDelete(dat) {
	$('#shelfobjectDelete').html(dat);
	$("#object_delete").modal('show');
}
function processResponseshelfobjectUpdate(dat) {
	$('#shelfobjectUpdate').html(dat);
	// clean the form
	$("#object_update").modal('show');
}
function see_prototype_shelf_field(){
	$("#shelf").html($("#prototype_shelf_field").html());
}

function function_name_furniture(argument) {
	ajax({
		url : document.furniture_list,
		data : {
			"namelaboratoryRoom" : argument
		},
		cache : false,
		type : "GET",
		success : function processResponsefurniture(dat) {
			$('#furnitures').html(dat);

		}
	});
}

function function_name_shelf(argument) {
		ajax({
			url : document.shelf_list,
			data : {
				"furniture" : argument
			},
			cache : false,
			type : "GET",
			success : function processResponseshelf(dat) {
				$('#shelf').html(dat);
			}
		});

	}
	
function function_name_shelfobject(argument) {
		ajax({
			url : document.shelfobject_list,
			data : {
				"shelf" : argument
			},
			cache : false,
			type : "GET",
			success : function processResponseshelfobject(dat) {
				$('#shelfobject').html(dat);
			}
		});

	}