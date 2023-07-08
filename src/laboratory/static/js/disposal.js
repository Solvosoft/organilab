$(document).ready(function() {
var chart ="";
var shelfname="";
$('.shelf_button').click(e=>{
    shelf=e.currentTarget.dataset.shelf;
    unit=e.currentTarget.dataset.unit;
    quantity=e.currentTarget.dataset.quantity;
    shelfname=e.currentTarget.dataset.shelfname;
    document.querySelector('#shelf_description').textContent=`${limit} ${quantity} ${unit}`;
    document.querySelector('#shelf_title').textContent=shelfname;
    $.ajax({
            url: shelfurl['list']+'?shelf='+shelf,
            type: 'GET',
            success: function(data) {
                let rows=""

                let table = document.querySelector('#tbody_substance');
                table.innerHTML="";
                data.forEach(e=>
                    rows+=`<tr><td>${e.object_name}</td><td>${e.quantity} ${e.unit}</td><td>${e.last_update}</td><td>${e.created_by}</td><td>${e.action}</td></tr>`
                );
                table.innerHTML=rows;
                const total = data.reduce((accumulator, currentValue) => accumulator + currentValue.quantity,0);
                document.querySelector('#foot').innerHTML=`<tr><td>Total</td><td>${total}</td></tr>`;
            }
            });
     });

     $('.shelf_graphic').click(e=>{
          shelf=e.currentTarget.dataset.shelf;
          shelfname=e.currentTarget.dataset.shelfname;
      $.ajax({
            url: shelfurl['graphic']+'?shelf='+shelf,
            type: 'GET',
            success: function({data,labels}) {
                set_graphic(data,labels)
            }
     });
     });
     function set_graphic(data,labels){
        var ctx = document.getElementById('myChart');
        if(chart){
            chart.destroy()
        }
        chart = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: "Sustancias",
                data: data,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            plugins: {
                   legend: {
                            display: false
                             },
                   title: {
                            display:true,
                            text:shelfname

                   }
          },
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }]
            }
        }
    });
}
document.getElementById('graphic_download').addEventListener('click', function(e) {
    let canvasUrl = document.getElementById('myChart').toDataURL('image/jpg');

    const createA = document.createElement('a');
    createA.href = canvasUrl;
    createA.download = shelfname;
    createA.click();
    createA.remove();

     });
$('.close_div').click((e)=> {
    let icon = $(e).find('i');
    console.log(icon)
      icon.toggleClass('fa-chevron-up fa-chevron-down');

     });
});
