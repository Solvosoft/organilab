document.addEventListener("DOMContentLoaded", () => {
    const STATUS = {
        PENDING: 0,
        IN_PROCESS: 1,
        FINISHED: 2,
    };

    let temporaryTasks = [
        {
            id: 1,
            description: "Documentar organilab",
            status: STATUS.PENDING,
            profile: "Wilfredo",
            link: "",
        },
        {
            id: 2,
            description: "Renombrar los reportes a nombres más significativos",
            status: STATUS.PENDING,
            profile: "Wilfredo",
            link: "",
        },
        {
            id: 3,
            description: "Eliminar async notification",
            status: STATUS.PENDING,
            profile: null,
            link: "",
        },
        {
            id: 4,
            description: "Migrar de Django 5.2 a 6",
            status: STATUS.IN_PROCESS,
            profile: "Admin",
            link: "",
        },
        {
            id: 5,
            description: "Agregar el Punto G",
            status: STATUS.FINISHED,
            profile: null,
            link: "https://example.com",
        },
    ];

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

    const createTaskBtn = document.getElementById("create-task-btn");

    function getStatusColor(status) {
        if (status === STATUS.PENDING) return "border-warning";
        if (status === STATUS.IN_PROCESS) return "border-info";
        if (status === STATUS.FINISHED) return "border-success";
        return "border-secondary";
    }

    // console.log("columnMap:", columnMap);
    // console.log("counters:", counters);

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

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text ?? "";
        return div.innerHTML;
    }

    function getStatusLabel(status) {
        if (status === STATUS.PENDING) return gettext("Pending");
        if (status === STATUS.IN_PROCESS) return gettext("In process");
        if (status === STATUS.FINISHED) return gettext("Finished");
        return "";
    }

    function createTaskCard(task) {
        const card = document.createElement("div");
        card.className = `task-card card mb-3 shadow-sm border-2 ${getStatusColor(task.status)}`;
        card.draggable = true;
        card.dataset.taskId = task.id;

        card.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div class="pe-2 flex-grow-1">
                        <h6 class="card-title mb-1">#${task.id} ${escapeHtml(task.description)}</h6>
                        <div class="small text-muted">${getStatusLabel(task.status)}</div>
                    </div>

                    <div class="dropdown">
                        <button
                            class="btn btn-sm btn-link text-muted p-0"
                            type="button"
                            title=${gettext('Actions')}
                            data-bs-toggle="dropdown"
                            aria-expanded="false"
                        >
                          <i class="fa fa-ellipsis-v me-1" aria-hidden="true"></i>
                        </button>

                        <ul class="dropdown-menu dropdown-menu-end">
                            <li>
                                <button class="dropdown-item js-edit-task" type="button" data-task-id="${task.id}">
                                    <i class="fa fa-pencil me-2 text-warning" aria-hidden="true"></i>
                                    ${gettext("Edit task")}
                                </button>
                            </li>
                            <li>
                                <button class="dropdown-item js-delete-task" type="button" data-task-id="${task.id}">
                                    <i class="fa fa-trash me-2 text-danger" aria-hidden="true"></i>
                                    ${gettext("Delete task")}
                                </button>
                            </li>
                        </ul>
                    </div>
                </div>

                ${
            task.profile
                ? `
                        <div class="mb-2 text-muted small">
                            <i class="fa fa-user me-1" aria-hidden="true"></i>
                            ${escapeHtml(task.profile)}
                        </div>
                    `
                : `
                        <div class="mb-2 text-muted small">
                            <i class="fa fa-user me-1" aria-hidden="true"></i>
                            ${gettext("Unassigned")}
                        </div>
                    `
        }

                ${
            task.link
                ? `
                        <div class="mb-2">
                            <a href="${escapeHtml(task.link)}" target="_blank" rel="noopener noreferrer">
                                <i class="fa fa-link" aria-hidden="true"></i>
                                ${gettext("Open link")}
                            </a>
                        </div>
                    `
                : ""
        }

            </div>
        `;

        card.addEventListener("dragstart", handleDragStart);
        card.addEventListener("dragend", handleDragEnd);

        return card;
    }

    function renderTasks() {
        Object.values(columnMap).forEach(column => {
            if (column) {
                column.innerHTML = "";
            }
        });

        temporaryTasks.forEach(task => {
            const column = columnMap[task.status];
            if (column) {
                column.appendChild(createTaskCard(task));
            }
        });

        renderEmptyStates();
        updateCounters();
        bindCardActions();
    }

    function renderEmptyStates() {
        Object.entries(columnMap).forEach(([status, column]) => {
            if (!column) return;

            const hasTasks = temporaryTasks.some(task => String(task.status) === String(status));

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
        const pendingCount = temporaryTasks.filter(task => task.status === STATUS.PENDING).length;
        const inProcessCount = temporaryTasks.filter(task => task.status === STATUS.IN_PROCESS).length;
        const finishedCount = temporaryTasks.filter(task => task.status === STATUS.FINISHED).length;

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

    function bindCardActions() {
        document.querySelectorAll(".js-delete-task").forEach(button => {
            button.addEventListener("click", () => {
                const taskId = Number(button.dataset.taskId);
                deleteTask(taskId);
            });
        });

        document.querySelectorAll(".js-edit-task").forEach(button => {
            button.addEventListener("click", () => {
                const taskId = Number(button.dataset.taskId);
                editTask(taskId);
            });
        });
    }

    function createTemporaryTask() {
        const description = window.prompt("Ingrese la descripción de la tarea:");
        if (!description || !description.trim()) return;

        const maxId = temporaryTasks.length
            ? Math.max(...temporaryTasks.map(task => task.id))
            : 0;

        const newTask = {
            id: maxId + 1,
            description: description.trim(),
            status: STATUS.PENDING,
            profile: null,
            link: "",
        };

        temporaryTasks.unshift(newTask);
        renderTasks();
    }

    function editTask(taskId) {
        const task = temporaryTasks.find(item => item.id === taskId);
        if (!task) return;

        const newDescription = window.prompt("Editar descripción de la tarea:", task.description);
        if (!newDescription || !newDescription.trim()) return;

        task.description = newDescription.trim();
        renderTasks();
    }

    function deleteTask(taskId) {
        const confirmed = window.confirm("¿Desea eliminar esta tarea?");
        if (!confirmed) return;

        temporaryTasks = temporaryTasks.filter(task => task.id !== taskId);
        renderTasks();
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
        const task = temporaryTasks.find(item => item.id === taskId);
        if (!task) return;

        task.status = newStatus;
        renderTasks();
    }

    if (createTaskBtn) {
        createTaskBtn.addEventListener("click", createTemporaryTask);
    }

    setupColumnsDragAndDrop();
    renderTasks();
});
