
datatableuserpermelement=createDataTable('#userpermelement', prolabor_api_url, {
language: {"url": datatables_lang },
 columns: [
        {data: "user", name: "user", title: gettext("Name"), type: "string", visible: true},
        {data: "email", name: "email", title: gettext("Email"), type: "string", visible: true},
        {data: "rols", name: "rols", title: gettext("Rols"), type: "string", visible: true},
        {data: "action", name: "action", title: gettext("Actions"), type: "string", visible: true},
      ],
 ajax: {
    url: prolabor_api_url,
    type: 'GET',
    data: function(dataTableParams, settings) {
        var data= formatDataTableParams(dataTableParams, settings);
        data['organization'] = $('.nodeorg:checked').val();
        data['laboratory'] = $('#id_laboratories').val();
        return data;
    }
}
}, addfilter=false);
    relateusertoorg

datatableorpermelement=createDataTable('#orpermelement', userinorg_api_url, {
language: {"url": datatables_lang },
 columns: [
        {data: "user", name: "user", title: gettext("Name"), type: "string", visible: true},
        {data: "email", name: "email", title: gettext("Email"), type: "string", visible: true},
        {data: "rols", name: "rols", title: gettext("Rols"), type: "string", visible: true},
        {data: "action", name: "action", title: gettext("Actions"), type: "string", visible: true},
      ],
 ajax: {
    url: userinorg_api_url,
    type: 'GET',
    data: function(dataTableParams, settings) {
        var data= formatDataTableParams(dataTableParams, settings);
        data['organization'] = $('.nodeorg:checked').val();
        return data;
    }
}
}, addfilter=false);

$('input[name="nodes"]').on('ifChecked', function(e){
        $("#id_laboratories").val(null).trigger('change');
        datatableuserpermelement.ajax.reload();
        datatableorpermelement.ajax.reload();


});
$('#id_laboratories').on('select2:select', function (e) {
    datatableuserpermelement.ajax.reload();
});

function add_rol_org(url, data){

     data = {
        'name': $(data[0]).val(),
        'rol': $(data[1]).val()
    }

    if($("input[name='relate_rols']")[0].checked){
        data['relate_rols'] = $("#addrolmodal select").val();
    }

    $.ajax({
      type: "POST",
      url: url,
      data: JSON.stringify(data),
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: function( data ) {
          datatableuserpermelement.ajax.reload();
          datatableorpermelement.ajax.reload();
          $('#addrolmodal').modal('hide');
          Swal.fire({
          icon: 'success',
          title: gettext('Your rol was set successfully'),
          text: gettext('Now you can set this rol in laboratory user table'),
        })
      },
      error: function( jqXHR, textStatus, errorThrown ){
        Swal.fire({
          icon: 'error',
          title: gettext('Name'),
          text: jqXHR.responseJSON.name[0],
        })
      },
      dataType: 'json'
    });
}


function copy_rol_org(url){
     $("#addrolmodal form").attr('action', url);
     $("#addrolmodal form").submit();
}


$("#saveroluserorg").on('click', function(){
    var btnsave = $("#addrolmodal button.active");
    var url = btnsave.data('url');

    if(btnsave.data('copy')){
        copy_rol_org(url);
    }else{
        add_rol_org(url, $("#addrolmodal div#add_rol_container").find('input'));
    }
});


document.contextroletable={
    as_conttentype: false,
    as_user: false,
    as_role: true,
    profile: null,
    contenttypeobj: null,
    user: null
}

function reload_datatables(){
           datatableorpermelement.ajax.reload();
           datatableuserpermelement.ajax.reload();
}

function send_create_profile_on_conttentype(data){
    $.ajax({
      type: "POST",
      url: create_profile_ctt_url,
      data: data,
      //contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: reload_datatables,
      dataType: 'json'
    });

}

