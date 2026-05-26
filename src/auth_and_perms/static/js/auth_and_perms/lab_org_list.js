
datatableorgs=createDataTable('#orgtable', org_api_url, {
 columns: [
        {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
        {data: "laboratories", name: "laboratories", title: gettext("Associated laboratories"), type: "string", visible: true},
      ],
 ajax: {
    url: org_api_url,
    type: 'GET',
    data: function(dataTableParams, settings) {
        var data= formatDataTableParams(dataTableParams, settings);
        return data;
    }
}
}, addfilter=false
);

datatablelabs=createDataTable('#labtable', lab_api_url, {
 columns: [
        {data: "name", name: "name", title: gettext("Name"), type: "string", visible: true},
        {data: "organizations", name: "organizations", title: gettext("Partner organizations"), type: "string", visible: true},
      ],
 ajax: {
    url: lab_api_url,
    type: 'GET',
    data: function(dataTableParams, settings) {
        var data= formatDataTableParams(dataTableParams, settings);
        return data;
    }
}
}, addfilter=false
);
