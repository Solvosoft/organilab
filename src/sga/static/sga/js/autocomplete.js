/*
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 13 sept. 2018
@author: Guillermo Castro Sánchez
@email: guillermoestebancs@gmail.com
*/

var $conflict = jQuery.noConflict();
$conflict(document).ready(function () {
    //Search sustance with autocomplete
    $conflict("#sustances").autocomplete({
        source: "search_autocomplete_sustance",
        //Start predicting at character #1
        minLength: 1
    })
});