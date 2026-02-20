Chart.plugins.unregister(ChartDataLabels);
Chart.plugins.register({
    afterDatasetsDraw: function(chart) {
        if (!chart.options.plugins || !chart.options.plugins.showDataLabels) return;

        var ctx = chart.ctx;
        chart.data.datasets.forEach(function(dataset, i) {
            var meta = chart.getDatasetMeta(i);
            if (!meta.hidden) {
                meta.data.forEach(function(element, index) {
                    var dataString = dataset.data[index];
                    if (dataString === 0) return;
                    ctx.fillStyle = '#333';
                    ctx.font = 'bold 11px Arial';
                    ctx.textAlign = 'left';
                    ctx.textBaseline = 'middle';
                    var position = element.tooltipPosition();
                    ctx.fillText(dataString, position.x + 5, position.y);
                });
            }
        });
    }
});
