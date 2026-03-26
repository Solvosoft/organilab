document.addEventListener("DOMContentLoaded", () => {
    const STATUS = {
        PENDING: 0,
        IN_PROCESS: 1,
        FINISHED: 2,
    };

    let tasks = [];
    let searchQuery = "";

    const columnMap = {
        [STATUS.PENDING]: document.querySelector('[data-status="0"]'),
        [STATUS.IN_PROCESS]: document.querySelector('[data-status="1"]'),
        [STATUS.FINISHED]: document.querySelector('[data-status="2"]'),
    };

    const counters = {
        [STATUS.PENDING]: document.querySelector('[data-counter-status="0"]'),
        [STATUS.IN_PROCESS]: document.querySelector('[data-counter-status="1"]'),
        [STATUS.FINISHED]: document.querySelector('[data-counter-status="2"]'),
    };

    Object.entries(columnMap).forEach(([status, element]) => {
        if (!element) {
            console.warn(`No se encontró la columna para el estado ${status}`);
        }
    });

    Object.entries(counters).forEach(([status, element]) => {
        if (!element) {
            console.warn(`No se encontró el contador para el estado ${status}`);
        }
    });

    function getStatusColor(status) {
        if (status === STATUS.PENDING) return "border-warning";
        if (status === STATUS.IN_PROCESS) return "border-info";
        if (status === STATUS.FINISHED) return "border-success";
        return "border-secondary";
    }


    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text ?? "";
        return div.innerHTML;
    }

    function stripHtml(html) {
        const div = document.createElement("div");
        div.innerHTML = html ?? "";
        return div.textContent || div.innerText || "";
    }

    function createTaskCard(task) {
        const card = document.createElement("div");
        card.className = `task-card card mb-3 shadow-sm border-2 ${getStatusColor(task.status)}`;
        card.draggable = true;
        card.dataset.taskId = task.id;

        card.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2 border-bottom border-3">
                    <div class="pe-2 flex-grow-1  ">
                        <h6 class="card-title mb-1 text-break"
                            ${task.name.length > 60 ? `title="${escapeHtml(task.name)}" data-bs-toggle="tooltip"` : ""}
                        >${escapeHtml(task.name.length > 60 ? task.name.slice(0, 60) + "…" : task.name)}</h6>
                    </div>

                  <button class="btn btn-sm text-muted p-0 border-0 me-3 expand-description-btn btn-card-task"
                                data-task-id="${task.id}"
                                title="${gettext('Expand description')}"
                                type="button">
                                <i class="fa fa-arrows-alt" aria-hidden="true"></i>
                            </button>

                    <div class="dropdown ">
                        <button
                            class="btn btn-sm text-muted p-0 border-0 btn-card-task"
                            type="button"
                            title=${gettext('Actions')}
                            data-bs-toggle="dropdown"
                            aria-expanded="false"
                        >
                          <i class="fa fa-ellipsis-v me-1" aria-hidden="true"></i>
                        </button>

                        <ul class="dropdown-menu dropdown-menu-end">
                            <li>
                                <button class="dropdown-item update-task-btn" type="button" data-task-id="${task.id}">
                                    <i class="fa fa-pencil me-2 text-warning" aria-hidden="true"></i>
                                    ${gettext("Edit task")}
                                </button>
                            </li>
                            <li>
                                <button class="dropdown-item delete-task-btn" type="button" data-task-id="${task.id}" data-task-name="${task.name}">
                                    <i class="fa fa-trash me-2 text-danger" aria-hidden="true"></i>
                                    ${gettext("Delete task")}
                                </button>
                            </li>
                            ${task.status === STATUS.FINISHED ? `
                            <li>
                                <button class="dropdown-item archive-task-btn" type="button" data-task-id="${task.id}">
                                    <i class="fa fa-archive me-2 text-secondary" aria-hidden="true"></i>
                                    ${gettext("Archive task")}
                                </button>
                            </li>
                            ` : ""}
                        </ul>
                    </div>
                </div>

                ${task.description ? `<div class="mb-2 small text-secondary text-break description-text py-2 wysiwyg-preview"></div>` : ""}

                <div class="row mb-2 mx-0 gx-2 pt-1">
                    <div class="col text-muted small text-break"
                        ${task.profile && task.profile.length > 40 ? `title="${escapeHtml(task.profile)}" data-bs-toggle="tooltip"` : ""}
                    >
                        <i class="fa fa-user me-1" aria-hidden="true"></i>
                        ${task.profile
            ? escapeHtml(task.profile.length > 40 ? task.profile.slice(0, 40) + "…" : task.profile)
            : gettext("Unassigned")
        }
                    </div>
                    ${task.link
            ? `<div class="col-auto small">
                                <a href="${escapeHtml(task.link)}" target="_blank" rel="noopener noreferrer">
                                    <i class="fa fa-link" aria-hidden="true"></i>
                                    ${gettext("Open link")}
                                </a>
                            </div>`
            : ""
        }
                </div>

            </div>
        `;

        if (task.description) {
            card.querySelector(".wysiwyg-preview").innerHTML = task.description;
        }

        card.addEventListener("dragstart", handleDragStart);
        card.addEventListener("dragend", handleDragEnd);

        return card;
    }

    document.addEventListener("click", event => {
        const btn = event.target.closest(".expand-description-btn");
        if (!btn) return;

        const task = tasks.find(t => t.id === Number(btn.dataset.taskId));
        if (!task) return;

        document.getElementById("descriptionModalLabel").textContent = task.name;
        document.getElementById("descriptionModalBody1").innerHTML = task.description || "";
        document.getElementById("descriptionModalFooter").textContent = task.profile || gettext("Unassigned");

        const linkRow = document.getElementById("descriptionModalLinkRow");
        const linkEl = document.getElementById("descriptionModalBody2");
        if (task.link) {
            linkEl.href = task.link;
            linkRow.classList.remove("d-none");
        } else {
            linkRow.classList.add("d-none");
        }

        $("#descriptionModal").modal("show");
    });

    function getFilteredTasks() {
        if (!searchQuery) return tasks;
        const q = searchQuery.toLowerCase();
        return tasks.filter(task =>
            task.name.toLowerCase().includes(q)
        );
    }

    function renderTasks() {
        Object.values(columnMap).forEach(column => {
            if (column) {
                column.innerHTML = "";
            }
        });

        getFilteredTasks().forEach(task => {
            const column = columnMap[task.status];
            if (column) {
                column.appendChild(createTaskCard(task));
            }
        });

        renderEmptyStates();
        updateCounters();
        updateArchiveFinishedBtn();
    }

    function renderEmptyStates() {
        Object.entries(columnMap).forEach(([status, column]) => {
            if (!column) return;

            const hasTasks = tasks.some(task => String(task.status) === String(status));

            if (!hasTasks) {
                const empty = document.createElement("div");
                empty.className = "empty-column text-center text-muted py-4";
                empty.innerHTML = `
                    <i class="fa fa-inbox fs-3 d-block mb-2" aria-hidden="true"></i>
                    ${gettext("No tasks in this column")}
                `;
                column.appendChild(empty);
            }
        });
    }

    function updateCounters() {
        const filtered = getFilteredTasks();
        const pendingCount = filtered.filter(task => task.status === STATUS.PENDING).length;
        const inProcessCount = filtered.filter(task => task.status === STATUS.IN_PROCESS).length;
        const finishedCount = filtered.filter(task => task.status === STATUS.FINISHED).length;

        if (counters[STATUS.PENDING]) {
            counters[STATUS.PENDING].textContent = pendingCount;
        }

        if (counters[STATUS.IN_PROCESS]) {
            counters[STATUS.IN_PROCESS].textContent = inProcessCount;
        }

        if (counters[STATUS.FINISHED]) {
            counters[STATUS.FINISHED].textContent = finishedCount;
        }
    }

    function loadTasks() {
        fetch(object_urls.list_url, {
            headers: {"X-CSRFToken": getCookie("csrftoken")}
        })
            .then(r => r.json())
            .then(data => {
                tasks = (data.data || []).map(task => ({
                    id: task.id,
                    name: task.name,
                    description: task.description,
                    status: task.status.id,
                    profile: task.profile ? task.profile.text : null,
                    link: task.link || "",
                    is_archived: task.is_archived
                }));
                renderTasks();
            })
            .catch(err => {
                console.error("Error loading tasks:", err);
            });
    }

    let draggedTaskId = null;

    function handleDragStart(event) {
        draggedTaskId = Number(event.currentTarget.dataset.taskId);
        event.currentTarget.classList.add("dragging");
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", String(draggedTaskId));
    }

    function handleDragEnd(event) {
        event.currentTarget.classList.remove("dragging");
        document.querySelectorAll(".kanban-list").forEach(column => {
            column.classList.remove("drag-over");
        });
    }

    function setupColumnsDragAndDrop() {
        document.querySelectorAll(".kanban-list").forEach(column => {
            column.addEventListener("dragover", event => {
                event.preventDefault();
                column.classList.add("drag-over");
            });

            column.addEventListener("dragleave", () => {
                column.classList.remove("drag-over");
            });

            column.addEventListener("drop", event => {
                event.preventDefault();
                column.classList.remove("drag-over");

                const taskId = Number(event.dataTransfer.getData("text/plain") || draggedTaskId);
                const newStatus = Number(column.dataset.status);

                moveTaskToStatus(taskId, newStatus);
            });
        });
    }

    function moveTaskToStatus(taskId, newStatus) {
        const task = tasks.find(item => item.id === taskId);
        if (!task || task.status === newStatus) return;

        fetch(object_urls.update_url.replace("/0/", "/" + taskId + "/"), {
            method: "PATCH",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "Content-Type": "application/json",
            },
            body: JSON.stringify({status: newStatus}),
        })
            .then(r => {
                if (!r.ok) {
                    console.error("Error updating task status:", r.status, r.statusText);
                    return;
                }
                loadTasks();
            })
            .catch(err => console.error("Error updating task status:", err));
    }

    // Created action
    const createTaskBtn = document.getElementById("create-task-btn");
    let gtformecreate = GTBaseFormModal("#create_obj_modal", {}, {reload_table: false, type: "POST"});
    gtformecreate.hide_modal = function () {
        $(gtformecreate.form).find("ul.form_errors").remove();
        gtformecreate.instance.modal('hide');
    };
    gtformecreate.success = function (instance, data) {
        loadTasks();
    };
    gtformecreate.init();

    if (createTaskBtn) {
        createTaskBtn.addEventListener("click", () => {
            gtformecreate.instance.modal("show");
        });
    }

    // Update action
    let gtformupdate = GTBaseFormModal("#update_obj_modal", {}, {reload_table: false, type: "PUT"});
    gtformupdate.hide_modal = function () {
        $(gtformupdate.form).find("ul.form_errors").remove();
        gtformupdate.instance.modal('hide');
    };
    gtformupdate.success = function (instance, data) {
        loadTasks();
    };
    gtformupdate.init();

    let pendingUpdateData = null;
    let updateModalInitialized = false;

    gtformupdate.instance.on("shown.bs.modal", function () {
        if (!updateModalInitialized) {
            gt_find_initialize(gtformupdate.instance);
            updateModalInitialized = true;
        }
        if (pendingUpdateData) {
            gtformupdate.fill_form(pendingUpdateData);
            pendingUpdateData = null;
        }
    });

    document.addEventListener("click", function (e) {
        const btn = e.target.closest(".update-task-btn");
        if (!btn) return;

        const taskId = btn.dataset.taskId;
        gtformupdate.url = object_urls.update_url.replace("/0/", "/" + taskId + "/");

        fetch(object_urls.get_values_for_update_url.replace("/0/", "/" + taskId + "/"), {
            headers: {"X-CSRFToken": getCookie("csrftoken")}
        })
            .then(r => r.json())
            .then(data => {
                pendingUpdateData = data;
                gtformupdate.instance.modal("show");
            });
    });

    // Delete action
    let gtformdelete = GTBaseFormModal("#delete_obj_modal", {}, {reload_table: false, type: "DELETE", btn_class: ".delbtn"});
    gtformdelete.hide_modal = function () {
        gtformdelete.instance.modal('hide');
    };
    gtformdelete.success = function (instance, data) {
        loadTasks();
    };
    gtformdelete.init();

    document.addEventListener("click", function (e) {
        const btn = e.target.closest(".delete-task-btn");
        if (!btn) return;

        const taskId = btn.dataset.taskId;
        const taskName = btn.dataset.taskName;

        gtformdelete.url = object_urls.destroy_url.replace("/0/", "/" + taskId + "/");
        gtformdelete.instance.find(".objtext").text(taskName);
        gtformdelete.instance.modal("show");
    });

    // Archive all finished tasks action
    const archiveFinishedBtn = document.getElementById("archive-finished-btn");
    if (archiveFinishedBtn) {
        archiveFinishedBtn.addEventListener("click", function () {
            fetch(object_urls.archive_finished_url, {
                method: "POST",
                headers: {"X-CSRFToken": getCookie("csrftoken")},
            })
                .then(r => {
                    if (!r.ok) {
                        console.error("Error archiving finished tasks:", r.status, r.statusText);
                        return;
                    }
                    loadTasks();
                })
                .catch(err => console.error("Error archiving finished tasks:", err));
        });
    }

    function updateArchiveFinishedBtn() {
        const btn = document.getElementById("archive-finished-btn");
        if (!btn) return;
        const finishedCount = tasks.filter(task => task.status === STATUS.FINISHED).length;
        btn.classList.toggle("d-none", finishedCount < 1);
    }

    // search action
    const searchInput = document.getElementById("task-search-input");
    if (searchInput) {
        searchInput.addEventListener("input", function () {
            searchQuery = this.value.trim();
            renderTasks();
        });
    }

    // Archive action
    document.addEventListener("click", function (e) {
        const btn = e.target.closest(".archive-task-btn");
        if (!btn) return;

        const taskId = btn.dataset.taskId;

        fetch(object_urls.update_url.replace("/0/", "/" + taskId + "/"), {
            method: "PATCH",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "Content-Type": "application/json",
            },
            body: JSON.stringify({is_archived: true}),
        })
            .then(r => {
                if (!r.ok) {
                    console.error("Error archiving task:", r.status, r.statusText);
                    return;
                }
                loadTasks();
            })
            .catch(err => console.error("Error archiving task:", err));
    });

    setupColumnsDragAndDrop();
    loadTasks();
});
