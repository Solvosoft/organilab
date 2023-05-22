function add_status(url){
    Swal.fire({
        title: gettext('New status'),
        input: 'text',
        inputAttributes: {required: 'true'},
        showCancelButton: true,
        CancelButtonText: gettext("Cancel"),
        confirmButtonText: gettext("Send"),
    }).then((result) => {
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
                    if(data['description']){
                        error_msg = data['description'][0];  // specific api validation errors
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
});

}