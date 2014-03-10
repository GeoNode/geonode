function pieChart() {
  nv.addGraph(function() {
    var chart = nv.models.pieChart()
        .x(function(d) { return d.label })
        .y(function(d) { return d.value })
        .showLabels(true)


    d3.select("#chart")
        .datum(exampleData())
        .transition().duration(1200)
        .call(chart);

    return chart;
  });
}

function donut() {
  nv.addGraph(function() {
    var chart = nv.models.pieChart()
        .x(function(d) { return d.label })
        .y(function(d) { return d.value })
        .showLabels(true)
        .labelThreshold(.05)  //Configure the minimum slice size for labels to show up
        .labelType("key")	//Configure what type of data to show in the label. Can be "key", "value" or "percent"
        .donut(true)
        .donutRatio(0.35);


    d3.select("#chart2")
        .datum(exampleData())
        .transition().duration(1200)
        .call(chart);

    return chart;
  });
};

 function exampleData() {
   return [
	   { 
		 "label" : "CDS / Options" ,
		 "value" : 29.765957771107
	   } , 
	   { 
		 "label" : "Cash" , 
		 "value" : 0
	   } , 
	   { 
		 "label" : "Corporate Bonds" , 
		 "value" : 32.807804682612
	   } , 
	   { 
		 "label" : "Equity" , 
		 "value" : 196.45946739256
	   } , 
	   { 
		 "label" : "Index Futures" ,
		 "value" : 0.19434030906893
	   } , 
	   { 
		 "label" : "Options" , 
		 "value" : 98.079782601442
	   } , 
	   { 
		 "label" : "Preferred" , 
		 "value" : 13.925743130903
	   } , 
	   { 
		 "label" : "Not Available" , 
		 "value" : 5.1387322875705
	   }
	 ]
 };
pieChart();
