$(function () {

    Morris.Bar({
        element: 'paperType-Graph',
        data: [{
                paperType: 'Paper Type 1',
                requested: 136
            },
            {
                paperType: 'Paper Type 2',
                requested: 137
            },
            {
                paperType: 'Paper Type 3',
                requested: 275
            },
            {
                paperType: 'Paper Type 4',
                requested: 380
            },
            {
                paperType: 'Paper Type 5',
                requested: 655
            },
            {
                paperType: 'Paper Type 5',
                requested: 1571
            }
        ],
        xkey: 'paperType',
        ykeys: ['requested'],
        labels: ['Orders with this paper type'],
        barRatio: 0.4,
        xLabelAngle: 35,
        hideHover: 'auto'
    });

    Morris.Donut({
        element: 'morris-donut-chart',
        data: [{
            label: "Orders Delivered",
            value: 5
        }, {
            label: "Orders In Process",
            value: 20
        }, {
            label: "Orders On The Way",
            value: 10
        }],
        resize: true
    });


});