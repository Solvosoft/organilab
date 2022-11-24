      var pk_global=0
      datatableElement=createDataTable('#zone_type_table',document.zone_type_url, {
      columns: [
            {className:"text-center align-middle", data: "name", name: "name", title: "Name", type: "string", visible: true},
            {className:"text-center align-middle", data: "priority_validator", name: "priority_validator", title: "Priority calculate operator", type: "string", visible: true},
            {className:"text-center align-middle", data: "action", name: "action", title: "Action", type: "readonly", visible: true},
        ]
      });

      function open_modal_add_zone_type(){

          $.ajax({
            url: document.zone_type_form,
            type : "GET",
            headers: {'X-CSRFToken': getCookie('csrftoken') },
            dataType : 'json',
            success : function(result) {
                $('#modalCreate-body').html(result['message']);
                    eval(result['script'])

            },
            error: function(xhr, resp, text) {
                console.log(xhr, resp, text);
            }
        });
      }

       function create_zone_type(){

          urlApi= document.zone_type_create

          var modal = $('#create_zone_type_modal')
          $.ajax({
            url: urlApi,
            type : "POST",
            headers: {'X-CSRFToken': getCookie('csrftoken') },
            dataType : 'json',
            data: $('#formCreateZoneType').serialize(),
            success : function(result) {
                 datatableElement.ajax.reload()
                 modal.modal('hide')
            },
           error: function(xhr, resp, text) {
                if(xhr.status == 400 ){
                    keys = Object.keys(xhr.responseJSON)

                    $.each(keys, function(i, e){
                        var item = $('#formZoneType').find('*[name='+e+']');
                        item.after('<p class="text-danger error">'+xhr.responseJSON[e].join("<br>")+'<p>');
                    });
                }
            }
        });
      }

      function show_zone_type(pk){
        pk_global=pk;
        urlApi=document.zone_type_retrieve

        urlApi=urlApi.replace('0',pk)

          $.ajax({
            url: urlApi,
            type : "GET",
            headers: {'X-CSRFToken': getCookie('csrftoken') },
            dataType : 'json',
            success : function(result) {
                $('#modal-body').html(result['message']);
                eval(result['script'])

            },
            error: function(xhr, resp, text) {
                console.log(xhr, resp, text);
            }
        });
    }

    function update_zone_type(){
        urlApi=document.zone_type_retrieve
        urlApi=urlApi.replace('0', pk_global)
        var modal = $('#update_zone_type_modal')

        $.ajax({
            url: urlApi,
            type : "PUT",
            headers: {'X-CSRFToken': getCookie('csrftoken') },
            dataType : 'json',
            data: $('#formZoneType').serialize(),
            success : function(result) {
                 datatableElement.ajax.reload()
                 modal.modal('hide')
            },
            error: function(xhr, resp, text) {
                if(xhr.status == 400 ){
                    keys = Object.keys(xhr.responseJSON)

                    $.each(keys, function(i, e){
                        var item = $('#formZoneType').find('*[name='+e+']');
                        item.after('<p class="text-danger error">'+xhr.responseJSON[e].join("<br>")+'<p>');
                    });
                }
            }
        });
    }
      function delete_zone_type(pk){
        urlApi=document.zone_type_retrieve
        urlApi=urlApi.replace('0', pk)

        $.ajax({
            url: urlApi,
            type : "DELETE",
            headers: {'X-CSRFToken': getCookie('csrftoken') },
            dataType : 'json',
            success : function(result) {
                 datatableElement.ajax.reload()

            },
            error: function(xhr, resp, text) {
                console.log(xhr, resp, text);
            }
        });
    }