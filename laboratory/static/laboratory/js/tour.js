/**
 * Created by jaquer on 09/01/17.
 */

var print = x => console.log(x);

$.ajax({
    method: 'get',
    url: '/_ajax/get_tour_steps',
    success: (data) => {
        /*var tour_steps = JSON.parse(data.content);
        var tour = new Tour({
            steps: tour_steps,
            template: 'tourtemplate'
        });*/
        //print(JSON.parse(data.content));
        print(data);
        var aux = JSON.parse(data.content);
        print(aux);
        var tour = new Tour({
          steps : aux.steps,
          template : aux.template
        });
        print(tour);

        tour.init();
        tour.start();
    }
});
