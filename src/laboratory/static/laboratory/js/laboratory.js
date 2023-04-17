$(document).ready(function(){
    var toggler = document.getElementsByClassName("box");
    var i;

    for (i = 0; i < toggler.length; i++) {
      toggler[i].addEventListener("click", function() {
        this.parentElement.querySelector(".nested").classList.toggle("active");
        this.classList.toggle("check-box");
      });
    }


    datatableelement=createDataTable('#shelfobjecttable', document.url_shelfobject, {
     columns: [
            {data: "object_name", name: "object_name", title: gettext("Name"), type: "string", visible: true},
            {data: "quantity", name: "quantity", title: gettext("Quantity"), type: "string", visible: true },
            {data: "unit", name: "unit", title: gettext("Unit"), type: "string", visible: true},
             {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true},
        ],
     ajax: {
        url: document.url_shelfobject,
        type: 'GET',
        data: function(dataTableParams, settings) {
            var data= formatDataTableParams(dataTableParams, settings);
            data['organization'] = $('#id_organization').val();
            data['laboratory'] = $('#id_laboratory').val();
            data['shelf'] = $('input[name="shelfselected"]:checked').val();
            return data;
        }
    }
    }, addfilter=false);
    //shelfselected

$('input[name="shelfselected"]').change(function(){
    datatableelement.ajax.reload();
});

});