/**
 * OrganiLab Tutorial Engine
 * Uses SweetAlert2 (already loaded) for modals and custom CSS overlay for highlights.
 */
(function () {
    'use strict';

    var config = null;
    var currentTutorial = null;
    var currentStepIndex = 0;
    var overlay = null;
    var tooltip = null;
    var menu = null;

    function getCookie(name) {
        var value = '; ' + document.cookie;
        var parts = value.split('; ' + name + '=');
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }

    function sendProgress(tutorialId, stepOrder, completed, dismissed) {
        if (!config || !config.progressUrl) return;
        var data = {
            tutorial_id: tutorialId,
            step_order: stepOrder,
            completed: !!completed,
            dismissed: !!dismissed
        };
        fetch(config.progressUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        }).catch(function () {});
    }

    function removeOverlay() {
        if (overlay) {
            overlay.remove();
            overlay = null;
        }
    }

    function removeTooltip() {
        if (tooltip) {
            tooltip.remove();
            tooltip = null;
        }
        var highlighted = document.querySelector('.tutorial-highlighted');
        if (highlighted) {
            highlighted.classList.remove('tutorial-highlighted');
        }
    }

    function cleanup() {
        removeOverlay();
        removeTooltip();
        closeMenu();
    }

    function createOverlay() {
        removeOverlay();
        overlay = document.createElement('div');
        overlay.className = 'tutorial-overlay';
        overlay.addEventListener('click', function (e) {
            e.stopPropagation();
        });
        document.body.appendChild(overlay);
    }

    function positionTooltip(targetEl, step) {
        var rect = targetEl.getBoundingClientRect();
        var pos = step.position || 'bottom';
        var gap = 16;

        tooltip.classList.remove('tooltip-top', 'tooltip-bottom', 'tooltip-left', 'tooltip-right');
        tooltip.classList.add('tooltip-' + pos);

        // Reset
        tooltip.style.top = '';
        tooltip.style.bottom = '';
        tooltip.style.left = '';
        tooltip.style.right = '';

        var tooltipRect = tooltip.getBoundingClientRect();

        var scrollX = window.scrollX || window.pageXOffset;
        var scrollY = window.scrollY || window.pageYOffset;

        switch (pos) {
            case 'bottom':
                tooltip.style.top = (rect.bottom + scrollY + gap) + 'px';
                tooltip.style.left = Math.max(8, rect.left + scrollX + (rect.width / 2) - (tooltipRect.width / 2)) + 'px';
                break;
            case 'top':
                tooltip.style.top = (rect.top + scrollY - tooltipRect.height - gap) + 'px';
                tooltip.style.left = Math.max(8, rect.left + scrollX + (rect.width / 2) - (tooltipRect.width / 2)) + 'px';
                break;
            case 'right':
                tooltip.style.top = (rect.top + scrollY + (rect.height / 2) - (tooltipRect.height / 2)) + 'px';
                tooltip.style.left = (rect.right + scrollX + gap) + 'px';
                break;
            case 'left':
                tooltip.style.top = (rect.top + scrollY + (rect.height / 2) - (tooltipRect.height / 2)) + 'px';
                tooltip.style.left = (rect.left + scrollX - tooltipRect.width - gap) + 'px';
                break;
        }
    }

    function renderStepNav(step, stepIndex, totalSteps) {
        var prevLabel = gettext ? gettext('Previous') : 'Anterior';
        var nextLabel = gettext ? gettext('Next') : 'Siguiente';
        var skipLabel = gettext ? gettext('Skip') : 'Omitir';
        var finishLabel = gettext ? gettext('Finish') : 'Finalizar';

        var isFirst = stepIndex === 0;
        var isLast = stepIndex === totalSteps - 1;

        var html = '<div class="tutorial-nav">';
        if (!isFirst) {
            html += '<button class="btn btn-sm btn-default tutorial-prev">' + prevLabel + '</button>';
        } else {
            html += '<button class="btn btn-sm btn-default tutorial-skip">' + skipLabel + '</button>';
        }
        html += '<span class="tutorial-step-indicator">' + (stepIndex + 1) + ' / ' + totalSteps + '</span>';
        if (isLast) {
            html += '<button class="btn btn-sm btn-success tutorial-finish">' + finishLabel + '</button>';
        } else {
            html += '<button class="btn btn-sm btn-primary tutorial-next">' + nextLabel + '</button>';
        }
        html += '</div>';
        return html;
    }

    function showHighlightStep(step, stepIndex, totalSteps) {
        var selector = step.selector;
        // Also look for data-tutorial-step markers
        if (!selector) {
            var marker = document.querySelector('[data-tutorial-step="' + step.key + '"]');
            if (marker) {
                var target = marker.getAttribute('data-tutorial-target');
                if (target) {
                    selector = target;
                } else {
                    selector = '[data-tutorial-step="' + step.key + '"]';
                }
            }
        }

        var targetEl = selector ? document.querySelector(selector) : null;
        if (!targetEl) {
            // Fallback to modal if element not found
            showModalStep(step, stepIndex, totalSteps);
            return;
        }

        targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });

        setTimeout(function () {
            createOverlay();
            targetEl.classList.add('tutorial-highlighted');

            removeTooltip();
            tooltip = document.createElement('div');
            tooltip.className = 'tutorial-tooltip tooltip-' + (step.position || 'bottom');

            var imgHtml = step.imageUrl ? '<img src="' + step.imageUrl + '" alt="">' : '';
            tooltip.innerHTML =
                '<div class="tutorial-step-title">' + step.title + '</div>' +
                '<div class="tutorial-step-content">' + step.content + imgHtml + '</div>' +
                renderStepNav(step, stepIndex, totalSteps);

            document.body.appendChild(tooltip);
            positionTooltip(targetEl, step);

            bindNavEvents(tooltip);
        }, 400);
    }

    function showPopoverStep(step, stepIndex, totalSteps) {
        // Use same logic as highlight but without overlay
        var selector = step.selector;
        if (!selector) {
            var marker = document.querySelector('[data-tutorial-step="' + step.key + '"]');
            if (marker) {
                var target = marker.getAttribute('data-tutorial-target');
                selector = target || '[data-tutorial-step="' + step.key + '"]';
            }
        }

        var targetEl = selector ? document.querySelector(selector) : null;
        if (!targetEl) {
            showModalStep(step, stepIndex, totalSteps);
            return;
        }

        targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });

        setTimeout(function () {
            removeOverlay();
            targetEl.classList.add('tutorial-highlighted');

            removeTooltip();
            tooltip = document.createElement('div');
            tooltip.className = 'tutorial-tooltip tooltip-' + (step.position || 'bottom');

            var imgHtml = step.imageUrl ? '<img src="' + step.imageUrl + '" alt="">' : '';
            tooltip.innerHTML =
                '<div class="tutorial-step-title">' + step.title + '</div>' +
                '<div class="tutorial-step-content">' + step.content + imgHtml + '</div>' +
                renderStepNav(step, stepIndex, totalSteps);

            document.body.appendChild(tooltip);
            positionTooltip(targetEl, step);

            bindNavEvents(tooltip);
        }, 400);
    }

    function showModalStep(step, stepIndex, totalSteps) {
        removeOverlay();
        removeTooltip();

        var prevLabel = gettext ? gettext('Previous') : 'Anterior';
        var nextLabel = gettext ? gettext('Next') : 'Siguiente';
        var skipLabel = gettext ? gettext('Skip') : 'Omitir';
        var finishLabel = gettext ? gettext('Finish') : 'Finalizar';

        var isFirst = stepIndex === 0;
        var isLast = stepIndex === totalSteps - 1;

        var imgHtml = step.imageUrl ? '<img src="' + step.imageUrl + '" style="max-width:100%;border-radius:4px;margin:10px 0" alt="">' : '';
        var footerHtml = '<div class="tutorial-step-indicator" style="margin-bottom:8px">' +
            (stepIndex + 1) + ' / ' + totalSteps + '</div>';

        Swal.fire({
            title: step.title,
            html: step.content + imgHtml + footerHtml,
            showCancelButton: true,
            showDenyButton: !isFirst,
            confirmButtonText: isLast ? finishLabel : nextLabel,
            cancelButtonText: skipLabel,
            denyButtonText: prevLabel,
            confirmButtonColor: '#1ABB9C',
            denyButtonColor: '#6c757d',
            allowOutsideClick: false,
            customClass: {
                popup: 'tutorial-swal-popup'
            }
        }).then(function (result) {
            if (result.isConfirmed) {
                if (isLast) {
                    completeTutorial();
                } else {
                    nextStep();
                }
            } else if (result.isDenied) {
                prevStep();
            } else if (result.dismiss === Swal.DismissReason.cancel) {
                skipTutorial();
            }
        });
    }

    function showStep(stepIndex) {
        if (!currentTutorial || stepIndex < 0 || stepIndex >= currentTutorial.steps.length) return;

        cleanup();
        currentStepIndex = stepIndex;
        var step = currentTutorial.steps[stepIndex];
        var totalSteps = currentTutorial.steps.length;

        sendProgress(currentTutorial.id, stepIndex, false, false);

        switch (step.type) {
            case 'HIGHLIGHT':
                showHighlightStep(step, stepIndex, totalSteps);
                break;
            case 'POPOVER':
                showPopoverStep(step, stepIndex, totalSteps);
                break;
            case 'MODAL':
            default:
                showModalStep(step, stepIndex, totalSteps);
                break;
        }
    }

    function bindNavEvents(container) {
        var prevBtn = container.querySelector('.tutorial-prev');
        var nextBtn = container.querySelector('.tutorial-next');
        var skipBtn = container.querySelector('.tutorial-skip');
        var finishBtn = container.querySelector('.tutorial-finish');

        if (prevBtn) prevBtn.addEventListener('click', prevStep);
        if (nextBtn) nextBtn.addEventListener('click', nextStep);
        if (skipBtn) skipBtn.addEventListener('click', skipTutorial);
        if (finishBtn) finishBtn.addEventListener('click', completeTutorial);
    }

    function nextStep() {
        var step = currentTutorial.steps[currentStepIndex];
        if (step && step.actionUrl) {
            // Save state for cross-page continuation
            sessionStorage.setItem('_tutorial_resume', JSON.stringify({
                slug: currentTutorial.slug,
                step: currentStepIndex + 1
            }));
            window.location.href = step.actionUrl;
            return;
        }
        if (currentStepIndex < currentTutorial.steps.length - 1) {
            showStep(currentStepIndex + 1);
        }
    }

    function prevStep() {
        if (currentStepIndex > 0) {
            showStep(currentStepIndex - 1);
        }
    }

    function skipTutorial() {
        if (currentTutorial) {
            sendProgress(currentTutorial.id, currentStepIndex, false, true);
        }
        currentTutorial = null;
        cleanup();
    }

    function completeTutorial() {
        if (currentTutorial) {
            sendProgress(currentTutorial.id, currentTutorial.steps.length - 1, true, false);
        }
        currentTutorial = null;
        cleanup();

        var finishedMsg = gettext ? gettext('Tutorial completed!') : 'Tutorial completado!';
        Swal.fire({
            icon: 'success',
            title: finishedMsg,
            timer: 2000,
            showConfirmButton: false
        });
    }

    function showMenu() {
        if (menu) {
            closeMenu();
            return;
        }
        if (!config || !config.tutorials || config.tutorials.length === 0) return;

        menu = document.createElement('div');
        menu.className = 'tutorial-menu';

        var headerText = gettext ? gettext('Available tutorials') : 'Tutoriales disponibles';
        var html = '<div class="tutorial-menu-header">' + headerText + '</div>';
        config.tutorials.forEach(function (t) {
            html += '<button class="tutorial-menu-item" data-slug="' + t.slug + '">' +
                '<div class="tutorial-menu-title">' + t.title + '</div>' +
                (t.description ? '<div class="tutorial-menu-desc">' + t.description + '</div>' : '') +
                '</button>';
        });
        menu.innerHTML = html;
        document.body.appendChild(menu);

        menu.querySelectorAll('.tutorial-menu-item').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var slug = this.getAttribute('data-slug');
                closeMenu();
                startTutorial(slug);
            });
        });

        // Close menu on outside click
        setTimeout(function () {
            document.addEventListener('click', closeMenuOnOutsideClick);
        }, 100);
    }

    function closeMenu() {
        if (menu) {
            menu.remove();
            menu = null;
        }
        document.removeEventListener('click', closeMenuOnOutsideClick);
    }

    function closeMenuOnOutsideClick(e) {
        if (menu && !menu.contains(e.target) && !e.target.classList.contains('tutorial-fab')) {
            closeMenu();
        }
    }

    function startTutorial(slug) {
        if (!config || !config.tutorials) return;
        for (var i = 0; i < config.tutorials.length; i++) {
            if (config.tutorials[i].slug === slug) {
                currentTutorial = config.tutorials[i];
                showStep(currentTutorial.currentStep || 0);
                return;
            }
        }
    }

    function init(cfg) {
        config = cfg;
        if (!config || !config.tutorials || config.tutorials.length === 0) return;

        // Check for cross-page resume
        var resumeData = sessionStorage.getItem('_tutorial_resume');
        if (resumeData) {
            sessionStorage.removeItem('_tutorial_resume');
            try {
                var resume = JSON.parse(resumeData);
                for (var i = 0; i < config.tutorials.length; i++) {
                    if (config.tutorials[i].slug === resume.slug) {
                        currentTutorial = config.tutorials[i];
                        showStep(resume.step);
                        return;
                    }
                }
            } catch (e) {}
        }

        // Auto-start tutorials
        if (config.autoStart && config.autoStart.length > 0) {
            setTimeout(function () {
                startTutorial(config.autoStart[0]);
            }, 800);
        }
    }

    // Public API
    window.OrganiLabTutorial = {
        init: init,
        start: startTutorial,
        next: nextStep,
        prev: prevStep,
        skip: skipTutorial,
        complete: completeTutorial,
        showMenu: showMenu
    };

    // Auto-init when config is available
    document.addEventListener('DOMContentLoaded', function () {
        if (window._tutorialConfig) {
            init(window._tutorialConfig);
        }
    });
})();
