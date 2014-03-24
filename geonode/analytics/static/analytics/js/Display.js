var Display = {

  schemas : null,
  schema : null,
  cubes : null,
  cube : null,
  measures : null,
  mesure : null,

  init : function (mapSelector, chartSelector, timelineSelector, tableSelector) {

    //// DATA INIT

    // Select 1st schema
    this.schemas = Query.getSchemas();
    for (this.schema in this.schemas) break;
    
    // Select 1st cube
    this.cubes = Query.getCubes(this.schema);
    for (this.cube in this.cubes) break;

    // Select 1st measure
    this.measures = Query.getMesures(this.schema, this.cube);
    for (this.measure in this.measures) break;

    // Select 1st measure
    this.measures = Query.getMesures(this.schema, this.cube);
    for (this.measure in this.measures) break;

    // Get dimensions
    geoDimension = Query.getGeoDimension(this.schema, this.cube);
    timeDimension = Query.getTimeDimension(this.schema, this.cube);

    // geoHierachy
    for (geoHierachy in Query.getHierachies(this.schema, this.cube, geoDimension)) break;

    // Get geo property
    geoProperty = Query.getGeoProperty(this.schema, this.cube, geoDimension, geoHierachy);

    //// DISPLAY INIT

    // init map
    Map.init(mapSelector);

    //// DISPLAY MAP

    // Affichage de la carte
    Map.setGeoData(Query.getPropertyValues(this.schema, this.cube, geoDimension, geoHierachy, 0, geoProperty), 0);

    // Calcul des couleurs des données
    biData = Display.quantize(Query.getData(), 30);

    // Coloration de la carte
    Map.setData(biData);
    
    //// DISPLAY TABLE
    Table.init(tableSelector);
    
    // TODO modifier le paramètre labels
    Table.setData(biData,['Pays','Valeur'],false);    
    
    //// DISPLAY CHART
    Charts.init(chartSelector);
    Charts.setType('pie');
    Charts.setData(biData);  
  },

  /**
   * Quantize the data : for each element in the data, define a class number (quantize member in each element) and a color (color member)
   */
  quantize : function (data, nbColors) {

    var dataList = d3.map(data).values(data);

    var minMax = d3.extent(dataList, function (d) { return d.measure; });
    
    // Function that will translate value to colorClass
    var quantize = d3.scale.quantize()
        .domain(minMax)
        .range(d3.range(nbColors));
        //.map(function(i) { return "q" + i + "-9"; }));

    // Generate color gradient
    var color = d3.scale.linear()
    .domain([0, (nbColors - 1) / 2, nbColors - 1])
    .range(["#f7fbff", "#6baed6", "#08306b"]);

    // compute class and color for each data
    d3.map(data).forEach(function(key, value) {
      data[key].quantize = quantize(value.measure);
      data[key].color    = color(data[key].quantize);
    });

    return data;
  },



}