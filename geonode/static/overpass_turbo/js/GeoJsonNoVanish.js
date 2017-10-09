L.GeoJsonNoVanish = L.GeoJSON.extend({
  initialize: function (geojson, options) {
    this.options = {
      threshold: 10
    };
    L.GeoJSON.prototype.initialize.call(this,geojson,options);
  },
  onAdd: function(map) {
    this._map = map;
    this.eachLayer(map.addLayer, map);

    this._map.addEventListener("zoomend", this._onZoomEnd, this);
    this._onZoomEnd();
  },
  onRemove: function(map) {
    this._map.removeEventListener("zoomend", this._onZoomEnd, this);

    this.eachLayer(map.removeLayer, map);
    this._map = null;
  },
  _onZoomEnd: function() { // todo: name
    // todo: possible optimizations: zoomOut = skip already compressed objects (and vice versa)
    var is_max_zoom = this._map.getZoom() == this._map.getMaxZoom();
    this.eachLayer(function(o) {
      if (!o.feature || !o.feature.geometry)
        return; // skip invalid layers
      if (o.feature.geometry.type == "Point" && !o.obj)
        return; // skip node features
      var crs = this._map.options.crs;
      if (o.obj) { // already compressed feature
        var bounds = o.obj.getBounds();
        var p1 = crs.latLngToPoint(bounds.getSouthWest(), o._map.getZoom());
        var p2 = crs.latLngToPoint(bounds.getNorthEast(), o._map.getZoom());
        var d = Math.sqrt(Math.pow(p1.x-p2.x,2)+Math.pow(p1.y-p2.y,2));
        if (d > this.options.threshold || is_max_zoom) {
          delete o.obj.placeholder;
          this.addLayer(o.obj);
          this.removeLayer(o);
        }
        return;
      }
      if (is_max_zoom)
        return; // do not compress objects at max zoom
      if (this.options.compress &&
          !this.options.compress(o.feature))
        return;
      var bounds = o.getBounds();
      var p1 = crs.latLngToPoint(bounds.getSouthWest(), o._map.getZoom());
      var p2 = crs.latLngToPoint(bounds.getNorthEast(), o._map.getZoom());
      var d = Math.sqrt(Math.pow(p1.x-p2.x,2)+Math.pow(p1.y-p2.y,2));
      if (d > this.options.threshold)
        return;
      /*var c = this.options.pointToLayer ? 
                this.options.pointToLayer(o.feature, bounds.getCenter()) : 
                new L.Marker(bounds.getCenter());*/
      var center = bounds.getCenter();
      var f = L.extend({},o.feature);
      f.is_placeholder = true;
      f.geometry = {
        "type": "Point",
        "coordinates": [center.lng, center.lat],
      };
      var c = L.GeoJSON.geometryToLayer(f, this.options.pointToLayer);
      o.placeholder = c;
      c.feature = f;
      this.resetStyle(c);
      c.obj = o;
      //c.addEventListener("click dblclick mousedown mouseover mouseout contextmenu", function(e) {
      c.on("click",function(e) {
        this.obj.fireEvent(e.type,e);
      });
      this.addLayer(c);
      this.removeLayer(o);
    },this);
  }
});
L.geoJsonNoVanish = function (geojson, options) {
  return new L.GeoJsonNoVanish(geojson, options);
};
