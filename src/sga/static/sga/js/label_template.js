/*
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 03 oct. 2018
@author: Guillermo Castro Sánchez
@email: guillermoestebancs@gmail.com
*/

$(document).ready(function () {
    // Change tab content  according to selected blank template 
    // Blank Templates
    // Blank Template: Vertical

    $("#button_blank_template_vertical").on("click", function () {

        //$("#blank_template").load('label_information.html');

        /*$.ajax({
             type: "POST",
             url: "{% include 'label_blank_template.html' %} ",
             dataType: "html",
         }).done(function (response) {
             $("#blank_template").attr("label_blank", "_vertical");
             $("#blank_template").html(response);
         });*/

        /*
        $.ajax({
            data: {
                csrfmiddlewaretoken: getCookie('csrftoken')
            },
            type: 'POST',
            async: false,
            url: 'label_blank_template',
            success: function (response) {
                $('#blank_template').html(response);
            }
        });*/


        $.ajax({
            url: "label_blank_template",
            dataType: "html",
            success: function(html) {
               $("#blank_template").attr("label_blank", "_vertical");
               $("#blank_template").html(html);   
            }
         });

    });
    // Blank Template: Horizontal
    $("#button_blank_template_horizontal").on("click", function () {
    });
    // Pre Designed Template: Vertical
    $("#button_pre_designed_template_vertical").on("click", function () {
        /* $("#blank_template").load("dir/page.html"); */
        alert("Click on pre designed template vertical");
    });
    // Pre Designed Template: Horizontal
    $("#button_pre_designed_template_horizontal").on("click", function () {
        /* $("#blank_template").load("dir/page.html"); */
        alert("Click on pre designed template horizontal");
    });
});

/* Set blank templates images according to recipient size */
function set_template_image() {

    // Show loading message
    waitingDialog.show('Loading...');

    var label_information = JSON.parse(localStorage.getItem('label_storage'));
    //Blank Template: Vertical
    $("#blank_template_vertical").attr("src", "https://dummyimage.com/300x400/ededed/0000007c/&text=" + label_information.height + label_information.height_unit + "+x+" + label_information.width + label_information.width_unit);
    //Blank Template: Horizontal
    $("#blank_template_horizontal").attr("src", "https://dummyimage.com/300x250/ededed/0000007c/&text=" + label_information.height + label_information.height_unit + "+x+" + label_information.width + label_information.width_unit);

    // Hide loading message after 3 seconds
    setTimeout(function () { waitingDialog.hide() }, 500);
}