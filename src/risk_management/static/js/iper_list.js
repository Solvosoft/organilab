const iper_status_badges = {
    completed: "bg-success",
    obsolete: "bg-dark",
};

function iper_escape(text) {
    return $("<div>").text(text || "").html();
}

datatable_inits = {
    columns: [
        {data: "id", name: "id", title: "ID", type: "string", visible: false},
        {
            data: "laboratory",
            name: "laboratory",
            title: gettext("Laboratory"),
            type: "string",
            visible: true,
            render: function (data, type, full) {
                // laboratory llega null cuando la evaluación es anónima: el
                // serializer nunca envía el nombre en ese caso.
                if (full.is_anonymous) {
                    return '<span class="text-muted fst-italic">' + gettext("Anonymous") + '</span>' +
                        ' <i class="fa fa-lock text-muted ms-1" title="' + gettext("Laboratory name hidden") + '"></i>';
                }
                return iper_escape(data) +
                    ' <i class="fa fa-unlock text-success ms-1" title="' + gettext("Laboratory name visible") + '"></i>';
            }
        },
        {data: "assessment_date", name: "assessment_date", title: gettext("Date"), type: "string", visible: true},
        {data: "version", name: "version", title: gettext("Version"), type: "string", visible: true},
        {
            data: "status",
            name: "status",
            title: gettext("Status"),
            type: "string",
            visible: true,
            render: function (data, type, full) {
                let badge = iper_status_badges[data] || "bg-secondary";
                return '<span class="badge ' + badge + '">' + iper_escape(full.status_display) + '</span>';
            }
        },
        {
            data: "responsible", name: "responsible", title: gettext("Responsible"),
            type: "string", visible: true,
            render: data => data ? iper_escape(data) : "—"
        },
        {
            data: "due_date", name: "due_date", title: gettext("Next update"),
            type: "string", visible: true,
            render: data => data ? iper_escape(data) : "—"
        },
        {
            data: "actions", name: "actions", title: gettext("Actions"),
            type: "string", visible: true, filterable: false, sortable: false
        },
    ],
    addfilter: false,
}

const modalids = {};
if (has_delete_perm) {
    modalids.destroy = "#delete_obj_modal";
}

const actions = {
    table_actions: [],
    // "open" navega a la página de detalle (link:true en do_action de
    // obj_api_management.js); el serializer gatea la acción por permiso.
    object_actions: [{
        name: "open",
        title: gettext("Open"),
        i_class: "fa fa-eye fa-lg me-2",
        link: true,
        url_fn: data => iper_detail_url.replace('/0/', '/' + data.id + '/'),
    },
        {
            name:"duplicate",
            title: gettext("Duplicate"),
            i_class: "fa fa-clone me-2"
        }],
    title: gettext('Actions'),
    className: "no-export-col"
}

const objconfig = {
    datatable_element: "#table-iper",
    modal_ids: modalids,
    actions: actions,
    datatable_inits: datatable_inits,
    delete_display: function (data) {
        let lab = data.laboratory || gettext("Anonymous");
        return iper_escape(lab + " v" + data.version + " (" + data.assessment_date + ")");
    },
    urls: object_urls,
}

const ocrud = ObjectCRUD("iper_crud", objconfig);
ocrud.duplicate = function (data) {
    // Set the assessment ID in the hidden field
    document.getElementById('duplicate_assessment_id').value = data.id;
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('duplicateModal'));
    modal.show();
}

// Handle duplicate form submission
document.addEventListener('DOMContentLoaded', function() {
    const duplicateForm = document.getElementById('duplicateForm');
    if (duplicateForm) {
        duplicateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const form = this;
            const assessmentId = document.getElementById('duplicate_assessment_id').value;
            const url = iper_duplicate_url.replace('/0/', '/' + assessmentId + '/');
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> ' + gettext('Duplicating...');

            fetch(url, {
                method: 'POST',
                body: new FormData(form),
                headers: {'X-Requested-With': 'XMLHttpRequest'}
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success) {
                    window.location.href = data.redirect_url;
                } else if (data.error) {
                    alert(data.error);
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fa fa-clone"></i> ' + gettext('Duplicate');
                    bootstrap.Modal.getInstance(document.getElementById('duplicateModal')).hide();
                } else if (data.errors) {
                    let msg = Object.values(data.errors).flat().join('\n');
                    alert(msg || gettext('Error duplicating assessment'));
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fa fa-clone"></i> ' + gettext('Duplicate');
                }
            })
            .catch(function(err) {
                alert(gettext('Error duplicating assessment'));
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fa fa-clone"></i> ' + gettext('Duplicate');
            });
        });
    }
});

ocrud.init();
