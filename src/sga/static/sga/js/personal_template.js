$( document ).ready(function() {
$('#table_template_list').DataTable();

});

function delete_template(element){
let pk=element.getAttribute('data-id');
     $.ajax({
        url: 'sga/getData/',
        type:'GET',
        data: {pk},
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        datatype:'json',
        success: function (data) {
        data=JSON.parse(data);
        let tbody=document.querySelector('#template_list');
        tbody.innerHTML='';
        data.forEach((item,i)=>{
         tbody.innerHTML+=`<tr>
                <td>${item['fields']['name']}</td>
                <td><a class="btn btn-md btn-info"><i class="fa fa-file-pdf-o" aria-hidden="true"></i></a>
                    <a class="deleted btn btn-md btn-danger" onclick="delete_template(this)" data-id=${item['pk']}><i class="fa fa-trash"></i></a></td>
            </tr>`

      });

      }
        });
}