$("#relateusertoorg").on('click', function(){
    $("#id_typeofcontenttype").val('organization');
     $("#id_profile").val(null).change();
     $("#relprofilelabmodalLabel").html(gettext('Relate user to organization'));
     $("#relprofilelabmodal").modal('show');
})
$("#relateusertolab").on('click', function(){
    let laboratory=$('.nodeorg:checked').val();
    $("#id_typeofcontenttype").val('laboratory');

    if (laboratory != undefined){
        $("#id_profile").val(null).change();
        $("#relprofilelabmodalLabel").html(gettext('Relate user to laboratory'));
        $("#relprofilelabmodal").modal('show');
    }else{
    Swal.fire({
          icon: 'error',
          title: gettext('Laboratory needs to be selected'),
          text: gettext('Sorry you need to select laboratory before relate user to it'),
        })
    }

});
$("#relprofilewithlaboratorybtn").on('click', function(){
    data = {
      'typeofcontenttype': $("#id_typeofcontenttype").val(),
      'user': $("#id_profile").val(),
      'organization': $(".nodeorg:checked").val()
    }

    if (data['typeofcontenttype'] == "laboratory"){
        data[ 'laboratory'] = $("#id_laboratories").val();
    }
    send_create_profile_on_conttentype(data);
});



function deleteuserlab(elementid, contentTypeobj){
    var element=$("#ndel_"+elementid)[0]
    Swal.fire(
    {
        showCancelButton: true,
        title:  gettext('Are you sure you want to delete?'),
        icon:  'question',
        html: element.dataset.profile + gettext(' from ') + element.dataset.org,
        confirmButtonText: gettext('Yes, delete it'),
        input: 'checkbox',
        inputValue: 0,
        inputPlaceholder: gettext('Also disable user login on platform'),
    }
    ).then((result) => {
      /* Read more about isConfirmed, isDenied below */
      if (result.isConfirmed) {
          $.ajax({
              type: "DELETE",
              url: delete_rol_profile_url,
              data: {'profile': elementid,
                      'app_label': element.dataset.appname,
                      'model': element.dataset.model,
                      'object_id': element.dataset.objectid,
                      'organization': contentTypeobj,
                      'disable_user': result.value},
             // contentType: 'application/json',
              headers: {'X-CSRFToken': getCookie('csrftoken')},
              success: reload_datatables,
            //  dataType: 'json'
            });
          }
    })
}

function newuserrol(profile){
    var element=$("#profile_"+profile)[0]

    document.contextroletable.as_conttentype=false;
    document.contextroletable.as_user=false;
    document.contextroletable.user=null;
    document.contextroletable.as_role=true;
    document.contextroletable.contenttypeobj=Object.assign({}, element.dataset);
    document.contextroletable.profile=profile;
    $("#modal"+element.dataset.org).modal('show');
}
function applyasrole(elementid, profile){
    var element=$("#rol_"+elementid)[0]

    document.contextroletable.as_conttentype=false;
    document.contextroletable.as_user=false;
    document.contextroletable.user=null;
    document.contextroletable.as_role=true;
    document.contextroletable.contenttypeobj=Object.assign({}, element.dataset);
    document.contextroletable.profile=profile;
    $("#modal"+element.dataset.org).modal('show');
}

$(".userbtnadd").on('click', function(e){
    document.contextroletable.as_conttentype=true;
    document.contextroletable.as_user=false;
    document.contextroletable.user=null;
    document.contextroletable.as_role=false;
    document.contextroletable.contenttypeobj=Object.assign({}, e.target.dataset);
    document.contextroletable.profile=null;
    $("#modaluser"+e.target.dataset.id).modal('show');
});

document.profileroleselects={}


function add_selected_elements_to_select2(select){

    return (data) => {
        $(select).val(null).trigger('change');
        for(let x=0; x<data['results'].length; x++){
         if ($(select).find("option[value='" + data['results'][x].id + "']").length){
              $(select).find("option[value='" + data['results'][x].id + "']").remove();
              var newOption = new Option(data['results'][x].text, data['results'][x].id, true, true);
              $(select).append(newOption).trigger('change');
         }
        }
    }
}

