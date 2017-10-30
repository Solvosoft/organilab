/**
 * Created by jaquer on 09/01/17.
 */

$.ajax({
    method: 'get',
    url: '/_ajax/get_tour_steps_furniture',
    success: (data) => {
        var aux = JSON.parse(data.content);
        var tour = new Tour({
          steps : JSON.parse(aux.steps),
          template : aux.template
        });

        console.log(aux);

        tour.init();
        tour.start();
    }
});
