/*
 * Copyright (c) 2010 Bjoern Hoehrmann <http://bjoern.hoehrmann.de/>.
 * This module is licensed under the same terms as OpenLayers itself.
 *
 */

Heatmap = {};

/**
 * Class: Heatmap.Source
 */
Heatmap.Source = OpenLayers.Class({

  /** 
   * APIProperty: lonlat
   * {OpenLayers.LonLat} location of the heat source
   */
  lonlat: null,

  /** 
   * APIProperty: radius
   * {Number} Heat source radius
   */
  radius: null,

  /** 
   * APIProperty: intensity
   * {Number} Heat source intensity
   */
  intensity: null,

  /**
   * Constructor: Heatmap.Source
   * Create a heat source.
   *
   * Parameters:
   * lonlat - {OpenLayers.LonLat} Coordinates of the heat source
   * radius - {Number} Optional radius
   * intensity - {Number} Optional intensity
   */
  initialize: function(lonlat, radius, intensity) {
    this.lonlat = lonlat;
    this.radius = radius;
    this.intensity = intensity;
  },

  CLASS_NAME: 'Heatmap.Source'
});

/**
 * Class: Heatmap.Layer
 * 
 * Inherits from:
 *  - <OpenLayers.Layer>
 */
Heatmap.Layer = OpenLayers.Class(OpenLayers.Layer, {

  /** 
   * APIProperty: isBaseLayer 
   * {Boolean} Heatmap layer is never a base layer.  
   */
  isBaseLayer: false,

  /** 
   * Property: points
   * {Array(<Heatmap.Source>)} internal coordinate list
   */
  points: null,

  /** 
   * Property: cache
   * {Object} Hashtable with CanvasGradient objects
   */
  cache: null,

  /** 
   * Property: gradient
   * {Array(Number)} RGBA gradient map used to colorize the intensity map.
   */
  gradient: null,

  /** 
   * Property: canvas
   * {DOMElement} Canvas element.
   */
  canvas: null,

  /** 
   * APIProperty: defaultRadius
   * {Number} Heat source default radius
   */
  defaultRadius: null,

  /** 
   * APIProperty: defaultIntensity
   * {Number} Heat source default intensity
   */
  defaultIntensity: null,

  /**
   * Constructor: Heatmap.Layer
   * Create a heatmap layer.
   *
   * Parameters:
   * name - {String} Name of the Layer
   * options - {Object} Hashtable of extra options to tag onto the layer
   */
  initialize: function(name, options) {
    OpenLayers.Layer.prototype.initialize.apply(this, arguments);
    this.points = [];
    this.cache = {};
    this.canvas = document.createElement('canvas');
    this.canvas.style.position = 'absolute';
    this.defaultRadius = 20;
    this.defaultIntensity = 0.2;
    this.setGradientStops({
      0.00: 0xffffff00,
      0.10: 0x99e9fdff,
      0.20: 0x00c9fcff,
      0.30: 0x00e9fdff,
      0.30: 0x00a5fcff,
      0.40: 0x0078f2ff,
      0.50: 0x0e53e9ff,
      0.60: 0x4a2cd9ff,
      0.70: 0x890bbfff,
      0.80: 0x99019aff,
      0.90: 0x990664ff,
      0.99: 0x660000ff,
      1.00: 0x000000ff
    });

    // For some reason OpenLayers.Layer.setOpacity assumes there is
    // an additional div between the layer's div and its contents.
    var sub = document.createElement('div');
    sub.appendChild(this.canvas);
    this.div.appendChild(sub);
  },

  /**
   * APIMethod: setGradientStops
   * ...
   *
   * Parameters:
   * stops - {Object} Hashtable with stop position as keys and colors
   *                  as values. Stop positions are numbers between 0
   *                  and 1, color values numbers in 0xRRGGBBAA form.
   */
  setGradientStops: function(stops) {

    // There is no need to perform the linear interpolation manually,
    // it is sufficient to let the canvas implementation do that.

    var ctx = document.createElement('canvas').getContext('2d');
    var grd = ctx.createLinearGradient(0, 0, 256, 0);

    for (var i in stops) {
      grd.addColorStop(i, 'rgba(' +
        ((stops[i] >> 24) & 0xFF) + ',' +
        ((stops[i] >> 16) & 0xFF) + ',' +
        ((stops[i] >>  8) & 0xFF) + ',' +
        ((stops[i] >>  0) & 0xFF) + ')');
    }

    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, 256, 1);
    this.gradient = ctx.getImageData(0, 0, 256, 1).data;
  },

  /**
   * APIMethod: addSource
   * Adds a heat source to the layer.
   *
   * Parameters:
   * source - {<Heatmap.Source>} 
   */
  addSource: function(source) {
    this.points.push(source);
  },

  /**
   * APIMethod: removeSource
   * Removes a heat source from the layer.
   * 
   * Parameters:
   * source - {<Heatmap.Source>} 
   */
  removeSource: function(source) {
    if (this.points && this.points.length) {
      OpenLayers.Util.removeItem(this.points, source);
    }
  },

  /** 
   * Method: moveTo
   *
   * Parameters:
   * bounds - {<OpenLayers.Bounds>} 
   * zoomChanged - {Boolean} 
   * dragging - {Boolean} 
   */
  moveTo: function(bounds, zoomChanged, dragging) {

    OpenLayers.Layer.prototype.moveTo.apply(this, arguments);

    // The code is too slow to update the rendering during dragging.
    if (dragging)
      return;

    // Pick some point on the map and use it to determine the offset
    // between the map's 0,0 coordinate and the layer's 0,0 position.
    var someLoc = new OpenLayers.LonLat(0,0);
    var offsetX = this.map.getViewPortPxFromLonLat(someLoc).x -
                  this.map.getLayerPxFromLonLat(someLoc).x;
    var offsetY = this.map.getViewPortPxFromLonLat(someLoc).y -
                  this.map.getLayerPxFromLonLat(someLoc).y;

    this.canvas.width = this.map.getSize().w;
    this.canvas.height = this.map.getSize().h;

    var ctx = this.canvas.getContext('2d');

    ctx.save(); // Workaround for a bug in Google Chrome
    ctx.fillStyle = 'transparent';
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.restore();

    for (var i=0;i<this.points.length;i++) {

      var src = this.points[i];
      if(!src.lonlat){
        var src = '';
      }
      var rad = src.radius || this.defaultRadius;
      var integer = src.intensity || this.defaultIntensity;
      var pos = this.map.getLayerPxFromLonLat(src.lonlat);
      var x = pos.x - rad + offsetX;
      var y = pos.y - rad + offsetY;

      if (!this.cache[integer]) {
        this.cache[integer] = {};
      }

      if (!this.cache[integer][rad]) {
        var grd = ctx.createRadialGradient(rad, rad, 0, rad, rad, rad);
        grd.addColorStop(0.0, 'rgba(0, 0, 0, ' + integer + ')');
        grd.addColorStop(1.0, 'transparent');
        this.cache[integer][rad] = grd;
      }

      ctx.fillStyle = this.cache[integer][rad];
      ctx.translate(x, y);
      ctx.fillRect(0, 0, 2 * rad, 2 * rad);
      ctx.translate(-x, -y);
    }

    var dat = ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
    var dim = this.canvas.width * this.canvas.height * 4;
    var pix = dat.data;

    for (var p = 0; p < dim; /* */) {
      var a = pix[ p + 3 ] * 4;
      pix[ p++ ] = this.gradient[ a++ ];
      pix[ p++ ] = this.gradient[ a++ ];
      pix[ p++ ] = this.gradient[ a++ ];
      pix[ p++ ] = this.gradient[ a++ ];
    }

    ctx.putImageData(dat, 0, 0);

    // Unfortunately OpenLayers does not currently support layers that
    // remain in a fixed position with respect to the screen location
    // of the base layer, so this puts this layer manually back into
    // that position using one point's offset as determined earlier.
    this.canvas.style.left = (-offsetX) + 'px';
    this.canvas.style.top = (-offsetY) + 'px';
  },

  /** 
   * APIMethod: getDataExtent
   * Calculates the max extent which includes all of the heat sources.
   * 
   * Returns:
   * {<OpenLayers.Bounds>}
   */
  getDataExtent: function () {
    var maxExtent = null;
        
    if (this.points && (this.points.length > 0)) {
      var maxExtent = new OpenLayers.Bounds();
      for(var i = 0, len = this.points.length; i < len; ++i) {
        var point = this.points[i];
        maxExtent.extend(point.lonlat);
      }
    }

    return maxExtent;
  },

  CLASS_NAME: 'Heatmap.Layer'

});
