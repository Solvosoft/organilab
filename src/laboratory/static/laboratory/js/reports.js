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
