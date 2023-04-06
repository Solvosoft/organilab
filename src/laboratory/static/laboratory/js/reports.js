var filter =""
$('#send').on('click', function(){
    filter=get_doc_filter();
    filter= filter.substring(1,filter.length);
    filter="?"+filter;
    document.querySelector('#spiner').classList.add('spinner-border', 'spinner-border-sm')
    url=report_urls['create_request']+filter;
    $(this).attr('disabled',true)
    $(".statuspanel").addClass("d-none")

    $("#button-text").text('Loading the report may take a few minutes...')
    $.ajax({
        url: url,
        type : "GET",
        dataType : 'json',
        success : function({result,report, celery_id}) {
        if (result==true){
             get_doc(report,celery_id);
        }
        }
        });

});

function open_new_window(url_file){
    let link = document.createElement('a');
    link.href = url_file;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    link.remove();
}

function accept_request(){
    document.querySelector('#spiner').classList.remove('spinner-border', 'spinner-border-sm')
    document.querySelector("#button-text").textContent = 'Send'
    document.querySelector("#send").removeAttribute('disabled');
}

function get_doc(pk,task){

    filter=`?taskreport=${pk}&task=${task}`;
    url=report_urls['generate_report']+filter;

    $.ajax({
        url: url,
        type : "GET",
        dataType : 'json',
        success : function({result, url_file, type_report}) {

        if (result==true){

            if(type_report==='html'){
                open_new_window(url_file);
                accept_request();
            }else{
                accept_request();
                $("#download-report").attr("href",url_file)
                $("#download_file").attr("href",url_file)
                $(".statuspanel").removeClass("d-none")
                $("#reportModal").modal('show');
            }
         }else{
            setTimeout(function(){
                        get_doc(pk,task);
                        }, 3000);
         }
         }
    });
 }

function get_doc_filter(){
    dev ="";
    var formdata = $("#form").serializeArray();
        for(var x=0; x<formdata.length; x++){
               dev+="&"+formdata[x].name+"="+formdata[x].value;
        }
      return dev;
}


function add_data_to_select(select, selecteditems){

    $(select).find('option').remove();
    $(select).val(null).trigger('change');

    return (data)=>{
        let has_selected=false;
        for(let x=0; x<data.results.length; x++){

            if(data.results[x].selected || selecteditems.includes(String(data.results[x].id))){
                has_selected=true;
                if(selecteditems.includes(String(data.results[x].id))){
                    data.results[x].selected = true;
                }
            }
            if ($(select).find("option[value='" + data.results[x].id + "']").length) {
                $(select).val(data.results[x].id).trigger('change');
            }else{
                var newOption = new Option(data.results[x].text, data.results[x].id, data.results[x].selected,
                        data.results[x].selected);
                $(select).append(newOption)

            }
        }
        if(!has_selected) {
            $(select).val(null).trigger('change');
        }else{
            $(select).trigger('change');
        }
    }
}

document.select_data = {
    all_labs_org: false,
    organization: $("#id_organization").val(),
    laboratory: $("#id_laboratory").val(),
}

function update_lab_rooms(){
    var select_labroom = $("form select#id_lab_room");
    var url = $(select_labroom).data('url');
    var selecteditems = select_labroom.val();

    $.ajax({
      type: "GET",
      url: url,
      data: document.select_data,
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: add_data_to_select(select_labroom, selecteditems),
      dataType: 'json'
    });
}

function update_furniture(){
    var select_furniture = $("form select#id_furniture");
    var url = $(select_furniture).data('url');
    var selecteditems = select_furniture.val();

    $.ajax({
      type: "GET",
      url: url,
      data: document.select_data,
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: add_data_to_select(select_furniture, selecteditems),
      dataType: 'json'
    });
}


$('#id_all_labs_org').on('change', function(){
    document.select_data.all_labs_org = false;
     if($(this).is(":checked")){
        document.select_data.all_labs_org = true;
    }
    update_lab_rooms();
    update_furniture();
});


$(document).ready(function() {
    update_lab_rooms();
    update_furniture();
});