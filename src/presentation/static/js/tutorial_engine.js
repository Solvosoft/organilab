/**
 * OrganiLab Tutorial Engine
 * Shows tutorial steps as a sticky banner at the top of .right_col,
 * pushing content down and staying visible on scroll.
 */
(function () {
    'use strict';

    var config = null;
    var currentTutorial = null;
    var currentStepIndex = 0;
    var overlay = null;
    var banner = null;
    var menu = null;

    function getCookie(name) {
        var value = '; ' + document.cookie;
        var parts = value.split('; ' + name + '=');
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }

    function sendProgress(tutorialId, stepOrder, completed, dismissed) {
        if (!config || !config.progressUrl) return;
        fetch(config.progressUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tutorial_id: tutorialId,
                step_order: stepOrder,
                completed: !!completed,
                dismissed: !!dismissed
            })
        }).catch(function () {});
    }

    /* ------------------------------------------------------------------ */
    /* Overlay (for HIGHLIGHT steps)                                        */
    /* ------------------------------------------------------------------ */

    function createOverlay() {
        removeOverlay();
        overlay = document.createElement('div');
        overlay.className = 'tutorial-overlay';
        overlay.addEventListener('click', function (e) { e.stopPropagation(); });
        document.body.appendChild(overlay);
    }

    function removeOverlay() {
        if (overlay) { overlay.remove(); overlay = null; }
        var highlighted = document.querySelector('.tutorial-highlighted');
        if (highlighted) { highlighted.classList.remove('tutorial-highlighted'); }
    }

    /* ------------------------------------------------------------------ */
    /* Banner                                                               */
    /* ------------------------------------------------------------------ */

    function getRightCol() {
        return document.querySelector('.right_col');
    }

    function removeBanner() {
        if (banner) { banner.remove(); banner = null; }
    }

    function showBanner(step, stepIndex, totalSteps) {
        removeBanner();

        var prevLabel   = typeof gettext === 'function' ? gettext('Previous') : 'Anterior';
        var nextLabel   = typeof gettext === 'function' ? gettext('Next')     : 'Siguiente';
        var skipLabel   = typeof gettext === 'function' ? gettext('Skip')     : 'Omitir';
        var finishLabel = typeof gettext === 'function' ? gettext('Finish')   : 'Finalizar';

        var isFirst = stepIndex === 0;
        var isLast  = stepIndex === totalSteps - 1;

        var imgHtml = step.imageUrl
            ? '<img src="' + step.imageUrl + '" class="tutorial-banner-img" alt="">'
            : '';

        var leftBtn = isFirst
            ? '<button class="btn btn-sm btn-outline-light tutorial-skip">' + skipLabel + '</button>'
            : '<button class="btn btn-sm btn-outline-light tutorial-prev">' + prevLabel + '</button>';

        var rightBtn = isLast
            ? '<button class="btn btn-sm btn-success tutorial-finish">' + finishLabel + '</button>'
            : '<button class="btn btn-sm btn-light tutorial-next">' + nextLabel + '</button>';

        banner = document.createElement('div');
        banner.className = 'tutorial-banner';
        banner.innerHTML =
            '<div class="tutorial-banner-inner">' +
                '<div class="tutorial-banner-text">' +
                    '<div class="tutorial-banner-title">' + step.title + '</div>' +
                    '<div class="tutorial-banner-content">' + step.content + imgHtml + '</div>' +
                '</div>' +
                '<div class="tutorial-banner-controls">' +
                    '<span class="tutorial-banner-counter">' + (stepIndex + 1) + ' / ' + totalSteps + '</span>' +
                    leftBtn +
                    rightBtn +
                '</div>' +
            '</div>';

        // Insert as first child of .right_col so it pushes content down
        var rightCol = getRightCol();
        if (rightCol) {
            rightCol.insertBefore(banner, rightCol.firstChild);
        } else {
            document.body.insertBefore(banner, document.body.firstChild);
        }

        banner.querySelector('.tutorial-skip')   && banner.querySelector('.tutorial-skip').addEventListener('click', skipTutorial);
        banner.querySelector('.tutorial-prev')   && banner.querySelector('.tutorial-prev').addEventListener('click', prevStep);
        banner.querySelector('.tutorial-next')   && banner.querySelector('.tutorial-next').addEventListener('click', nextStep);
        banner.querySelector('.tutorial-finish') && banner.querySelector('.tutorial-finish').addEventListener('click', completeTutorial);
    }

    /* ------------------------------------------------------------------ */
    /* Steps                                                                */
    /* ------------------------------------------------------------------ */

    function resolveSelector(step) {
        if (step.selector) return step.selector;
        var marker = document.querySelector('[data-tutorial-step="' + step.key + '"]');
        if (!marker) return null;
        return marker.getAttribute('data-tutorial-target') || '[data-tutorial-step="' + step.key + '"]';
    }

    function showStep(stepIndex) {
        if (!currentTutorial || stepIndex < 0 || stepIndex >= currentTutorial.steps.length) return;

        removeOverlay();
        currentStepIndex = stepIndex;
        var step = currentTutorial.steps[stepIndex];
        var totalSteps = currentTutorial.steps.length;

        sendProgress(currentTutorial.id, stepIndex, false, false);

        if (step.type === 'HIGHLIGHT') {
            var selector = resolveSelector(step);
            var targetEl = selector ? document.querySelector(selector) : null;
            if (targetEl) {
                targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                createOverlay();
                targetEl.classList.add('tutorial-highlighted');
            }
        }

        showBanner(step, stepIndex, totalSteps);
    }

    function nextStep() {
        var step = currentTutorial.steps[currentStepIndex];
        if (step && step.actionUrl) {
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
        if (currentStepIndex > 0) showStep(currentStepIndex - 1);
    }

    function skipTutorial() {
        if (currentTutorial) sendProgress(currentTutorial.id, currentStepIndex, false, true);
        currentTutorial = null;
        removeOverlay();
        removeBanner();
    }

    function completeTutorial() {
        if (currentTutorial) {
            sendProgress(currentTutorial.id, currentTutorial.steps.length - 1, true, false);
        }
        currentTutorial = null;
        removeOverlay();
        removeBanner();
    }

    /* ------------------------------------------------------------------ */
    /* FAB Menu                                                             */
    /* ------------------------------------------------------------------ */

    function showMenu() {
        if (menu) { closeMenu(); return; }
        if (!config || !config.tutorials || config.tutorials.length === 0) return;

        menu = document.createElement('div');
        menu.className = 'tutorial-menu';

        var headerText = typeof gettext === 'function' ? gettext('Available tutorials') : 'Tutoriales disponibles';
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

        setTimeout(function () {
            document.addEventListener('click', closeMenuOnOutsideClick);
        }, 100);
    }

    function closeMenu() {
        if (menu) { menu.remove(); menu = null; }
        document.removeEventListener('click', closeMenuOnOutsideClick);
    }

    function closeMenuOnOutsideClick(e) {
        if (menu && !menu.contains(e.target) && !e.target.classList.contains('tutorial-fab')) {
            closeMenu();
        }
    }

    /* ------------------------------------------------------------------ */
    /* Public                                                               */
    /* ------------------------------------------------------------------ */

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

        // Cross-page resume
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

        // Auto-start
        if (config.autoStart && config.autoStart.length > 0) {
            setTimeout(function () { startTutorial(config.autoStart[0]); }, 800);
        }
    }

    window.OrganiLabTutorial = {
        init: init,
        start: startTutorial,
        next: nextStep,
        prev: prevStep,
        skip: skipTutorial,
        complete: completeTutorial,
        showMenu: showMenu
    };

    document.addEventListener('DOMContentLoaded', function () {
        if (window._tutorialConfig) init(window._tutorialConfig);
    });
})();
