//The default pie is a pieChart
var type = "pie";

function pieChart(data) {
  nv.addGraph(function() {
    var chart = nv.models.pieChart()
        .x(function(d) { return d.caption })
        .y(function(d) { return d.measure })
        .showLabels(true)
        .showLegend(false)
        .labelThreshold(10)  	//Configure the minimum slice size for labels to show up
        .labelType("value")	//Configure what type of data to show in the label. Can be "key", "value" or "percent"

    d3.select("#chart")
        .datum(data)
        .transition().duration(1200)
        .call(chart);

    return chart;
  });
}

function donutChart(data) {
  nv.addGraph(function() {
    var chart = nv.models.pieChart()
        .x(function(d) { return d.caption })
        .y(function(d) { return d.measure })
        .showLabels(true)
        .showLegend(false)
        .labelThreshold(.05)  	//Configure the minimum slice size for labels to show up
        .labelType("key")	//Configure what type of data to show in the label. Can be "key", "value" or "percent"
        .donut(true)
        .donutRatio(0.35);

    d3.select("#chart")
        .datum(data)
        .transition().duration(1200)
        .call(chart);

    return chart;
  });
};

function setType(type){
  this.type = type;
}

function setData(data){
  var funct;
  if(type=="pie"){
    console.log(type);
    funct = pieChart;
  }else{
    funct = donutChart;
  }
  funct(data);
}

// In the future this json will not more exist setData will be called by the class Display
d3.json("http://127.0.0.1:8000/static/analytics/data/data.json", function (biData) {
  setType("donut");
  setData(biData);
});