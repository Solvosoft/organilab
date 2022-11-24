
  var pk_global=0

  datatableElement=createDataTable('#risk_zone_table',document.risk_zone_url, {

     columns: [
            {className:"text-center align-middle", data: "laboratories_count", name: "laboratories_count", title: "laboratories", type: "string", visible: true},
            {className:"text-center align-middle", data: "name", name: "name", title: "Rick zone", type: "string", visible: true},
            {className:"text-center align-middle", data: "action", name: "action", title: "Action", type: "readonly", visible: true},
        ]
    });

    function show_risk_zone(pk){
        pk_global=pk;
        urlApi=document.risk_zoneRetrieve
        urlApi=urlApi.replace('0',pk)

          $.ajax({
            url: urlApi, // url where to submit the request
            type : "GET", // type of action POST || GET
            dataType : 'json', // data type
            success : function(result) {
                $('#modal-body').html(result['message']);
                eval(result['script']);
            },
            error: function(xhr, resp, text) {
                console.log(xhr, resp, text);
            }
        });
    }

    function update_risk_zone(){
        urlApi=document.risk_zoneRetrieve
        urlApi=urlApi.replace('0', pk_global)
        var modal = $('#update_zone_risk_modal')

        $.ajax({
            url: urlApi, // url where to submit the request
            type : "PUT", // type of action POST || GET
            headers: {'X-CSRFToken': getCookie('csrftoken') },
            dataType : 'json', // data type
            data: $('#formRiskZone').serialize(),
            success : function(result) {
                 datatableElement.ajax.reload()
                 modal.modal('hide')
            },
            error: function(xhr, resp, text) {
                console.log(xhr, resp, text);
            }
        });
    }
