$(".rol_edit").on('click', function(e){
		let rol = $(this).data('rol');
		rol_action_url = rol_url.replace('/0', "/"+rol);
		get_rol_url = get_rol.replace('/0', "/"+rol);
		$("#rol_form").attr('action', rol_action_url);
		    $.ajax({
      type: "GET",
      url: get_rol_url,
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: function( data ) {
          $("#rol_form").find('input[name="name"]').val(data.name);
          $("#rol_form").find('textarea[name="description"]').val(data.description);
      }
    });
		$("#rol_details").modal('show');
});

$(".save_rol").on('click', function(e){
		$("#rol_form").submit();
});
