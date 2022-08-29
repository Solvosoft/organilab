$('#id_prudence_advice').change(function(){

    let pk=$(this).find('option:selected').val();
    $.ajax({
        url: 'sga/prudence/',
        type:'POST',
        data: {pk},
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        success: function (message) {
        if($('.prudence_message').length==0){
        $("#id_prudence_advice").parent().append(create_container(message,'prudence_message'));
        }else{
        $('.prudence_message').find('p').text(message);
        }
      }
        });
        });

$('#id_danger_indication').change(function(){
    let pk=$(this).find('option:selected').val();
    $.ajax({
        url: 'sga/get_danger_indication/',
        type:'POST',
        data: {pk},
        headers: {'X-CSRFToken': getCookie('csrftoken') },
        success: function (message) {
        if($('.danger_message').length==0){
        $("#id_danger_indication").parent().append(create_container(message,'danger_message'));
        }else{
        $('.danger_message').find('p').text(message);
        }
      }
        });
        });
function create_container(message,classname){
    let div= document.createElement('div')
    div.innerHTML=`<span class="delete_message">x</span>`;
    div.classList.add(classname);
    div.append(create_message(message));

    return div;
 }
 function create_message(message){
    let textbox= document.createElement('p');
    textbox.classList.add('text_content');
    textbox.textContent=message;
    textbox.setAttribute('title',message);
 return textbox;
 }

 $(document).on('click','.delete_message',function(){
    $(this).parent().remove();

});
