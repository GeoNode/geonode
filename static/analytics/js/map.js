
var container = d3.select("body").append("svg")
	.attr("width", 2000)
	.attr("height", 2000)
	  


d3.json("continent_Europe_subunits", function (data) {
	  
	var zoom = d3.behavior.zoom()
		  .translate([0, 0])
		  .scale(1)
		  .scaleExtent([1, 8])
		  .on("zoom", zoomed);	
		  
	var drag = d3.behavior.drag()
		.origin(function(d) {return d;})
		.on("dragstart", dragstarted)
		.on("drag", dragged)
		.on("dragend", dragended);
		  
		  var group = container.selectAll("g")
			  .data(data.features)
			.enter()
			  .append("g")
			  .call(zoom)
			  .call(drag)
			  
		  var projection = d3.geo.mercator().center([40, 60]).scale(400)
		  var path = d3.geo.path().projection(projection);
		  
		  var areas = group.append("path")
			  .attr("d", path)
			  .attr("fill", "steelblue")
			  .on("mouseover", color)
			  .on("mouseout", decolor);
});
	
function zoomed() {
  container.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
}
	
function dragstarted(d) {
  d3.event.sourceEvent.stopPropagation();
  d3.select(this).classed("dragging", true);
}

function dragged(d) {
}

function dragended(d) {
  d3.select(this).classed("dragging", false);
}

function color(d) {
  d3.select(this).classed("rouge",true);
  d3.select(this).classed("area",false);
}

function decolor(d) {
  d3.select(this).classed("area",true);
  d3.select(this).classed("rouge",false);
} 
