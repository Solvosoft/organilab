/**
 * Created by jaquer on 09/01/17.
 */

$.ajax({
    method: 'get',
    url: '/_ajax/get_tour_steps',
    success: function (data){
        var tour_steps = JSON.parse(data.content);
        console.log(tour_steps);
        var tour = new Tour({
            steps: tour_steps
        });
        
        tour.init();
        tour.start();
    }
});