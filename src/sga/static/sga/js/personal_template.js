$( document ).ready(function() {
    $('#table_template_list').DataTable();
});


function delete_template(element){

    var id = element.getAttribute('data-id');
    var url = document.url_delete_sgalabel;

    if(id){
        url = url.replace('0', id);
    }
    $("#btndeletesgalabel").attr('href', url);
    $("#deletesgalabelmodal").modal('show');
}


$(".btnpreview").on('click', function(){
    var url = document.url_get_preview;
    var id = $(this).data('id');
    if(id){
        url = url.replace('0', id);
    }

    $.ajax({
        url: url,
        type: 'GET',
        success: function(result) {
          if(result.svgString){
            var decoded = unescape(encodeURIComponent(result.svgString));
            var base64 = btoa(decoded);
            var imgSource = 'data:image/svg+xml;base64,'+base64;
            $("#svgtemplate img").attr('src', imgSource);
            $("#svgtemplate").modal('show');
          }
        },
        error: function(xhr, resp, text) {
            console.log(xhr, resp, text);
        }
    });
});