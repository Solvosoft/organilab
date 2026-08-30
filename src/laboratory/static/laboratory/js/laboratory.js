
$(document).ready(function(){
    const searchLaboratory={
        init: function(){
            this.init_box();
        },
        init_box: function(){
            var toggler = document.getElementsByClassName("box");
            var i;

            for (i = 0; i < toggler.length; i++) {
              toggler[i].addEventListener("click", function() {
                this.parentElement.querySelector(".nested").classList.toggle("active");
                this.classList.toggle("check-box");
              });
            }
        }
    };

    searchLaboratory.init();

    var shelfObjectButtons = get_shelfobject_table_buttons();

    datatableelement = createDataTable('#shelfobjecttable', document.url_shelfobject, {
        columns: [
            {data: "pk", name: "pk", title: gettext("Id"), type: "string", visible: true},
            {data: "shelfobject_code", name: "shelfobject_code", title: gettext("Code"), type: "string", visible: true},
            {data: "object_type", name: "object__type", title: gettext("Type"), type: "string", visible: true},
            {data: "object_name", name: "object__name", title: gettext("Name"), type: "string", visible: true},
            {data: "quantity", name: "quantity", title: gettext("Quantity"), type: "string", visible: true},
            {data: "unit", name: "measurement_unit__description", title: gettext("Unit"), type: "string", render: truncateTextRenderer(), visible: true},
            {data: "container", name: "container__object__name", title: gettext("Container"), type: "string", visible: true},
            {data: "actions", name: "actions", title: gettext("Actions"), type: "string", visible: true, filterable: false, sortable: false},
        ],
        buttons: shelfObjectButtons,
        layout: {
            topStart: 'pageLength',
            top: 'buttons',
            topEnd: 'search',
            bottomStart: 'info',
            bottomEnd: 'paging'
        },
        ajax: {
            url: document.url_shelfobject,
            type: 'GET',
            data: function(dataTableParams, settings) {
                var data = formatDataTableParams(dataTableParams, settings);
                data['organization'] = $('#id_organization').val();
                data['laboratory'] = $('#id_laboratory').val();
                data['shelf'] = tableObject.get_active_shelf(show_alert=false);
                return data;
            }
        }
    }, addfilter=false);

    init_transfer_list_table();


    //shelfselected
    $('input[name="shelfselected"]').change(function(event){
        if(event.currentTarget.checked ){
            datatableelement.ajax.reload();
        }

    });

    $('#shelfobjecttable').on( 'init.dt', function () {
        if(document.search_by_url){
            labviewSearch.select_objs(document.search_by_url);
        }
    });
});

var inputElm = document.querySelector('input[name=tags-search]');



const tagify = new Tagify(inputElm, {
    delimiters : null,
    templates : {
        tag : function(tagData){
            try{
                return `<tag title='${tagData.value}' objtype='${tagData.objtype}' pk='${tagData.pk}' style='--tag-bg: ${tagData.color}' contenteditable='false' spellcheck="false" class='tagify__tag ${tagData.class ? tagData.class : ""}' ${this.getAttributes(tagData)}>
                        <x title='remove tag' class='tagify__tag__removeBtn'></x>
                        <div>
                            <span class='tagify__tag-text fs-6'>${tagData.value}</span>
                        </div>
                    </tag>`
            }
            catch(err){}
        },
        dropdownItem : function(tagData){
            try{
                return `<div ${this.getAttributes(tagData)} class='tagify__dropdown__item ${tagData.class ? tagData.class : ""}' >

                            <span class='fs-6' style='background-color: ${tagData.color}; color: black;'>${tagData.value}</span>
                        </div>`
            }
            catch(err){ console.error(err)}
        }
    },
    enforceWhitelist: true,
    whitelist: document.suggestions_tag,
    placeholder: gettext("Search")
});

$("#btnremovealltags").on('click', function(){
    tagify.removeAllTags();
    labviewSearch.restart_objs();
});

tagify.on('add', function(e){
        labviewSearch.search(e.detail.tagify.value);
    }).on("invalid", function(e, tagName){
        console.log('JQUERY EVENT: ',"invalid", e, ' ', tagName);
    }).on('remove', function(e){
        var obj_list = e.detail.tagify.value;

        if(obj_list.length){
            labviewSearch.search(obj_list);
        }else{
            labviewSearch.restart_objs();
        }
    });


