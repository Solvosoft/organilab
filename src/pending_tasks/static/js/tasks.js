document.addEventListener("DOMContentLoaded", () => {
    const STATUS = {
        PENDING: 0,
        IN_PROCESS: 1,
        FINISHED: 2
    };
    const STATUS_COLOR = {
        [STATUS.PENDING]: "border-warning",
        [STATUS.IN_PROCESS]: "border-info",
        [STATUS.FINISHED]: "border-success",
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

    //  API

    function apiPatch(taskId, data) {
        return fetch(object_urls.update_url.replace("/0/", `/${taskId}/`), {
            method: "PATCH",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        });
    }

    // Card
    function createTaskCard(task) {
        const tpl = document.getElementById("task-card-tpl");
        const card = tpl.content.cloneNode(true).firstElementChild;

        card.classList.add(STATUS_COLOR[task.status] ?? "border-secondary");
        card.dataset.taskId = task.id;

        // Name
        const nameEl = card.querySelector(".js-name");
        nameEl.textContent = task.name.length > 60 ? task.name.slice(0, 60) + "…" : task.name;
        if (task.name.length > 60) {
            nameEl.title = task.name;
            nameEl.dataset.bsToggle = "tooltip";
        }

        // Task id on action buttons
        card.querySelector(".expand-description-btn").dataset.taskId = task.id;
        card.querySelector(".update-task-btn").dataset.taskId = task.id;
        card.querySelector(".delete-task-btn").dataset.taskId = task.id;
        card.querySelector(".delete-task-btn").dataset.taskName = task.name;

        // Archive (only for finished)
        const archiveItem = card.querySelector(".js-archive-item");
        if (task.status === STATUS.FINISHED) {
            archiveItem.classList.remove("d-none");
            archiveItem.querySelector(".archive-task-btn").dataset.taskId = task.id;
        }

        // Description (wysiwyg HTML)
        if (task.description) {
            const descEl = card.querySelector(".js-description");
            descEl.classList.remove("d-none");
            descEl.innerHTML = task.description;
        }

        // Profile
        const profileSpan = card.querySelector(".js-profile-text");
        if (task.profile) {
            profileSpan.textContent = task.profile.length > 40 ? task.profile.slice(0, 40) + "…" : task.profile;
            if (task.profile.length > 40) {
                card.querySelector(".js-profile").title = task.profile;
                card.querySelector(".js-profile").dataset.bsToggle = "tooltip";
            }
        } else {
            profileSpan.textContent = gettext("Unassigned");
        }

        // Link
        if (task.link) {
            const linkEl = card.querySelector(".js-link");
            linkEl.classList.remove("d-none");
            linkEl.querySelector(".js-link-anchor").href = task.link;
        }

        card.addEventListener("dragstart", handleDragStart);
        card.addEventListener("dragend", handleDragEnd);

        return card;
    }

    // --------- Render ---------

    function getFilteredTasks() {
        if (!searchQuery) return tasks;
        const q = searchQuery.toLowerCase();
        return tasks.filter(t =>
            t.name.toLowerCase().includes(q) ||
            (t.profile && t.profile.toLowerCase().includes(q))
        );
    }

    function renderTasks() {
        Object.values(columnMap).forEach(col => {
            if (col) col.innerHTML = "";
        });
        getFilteredTasks().forEach(task => {
            const col = columnMap[task.status];
            if (col) col.appendChild(createTaskCard(task));
        });
        renderEmptyStates();
        updateCounters();
        updateArchiveFinishedBtn();
    }

    function renderEmptyStates() {
        Object.entries(columnMap).forEach(([status, col]) => {
            if (!col) return;
            if (!tasks.some(t => String(t.status) === String(status))) {
                const empty = document.createElement("div");
                empty.className = "empty-column text-center text-muted py-4";
                empty.innerHTML = `<i class="fa fa-inbox fs-3 d-block mb-2" aria-hidden="true"></i>${gettext("No tasks in this column")}`;
                col.appendChild(empty);
            }
        });
    }

    function updateCounters() {
        const filtered = getFilteredTasks();
        Object.entries(counters).forEach(([status, el]) => {
            if (el) el.textContent = filtered.filter(t => t.status === Number(status)).length;
        });
    }

    function updateArchiveFinishedBtn() {
        const btn = document.getElementById("archive-finished-btn");
        if (btn) btn.classList.toggle("d-none", !tasks.some(t => t.status === STATUS.FINISHED));
    }

    // --------- Drag & Drop ---------
    let draggedTaskId = null;

    function handleDragStart(event) {
        draggedTaskId = Number(event.currentTarget.dataset.taskId);
        event.currentTarget.classList.add("dragging");
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", String(draggedTaskId));
    }

    function handleDragEnd(event) {
        event.currentTarget.classList.remove("dragging");
        document.querySelectorAll(".kanban-list").forEach(col => col.classList.remove("drag-over"));
    }

    function setupColumnsDragAndDrop() {
        document.querySelectorAll(".kanban-list").forEach(col => {
            col.addEventListener("dragover", e => {
                e.preventDefault();
                col.classList.add("drag-over");
            });
            col.addEventListener("dragleave", () => col.classList.remove("drag-over"));
            col.addEventListener("drop", e => {
                e.preventDefault();
                col.classList.remove("drag-over");
                const taskId = Number(e.dataTransfer.getData("text/plain") || draggedTaskId);
                const newStatus = Number(col.dataset.status);
                const task = tasks.find(t => t.id === taskId);
                if (!task || task.status === newStatus) return;
                apiPatch(taskId, {status: newStatus})
                    .then(r => {
                        if (r.ok) loadTasks(); else console.error("Error updating task status:", r.status);
                    })
                    .catch(err => console.error("Error updating task status:", err));
            });
        });
    }

    // --------- CRUD Modals ---------
    // Action list
    function loadTasks() {
        fetch(object_urls.list_url, {headers: {"X-CSRFToken": getCookie("csrftoken")}})
            .then(r => r.json())
            .then(data => {
                tasks = (data.data || []).map(t => ({
                    id: t.id,
                    name: t.name,
                    description: t.description,
                    status: t.status.id,
                    profile: t.profile ? t.profile.text : null,
                    link: t.link || "",
                    is_archived: t.is_archived,
                }));
                renderTasks();
            })
            .catch(err => console.error("Error loading tasks:", err));
    }

    // Action create
    let gtformecreate = GTBaseFormModal("#create_obj_modal", {}, {reload_table: false, type: "POST"});
    gtformecreate.hide_modal = () => {
        $(gtformecreate.form).find("ul.form_errors").remove();
        gtformecreate.instance.modal("hide");
    };
    gtformecreate.success = () => loadTasks();
    gtformecreate.init();

    const createTaskBtn = document.getElementById("create-task-btn");
    if (createTaskBtn) createTaskBtn.addEventListener("click", () => gtformecreate.instance.modal("show"));

    let gtformupdate = GTBaseFormModal("#update_obj_modal", {}, {reload_table: false, type: "PUT"});
    gtformupdate.hide_modal = () => {
        $(gtformupdate.form).find("ul.form_errors").remove();
        gtformupdate.instance.modal("hide");
    };
    gtformupdate.success = () => loadTasks();
    gtformupdate.init();

    // Action update
    let pendingUpdateData = null;
    let updateModalInitialized = false;

    gtformupdate.instance.on("shown.bs.modal", () => {
        if (!updateModalInitialized) {
            gt_find_initialize(gtformupdate.instance);
            updateModalInitialized = true;
        }
        if (pendingUpdateData) {
            gtformupdate.fill_form(pendingUpdateData);
            pendingUpdateData = null;
        }
    });

    // Action delete
    let gtformdelete = GTBaseFormModal("#delete_obj_modal", {}, {
        reload_table: false,
        type: "DELETE",
        btn_class: ".delbtn"
    });
    gtformdelete.hide_modal = () => gtformdelete.instance.modal("hide");
    gtformdelete.success = () => loadTasks();
    gtformdelete.init();

    // --- Event delegation ---
    document.addEventListener("click", e => {
        //update task
        const updateBtn = e.target.closest(".update-task-btn");
        if (updateBtn) {
            const taskId = updateBtn.dataset.taskId;
            gtformupdate.url = object_urls.update_url.replace("/0/", `/${taskId}/`);
            fetch(object_urls.get_values_for_update_url.replace("/0/", `/${taskId}/`), {
                headers: {"X-CSRFToken": getCookie("csrftoken")}
            }).then(r => r.json()).then(data => {
                pendingUpdateData = data;
                gtformupdate.instance.modal("show");
            });
            return;
        }

        // delete task
        const deleteBtn = e.target.closest(".delete-task-btn");
        if (deleteBtn) {
            gtformdelete.url = object_urls.destroy_url.replace("/0/", `/${deleteBtn.dataset.taskId}/`);
            gtformdelete.instance.find(".objtext").text(deleteBtn.dataset.taskName);
            gtformdelete.instance.modal("show");
            return;
        }

        //archive task
        const archiveBtn = e.target.closest(".archive-task-btn");
        if (archiveBtn) {
            apiPatch(archiveBtn.dataset.taskId, {is_archived: true})
                .then(r => {
                    if (r.ok) loadTasks(); else console.error("Error archiving task:", r.status);
                })
                .catch(err => console.error("Error archiving task:", err));
            return;
        }

        // expand card task
        const expandBtn = e.target.closest(".expand-description-btn");
        if (expandBtn) {
            const task = tasks.find(t => t.id === Number(expandBtn.dataset.taskId));
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
            return;
        }
    });

    // archived all task finished
    const archiveFinishedBtn = document.getElementById("archive-finished-btn");
    if (archiveFinishedBtn) {
        archiveFinishedBtn.addEventListener("click", () => {
            fetch(object_urls.archive_finished_url, {
                method: "POST",
                headers: {"X-CSRFToken": getCookie("csrftoken")},
            })
                .then(r => {
                    if (r.ok) loadTasks(); else console.error("Error archiving finished tasks:", r.status);
                })
                .catch(err => console.error("Error archiving finished tasks:", err));
        });
    }

    // search task by name
    const searchInput = document.getElementById("task-search-input");
    if (searchInput) searchInput.addEventListener("input", function () {
        searchQuery = this.value.trim();
        renderTasks();
    });

    setupColumnsDragAndDrop();
    loadTasks();
});
