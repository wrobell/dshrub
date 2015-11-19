function DataView(name) {
    this.name = name;
    this.div_id = '#plot-' + name;
    this.plot_params = {
        xaxis: {mode: 'time'},
        'shadowSize': 0,
        'points': {
            'show': true,
            'fillColor': 'black',
            'lineWidth': 0,
            'radius': 2,
        },
    };
    this.plot = $.plot($('#plot-' + name), [[]], this.plot_params);
    this.data = new Array();
}

DataView.prototype.add = function(x, y) {
    this.data.push([x, y]);
    if (this.data.length > 24 * 3600)
        this.data.shift();
}

DataView.prototype.draw = function() {
    this.plot.setData([this.data]);
    this.plot.setupGrid();
    this.plot.draw();
}

function create_view(name) {
    $('#dashboard').append(
        '<div id="panel-' + name + '" class="data-plot">'
        + '<div class="title"></div>'
        + '<div id="plot-' + name + '" class="plot"></div>'
        + '</div>'
    );
    return new DataView(name);
}

// vim: sw=4:et:ai
