$(document).on('click', '.beditbtn', function(){
    $(this).closest('.observacionklass').trigger('dblclick');
});
$(document).on('dblclick', ".observacionklass", function(){
    var e = $(this);

    if(e.data('manage') == "1"){
        $("#observation_id").val(e.data('pk'));
        $("#descriptionarea").val(e.find(".message").text());
        $("#textdescription").html(e.find(".message").text());
        $("#editObservacion").modal('show');
    }
});
$("#obdelbtn").on('click', function(){
    $("#editObservacion").modal('hide');
    $("#delObservacion").modal('show');

});

$("#obeditbtn").on('click', function(){
    $.ajax({
      method: "POST",
      url: $(this).data('url'),
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      data: { pk: $("#observation_id").val(), description: $("#descriptionarea").val() }
    }).done(function(data){
        window.location.reload();
    })
});

$("#delete_observation").on('click', function(){
   $.ajax({
      method: "POST",
      url: $(this).data('url'),
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      data: { pk: $("#observation_id").val() }
    }).done(function(data){
        if(data.status == true){
        window.location.reload();
        }
    });
});