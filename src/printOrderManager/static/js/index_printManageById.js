// This functions is called when the document is ready
$(document).ready(function () {});

function updateText() {
    //alert("Cambie de estado");
}

$('.count').each(function () {
    $(this).prop('Counter', 0).animate({
        Counter: $(this).text()
    }, {
        duration: 2000,
        easing: 'swing',
        step: function (now) {
            $(this).text(Math.ceil(now));
        }
    });
});