// This functions is called when the document is ready
$(document).ready(function () {
    // Get each element from a li with the id=messages
    $("#messages li").each(function (index) {
        swal("Print registered!", $(this).text(), "success");
    });
});