function add_data_to_select(rols){

    $(rols).find('option').remove();
    $(rols).val(null).trigger('change');

    return (data)=>{
        let has_selected=false;
        for(let x=0; x<data.results.length; x++){
            if(data.results[x].selected){
                has_selected=true;
            }
            if ($(rols).find("option[value='" + data.results[x].id + "']").length) {
                $(rols).val(data.results[x].id).trigger('change');
            }else{
                var newOption = new Option(data.results[x].text, data.results[x].id, data.results[x].selected,
                        data.results[x].selected);
                $(rols).append(newOption)

            }
        }
        if(!has_selected) {
            $(rols).val(null).trigger('change');
        }else{
            $(rols).trigger('change');
        }
    }
}

$(".addprofilerol").on('show.bs.modal', function (e) {


    let modalid=e.target.id;
    var selecttarget = $("#"+modalid+' select');
    var rols = selecttarget;
    var organization = this.dataset.id;
    var url = $(rols).data('url');
    var selecteditems = [];

    if(Object.hasOwnProperty(document.profileroleselects, modalid) ){
        $(rols).select2('destroy');

    }

    $.ajax({
      type: "GET",
      url: url,
      data: document.contextroletable,
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: add_data_to_select(rols),
      dataType: 'json'
    });
    $(rols).select2({theme: 'bootstrap-5',  dropdownParent: $(this)});

});


$(".relatedusermodal").on('show.bs.modal', function (e) {


    let modalid=e.target.id;
    var selecttarget = $("#"+modalid+' select');
    var users = selecttarget;
    var organization = this.dataset.id;
    var url = $(users).data('url');

    $.ajax({
      type: "GET",
      url: url,
      data: document.contextroletable,
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: add_data_to_select(users),
      dataType: 'json'
    });
    $(users).select2({theme: 'bootstrap-5',  dropdownParent: $(this)});
});


$(".btnsaverole").on('click', function(e){
    let form = $(e.target).closest('form')[0]
    let url = form.action;
    let dataform = {
        'rols': $(form).find('select[name="rols"]').val(),
        'mergeaction': $(form).find('input[name="mergeaction"]:checked').val(),
        'csrfmiddlewaretoken': $(form).find('input[name="csrfmiddlewaretoken"]').val(),
    }
    let data=Object.assign(dataform, document.contextroletable);


    $.ajax({
      type: "PUT",
      url: url,
      data: JSON.stringify(data),
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: function( data ) {
           datatableorpermelement.ajax.reload();
           datatableuserpermelement.ajax.reload();
           $(".modal").modal('hide');
      },
      dataType: 'json'
    });
});

$(".addOrgStructure").on('click', function(e){
    let parent=this.dataset.parent;
    $('#id_parent').val(parent);
    $("#addOrganizationmodal").modal('show');
});

$(".addOrgStructureEmpty").on('click', function(e){
    $('#id_parent').val('');
    $("#addOrganizationmodal").modal('show');
});

$(".contenttyperelobjbtnadd").on('click', function(e){
    var url = this.dataset.href;
    var select = $("#relOrganizationmodal select");
    var organizationinput = $('#relOrganizationmodal input[name="organization"]');
    organizationinput.val(this.dataset.org)
    $(select).val(null).trigger('change');
    $("#relOrganizationmodal").modal('show');
});

$(".rolbtnadd").on('click', function(){
    var orgpk = $(this).data('id');
    $("#addrolmodal div#add_rol_container input[name='orgpk']").val(orgpk);
    $("#btn_copy_rol").attr('data-url', $(this).data('url'));
    $("#addrolmodal").modal('show');
    $("#addrolmodal select").val(null).trigger('change');
});

$("#addrolmodal").on('hidden.bs.modal', function () {
    $("#btn_copy_rol").removeAttr('data-url');
    $("#addrolmodal div#add_rol_container input#rolname").val('');
    $("#addrolmodal div#add_rol_container input[name='orgpk']").val('');
    $("#addrolmodal input[name='relate_rols']").prop('checked', true).trigger("click");
    $("#addrolmodal select").val(null).trigger('change');
})

