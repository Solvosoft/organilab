$("#edit_button").click((e)=>{
    $("#equipment_form").find('ul.form_errors').remove();
    $.ajax({
        url: edit_equipment_urls["get"],
		type: "GET",
		dataType: "json",
		headers: {
		    "X-Requested-With": "XMLHttpRequest",
			"X-CSRFToken": getCookie("csrftoken"),
			},
			success: (data) => {
			Object.entries(data).forEach(function([name, value]){
			    var inputfield = $("#equipment_form").find('input[name="'+name+'"], textarea[name="'+name+'"]')
				var select_input = $("#id_"+name)
				let done=false;

				if(inputfield.attr('class') === "chunkedvalue"){

                    if(value){
                        var chunked=$("#equipment_form").find('input[name="'+name+'_widget"]').data('fileUploadWidget');
                        chunked.addRemote(value);
                    }else{
                        $("#equipment_form").find('input[name="'+name+'_widget"]').data('fileUploadWidget').resetEmpty();
                    }

                    done=true;
                } else if(inputfield.attr('type') === 'file'){

				    if(value){
					    var newlink = document.createElement('a');
					    newlink.href = value.url;
						newlink.textContent = value.name;
						newlink.target = "_blank";
						newlink.classList.add("link-primary");
						newlink.classList.add("file-link");
						newlink.classList.add("d-block");
						inputfield.before(newlink)
				    }
					done=true;

				} else if(inputfield.attr('type') === "radio"){
				    var is_icheck = inputfield.closest('.gtradio').length > 0;
					var sel = inputfield.filter(function() { return this.value === value.toString() });
					if(sel.length>0){
					    sel.prop( "checked", true);
						if(is_icheck){
						    sel.iCheck('update');
							sel.iCheck('check');
						}
					}else{
					    inputfield.prop( "checked", false);
						if(is_icheck){
						    inputfield.iCheck('update');
						    inputfield.iCheck('uncheck');
						}
					}
					done=true;
				}
				if(select_input){
				    if(["Select", "SelectMultiple"].includes(select_input.data().widget)){
					    $(select_input).val(null).trigger('change');
						if(value){
						    select_input.val(value).trigger("change");
						}
					}
				}
				if(!done) { inputfield.val(value); }

			});
		},
	});
})

function load_errors(error_list, obj, display_on_top=false){
    ul_obj = "<ul class='errorlist form_errors d-flex justify-content-center flex-wrap'>";
    error_list.forEach((item)=>{
        ul_obj += "<li>"+item+"</li>";
        console.log(item)
    });
    ul_obj += "</ul>"
    var obj_to_prepend = display_on_top ? $(obj) : $(obj).parents(".form-group");
    obj_to_prepend.prepend(ul_obj);
    return ul_obj;
}

function form_field_errors(target_form, form_errors){
    var item = "";
    for (const [key, value] of Object.entries(form_errors)) {
        item = " #id_"+key;
        if(target_form.find(item).length > 0){
            if(target_form.find(item).attr("type") == "hidden"){
                load_errors(form_errors[key], target_form, display_on_top=true);
            }else{
               load_errors(form_errors[key], item);
            }
        }
    }
}

$("#save_equipment").click((e)=>{
    data=$("#equipment_form").serializeArray()
	form = $("#equipment_form")
	$.ajax({
	    url: edit_equipment_urls["edit"],
		type: "PUT",
		data: data,
		headers: {
    				"X-Requested-With": "XMLHttpRequest",
	    			"X-CSRFToken": getCookie("csrftoken"),
	    },
		success: (success) => {
		    Swal.fire(
			    '',
				gettext("Successfully updated"),
				'success'
			)
			$("#edit_equipment").modal("hide");
		},
		error: function(xhr, resp, text) {
	        var errors = xhr.responseJSON.errors;
            if(errors){
                form.find('ul.form_errors').remove();
                form_field_errors(form, errors);
            }else{
                let error_msg = gettext('There was a problem performing your request. Please try again later or contact the administrator.');  // any other error
                if(xhr.responseJSON.detail){
                    error_msg = xhr.responseJSON.detail;
                }
            }
        }
	});
})
