var Charts = {  
  chart : null,
  type : "pie",
  
  init : function (selector) {
    this.chart = d3.select(selector);    
  },
  
  setType : function (type){
    this.type = type;
  },
  
  setData: function (data){
    var funct;
    
    //TODO Modifie this when we have more graphs
    if(this.type=="pie"){
      funct = this.pieChart;
    }else{
      funct = this.donutChart;
    }
    funct(data);
  },  
  
  pieChart : function (data) {
    nv.addGraph(function() {
      var values = d3.values(data);
      
      var pie = nv.models.pieChart()
          .x(function(d) { return d.caption })
          .y(function(d) { return d.measure })
          .showLabels(true)
          .showLegend(false)
          .labelThreshold(10)     //Configure the minimum slice size for labels to show up
          .labelType("value")     //Configure what type of data to show in the label. Can be "key", "value" or "percent"

      Charts.chart
          .datum(values)
          .transition().duration(1200)
          .call(pie);

      return chart;
    });
  },

  donutChart : function (data) {
    nv.addGraph(function() {
      var values = d3.values(data);
      
      var donut = nv.models.pieChart()
          .x(function(d) { return d.caption })
          .y(function(d) { return d.measure })
          .showLabels(true)
          .showLegend(false)
          .labelThreshold(.05)    //Configure the minimum slice size for labels to show up
          .labelType("key")       //Configure what type of data to show in the label. Can be "key", "value" or "percent"
          .donut(true)
          .donutRatio(0.35);

      Charts.chart
          .datum(values)
          .transition().duration(1200)
          .call(donut);

      return chart;
    });
  },
}