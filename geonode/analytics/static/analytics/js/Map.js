var Map = {

  width: null,
  height: null,

  projection : null,
  path : null,

  //var zoom = d3.behavior.zoom()
  //    .on("zoom", zoomed);

  svg : null,
  g : null,

  geoFeatures : null,
  areas : null,

  init : function (svgSelector) {
    this.svg = d3.select(svgSelector);

    this.svg.on('mousewheel', function() {console.log('tot'); })
        .on("DOMMouseScroll",  function() {console.log('tot'); }) // older versions of Firefox
        .on("wheel",  function() {console.log('tot'); }); // newer versions of Firefox

    this.width = $(svgSelector).width();
    this.height = $(svgSelector).height();
    this.g = this.svg.append("g");

    this.projection = d3.geo.mercator()
  //    .scale((width + 1) / 2 / Math.PI)
        .translate([0, 0]).center([0,0]);

    this.path = d3.geo.path()
      .projection(this.projection);
  },

  /**
   * Set the geographical data on the map
   */
  setGeoData : function (geoData, levelID, transition) {
    if (transition == undefined)
      transition = 0;

    this.geoFeatures = topojson.feature(geoData, geoData.objects.europe);
      
    this.areas = this.g.selectAll("path")
        .data(this.geoFeatures.features)
      .enter().append("path")
        .attr("d", this.path)
        .attr("class", "feature geo-level-"+levelID)
        .on("mousewheel", this.onMouseWheelDrillDownRollUp)
        .on("click", this.drillDown)
        .on("DOMMouseScroll",  this.onMouseWheelDrillDownRollUp) // older versions of Firefox
        .on("wheel",  this.onMouseWheelDrillDownRollUp); // newer versions of Firefox

    this.adaptTo(this.geoFeatures, transition);

    //svg.call(zoom);
    this.svg.call(d3.behavior.drag().on("drag", this.panMap));
  },

  /**
   * Color the map according to the data given
   */
  setData : function (data, levelID) {
  
    // TODO assert geoData as been used

    // color the map
    this.areas.attr("fill", function(d) { return data[d.id].color; });
  },

  /**
   * Callback to pan the map during drag
   */
  panMap : function () {
    Map.addTranslate([d3.event.dx, d3.event.dy], 0);
  },

  /**
   * Zoom in on the center of the map
   */
  zoomIn : function(scale) {
    if (scale == undefined)
      scale = 1.2;

    this.addScale(scale, 350);
  },

  /**
   * Zoom out off the center of the map
   */
  zoomOut : function(scale) {
    if (scale == undefined)
      scale = 1.2;

    this.addScale(1 / scale, 350);
  },

  onMouseWheelRollUp : function (d) {
    Map.onMouseWheel(d, false, true);
  },

  onMouseWheelDrillDown : function (d) {
    Map.onMouseWheel(d, true, false);
  },

  onMouseWheelDrillDownRollUp : function (d) {
    Map.onMouseWheel(d, true, true);
  },

  /**
   * Called when scrolling with mouse wheel
   */
  onMouseWheel : function (d, drillDown, rollUp) {

    if (drillDown == undefined)
      drillDown = true;
    if (rollUp == undefined)
      rollUp = true;

    // drill down if zoom-in
    if (d3.event.deltaY < 0 && drillDown) {
      if (!Map.disabledActions.allMouseWheel) {
        Map.delayAction('allMouseWheel', 700);
        Map.drillDown(d);
      }
    }
    // roll up if zoom-out
    else if (d3.event.deltaY > 0 && rollUp) {
      if (!Map.disabledActions.allMouseWheel) {
        Map.delayAction('allMouseWheel', 700);
        Map.rollUp();
      }
    }
    
    // prevent scrolling on page
    d3.event.preventDefault();
    return false;
  },

  /**
   * These 3 elements below allow to disable roll-up and drill-down during a certain time.
   * It is necessary because the mousewheel call the function several time successively.
   */
  disabledActions : {
    allMouseWheel : false,
  }, 

  delayAction : function (name, delay) {
    this.disabledActions[name] = true;
    d3.timer(function () { Map.enableAction(name); return true; }, delay);
  },

  enableAction : function (name) {
    this.disabledActions[name] = false;
  },


  /**
   * Function called when drilling down on d
   */
  drillDown : function (d) {
    
    Map.adaptTo(d, 750);
  },

  /**
   * Called when rolling up from the current level
   */
  rollUp : function () {

    this.adaptTo(this.geoFeatures, 750);
    // TODO : generalise to multiple levels
  },

  /**
   * Adapt the SVG display to a geographic feature (an element or a set of elements) of the map
   */
  adaptTo : function (feature, transition) {
    var b = this.path.bounds(feature);
    var t = this.getTransformFromBounds(b);
    this.setTransform(t.scale, t.translate, transition);
  },

  /**
   * Translate the current SVG shown
   */
  addTranslate : function (translate, transition) {
    this.g.transition().duration(transition).attr("transform", "translate(" + translate + ") " + this.g.attr("transform"));

    /*if (!fromZoom) {
      zoom.translate(translate);
    }*/
  },

  /**
   * Scale (zoom / unzoom) on the SVG from the center of the current display
   */
  addScale : function (scale, transition) {
    var transformInit = this.parseTransform(this.g.attr("transform"));
    
    var scaleInit = transformInit.scale[0];

    var t = transformInit.translate;
    var c = [this.width / 2, this.height / 2];
    
    var translate = [c[0] + (t[0] - c[0]) * scale, 
                     c[1] + (t[1] - c[1]) * scale];

    this.setTransform(scaleInit * scale, translate, transition);
  },


  /**
   * Set the transform (scale & translate) of the SVG from scratch
   */
  setTransform : function (scale, translate, transition) {
    this.g.transition().duration(transition).attr("transform", "translate(" + translate + ") scale(" + scale + ") ");

    /*if (!fromZoom) {
      zoom.translate(translate);
      zoom.scale(scale);
    }*/
  },

  /** 
   * Get translate & scale parameters needed to adapt to the input bounds
   */
  getTransformFromBounds : function (b) {
    s = .95 / Math.max((b[1][0] - b[0][0]) / this.width, (b[1][1] - b[0][1]) / this.height);
    t = [(this.width - s * (b[1][0] + b[0][0])) / 2, (this.height - s * (b[1][1] + b[0][1])) / 2];
    
    return {scale: s, translate: t};
  },

  /**
   * Function to parse the transform parameter of the SVG
   */
  parseTransform : function (transform) {
    var translate  = /translate\(\s*([^\s,)]+)[ ,]([^\s,)]+)/.exec(transform);
    var translateX = translate[1];
    var translateY = translate[2];
    var scale  = /scale\(\s*([^\s,)]+)[ ,]([^\s,)]+)/.exec(transform);
    var scaleX = scale[1];
    var scaleY = scale[2];

    return {
      translate: [translateX, translateY],
      scale: [scaleX, scaleY]
    };
  }

}