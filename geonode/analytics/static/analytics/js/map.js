var width = $('#map-pane').width(),
//height = $('#map-pane').height();
height = 700;

d3.json("http://127.0.0.1:8000/static/analytics/data/europe.topo.json", function (geographicalData) {
  d3.json("http://127.0.0.1:8000/static/analytics/data/donnees.json", function (biData) {
    //Will be modified in the future
    var active;    
    
    // Begin of the class

    // class attribute
    var geoData = null;
    var areas = null;


    var svg = d3.select("#map-pane").append("svg")
	.attr("width", width)
	.attr("height", height);

    var g = svg.append("g");

    g.append("rect")
	.attr("class", "background")
	.attr("width", width)
	.attr("height", height)
	.on("click", reset);

    var europe = g.append("g")
	.attr("id", "Europe");

    // Create a unit projection.
    var projection = d3.geo.mercator()
	.scale(1)
	.translate([0, 0]);

    // Create a path generator.
    var path = d3.geo.path()
	.projection(projection);

    function setGeoData(geoData,levelID){
      var b = path.bounds(topojson.feature(geoData, geoData.objects.europe));
      var s = 0.95 / Math.max((b[1][0] - b[0][0]) / width, (b[1][1] - b[0][1]) / height);
      var t = [(width - s * (b[1][0] + b[0][0])) / 2, (height - s * (b[1][1] + b[0][1])) / 2];

      var center = d3.geo.centroid(topojson.feature(geoData, geoData.objects.europe));

      var t = [width/2, height/2];

      // Update the projection to center wuth the computed scale & center & translate.
      projection
	  .scale(s)
	  .center(center)
	  .translate(t);

      areas = europe.selectAll("path")
	  .data(topojson.feature(geoData, geoData.objects.europe).features)
	.enter().append("path")
	  .attr("d", path)
	  .on("click", clicked);

      function clicked(d) {
	if (active === d) return reset();
	g.selectAll(".active").classed("active", false);
	d3.select(this).classed("active", active = d);

	var b = path.bounds(d);
	var s = .95 / Math.max((b[1][0] - b[0][0]) / width, (b[1][1] - b[0][1]) / height);
	var t = [-(b[1][0] + b[0][0]) / 2 , -(b[1][1] + b[0][1]) / 2];

	g.transition().duration(750).attr("transform",
	    "translate(" + projection.translate() + ")"
	    + "scale(" + s + ")"
	    + "translate(" + t + ")");
      }
    }

    function reset() {
      g.selectAll(".active").classed("active", active = false);

      var b = path.bounds(geoData);
      var s = .95 / Math.max((b[1][0] - b[0][0]) / width, (b[1][1] - b[0][1]) / height);
      var t = [-(b[1][0] + b[0][0]) / 2 , -(b[1][1] + b[0][1]) / 2];

      g.transition().duration(750).attr("transform",
	  "translate(" + projection.translate() + ")"
	  + "scale(" + s + ")"
	  + "translate(" + t + ")");
    }

    // To do : before : one assert geoData was make
    function setData(data, levelID){
      var minMax = getMinMax(data);
      var measures = data.map(function (d){ return d.measure;});

      // Function that will translate value to colorClass
      var quantize = d3.scale.quantize()
          .domain(minMax)
          .range(d3.range(9).map(function(i) { return "q" + i + "-9"; }));

      areas.attr("class", function(d){ return idToColorClass(d.id); });

      function idToColorClass(id){
	var names = data.map(function(d){return d.name});

	return quantize(measures[indexOfInArrayOfArray(names,id)]);
      }
    }

    // tanks to indexOf that doesn't work on array of array we need this
    function indexOfInArrayOfArray(array,elmt){
      var i=0;
      var more = true;
      while((i<array.length) && more){
	if(equalsArrays(array[i],elmt)){
	  more = false;
	}
	i++;
      }
      if(more==false){
        return i-1;
      }else{
	return undefined;
      }
    }

    function equalsArrays(array1, array2) {
      if (array1.length == array2.length){
	var result=true;
	array1.forEach(function(d,i){
	  result = result && (d == array2[i])
	});
	return result;
      }else{
	return false;
      }
    }


    // Function that gives min and max of our data
    function getMinMax(data){
      var mesures=data.map(function(d) {return d.measure;});

      var result=[];
      result[0]=d3.min(mesures);
      result[1]=d3.max(mesures);
      return result;
    }

//     var t1 = ["Europe", "Pays1"];
//     var t2 = ["Europe", "Pays1"];
//     var t3 = ["Europe", "Pays2"];
//     var t4 = ["Europe", "Pays2", "test"];
//     var t5 = ["Europe", "Pays2", "test"];
//     console.log("test must be true : "+equalsArrays(t1,t2));
//     console.log("test must be false : "+equalsArrays(t1,t3));
//     console.log("test must be false : "+equalsArrays(t1,t4));
//     console.log("test must be true : "+equalsArrays(t5,t4));
    
//     var array1 = [
// 	      ["Europe", "Pays0"],
// 	      ["Europe", "Pays1"],
// 	      ["Europe", "Pays2"],
// 	      ["Europe", "Pays3"],
// 	      ["Europe", "Pays4"],
// 	      ["Europe", "Pays5"]];
//     
//     var t1 = ["Europe", "Pays32"];
//     var t2 = ["Europe", "Pays1"];
//     var t3 = ["Europe", "Pays5"];
//     var t4 = ["Asia", "Pays1"];
//     
//     console.log(biData);
//     console.log("test must be true : "+(indexOfInArrayOfArray(array1,t2)==1));
//     console.log("test must be true : "+(indexOfInArrayOfArray(array1,t1)==undefined));
//     console.log("test must be true : "+(indexOfInArrayOfArray(array1,t3)==5));
//     console.log("test must be true : "+(indexOfInArrayOfArray(array1,t4)==undefined));

    setGeoData(geographicalData);
    setData(biData);

  });
});
