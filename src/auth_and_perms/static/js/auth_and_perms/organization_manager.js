

function add_rol_org(url, data){

     data = {
        'name': $(data[0]).val(),
        'rol': $(data[1]).val()
    }

    $.ajax({
      type: "POST",
      url: url,
      data: JSON.stringify(data),
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: function( data ) {
           window.location.reload();
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



$(".applyasrole").on('click', function(e){
    document.contextroletable.as_conttentype=false;
    document.contextroletable.as_user=false;
    document.contextroletable.user=null;
    document.contextroletable.as_role=true;
    document.contextroletable.contenttypeobj=Object.assign({}, e.target.dataset);
    document.contextroletable.profile= e.target.dataset.profile
    $("#modal"+e.target.dataset.org).modal('show');
});
$(".applybycontenttype").on('click', function(e){
    document.contextroletable.as_conttentype=true;
    document.contextroletable.as_user=false;
    document.contextroletable.user=null;
    document.contextroletable.as_role=false;
    document.contextroletable.profile=null;
    document.contextroletable.contenttypeobj=Object.assign({}, e.target.dataset);
    $("#modal"+e.target.dataset.org).modal('show');
});
$(".applybyuser").on('click', function(e){
    document.contextroletable.as_role=false;
    document.contextroletable.as_conttentype=false;
    document.contextroletable.contenttypeobj=null;
    document.contextroletable.as_user=true;
    document.contextroletable.profile=e.target.dataset.user;
    $("#modal"+e.target.dataset.org).modal('show');
});


$(".userbtnadd").on('click', function(e){
    document.contextroletable.as_conttentype=true;
    document.contextroletable.as_user=false;
    document.contextroletable.user=null;
    document.contextroletable.as_role=false;
    document.contextroletable.contenttypeobj=Object.assign({}, e.target.dataset);
    document.contextroletable.profile=null;
    $("#modaluser"+e.target.dataset.id).modal('show');
});

document.profileroleselects={

}


function add_selected_elements_to_select2(rols, data){
    return ()=>{
        for(let x=0; x<data.length; x++){
         if ($(rols).find("option[value='" + data[x].id + "']").length) {
            $(rols).val(data[x].id).trigger('change');
         }else{
            var newOption = new Option(data[x].text, data[x].id, true, true);
            $(rols).append(newOption).trigger('change');
         }
        }
    };

}

function add_data_to_select(rols){

    $(rols).find('option').remove();
    $(rols).val(null).trigger('change');

    return (data)=>{
        for(let x=0; x<data.results.length; x++){
            if ($(rols).find("option[value='" + data.results[x].id + "']").length) {
                $(rols).val(data.results[x].id).trigger('change');
            }else{
                var newOption = new Option(data.results[x].text, data.results[x].id, data.results[x].selected,
                        data.results[x].selected);
                $(rols).append(newOption)
            }
        }
        $(rols).trigger('change');
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
           window.location.reload();
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

        $.ajax({
      type: "GET",
      url: url,
      data: document.contextroletable,
      contentType: 'application/json',
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: add_data_to_select(select),
      dataType: 'json'
    });
    $(select).select2({theme: 'bootstrap-5',  dropdownParent: $("#relOrganizationmodal")});
    $("#relOrganizationmodal").modal('show');
});


$(".rolbtnadd").on('click', function(){
    var orgpk = $(this).data('id');
    $("#addrolmodal div#add_rol_container input[name='orgpk']").val(orgpk);
    $("#btn_copy_rol").attr('data-url', $(this).data('url'));
    $("#addrolmodal").modal('show');
});

$("#addrolmodal").on('hidden.bs.modal', function () {
    $("#btn_copy_rol").removeAttr('data-url');
    $("#addrolmodal div#add_rol_container input[name='orgpk']").val('');
})


$("#btn_add_rol").on('click', function(){
    $("#add_rol_container").show();
    $("#copy_rol_container").hide();
    $("#addrolmodal form").attr('action', $(this).data('url'));
});


$("#btn_copy_rol").on('click', function(){
    $("#add_rol_container").hide();
    $("#copy_rol_container").show();
    $("#addrolmodal form").attr('action', $(this).data('url'));
});


$('.btn-toggle').click(function() {
$(this).find('.btn').toggleClass('active');
  if ($(this).find('.btn-primary').length>0) {
      $(this).find('.btn').toggleClass('btn-primary');
    }
  $(this).find('.btn').toggleClass('btn-default');
 });


$(document).ready(function(){
    $("#copy_rol_container").hide();
 });


 $("#addrolmodal").on('show.bs.modal', function (e) {
    var selectusers = $("#addrolmodal select");
    var url = $(selectusers).data('url');

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