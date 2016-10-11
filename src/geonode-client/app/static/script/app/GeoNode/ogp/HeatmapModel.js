Ext.namespace("GeoNode");

var heatmapParams = {
  facet : "true",
  "facet.heatmap" : "bbox",
  "facet.heatmap.format" : "ints2D",
  "facet.heatmap.distErrPct": "0.05",
  fq: [
    "area:[0 TO 400]",
    "!(area:1 AND max_x:0 AND max_y:0)"
  ],
  'facet.heatmap.geom': "",
  rows: 0
};

GeoNode.HeatmapModel = Ext.extend(Ext.util.Observable, {

  radiusAdjust: 1.1,

  global_layers: 0,

  constructor: function(config) {
    var self = this;
    Ext.apply(this, config);
    this.addEvents({
      fireSearch: true
    });
    this.addListener('fireSearch', function(propagateToSearchTable){
      this.handleHeatmap();

      // should this search trigger also the search table?
      if(propagateToSearchTable){
        this.searchTable.doSearch();
      }
    });

    this.bbox_widget.viewer.mapPanel.map.events.register('moveend', '', function(){
      self.fireEvent('fireSearch', true);
    });

    this.bbox_widget.viewer.mapPanel.map.events.register('mousemove',this.bbox_widget.viewer.mapPanel.map, function(event){
      self.processEvent(event);
    },true);

    this.WGS84ToMercator = this.bbox_widget.WGS84ToMercator;

    Ext.QuickTips.init();

    this.tooltip = new Ext.ToolTip({
        html: 'test',
        cls: 'ogp-tooltip',
        hideDelay: 0,
        showDelay: 0,
        width: 80
      });

    //get the number of global layers
    // $.ajax({
    //   url: GeoNode.solrBackend,
    //   jsonp: "json.wrf",
    //   dataType: "jsonp",
    //   data : {
    //     q: '*',
    //     fq: 'area:[401 TO *]',
    //     rows: 0,
    //     wt: 'json'
    //   },
    //   success: function(response){
    //     self.global_layers = response.response.numFound;
    //   }
    // });
  },

  handleHeatmap: function(){
    this.deleteHeatmapLayer();
    this.makeHeatmapLayer();
  },

  setQueryParameters: function(){
    var extent = this.bbox_widget.viewer.mapPanel.map.getExtent();
    var center = extent.getCenterLonLat().transform(new OpenLayers.Projection('EPSG:900913'), new OpenLayers.Projection('EPSG:4326'));
    if (extent){
      extent = extent.transform(new OpenLayers.Projection('EPSG:900913'), new OpenLayers.Projection('EPSG:4326'));
      var bbox = {
        minX: extent.left,
        maxX: extent.right,
        minY: extent.bottom,
        maxY: extent.top
      };
      GeoNode.solr.center = {
        centerX: center.lat,
        centerY: center.lon
      }
      var params = GeoNode.solr.getOgpSpatialQueryParams(bbox);
      GeoNode.queryTerms.intx = params.intx;
      GeoNode.queryTerms.bf = params.bf;
      heatmapParams['facet.heatmap.geom'] = params['facet.heatmap.geom'];
    }
  },

  initHeatmapLayer:function(){
    return new Heatmap.Layer("Heatmap");
  },

  makeHeatmapLayer: function(){
    var self = this;
    this.setQueryParameters();
    var params = $.extend({}, GeoNode.queryTerms, heatmapParams);
    params.fq = $.merge([],  GeoNode.queryTerms.fq);
    $.merge(params.fq, heatmapParams.fq);
    $.ajax({
      url: GeoNode.solrBackend,
      jsonp: "json.wrf",
      dataType: "jsonp",
      data : $.param(params, true),
      success: function(response){
        var facetCounts = response.facet_counts;
        if (facetCounts != null){
          var heatmapObject = facetCounts.facet_heatmaps.bbox;
          self.heatmapObject = heatmapObject;
          self.drawHeatmapOpenLayers(heatmapObject);
        }
      }
    });
  },

  drawHeatmapOpenLayers: function(heatmapObject){

    var map = this.bbox_widget.viewer.mapPanel.map;

    if(!this.heatmapLayer){
      this.heatmapLayer = this.initHeatmapLayer();
    }
    this.heatmapLayer.points = [];

    var heatmap = heatmapObject[15];
    if (heatmap == null){ return };
    var stepsLatitude = heatmapObject[5];
    var stepsLongitude = heatmapObject[3];
    var minMaxValue = this.heatmapMinMax(heatmap, stepsLatitude, stepsLongitude);
    var maxValue = minMaxValue[1];
    if (maxValue == -1) return;
    var minimumLatitude = heatmapObject[11];
    var maximumLatitude = heatmapObject[13];
    var deltaLatitude = maximumLatitude - minimumLatitude;
    var minimumLongitude = heatmapObject[7];
    var maximumLongitude = heatmapObject[9];
    var deltaLongitude = maximumLongitude - minimumLongitude;

    var stepSizeLatitude = deltaLatitude / stepsLatitude;
    var stepSizeLongitude = deltaLongitude / stepsLongitude;

    var classifications = this.getClassifications(heatmap);
    var colorGradient = this.getColorGradient(classifications, maxValue);
    this.heatmapLayer.setGradientStops(colorGradient);

    for (var i = 0 ; i < stepsLatitude ; i++){
      for (var j = 0 ; j < stepsLongitude ; j++){
        try{
          var heatmapValue = heatmap[heatmap.length - i - 1][j];
          var currentLongitude = minimumLongitude + (j * stepSizeLongitude) + (.5 * stepSizeLongitude);
          var currentLatitude = minimumLatitude + (i * stepSizeLatitude) + (.5 * stepSizeLatitude);
          var radius = this.computeRadius(currentLatitude, currentLongitude, stepSizeLatitude, stepSizeLongitude);
          var mercator = this.WGS84ToMercator(currentLongitude, currentLatitude);
          var scaledValue = this.rescaleHeatmapValue(heatmapValue, classifications[1], maxValue);
          var radiusFactor = this.getRadiusFactor();
          if (heatmapValue > 0)
          {
              this.heatmapLayer.addSource(new Heatmap.Source(mercator, radius*radiusFactor*this.radiusAdjust, scaledValue));
          }
        }
        catch (error){
          console.log("error making heatmap: " + error);
        }
      }
    }
    this.heatmapLayer.setOpacity(0.50);

    if(map.getLayersByName("Heatmap").length == 0){
      map.addLayer(this.heatmapLayer);
      map.setLayerIndex(this.heatmapLayer, 2);
    }else{
      this.heatmapLayer.redraw();
    }
  },

  getRadiusFactor: function(){
      var factor = [1.6, 1.5, 2.6, 2.4, 2.2, 1.8, 2., 2., 2.];
      var zoomLevel = this.bbox_widget.viewer.mapPanel.map.getZoom();
      if (zoomLevel <1){
        return 1;
      };

      var index = zoomLevel - 1;
      if (index > factor.length - 1){
        return factor[factor.length - 1];
      }

      var value = factor[index];
      return value;
  },

  heatmapMinMax: function (heatmap, stepsLatitude, stepsLongitude){
    var max = -1;
    var min = Number.MAX_VALUE;
    for (var i = 0 ; i < stepsLatitude ; i++){
      var currentRow = heatmap[i];
      if (currentRow == null){heatmap[i] = currentRow = []};
      for (var j = 0 ; j < stepsLongitude ; j++){
        if (currentRow[j] == null){
          currentRow[j] = -1;
        }

        if (currentRow[j] > max){
          max = currentRow[j];
        }

        if (currentRow[j] < min && currentRow[j] > -1){
          min = currentRow[j];
        }
      }
    }
    return [min, max];
  },

  deleteHeatmapLayer: function(){
    var map = this.bbox_widget.viewer.mapPanel.map;
    var heatmaplayers = map.getLayersByName('Heatmap');
    if(heatmaplayers.length > 0){
      for(var i=0; i<heatmaplayers.length; i++){
        map.removeLayer(heatmaplayers[i]);
      }
    }
  },

  flattenValues: function(heatmap){
    var tmp = [];
    for (var i = 0 ; i < heatmap.length ; i++){
      tmp.push.apply(tmp, heatmap[i]);
    }
    return tmp;
  },

  /**
    uses a Jenks algorithm with 5 classifications
    the library supports many more options
  */
  getClassifications: function(heatmap)
  {
    var flattenedValues = this.flattenValues(heatmap);
    var series = new geostats(flattenedValues);

    var jenksClassifications = series.getClassJenks(this.getColors().length);

    for (var i = 0 ; i < jenksClassifications.length; i++){
      if (jenksClassifications[i] < 0){
        jenksClassifications[i] = 0;
      }
    }

    return this.cleanupClassifications(jenksClassifications);
  },

  cleanupClassifications: function(classifications){
    // classifications with multiple 0 can cause problems
    var lastZero = classifications.lastIndexOf(0);
    if (lastZero == -1){
      return classifications;
    };
    classifications = classifications.slice(lastZero, classifications.length);
    return classifications;
  },

  getColors: function(){
    return [0x00000000, 0x0000dfff, 0x00effeff, 0x00ff42ff, 0xfeec30ff, 0xff5f00ff, 0xff0000ff];
  },

  /*
    convert Jenks classifications to Brewer colors
  */
  getColorGradient: function(classifications, maxValue){

    var colors = this.getColors();
    var colorGradient = {};
    var classes = classifications.length;
    if(classifications.length == 8){
      classes -= 1;
    }
    for (var i = 0 ; i < classes; i++){
      var value = classifications[i];
      var scaledValue = this.rescaleHeatmapValue(value, classifications[0], maxValue);
      if (scaledValue < 0){
        scaledValue = 0;
      }
      colorGradient[scaledValue] = colors[i];
    }
    return colorGradient;
  },

  rescaleHeatmapValue: function(value, min, max){
    if (value == null){
      return 0;
    };

    if (value == -1){
      return -1;
    };

    if (value == 0){
      return 0;
    };

    value = value * 1.0;
    return value / max;
  },

  computeRadius: function(latitude, longitude, latitudeStepSize, longitudeStepSize){
    var mercator1 = this.WGS84ToMercator(longitude, latitude);
    var pixel1 = this.bbox_widget.viewer.mapPanel.map.getPixelFromLonLat(mercator1);
    var mercator2 = this.WGS84ToMercator(longitude + longitudeStepSize, latitude + latitudeStepSize);
    var pixel2 = this.bbox_widget.viewer.mapPanel.map.getPixelFromLonLat(mercator2);
    var deltaLatitude = Math.abs(pixel1.x - pixel2.x);
    var deltaLongitude = Math.abs(pixel1.y - pixel2.y);
    var delta = Math.max(deltaLatitude, deltaLongitude);
    return Math.ceil(delta / 2.);
  },

  getCountGeodetic: function(heatmapObject, latitude, longitude){
    var heatmap = heatmapObject[15];
      if (heatmap == null)
        return;
      var minimumLatitude = heatmapObject[11];
      var maximumLatitude = heatmapObject[13];
      var deltaLatitude = maximumLatitude - minimumLatitude;
      var minimumLongitude = heatmapObject[7];
      var maximumLongitude = heatmapObject[9];
      var deltaLongitude = maximumLongitude - minimumLongitude;

      var stepsLatitude = heatmap.length;
      var stepsLongitude = heatmap[0].length;
      var stepSizeLatitude = deltaLatitude / stepsLatitude;
      var stepSizeLongitude = deltaLongitude / stepsLongitude;

      var latitudeIndex = Math.floor((latitude - minimumLatitude) / stepSizeLatitude);
      var longitudeIndex = Math.floor((longitude - minimumLongitude) / stepSizeLongitude);

      if (latitudeIndex < 0) latitudeIndex = 0;
      if (longitudeIndex < 0) longitudeIndex = 0;
      try{
        var heatmapValue = heatmap[heatmap.length - latitudeIndex - 1][longitudeIndex];
        return heatmapValue;
      }
        catch (err)
      {
        return heatmap[0][0];
      }
  },

  processEvent: function(event){
      var map = this.bbox_widget.viewer.mapPanel.map;
      var pixel = event.xy;
      var mercator = map.getLonLatFromViewPortPx(pixel);
      var epsg4326 = new OpenLayers.Projection("EPSG:4326");
      var epsg900913 = new OpenLayers.Projection("EPSG:900913");
      var point = mercator.transform(epsg900913, epsg4326);
      var count = this.getCountGeodetic(this.heatmapObject, point.lat, point.lon) + this.global_layers;
      if (count < 0) count = 0;
      var message = count + " layers";
      this.tooltip.initTarget('ge_searchWindow');
      this.tooltip.show();
      this.tooltip.body.dom.innerHTML = message;

  }

});
