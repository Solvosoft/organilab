// Variables set from template: URLS, csrfToken, PERMS

let pendingRejectUrl = null;
let orgTableInitialized = false;
let labTableInitialized = false;

const org_datatable_inits = {
    columns: [
        {data: 'id', name: 'id', title: 'ID', type: 'readonly', visible: false},
        {data: 'name', name: 'name', title: gettext('Name'), type: 'readonly', visible: true},
        {data: 'level', name: 'level', title: gettext('Level'), type: 'readonly', visible: true},
        {
            data: null, name: 'actions', title: gettext('Actions'),
            type: 'string', visible: true, orderable: false,
            render: function(data, type, row) {
                return buildApprovalActions(row, URLS.org_approve, URLS.org_reject);
            }
        },
    ],
    addfilter: true,
};

const lab_datatable_inits = {
    columns: [
        {data: 'id', name: 'id', title: 'ID', type: 'readonly', visible: false},
        {data: 'name', name: 'name', title: gettext('Name'), type: 'readonly', visible: true},
        {data: 'created_by', name: 'created_by', title: gettext('Created by'), type: 'readonly', visible: true, render: selectobjprint({display_name: 'text'})},
        {data: 'creation_date', name: 'creation_date', title: gettext('Creation date'), type: 'readonly', visible: true},
        {
            data: null, name: 'actions', title: gettext('Actions'),
            type: 'string', visible: true, orderable: false,
            render: function(data, type, row) {
                return buildApprovalActions(row, URLS.lab_approve, URLS.lab_reject);
            }
        },
    ],
    addfilter: true,
};

function buildApprovalActions(row, approveUrlTpl, rejectUrlTpl) {
    let html = '';
    const actions = row.actions || {};
    if (actions.approve) {
        const url = approveUrlTpl.replace('{pk}', row.id);
        html += `<button class="btn btn-sm btn-success me-1" onclick="doApprove('${url}', this)">
            <i class="fa fa-check"></i> ${gettext('Approve')}
        </button>`;
    }
    if (actions.reject) {
        const url = rejectUrlTpl.replace('{pk}', row.id);
        html += `<button class="btn btn-sm btn-danger" onclick="openRejectModal('${url}', '${row.name}')">
            <i class="fa fa-times"></i> ${gettext('Reject')}
        </button>`;
    }
    return html;
}

function doApprove(url, btn) {
    btn.disabled = true;
    fetch(url, {
        method: 'POST',
        headers: {'X-CSRFToken': csrfToken, 'Content-Type': 'application/json'},
    }).then(r => r.json()).then(data => {
        if (data.ok) {
            location.reload();
        } else {
            alert(data.detail || gettext('Error'));
            btn.disabled = false;
        }
    }).catch(() => { btn.disabled = false; });
}

function openRejectModal(url, name) {
    pendingRejectUrl = url;
    document.getElementById('reject-obj-name').textContent = name;
    new bootstrap.Modal(document.getElementById('reject-modal')).show();
}

function initOrgTable() {
    if (orgTableInitialized || !PERMS.view_org) return;
    orgTableInitialized = true;
    gtCreateDataTable('#org-approval-table', URLS.org_list, org_datatable_inits);
}

function initLabTable() {
    if (labTableInitialized || !PERMS.view_lab) return;
    labTableInitialized = true;
    gtCreateDataTable('#lab-approval-table', URLS.lab_list, lab_datatable_inits);
}

// Init active tab table immediately
if (PERMS.view_org) {
    initOrgTable();
} else if (PERMS.view_lab) {
    initLabTable();
}

// Init hidden tab table on first show to avoid broken column widths
$('a[data-bs-toggle="tab"]').on('shown.bs.tab', function(e) {
    const target = $(e.target).attr('href');
    if (target === '#tab-orgs') initOrgTable();
    if (target === '#tab-labs') initLabTable();
});

$(document).ready(function() {
    $('#reject-confirm-btn').on('click', function() {
        if (!pendingRejectUrl) return;
        const btn = this;
        btn.disabled = true;
        fetch(pendingRejectUrl, {
            method: 'POST',
            headers: {'X-CSRFToken': csrfToken, 'Content-Type': 'application/json'},
        }).then(r => r.json()).then(data => {
            if (data.ok) {
                location.reload();
            } else {
                alert(data.detail || gettext('Error'));
                btn.disabled = false;
            }
        }).catch(() => { btn.disabled = false; });
    });
});