function setactiveTabButton(element){
    let btnteam = $(element).closest('.btn-toggle').find(".btn");
    btnteam.removeClass('btn-primary')
    btnteam.removeClass("active");
    btnteam.addClass('btn-default');
    element.addClass('btn-primary')
    element.addClass("active");
}

$("#btn_add_rol").on('click', function(e){
    if(!$(this).hasClass('active')){
        $("#addrolmodal select").val(null).trigger('change');
        $("#add_rol_container").show();
        $("#copy_rol_container").hide();
        var rolsS2 = $("#addrolmodal #selectroldiv");
        $("#add_rol_container").append(rolsS2);
        $("#addrolmodal form").attr('action', $(this).data('url'));
        $("#addrolmodal input[name='relate_rols']").parent().show();
        if($("input[name='relate_rols']")[0].checked){
            $("#addrolmodal div#rolS2container").show();
        }else{
            $("#addrolmodal div#rolS2container").hide();
        }
        setactiveTabButton($(this));
    }else{
        e.preventDefault()
    }
});


$("#btn_copy_rol").on('click', function(e){
    if(!$(this).hasClass('active')){
        $("#addrolmodal select").val(null).trigger('change');
        $("#add_rol_container").hide();
        $("#copy_rol_container").show();
        var rolsS2 = $("#addrolmodal #selectroldiv");
        $("#copy_rol_container").append(rolsS2);
        $("#addrolmodal form").attr('action', $(this).data('url'));
        $("#addrolmodal input[name='relate_rols']").parent().hide();
        $("#addrolmodal div#rolS2container").show();
        setactiveTabButton($(this));
    }else{
        e.preventDefault()
    }
});



$(document).ready(function(){
    $("#copy_rol_container").hide();
    $("#addrolmodal div#add_rol_container input#rolname").val('');
    $("#addrolmodal input[name='relate_rols']").prop('checked', true).trigger("click");
 });


$("input[name='relate_rols']").on('change', function(event){
    if($(this)[0].checked){
        $("#addrolmodal div#rolS2container").show();
    }else{
        $("#addrolmodal div#rolS2container").hide();
    }
});


 $("#addrolmodal").on('show.bs.modal', function (e) {
    var selectusers = $("#addrolmodal select");
    var url = $(selectusers).data('url');
    $("#btn_add_rol").click();

    $.ajax({
      type: "GET",
      url: url,
      data: document.contextroletable,
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: add_data_to_select(selectusers),
      dataType: 'json'
    });
    $(selectusers).select2({theme: 'bootstrap-5',  dropdownParent: $(this)});
});

 $(".orgbyuser").on('click', function (e) {
    $('#orgbyusermodal input[name="name"]').val(this.dataset.display);
    $('#orgbyusermodal form').attr('action', this.dataset.formaction);

    var selectorgbyusers = $("#orgbyusermodal select");
    let placeholder = selectorgbyusers.attr('placeholder');
    $("#orgbyusermodal option").remove();


    var url = $(selectorgbyusers).data('url');
        $.ajax({
          type: "GET",
          url: url,
          data: {'org': this.dataset.org},
          contentType: 'application/json',
          headers: {'X-CSRFToken': getCookie('csrftoken')},
          success: add_data_to_select(selectorgbyusers),
          dataType: 'json'
        });
    $(selectorgbyusers).select2({theme: 'bootstrap-5', placeholder: placeholder,
    allowClear: true,  dropdownParent: $("#orgbyusermodal")});

    $("#orgbyusermodal").modal('show');
});

function showhide_action_field(field_id, value){
    if(value === "3"){
       $(field_id).closest('.form-group').show();
    }else{
       $(field_id).closest('.form-group').hide();
    }
}

