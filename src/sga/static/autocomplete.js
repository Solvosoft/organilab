/*
Created on 13 sept. 2018

@author: Guillermo
*/

$(document).ready(function () {
    //Search sustance with autocomplete
    $("#sustances").autocomplete({
        source: "search_autocomplete_sustance",
        //Start predicting at character #1
        minLength: 1
    })
});