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

function get_url_parameters(){
	  var params = window.location.href.split("#");
	  if(params.length > 1){
	    params = params[1].split("&");
	  }

	  var obj={};

	  for(var x=0; x<params.length; x++){
	    var tmp = params[x].split("=");
	    if(tmp.length>1){
	      if(tmp[0]=='labroom') obj['labroom']=tmp[1];
	      if(tmp[0]=='furniture') obj['furniture']=tmp[1];
	      if(tmp[0]=='shelf') obj['shelf']=tmp[1];
	    }
	  }

	  var ok=false;
	  if(obj.labroom !== undefined && obj.furniture !== undefined && obj.shelf !== undefined){
	  ok=true;
	  }
	  if (!ok){
	    obj=undefined;
	  }
	   return obj;
}


function wait_furniture(){
 if( $("#furniture_"+obj.furniture).length ==0){
   setTimeout(wait_furniture, 1000);
 }else{
  $("#furniture_"+obj.furniture).click();
 
 }
}  

function wait_shelf(){
 if( $("#shelf_view_"+obj.shelf).length ==0){
    setTimeout(wait_shelf, 1000);
 }else{
   $("#shelf_view_"+obj.shelf).click();
   $("#shelf_view_"+obj.shelf).removeClass('collapse')
   $("#body_"+obj.shelf).addClass('show')
 }
}

function  load_self_from_uls(){
	obj = get_url_parameters();
	if (obj !== undefined){
       $('#room_'+obj.labroom).click();
		$('#room_'+obj.labroom).addClass('active');
		$('#idlab').addClass('active show');
		$('#room_'+obj.labroom).attr('aria-selected',true);
		wait_furniture();
		wait_shelf();


	}
}