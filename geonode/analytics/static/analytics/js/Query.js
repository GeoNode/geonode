var Query = {

  /**
   * List of metadatas already loaded from DB
   */
  metadatas : {},

  /** 
   * Save new metadatas
   */
  saveNewMetadatas : function (data) {

    this.metadatas = this.mergeObjects(this.metadatas, data);

  },

  /** 
   * Merge 2 JSON objects
   * Used to merge old metadatas with new one comming from the DB
   * 
   * TODO : Code this thing
   * Problem : metadatas aren't based on "key => value" scheme. We have a lot of simple arrays containing the key in the "name" attribute.
   * Therefore you need to check if an element with the same "name" attribute exists...
   * 
   * Idea : Change the metadatas to get a key => value system.
   */
  mergeObjects : function (obj1, obj2) {
    
    return obj2;

  },

  mapWithCaptionToSimpleMap : function (map) {
    var out = {};
    for (key in map)
    {
      out[key] = map[key]['caption'];
    }

    return out;
  },

  /**
   * Get schemas list
   */
  getSchemas : function () {
    
    // not cached ? load metadata
    // TODO real query
    if (this.metadatas.schemas == undefined) {

      that = this;
      
      $.ajaxSetup({async:false});
      $.get("/static/analytics/data/dimensions.json", function(response) {
        that.saveNewMetadatas(response.data);
      });
    }

    // retour de la map simple
    return this.mapWithCaptionToSimpleMap(this.metadatas.schemas);
  },

  /**
   * Get cubes of a schema
   */
  getCubes : function (schema) {

    var schemas = this.getSchemas();

    // schema non existing
    if (schemas[schema] == undefined)
      return false;

    // not cached
    // TODO real query
    if (this.metadatas.schemas[schema] == undefined) {

      that = this;
      
      $.ajaxSetup({async:false});
      $.get("/static/analytics/data/dimensions.json", function(response) {
        that.saveNewMetadatas(response.data);
      });
    }

    // retour de la map simple
    return this.mapWithCaptionToSimpleMap(this.metadatas.schemas[schema].cubes);
  },

  /**
   * Get mesures of a cube and a schema
   */
  getMesures : function (schema, cube) {
    // TODO
    return this.metadatas.schemas[schema].cubes[cube].measures;
  },

  getDimensions : function (schema, cube) {
    // TODO
    return this.mapWithCaptionToSimpleMap(this.metadatas.schemas[schema].cubes[cube].dimensions);
  },

  getGeoDimension : function (schema, cube) {

    return this.getXXDimension(schema, cube, "geometric");

  },

  getTimeDimension : function (schema, cube) {

    return this.getXXDimension(schema, cube, "time");

  },

  getXXDimension : function (schema, cube, type) {

    dimensions = this.getDimensions(schema, cube);
    for (dimension in dimensions) {
      hierarchies = this.getHierachies(schema, cube, dimension);
      for (hierachy in hierarchies) {
        levels = this.getLevels(schema, cube, dimension, hierachy);
        if (levels[0].type == type)
          return dimension;
      }
    }

    return false;

  },

  getGeoProperty : function (schema, cube, dimension, hierachy) {

    properties = this.getProperties(schema, cube, dimension, hierachy, 0);
    for (property in properties) {
      if (properties[property].type == "geometric")
          return property;
    }

    return false;

  },

  getHierachies : function (schema, cube, dimension) {

    // TODO
    return this.mapWithCaptionToSimpleMap(this.metadatas.schemas[schema].cubes[cube].dimensions[dimension].hierarchies);
  },

  getLevels : function (schema, cube, dimension, hierachy) {

    // TODO
    return this.metadatas.schemas[schema].cubes[cube].dimensions[dimension].hierarchies[hierachy].levels;
  },

  getMembers : function (schema, cube, dimension, hierachy, levelID) {
    // TODO
    //return this.metadatas.schemas[schema].cubes[cube].dimensions[dimension].hierarchies[hierachy].levels[levelID].properties;
  },

  getProperties : function (schema, cube, dimension, hierachy, levelID) {
    // TODO
    try {
      return this.metadatas.schemas[schema].cubes[cube].dimensions[dimension].hierarchies[hierachy].levels[levelID].properties;
    }
    catch(e) {
      return false;
    }
  },

  getPropertyValues : function (schema, cube, dimension, hierachy, levelID, property, members) {
    // TODO
    var data;

    $.ajaxSetup({async:false});
    $.get("/static/analytics/data/properties.topo.json", function(dataResponse) {
      data = dataResponse;
    });

    return data.data.schemas[schema].cubes[cube].dimensions[dimension].hierarchies[hierachy].levels[levelID].properties[property].values;
  },


  getData : function () {

    var dataReturn = null;

    $.ajaxSetup({async:false});
    $.get("/static/analytics/data/data.json", function(data) {
      dataReturn = data;
    });

    return dataReturn;
  },

  /**
   * Reset the query
   */
  reset : function () {
    this.jsonQuery = null;
  }

} 