const labviewSearch={
    show_deselected_previous_shelfs: function(shelf_list, key, value){
        var active_shelf = tableObject.get_active_shelf(show_alert=false);
        var shelf_obj = $("#"+key+"_"+active_shelf);

        if(active_shelf != undefined && value != active_shelf && shelf_list.hasOwnProperty('furniture')){
            if(shelf_list['furniture'].hasOwnProperty('furniture')){
                var furniture = $(shelf_obj).parents('li').children('span.furnitureroot');
                if($(furniture).length){
                    var furniture_parent = parseInt($(furniture)[0].id.split("_")[1]);
                    if(shelf_list['furniture']['furniture'].includes(furniture_parent)){
                        $(shelf_obj).parents('.shelfrow').children().show();
                    }
                }
            }
        }
    },
    check_objs: function(obj_list, key){
        obj_list.forEach(function(value) {
            span_obj = "#"+key+"_"+value;

            if($(span_obj).length  && !$(span_obj).hasClass('check-box')){
                $(span_obj).parent().show();
                $(span_obj).click();
            }

            if(key === 'labroom'){
                $(span_obj).next().children().show();
            }else{
                $(span_obj).next().children().find('div.input-group').show();
            }

        });
    },
    check_radios: function(shelf_list, obj_list, key, hide_related_shelf=true){
        obj_list.forEach(function(value) {
            var radio_obj = "#"+key+"_"+value;

            if($(radio_obj).length){
                labviewSearch.show_deselected_previous_shelfs(shelf_list, key, value);
                    $(radio_obj).parents('.shelfrow').children().hide();
                    $(radio_obj).parents('.shelves_rows').children().hide();
                    $(radio_obj).parents('.shelves_rows').parent().children().hide();

                $(radio_obj).parents('.col').show();
                $(radio_obj).prop('checked', true);
                $(radio_obj).change();
            }
        });

        obj_list.forEach(function(value) {
            var radio_obj = "#"+key+"_"+value;
            if($(radio_obj).length){
                $(radio_obj).parents('.shelves_rows').parent().show();
                $(radio_obj).parents('.shelves_rows').show();
                $(radio_obj).parent().parent().show();
            }
        });

    },
    select_labroom: function(labroom_list){
        labviewSearch.check_objs(labroom_list, "labroom");
    },
    select_furniture: function(furniture_list){
        if(furniture_list.hasOwnProperty('furniture')){
            labviewSearch.check_objs(furniture_list['furniture'], "furniture");
        }
        if(furniture_list.hasOwnProperty('labroom')){
            labviewSearch.select_labroom(furniture_list['labroom']);
        }
    },
    select_shelf: function(shelf_list, hide_related_shelf=true){
        if(shelf_list.hasOwnProperty('shelf')){
            labviewSearch.select_furniture(shelf_list['shelf']);

            if(shelf_list['shelf'].hasOwnProperty('shelf')){
                labviewSearch.check_radios(shelf_list, shelf_list['shelf']['shelf'], "shelf", hide_related_shelf=hide_related_shelf);
            }else{
                labviewSearch.check_radios(shelf_list, shelf_list['shelf'], "shelf", hide_related_shelf=hide_related_shelf);
            }
        }
    },
    select_shelfobject: function(shelfobject_list){
        labviewSearch.select_furniture(shelfobject_list);
        labviewSearch.select_shelf(shelfobject_list);
        var table_filter_input = $('div#shelfobjecttable_filter input[type="search"]');
        if(table_filter_input.length){
            table_filter_input.val('pk='+shelfobject_list['shelfobject'].slice(-1)[0]);
            table_filter_input.focus();
            table_filter_input.keyup();
            var tagify_input = $(".tagify__input")[0];
            $(tagify_input).focus();
            $(tagify_input).keyup();
        }
    },
    select_object: function(object_list){
        labviewSearch.select_shelf(object_list, hide_related_shelf=false);
        var table_filter_input = $('div#shelfobjecttable_filter input[type="search"]');
        if(table_filter_input.length){
            table_filter_input.val(object_list['object'][0]);
            table_filter_input.focus();
            table_filter_input.keyup();
            var tagify_input = $(".tagify__input")[0];
            $(tagify_input).focus();
            $(tagify_input).keyup();
        }

        if(object_list.hasOwnProperty('shelf')){
            if(object_list['shelf'].hasOwnProperty('shelf')){
                var shelf_result = object_list['shelf']['shelf'].length;
               $("#alert_msg").html("<b>"+gettext("Showing first result from ")+ shelf_result +gettext(" matched shelves")+"</b>");
               $("div.alert").addClass('show');
            }
        }
    },
    restart_objs: function(){
        $('input[name="shelfselected"]').prop('checked', false).change();
        $("span.check-box").click();
        $('div#shelfobjecttable_filter input[type="search"]').val('').keyup();
        $("span.box").parent().show();
        $('input[type="radio"]').parents('.shelfrow').children().show();
        $("div.alert").removeClass('show');
    },
    select_objs: function(search_list){
        labviewSearch.restart_objs();
        if(Object.keys(search_list).length){
            $("span.box").parent().hide();
            if('labroom' in search_list && Object.keys(search_list['labroom']).length){
                labviewSearch.select_labroom(search_list['labroom']);
            }
            if('furniture' in search_list && Object.keys(search_list['furniture']).length){
                labviewSearch.select_furniture(search_list['furniture']);
            }
            if('shelf' in search_list && Object.keys(search_list['shelf']).length){
                labviewSearch.select_shelf(search_list);
            }
            if('shelfobject' in search_list && Object.keys(search_list['shelfobject']).length){
                labviewSearch.select_shelfobject(search_list['shelfobject']);
            }
            if('object' in search_list && Object.keys(search_list['object']).length){
                labviewSearch.select_object(search_list['object']);
            }
        }
    },
    search: function(q){
        var data = "";

        if(q.length){
            q.forEach(function(item) {
                if(item.objtype == 'laboratoryroom'){
                    data += 'labroom=' + item.pk;
                }else{
                    data += item.objtype + "=" + item.pk;
                }
                data += '&';
            });
            data = data.slice(0, -1);
        }

        $.ajax({
            url: document.urls.search_labview,
            type: "GET",
            dataType: "json",
            data: data,
            traditional: true,
            headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': "application/json"},
            success: function(data){
                labviewSearch.select_objs(data.search_list);
            },
            error: function(xhr, resp, text) {
            }
        });
    }
}

$("#hide_alert").on('click', function(){
    $("#alert_msg").html("");
    $("div.alert").removeClass("show");
});

