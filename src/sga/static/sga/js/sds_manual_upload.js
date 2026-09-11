/*
 * Versión manual del autorrelleno de sustancias: la extracción solo se ejecuta
 * cuando el usuario hace clic en el botón de procesar.
 *
 * Requiere un botón con id="sds-process-btn" en el template.
 */
(function () {
  "use strict";

  var POLL_INTERVAL_MS = 2000;
  var MAX_POLLS = 60; // 2 minutos

  var config = window.sdsAutofill || {};
  var tokenInput = document.querySelector('input[type="hidden"][name="security_sheet"]');
  if (!tokenInput || !config.uploadUrl) {
    return;
  }

  var form = tokenInput.closest("form");
  var touched = new Set();
  var statusBox = createStatusBox();
  var processBtn = document.getElementById("sds-process-btn");

  if (!processBtn) {
    console.warn("sds_manual_upload: no se encontró el botón #sds-process-btn");
    return;
  }

  // Cualquier campo que la persona edite queda protegido frente al autorrelleno.
  if (form) {
    form.addEventListener("change", function (event) {
      if (event.target !== tokenInput && event.target.id) {
        touched.add(event.target.id);
      }
    });
  }

  // Habilitar/deshabilitar el botón según haya token
  function updateButtonState() {
    if (tokenInput.value) {
      processBtn.disabled = false;
      processBtn.classList.remove("disabled");
    } else {
      processBtn.disabled = true;
      processBtn.classList.add("disabled");
    }
  }

  // Verificar estado del botón periódicamente (el widget cambia el valor por JS)
  window.setInterval(updateButtonState, 500);
  updateButtonState();

  // Al hacer clic en el botón, ejecutar upload
  processBtn.addEventListener("click", function (event) {
    event.preventDefault();
    if (tokenInput.value) {
      upload(tokenInput.value);
    } else {
      setStatus(config.messages.uploadFailed || "No hay archivo para procesar", "warning");
    }
  });

  function createStatusBox() {
    var box = document.createElement("div");
    box.className = "sds-autofill-status";
    box.setAttribute("role", "status");
    box.setAttribute("aria-live", "polite");
    box.style.display = "none";
    box.style.marginTop = "8px";
    tokenInput.parentNode.parentNode.parentNode.appendChild(box);
    return box;
  }

  function setStatus(message, kind) {
    statusBox.textContent = message;
    statusBox.className = "sds-autofill-status text-" + (kind || "info");
    statusBox.style.display = message ? "block" : "none";
  }

  function upload(token) {
    var data = new FormData();
    data.append("security_sheet", token);
    data.append("csrfmiddlewaretoken", config.csrfToken);
    data.append("name", document.querySelector('input[type="text"][name="name"]').value);
    setStatus(config.messages.uploading, "info");

    // Deshabilitar botón mientras procesa
    processBtn.disabled = true;

    fetch(config.uploadUrl, {
      method: "POST",
      body: data,
      credentials: "same-origin",
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (response) {
        return response.json().then(function (payload) {
          if (!response.ok || !payload.ok) {
            throw new Error(payload.message || config.messages.uploadFailed);
          }
          return payload;
        });
      })
      .then(function (payload) {
        if (payload.substance_pk) {
          rememberSubstance(payload.substance_pk);
        }
        setStatus(config.messages.processing, "info");
        poll(payload.task_id, 0);

      })
      .catch(function (error) {
        setStatus(error.message || config.messages.uploadFailed, "danger");
        processBtn.disabled = false;
      });
  }

  function rememberSubstance(substancePk) {
    if (!form || !config.stepOneUrlTemplate) {
      return;
    }
    if (form.action.indexOf("/" + substancePk + "/") === -1) {
      form.action = config.stepOneUrlTemplate.replace("__pk__", substancePk);
    }
  }

  function poll(taskId, attempt) {
    if (!taskId) {
      setStatus(config.messages.uploadFailed, "danger");
      processBtn.disabled = false;
      return;
    }
    if (attempt >= MAX_POLLS) {
      setStatus(config.messages.timedOut, "warning");
      processBtn.disabled = false;
      return;
    }

    fetch(config.statusUrl + "?task_id=" + encodeURIComponent(taskId), {
      credentials: "same-origin",
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (response) {
        return response.json();
      })
      .then(function (payload) {
        if (!payload.end) {
          window.setTimeout(function () {
            poll(taskId, attempt + 1);
          }, POLL_INTERVAL_MS);
          return;
        }
        if (payload.state !== "SUCCESS" || !payload.result) {
          setStatus(config.messages.extractionFailed, "warning");
          processBtn.disabled = false;
          return;
        }
        applyResult(payload.result);

      })
      .catch(function () {
        setStatus(config.messages.extractionFailed, "warning");
        processBtn.disabled = false;
      });
  }

  function applyResult(result) {
    if (!result.ok) {
      setStatus(result.message || config.messages.extractionFailed, "warning");
      processBtn.disabled = false;
      return;
    }
    form.submit();

  }

})();
