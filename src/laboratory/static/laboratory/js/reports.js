var filter = ""

function get_archive_status() {
    url = report_urls['report_status'] + filter;
    $.ajax({
        url: url,
        type: "GET",
        dataType: 'json',
        success: function (data) {
            $("#textstatus").html(data['text']);

            if (data['state'] === 'FAILURE' || data['state'] === 'REVOKED') {
                show_error_message(gettext("Report failed"));
                accept_request();
                return;
            }

            if (data['end'] != true) {
                setTimeout(get_archive_status, 5000);
            }

        },
        error: function (xhr) {
            show_error_message(gettext("Error checking report status"));
            accept_request();
        }
    });
}

function load_errors(error_list, obj) {
    ul_obj = "<ul class='errorlist report_form_errors'>";
    error_list.forEach((item) => {
        ul_obj += "<li>" + item + "</li>";
    });
    ul_obj += "</ul>"
    $(obj).before(ul_obj);
    return ul_obj;
}

function form_field_errors(form_errors) {
    var item = "";
    for (const [key, value] of Object.entries(form_errors)) {
        item = "#id_" + key;
        if ($(item).length > 0) {
            load_errors(form_errors[key], item);
        }
    }
}

function show_error_message(error_message) {
    if (error_message) {
        if (!$("#diverrormessage").is(":visible")) {
            $("#errormessagecontent").html(error_message);
            $("#diverrormessage").show();
            accept_request();
        }
    }
}


$('#send').on('click', function () {
    $(".statuspanel, .card-footer").addClass("d-none");
    filter = get_doc_filter();
    filter = filter.substring(1, filter.length);
    filter = "?" + filter;
    url = report_urls['create_request'] + filter;
    $(this).attr('disabled', true);
    $("#button-text").text(gettext('Loading the report may take a few minutes...'));
    document.querySelector('#spiner').classList.add('spinner-border', 'spinner-border-sm');

    $.ajax({
        url: url,
        type: "GET",
        dataType: 'json',
        success: function (data) {
            $('ul.report_form_errors').remove();
            if (data['redirect_url']) {
                open_new_window(data['redirect_url']);
                accept_request();
                return;
            }
            if (data['result']) {
                $("#diverrormessage").hide();
                $("#textstatus").html("");
                $(".statuspanel").removeClass("d-none");
                setTimeout(get_archive_status, 1000);
                get_doc(data['report'], data['celery_id']);
            } else if (data['form_errors']) {
                form_field_errors(data['form_errors']);
                accept_request();
            }
        },
        error: function (xhr, resp, text) {
            show_error_message(text);
        }
    });

});

function open_new_window(url_file) {
    let link = document.createElement('a');
    link.href = url_file;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    link.remove();
}

function accept_request() {
    document.querySelector('#spiner').classList.remove('spinner-border', 'spinner-border-sm')
    document.querySelector("#button-text").textContent = gettext('Send');
    document.querySelector("#send").removeAttribute('disabled');
}

function get_doc(pk, task) {

    filter = `?taskreport=${pk}&task=${task}`;
    url = report_urls['generate_report'] + filter;
    $.ajax({
        url: url,
        type: "GET",
        dataType: 'json',
        success: function (data) {
            if (data['state'] === 'FAILURE' || data['state'] === 'REVOKED') {
                accept_request();
                return;
            }

            if (data['result'] == true) {
                if (data['type_report'] === 'html') {
                    open_new_window(data['url_file']);
                } else {
                    $("#download-report, #download_file").attr("href", data['url_file']);
                    $(".statuspanel, .card-footer").removeClass("d-none");
                    $("#reportModal").modal('show');
                }
                accept_request();
            } else {
                setTimeout(function () {
                    get_doc(pk, task);
                }, 3000);
            }
        },
        error: function (xhr, resp, text) {
            show_error_message(text);
        }
    });
}

function get_doc_filter() {
    dev = "";
    var formdata = $("#form").serializeArray();
    for (var x = 0; x < formdata.length; x++) {
        dev += "&" + formdata[x].name + "=" + formdata[x].value;
    }
    return dev;
}

document.select_data = {
    relfield: '',
    organization: $("#id_organization").val(),
    laboratory: $("#id_laboratory").val(),
}


function add_log_change_datatables(id, lab, obj, diff, unit, cas_code, url) {
    if (cas_code == "") {
        cas_code = gettext("No code");
    }
    if (cas_code == "False") {
        cas_code = "";
    }
    columns = [
        {data: "user", name: "user", title: gettext("User"), type: "string", visible: true},
        {data: "update_time", name: "update_time", title: gettext("Day"), type: "date", visible: true},
        {data: "old_value", name: "old_value", title: gettext("Initial amount"), type: "number", visible: true},
        {data: "new_value", name: "new_value", title: gettext("Final amount"), type: "number", visible: true},
        {data: "diff_value", name: "diff_value", title: gettext("Difference"), type: "number", visible: true},
    ],
        html_card = `<div class="card mt-5">
	<div class="card-title text-center fw-bold">
	<p>${lab} | ${obj} ${cas_code}  <br><p>${diff} ${unit}</p></p>
	<hr>
	</div>
	<div class="card-body"><table id=${id} class="log_changes_table mt-0 p-0 display table table-striped table-bordered text-center dt-responsive"></table>
	</div></div>`;
    $('#body_tables').append(html_card);

    data = createDataTable("#" + id, url, {
        responsive: true,
        columns: columns,

        ajax: {
            url: url,
            type: 'GET',
            data: function (dataTableParams, settings) {
                return formatDataTableParams(dataTableParams, settings);
            }
        },
        dom: "<'d-flex justify-content-between'<'m-2'l>" +
            "<'m-2'B><'m-2 d-flex justify-content-start'f>>" +
            "<'row'tr><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7 m-auto'p>>",

    }, addfilter = true,);

}


$("#download-report").on("click", function () {
    $("#reportModal").modal('hide');
});
