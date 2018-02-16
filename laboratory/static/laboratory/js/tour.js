/**
 * Created by jaquer on 09/01/17.
 */

$.ajax({
    method: 'get',
    url: '/_ajax/get_tour_steps',
    success: function (data){
        var tour_steps = JSON.parse(data.content);
        var tour = new Tour({
            steps: tour_steps,
            template: '<div class="popover" role="tooltip"> <div class="arrow"></div> <h3 class="popover-title"></h3> <div class="popover-content"></div> <div class="popover-navigation"> <div class="btn-group"> <button class="btn btn-sm btn-default" data-role="prev">Atras</button> <button class="btn btn-sm btn-default" data-role="next">Siguiente</button> <button class="btn btn-sm btn-default" data-role="pause-resume" data-pause-text="Pause" data-resume-text="Resume">Pause</button> </div> <button class="btn btn-sm btn-default" data-role="end">Finalizar tour</button> </div> </div>'
        });
        
        tour.init();
        tour.start();
    }
});