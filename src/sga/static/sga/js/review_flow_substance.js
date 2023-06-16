function review(btn){
    var url = $(btn).data('url');
    $("#review_substance form").attr("action", url);
    $("#review_substance").modal('show');
}

function waitForElementToDisplay(selector, checkFrequencyInMs, timeoutInMs) {
  var startTimeInMs = Date.now();
  (function loopSearch() {
    if (document.querySelector(selector) != null) {
        $(selector).on('click', function(){
            var url = $(this).data('url');
            $("#review_substance form").attr("action", url);
            $("#review_substance").modal('show');
        });
      return;
    }
    else {
      setTimeout(function () {
        if (timeoutInMs && Date.now() - startTimeInMs > timeoutInMs)
          return;
        loopSearch();
      }, checkFrequencyInMs);
    }
  })(jQuery);
}

function get_columns_logentry(){
    var columns = [
        {data: "creation_date", name: "creation_date", title: gettext("Creation Date"), type: "date",
        render: DataTable.render.datetime(), visible: true,  "dateformat":  document.datetime_format},
        {data: "created_by", name: "created_by", title: gettext('Creator'), type: "string", visible: true},
        {data: "comercial_name", name: "comercial_name", title: gettext('Substance'), type: "string", visible: true,  sortable: false},
        {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true, filterable: false, sortable: false},
    ];
    return columns;
}
$(document).ready(function() {
       substancetable = createDataTable("#substancetable", document.urls.review_datatable_url, {
          'columns': get_columns_logentry(),
          dom: "<'d-flex justify-content-between'<'m-2'l>" +
        "<'m-2'B><'m-2 d-flex justify-content-start'f>>" +
        "<'row'tr><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7 m-auto'p>>",
          ajax: {
            url: document.urls.review_datatable_url,
            type: 'GET',
            data: function(dataTableParams, settings) {
                var data = formatDataTableParams(dataTableParams, settings);
                if($('#showapprove').is(":checked")){
                    data['showapprove'] = 'True';
                }else{
                    data['showapprove'] = 'False';
                }
                return data;
            }
        }
    }, addfilter=true);


    $('#showapprove').on('change', function(){
        substancetable.ajax.reload();
        waitForElementToDisplay(".btn_review", 1, 9000);
    });

    waitForElementToDisplay(".btn_review", 1, 9000);


});
