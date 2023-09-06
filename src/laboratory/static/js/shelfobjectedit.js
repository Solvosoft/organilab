const float_regex= /^[+-]?\d+(\.\d+)?$/;

function processResponseshelfobject(dat){
    $("#closemodal").html(dat["inner-fragments"]["#closemodal"]);
    datatableelement.ajax.reload();
}

//Refactored delete method for Shelf Object
function shelfObjectDelete(shelf_object_id, text, type, container=false, container_name="") {
    $("#divobjname").html('<h6>'+gettext("Are you sure you want to delete")+' "'+text+'"?</h6>');
    var delete_container = $("#delete_shelfobject_modal #id_delete_container");
    $("#delete_shelfobject_modal #divcontainer").hide();

    if(type == '0' && container){
        var container_label = '<h6>'+gettext("Would you like to delete the container")+' "'+container_name+'" '+
        gettext("as well?")+'</h6>';
        $('label[for="id_delete_container"]').html(container_label);

        if(delete_container.length && $(delete_container[0]).prop("checked")){
            $(delete_container[0]).trigger("click").prop("checked", false);
        }

        $("#delete_shelfobject_modal #divcontainer").show();
    }
    $("#btndeleteso").data('shelfobject', shelf_object_id);
    $("#delete_shelfobject_modal").modal('show');
}


$("#btndeleteso").on("click", function(){
    $("#delete_shelfobject_modal").modal('hide');

    var url = $(this).data('url');
    var shelfobject = $(this).data('shelfobject');
    var delete_container = $('#id_delete_container:checked').val();

    if(url != undefined && shelfobject != undefined){
        fetch(url, {
        method: "delete",
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'},
        body: JSON.stringify({'shelfobj': shelfobject, 'delete_container': delete_container})})
        .then(response => {
            if(response.ok){ return response.json(); }
            return Promise.reject(response);  // then it will go to the catch if it is an error code
        })
        .then(data => {
            Swal.fire({
                title: gettext('Success'),
                text: data['detail'],
                icon: 'success',
                timer: 1500
            });
            datatableelement.ajax.reload();
        })
        .catch(response => {
            let error_msg = gettext('There was a problem performing your request. Please try again later or contact the administrator.');  // any other error
            response.json().then(data => {  // there was something in the response from the API regarding validation
                if(data['shelfobj']){
                    error_msg = data['shelfobj'][0];  // specific api validation errors
                }
            })
            .finally(() => {
                Swal.fire({
                    title: gettext('Error'),
                    text: error_msg,
                    icon: 'error'
                });
            });
        });
    }
    $("#btndeleteso").data('shelfobject', '');
});

function shelfObjectDetail(obj,){
    let url = $(obj).data('url')
    fetch(url, {
        headers: {'X-CSRFToken': getCookie('csrftoken')}})
        .then(response => response.json())
        .then(data => {
            configure_modal(data)
            $('#detail_modal_container').modal('show')
        }).catch(error => Swal.fire({
                                title: gettext('Error'),
                                text: gettext('An error has occurred'),
                                icon: 'error'
                            }))
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

function replaceLast(obj, search, replace) {
    return obj.replace(new RegExp(search+"([^"+search+"]*)$"), replace+"");
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
	      if(tmp[0]=='shelfobject') obj['shelfobject']=tmp[1];
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

function wait_shelfobject(){
 if( $("#shelfobject_view_"+obj.shelfobject).length ==0){
    setTimeout(wait_shelfobject, 1000);
 }else{
   $("#shelfobject_view_"+obj.shelfobject).click();
 }
}

function load_self_from_uls(){
	obj = get_url_parameters();
	if (obj !== undefined){
       $('#room_'+obj.labroom).click();
		$('#room_'+obj.labroom).addClass('active');
		$('#idlab').addClass('active show');
		$('#room_'+obj.labroom).attr('aria-selected',true);
		wait_furniture();
		wait_shelf();
		wait_shelfobject();

	}
}

function edit_object_limit(element){
   let pk = element.getAttribute('data-pk')
   let url = document.object_limit.replace('0',pk);
   $.ajax({
    url: url,
        type: "GET",
        dataType: "json",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        success: ({name, amount, msg}) => {
            send_limit_message(element,pk,amount)
        }
    });
 }
function send_limit_message(element,pk,amount){

    Swal.fire({
                title: msgs['limit'],
                input: 'text',
                confirmButtonText: msgs['confirm'],
                denyButtonText: 'No',
                showDenyButton: true,
                showCloseButton: true,
                inputValue: amount
            }).then(function(result) {
                if (result.isConfirmed) {
                    if(float_regex.test(result.value)){
                        update_limit(element,pk,result.value)
                    }else{
                        Swal.fire(
                                    '',
                                    msgs['error'],
                                    'error'
                                    )
                    setTimeout(()=>{
                     send_limit_message(element,pk,amount);

                    },3000);
                    }
                    }
                    })

}
function update_limit(element,pk,amount){
   let url = document.object_limit.replace('0',pk);
     $.ajax({
            url: url,
            type: "POST",
            dataType: "json",
            data: {'amount':amount},
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            success: (success) => {
                Swal.fire(
                    '',
                    success.msg,
                    'success'
                    )

                element.parentElement.children[1].innerHTML=`<strong>Cantidad límite de material: </strong>${amount}`
            },
        });
}

function displayShelfobjectFunction(data) {
	$("#shelfdetailmodalbody").html(data);
	activemodal = $("#shelfdetailmodal").modal('show');
}