$(document).ready(function(){
    showhide_action_field("#actionsmodal #id_name", $("#id_actions").val());
    showhide_action_field("#actionwimodal #id_wi-name", $("#id_wi-actions").val());

    $("#id_actions").on('select2:select', function(e){
        showhide_action_field("#actionsmodal #id_name", e.params.data.id);
    });
    $("#id_wi-actions").on('select2:select', function(e){
        showhide_action_field("#actionwimodal #id_wi-name", e.params.data.id);
    });
});

$(".orgactions").on('click', function(event){
    var dataset=event.currentTarget.dataset;
    var org = dataset.org;
    var modal = dataset.modal;
    var prefix = dataset.prefix;

    if(prefix != "clone"){
        var name=$(event.currentTarget).closest('.row').find('h6').text();
        $(modal+" #id_"+prefix+"name").val(name);
    }

    $('#id_'+prefix+'action_organization').val(org);
    $(modal).modal('show');
});

function add_groups_by_profile(select_group){
    return (data)=>{

        for(let x=0; x<data.results.length; x++){
            $(select_group).val(data["id"]);
        }
    }

}

$("#id_pg-profile").on('change', function(event){
    if($(this).val()){
        var selectgroup = $("#id_pg-groups")[0];

        $.ajax({
          type: "GET",
          url: groups_by_profile,
          data: {'profile': $(this).val()},
          contentType: 'application/json',
          headers: {'X-CSRFToken': getCookie('csrftoken')},
          success: add_selected_elements_to_select2(selectgroup),
          dataType: 'json'
        });
    }
});

function convertFormToJSON(form, prefix="", multiple_field=[]) {
  const re = new RegExp("^"+prefix);
  return form
    .serializeArray()
    .reduce(function (json, { name, value }) {
        name = name.replace(re, "");
        if(json.hasOwnProperty(name)){
            if(!Array.isArray(json[name])){
                json[name] = [json[name]];
            }
            json[name].push(value);
        }else if(multiple_field.includes(name)){
            json[name] = [value];
        }else{
            json[name] = value;
        }
      return json;
    }, {});
}

function convertToStringJson(form, multiple_field, prefix="", extras={}){
    var formjson =convertFormToJSON(form, prefix=prefix, multiple_field=multiple_field);
    formjson=Object.assign({}, formjson, extras)
    return JSON.stringify(formjson);
}

function reset_form(form){
    $(form).trigger('reset');
    $(form).find("select option:selected").prop("selected", false);
    $(form).find("select").val(null).trigger('change');
    $(form).find("ul.form_errors").remove();
}

$("#savegroupsbyprofile").on("click", function(){
    var url = $(this).data('url');
    $("#id_pg-organization").val($('.nodeorg:checked').val());
    var form = $("#groups_by_profile_form");
    $.ajax({
      type: "POST",
      url: url,
      data: convertToStringJson(form, ['groups'], prefix="pg-"),
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      dataType: 'json',
      success: function(data) {
        if(data.hasOwnProperty("detail")){
            Swal.fire({
                icon: 'success',
                title: gettext('Success'),
                text: data.detail,
                timer: 1500
            });
        }
      },
      error: function(xhr, resp, text) {
        var errors = xhr.responseJSON.errors;
        if(errors){  // form errors
            form.find('ul.form_errors').remove();
            form_field_errors(form, errors, "pg-");
        }else{
            let error_msg = gettext('There was a problem performing your request. Please try again later or contact the administrator.');  // any other error
            if(xhr.responseJSON.detail){
                error_msg = xhr.responseJSON.detail;
            }
            Swal.fire({
                icon: 'error',
                title: gettext('Error'),
                text: error_msg
            });
        }
      }
    });
    reset_form(form);
});

$('a[data-bs-toggle="tab"]').on('shown.bs.tab', function (e) {
    reset_form("#groups_by_profile_form");
    if(!$('.nodeorg:checked').val()){
        Swal.fire({
            icon: 'info',
            title: gettext('No organization selected'),
            text: gettext('You need to select a organization before using this tab.'),
        });
    }
});
