$( document ).ready(function() {
    $('#table_template_list').DataTable();
});


function delete_template(element){
    const swalWithBootstrapButtons = Swal.mixin({
        customClass: {
            confirmButton: 'btn btn-success',
            cancelButton: 'btn btn-danger'
        },
        buttonsStyling: false
    })

    swalWithBootstrapButtons.fire({
        title: 'Esta seguro de eliminar la plantilla?',
        text: "Estas a tiempo de revertir esta acción!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Si',
        cancelButtonText: 'No',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            var id =element.getAttribute('data-id');
            var url = document.url_delete_sgalabel;

            if(id){
                url = url.replace('0', id);
            }
            window.location = url;

    } else if (
        result.dismiss === Swal.DismissReason.cancel
    ){
        swalWithBootstrapButtons.fire(
            'Cancelado',
            'El archivo no fue eliminado :)',
            'error'
        )
    }
    })
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
            $("#svgtemplate").modal();
          }
        },
        error: function(xhr, resp, text) {
            console.log(xhr, resp, text);
        }
    });
});


$("#newsgalabel").on("click", function(){
    $("#newsgalabelmodal").modal();
});