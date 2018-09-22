var hash = document.location.hash;
if (hash) {
    $('.nav-tabs a[href=' + hash + ']').tab('show');
}

// Change hash for page-reload
$('.nav-tabs a').on('shown.bs.tab', function (e) {
    window.location.hash = e.target.hash;
});