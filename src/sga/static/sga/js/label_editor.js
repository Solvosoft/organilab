/*
@organization: Solvo
@license: GNU General Public License v3.0
@date: Created on 4 oct. 2018
@author: Guillermo Castro Sánchez
@email: guillermoestebancs@gmail.com
*/

// Default to true for browsers, false for node, it enables objectCaching at object level.
fabric.Object.prototype.objectCaching = false;
// Enabled to avoid blurry effects for big scaling
fabric.Object.prototype.noScaleCache = true;
// Improve Canvas perfomance
fabric.Object.prototype.statefullCache = false;
fabric.Object.prototype.needsItsOwnCache = false;

$(document).ready(function () {
    // Destroy canvas editor when user return to previous section and create a new canvas editor
    $("#Previous").click(function () {
        if (hasClass(label_editor, 'active')) {
            var _Canvas = null;
            $('#canvas_editor').hide();
            if (_Canvas)
                _Canvas.clear();
            _Canvas = null;
            $('#canvas_editor').siblings('.upper-canvas').remove();
            $('#canvas_editor').parent('.canvas-container').before($('#canvas_editor'));
            $('.canvas_editor').remove();
            var canvas = "<div class='col-sm-6 canvas_editor'><br><canvas id='canvas_editor' class='pre_designed_template'></canvas></div>";
            $("#addCanvas").after(canvas);
        }
    });
    // Side menu canvas editor
    $("#accordion").on("hidden.bs.collapse", function (e) {
        $(e.target).closest(".panel-primary")
            .find(".panel-heading span")
            .removeClass("glyphicon glyphicon-minus")
            .addClass("glyphicon glyphicon-plus");
    });
    $("#accordion").on("shown.bs.collapse", function (e) {
        $(e.target).closest(".panel-primary")
            .find(".panel-heading span")
            .removeClass("glyphicon glyphicon-plus")
            .addClass("glyphicon glyphicon-minus");
    });
});