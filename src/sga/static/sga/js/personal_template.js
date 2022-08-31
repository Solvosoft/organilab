$( document ).ready(function() {
$('#table_template_list').DataTable();

});
const sendrequest=(element=>{

let pk=element.getAttribute('data-id');
     $.ajax({
        url: 'sga/getData/',
        type:'GET',
        data: {pk},
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        datatype:'json',
        success: function (response) {
        data=JSON.parse(response);
        create_table(data);
      }
        });

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
  title: 'Esta seguro de eLiminar la plantilla?',
  text: "Estas a tiempo de revertir esta acción!",
  icon: 'warning',
  showCancelButton: true,
  confirmButtonText: 'Si',
  cancelButtonText: 'No',
  reverseButtons: true
}).then((result) => {
  if (result.isConfirmed) {
    swalWithBootstrapButtons.fire(
      'Eliminado!',
      'La plantilla a sido eliminada.',
      'success'
    )
        sendrequest(element);

  } else if (
    result.dismiss === Swal.DismissReason.cancel
  ) {
    swalWithBootstrapButtons.fire(
      'Cancelado',
      'El archivo no fue eliminado :)',
      'error'
    )
  }
})
}

function create_table(data){
      let tbody=document.querySelector('#template_list');
        tbody.innerHTML='';
        data.forEach((item,i)=>{
         tbody.innerHTML+=`<tr>
                <td>${item['fields']['name']}</td>
                <td><a class="btn btn-md btn-info" href="/sga/get_pdf/${item.pk}"><i class="fa fa-file-pdf-o" aria-hidden="true"></i></a>
                    <a class="deleted btn btn-md btn-danger" onclick="delete_template(this)" data-id=${item['pk']}><i class="fa fa-trash"></i></a></td>
            </tr>`

      });

}


$("#btnpreview").on('click', function(){
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