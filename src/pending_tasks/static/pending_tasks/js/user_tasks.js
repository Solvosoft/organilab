var PendingTasks = (function () {
    var apiBase = '/pending_tasks/api/api_pending_tasks/';

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    var csrftoken = getCookie('csrftoken');

    function ajaxSetup() {
        $.ajaxSetup({
            beforeSend: function (xhr, settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
    }

    function getStatusBadgeClass(statusId) {
        switch (statusId) {
            case 0: return 'badge bg-warning';
            case 1: return 'badge bg-info';
            case 2: return 'badge bg-success';
            default: return 'badge bg-secondary';
        }
    }

    function getNextStatus(currentStatus) {
        switch (currentStatus) {
            case 0: return 1;
            case 1: return 2;
            default: return currentStatus;
        }
    }

    function getCheckboxIcon(statusId) {
        switch (statusId) {
            case 0: return 'fa fa-square-o';
            case 1: return 'fa fa-minus-square-o';
            case 2: return 'fa fa-check-square-o';
            default: return 'fa fa-square-o';
        }
    }

    function renderTaskItem(task) {
        var statusId = task.status.id;
        var statusName = task.status.name;
        var isFinished = statusId === 2;
        var descStyle = isFinished ? 'text-decoration: line-through; color: #999;' : '';
        var canAdvance = statusId < 2;
        var createdByText = '';
        if (task.profile && task.profile.text) {
            createdByText = '';
        }

        var linkHtml = '';
        if (task.link) {
            linkHtml = ' <a href="' + task.link + '" target="_blank" title="' +
                gettext('Open link') + '">' +
                '<i class="fa fa-external-link"></i></a>';
        }

        var assignHtml = '';
        if (!task.profile || !task.profile.id) {
            assignHtml = '<button class="btn btn-xs btn-outline-primary task-assign" ' +
                'data-task-id="' + task.id + '" title="' + gettext('Assign to me') + '">' +
                '<i class="fa fa-hand-o-up"></i></button> ';
        }

        var html = '<li class="list-group-item d-flex justify-content-between align-items-center" ' +
            'data-task-id="' + task.id + '">';

        html += '<div class="d-flex align-items-center flex-grow-1">';

        if (canAdvance) {
            html += '<button class="btn btn-sm btn-link task-toggle-status p-0 me-2" ' +
                'data-task-id="' + task.id + '" data-current-status="' + statusId + '" ' +
                'title="' + gettext('Change status') + '">' +
                '<i class="' + getCheckboxIcon(statusId) + '"></i></button>';
        } else {
            html += '<span class="me-2"><i class="' + getCheckboxIcon(statusId) + '"></i></span>';
        }

        html += '<span style="' + descStyle + '">' + $('<span>').text(task.description).html() + '</span>';
        html += linkHtml;
        html += '</div>';

        html += '<div class="d-flex align-items-center">';
        html += assignHtml;
        html += '<span class="' + getStatusBadgeClass(statusId) + ' me-2">' + statusName + '</span>';
        html += '<button class="btn btn-xs btn-outline-danger task-delete" ' +
            'data-task-id="' + task.id + '" title="' + gettext('Delete') + '">' +
            '<i class="fa fa-trash"></i></button>';
        html += '</div>';

        html += '</li>';
        return html;
    }

    function loadTasks() {
        ajaxSetup();
        $.ajax({
            url: apiBase + '?status=0&status=1&limit=50',
            type: 'GET',
            dataType: 'json',
            success: function (response) {
                var tasks = response.data || [];
                var $list = $('#pending-tasks-list');
                $list.empty();

                if (tasks.length === 0) {
                    $list.html('<li class="list-group-item text-muted text-center">' +
                        gettext('No pending tasks') + '</li>');
                } else {
                    for (var i = 0; i < tasks.length; i++) {
                        $list.append(renderTaskItem(tasks[i]));
                    }
                }
                $('#pending-tasks-count').text(tasks.length);
            },
            error: function () {
                $('#pending-tasks-list').html(
                    '<li class="list-group-item text-danger">' +
                    gettext('Error loading tasks') + '</li>'
                );
            }
        });
    }

    function createTask() {
        ajaxSetup();
        var description = $('#task-description').val().trim();
        var link = $('#task-link').val().trim();

        if (!description) {
            $('#task-description').addClass('is-invalid');
            return;
        }
        $('#task-description').removeClass('is-invalid');

        var data = {
            description: description,
            rols: []
        };
        if (link) {
            data.link = link;
        }

        $.ajax({
            url: apiBase + 'create_task/',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            dataType: 'json',
            success: function () {
                $('#createTaskModal').modal('hide');
                $('#task-description').val('');
                $('#task-link').val('');
                loadTasks();
            },
            error: function (xhr) {
                var msg = gettext('Error creating task');
                if (xhr.responseJSON) {
                    var errors = xhr.responseJSON;
                    var messages = [];
                    for (var key in errors) {
                        if (errors.hasOwnProperty(key)) {
                            messages.push(key + ': ' + errors[key]);
                        }
                    }
                    if (messages.length) {
                        msg = messages.join(', ');
                    }
                }
                alert(msg);
            }
        });
    }

    function changeStatus(taskId, newStatus) {
        ajaxSetup();
        $.ajax({
            url: apiBase + taskId + '/updated_task_status/',
            type: 'PATCH',
            contentType: 'application/json',
            data: JSON.stringify({status: newStatus}),
            dataType: 'json',
            success: function () {
                loadTasks();
            },
            error: function (xhr) {
                var msg = gettext('Error updating task status');
                if (xhr.responseJSON && xhr.responseJSON.task) {
                    msg = xhr.responseJSON.task;
                }
                alert(msg);
            }
        });
    }

    function assignTask(taskId) {
        ajaxSetup();
        $.ajax({
            url: apiBase + taskId + '/task_assign/',
            type: 'GET',
            dataType: 'json',
            success: function () {
                loadTasks();
            },
            error: function (xhr) {
                var msg = gettext('Error assigning task');
                if (xhr.responseJSON && xhr.responseJSON.task) {
                    msg = xhr.responseJSON.task;
                }
                alert(msg);
            }
        });
    }

    function deleteTask(taskId) {
        if (!confirm(gettext('Are you sure you want to delete this task?'))) {
            return;
        }
        ajaxSetup();
        $.ajax({
            url: apiBase + taskId + '/',
            type: 'DELETE',
            success: function () {
                loadTasks();
            },
            error: function () {
                alert(gettext('Error deleting task'));
            }
        });
    }

    function init() {
        loadTasks();

        $(document).on('click', '.task-toggle-status', function () {
            var taskId = $(this).data('task-id');
            var currentStatus = $(this).data('current-status');
            var newStatus = getNextStatus(currentStatus);
            changeStatus(taskId, newStatus);
        });

        $(document).on('click', '.task-assign', function () {
            var taskId = $(this).data('task-id');
            assignTask(taskId);
        });

        $(document).on('click', '.task-delete', function () {
            var taskId = $(this).data('task-id');
            deleteTask(taskId);
        });

        $('#btn-create-task').on('click', function () {
            createTask();
        });

        $('#task-description').on('keypress', function (e) {
            if (e.which === 13) {
                e.preventDefault();
                createTask();
            }
        });
    }

    return {
        init: init,
        loadTasks: loadTasks
    };
})();

$(document).ready(function () {
    PendingTasks.init();
});
