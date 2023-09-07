function add_status(url){
    Swal.fire({
        title: gettext('New status'),
        input: 'text',
        showCancelButton: true,
        CancelButtonText: gettext("Cancel"),
        confirmButtonText: gettext("Send"),
    }).then((result) => {
        if(result.isConfirmed){
       fetch(url, {
        method:"post",
        headers:{'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': "application/json"},
        body:JSON.stringify({"description":result.value})})
            .then(response=>{
                if(response.ok){return response.json();}
                return Promise.reject(response);  // then it will go to the catch if it is an error code
            }).then(data=>{
                  Swal.fire({
                    text: gettext('Saved the new shelfobject status'),
                    icon: 'success',
                    timer: 1500,
                  })
            }).catch(response =>{
                    let error_msg = gettext('There was a problem performing your request. Please try again later or contact the administrator.');  // any other error
                    response.json().then(data => {  // there was something in the response from the API regarding validation
                        if(data["errors"] && data.errors['description']){
                            error_msg = data.errors['description'][0];  // specific api validation errors
                        }else if(data['detail']){
                            error_msg = data['detail'];
                        }
                    })
                    .finally(()=>{
                            Swal.fire({
                                title: gettext('Error'),
                                text: error_msg,
                                icon: 'error'
                            });
                    })
                    });
                    }
});

}

function update_selects(id,data){
    var select = $(id);
    var url = $(select).data('url');

    $.ajax({
      type: "GET",
      url: url,
      data: data,
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      traditional: true,
      dataType: 'json',
      success: function(data){
                         $(select).find('option').remove();
                        for(let x=0; x<data.results.length; x++){
                            $(select).append(new Option(data.results[x].text, data.results[x].id, data.results[x].selected, data.results[x].selected))
                        }
                    },
           });

    }