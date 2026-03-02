/* ============================================
   Organilab - Sitio de Capacitación
   JavaScript de navegación e interactividad
   ============================================ */

document.addEventListener('DOMContentLoaded', function () {
    initSidebar();
    initActiveNav();
});

/* ---- Sidebar Toggle (Móvil) ---- */
function initSidebar() {
    var toggleBtn = document.querySelector('.sidebar-toggle');
    var sidebar = document.querySelector('.sidebar');
    var overlay = document.querySelector('.sidebar-overlay');

    if (!toggleBtn || !sidebar) return;

    toggleBtn.addEventListener('click', function () {
        sidebar.classList.toggle('show');
        if (overlay) overlay.classList.toggle('show');
    });

    if (overlay) {
        overlay.addEventListener('click', function () {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }

    // Cerrar sidebar al hacer clic en un enlace (móvil)
    var navLinks = sidebar.querySelectorAll('.nav-link');
    navLinks.forEach(function (link) {
        link.addEventListener('click', function () {
            if (window.innerWidth <= 992) {
                sidebar.classList.remove('show');
                if (overlay) overlay.classList.remove('show');
            }
        });
    });
}

/* ---- Marcar enlace activo en la navegación ---- */
function initActiveNav() {
    var currentPath = window.location.pathname;
    var currentFile = currentPath.split('/').pop() || 'index.html';
    var navLinks = document.querySelectorAll('.sidebar-nav .nav-link');

    navLinks.forEach(function (link) {
        var href = link.getAttribute('href');
        if (!href) return;
        var linkFile = href.split('/').pop();

        link.classList.remove('active');

        if (linkFile === currentFile) {
            link.classList.add('active');
        }
    });
}
