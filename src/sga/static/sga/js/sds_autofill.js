/*
 * Paso 1 del asistente de sustancias: al subir la ficha de seguridad se encola
 * su extracción y se rellenan los campos con lo que el PDF haya dado.
 *
 * La extracción es heurística, así que el resultado es una propuesta: nunca se
 * pisa un campo que la persona ya haya tocado, y si falla la ficha queda subida
 * igual para rellenar a mano.
 */
(function () {
  "use strict";

  var POLL_INTERVAL_MS = 2000;
  var MAX_POLLS = 60; // 2 minutos

  var config = window.sdsAutofill || {};
  /* El widget de gentelella sube el PDF por trozos a su propio endpoint y deja
   * el token en este campo oculto; ahí es donde hay que engancharse, no en el
   * <input type="file"> visible, que solo alimenta esa subida. */
  var tokenInput = document.querySelector('input[type="hidden"][name="security_sheet"]');
  if (!tokenInput || !config.uploadUrl) {
    return;
  }

  var form = tokenInput.closest("form");
  var touched = new Set();
  var statusBox = createStatusBox();
  var lastToken = tokenInput.value;

  // Cualquier campo que la persona edite queda protegido frente al autorrelleno.
  if (form) {
    form.addEventListener("change", function (event) {
      if (event.target !== tokenInput && event.target.id) {
        touched.add(event.target.id);
      }
    });
  }

  // El widget rellena el campo oculto por JS, así que 'change' no siempre salta:
  // se vigila su valor.
  window.setInterval(function () {
    if (tokenInput.value && tokenInput.value !== lastToken) {
      lastToken = tokenInput.value;
      upload(tokenInput.value);
    }
  }, 500);

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
    // El token consume el ChunkedUpload en servidor y deja el PDF en la ficha.
    data.append("security_sheet", token);
    data.append("csrfmiddlewaretoken", config.csrfToken);
    data.append("name", document.querySelector('input[type="text"][name="name"]').value)
    setStatus(config.messages.uploading, "info");

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
      });
  }

  /* La sustancia puede haber nacido con esta subida: a partir de ahora el
   * formulario debe guardar sobre ella y no crear una segunda. */
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
      return;
    }
    if (attempt >= MAX_POLLS) {
      setStatus(config.messages.timedOut, "warning");
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
          return;
        }
        applyResult(payload.result);
      })
      .catch(function () {
        setStatus(config.messages.extractionFailed, "warning");
      });
  }

  function applyResult(result) {
    if (!result.ok) {
      setStatus(result.message || config.messages.extractionFailed, "warning");
      return;
    }
    reloadCharacteristics(result.fields || []);
  }

  /* La tarea ya escribió en la base de datos, así que en vez de reconstruir los
   * valores desde el JSON se recarga el formulario con los datos guardados: así
   * los selectores múltiples y los catálogos quedan coherentes.
   *
   * Recargar descartaría lo que la persona llevara escrito, así que solo se hace
   * sola si aún no ha tocado nada; si ya editó, se le ofrece decidir. */
  function reloadCharacteristics(fields) {
    if (!fields.length) {
      setStatus(config.messages.nothingExtracted, "warning");
      return;
    }

    if (touched.size === 0) {
      setStatus(config.messages.extracted, "success");
      window.setTimeout(function () {
        window.location.reload();
      }, 1200);
      return;
    }

    setStatus(config.messages.extractedNeedsReload, "success");
    if(!document.querySelector('input[type="text"][name="name"]')) {
        var button = document.createElement("button");
        button.type = "button";
        button.className = "btn btn-sm btn-success";
        button.style.marginLeft = "8px";
        button.textContent = config.messages.loadExtracted;
        button.addEventListener("click", function () {
            window.location.reload();
        });
        statusBox.appendChild(button);
    }else{
        var button = document.createElement("button");
        button.type = "submit";
        button.className = "btn btn-sm btn-success";
        button.style.marginLeft = "8px";
        button.textContent = gettext("Continue");
        statusBox.appendChild(button);
    }
  }
})();
