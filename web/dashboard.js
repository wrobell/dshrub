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
        + '<div>'
        + '<div class="value"></div>'
        + '<div id="plot-' + name + '" class="plot"></div>'
        + '</div>'
        + '</div>'
    );
    return new DataView(name);
}

function plot_add_item(plot, item) {
    x = new Date(item[0] * 1000);
    y = item[1];
    plot.add(x, y);
}

function panel_set_item_value(name, item) {
    $('div#panel-' + name + ' div.value').html(
        Math.round(item['value'] * 1000) / 1000
    );
}

function panel_initial_data(data) {
    size = data.length;
    console.log(
        'received initial data for ' + this.name + ', size=' + size
    );
    plot = this.plot;
    data.forEach(function(item, index, data) {
        plot_add_item(plot, item);
    });
    if (size > 0)
        panel_set_item_value(this.name, data[size - 1]);
    this.plot.draw();
}

// vim: sw=4:et:ai
