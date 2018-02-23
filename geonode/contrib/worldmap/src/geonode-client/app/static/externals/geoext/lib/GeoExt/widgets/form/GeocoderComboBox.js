/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * Published under the BSD license.
 * See http://geoext.org/svn/geoext/core/trunk/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = GeoExt.form
 *  class = GeocoderComboBox
 *  base_link = `Ext.form.ComboBox <http://dev.sencha.com/deploy/dev/docs/?class=Ext.form.ComboBox>`_
 */
Ext.namespace("GeoExt.form");

/** api: constructor
 *  .. class:: GeocoderComboBox(config)
 *
 *  Creates a combo box that handles results from a geocoding service. By
 *  default it uses OSM Nominatim, but it can be configured with a custom store
 *  to use other services. If the user enters a valid address in the search
 *  box, the combo's store will be populated with records that match the
 *  address.  By default, records have the following fields:
 *  
 *  * name - ``String`` The formatted address.
 *  * lonlat - ``Array`` Location matching address, for use with
 *      OpenLayers.LonLat.fromArray.
 *  * bounds - ``Array`` Recommended viewing bounds, for use with
 *      OpenLayers.Bounds.fromArray.
 */   
GeoExt.form.GeocoderComboBox = Ext.extend(Ext.form.ComboBox, {
    
    /** api: config[emptyText]
     *  ``String`` Text to display for an empty field (i18n).
     */
    emptyText: "Search",
    
    /** api: config[map]
     *  ``GeoExt.MapPanel|OpenLayers.Map`` The map that will be controlled by
     *  this GeoCoderComboBox. Only used if this component is not added as item
     *  or toolbar item to a ``GeoExt.MapPanel``.
     */
    
    /** private: property[map]
     *  ``OpenLayers.Map``
     */

    /** api: config[srs]
     *  ``String|OpenLayers.Projection`` The srs used by the geocoder service.
     *  Default is "EPSG:4326".
     */
    srs: "EPSG:4326",
    
    /** api: property[srs]
     *  ``OpenLayers.Projection``
     */
    
    /** api: config[zoom]
     *  ``String`` The minimum zoom level to use when zooming to a location.
     *  Not used when zooming to a bounding box. Default is 10.
     */
    zoom: 10,
    
    /** api: config[layer]
     *  ``OpenLayers.Layer.Vector`` If provided, a marker will be drawn on this
     *  layer with the location returned by the geocoder. The location will be
     *  cleared when the map panned. 
     */
    
    /** api: config[queryDelay]
     *  ``Number`` Delay before the search occurs.  Default is 100ms.
     */
    queryDelay: 100,
    
    /** api: config[valueField]
     *  ``String`` Field from selected record to use when the combo's
     *  :meth:`getValue` method is called.  Default is "bounds". This field is
     *  supposed to contain an array of [left, bottom, right, top] coordinates
     *  for a bounding box or [x, y] for a location. 
     */
    valueField: "bounds",

    /** api: config[displayField]
     *  ``String`` The field to display in the combo boy. Default is
     *  "name" for instant use with the default store for this component.
     */
    displayField: "name",
    
    /** api: config[locationField]
     *  ``String`` The field to get the location from. This field is supposed
     *  to contain an array of [x, y] for a location. Default is "lonlat" for
     *  instant use with the default store for this component.
     */
    locationField: "lonlat",
    
    /** api: config[url]
     *  ``String`` URL template for querying the geocoding service. If a
     *  :obj:`store` is configured, this will be ignored. Note that the
     *  :obj:`queryParam` will be used to append the user's combo box
     *  input to the url. Default is
     *  "http://nominatim.openstreetmap.org/search?format=json", for instant
     *  use with the OSM Nominatim geolocator. However, if you intend to use
     *  that, note the
     *  `Nominatim Usage Policy <http://wiki.openstreetmap.org/wiki/Nominatim_usage_policy>`_.
     */
    url: "http://nominatim.openstreetmap.org/search?format=json",
    
    /** api: config[queryParam]
     *  ``String`` The query parameter for the user entered search text.
     *  Default is "q" for instant use with OSM Nominatim.
     */
    queryParam: "q",
    
    /** api: config[minChars]
     *  ``Number`` Minimum number of entered characters to trigger a search.
     *  Default is 3.
     */
    minChars: 3,
    
    /** api: config[store]
     *  ``Ext.data.Store`` The store used for this combo box. Default is a
     *  store with a ScriptTagProxy and the url configured as :obj:`url`
     *  property.
     */
    
    /** private: property[center]
     *  ``OpenLayers.LonLat`` Last center that was zoomed to after selecting
     *  a location in the combo box.
     */
    
    /** private: property[locationFeature]
     *  ``OpenLayers.Feature.Vector`` Last location provided by the geolocator.
     *  Only set if :obj:`layer` is configured.
     */
    
    /** private: method[initComponent]
     *  Override
     */
    initComponent: function() {
        if (this.map) {
            this.setMap(this.map);
        }
        if (Ext.isString(this.srs)) {
            this.srs = new OpenLayers.Projection(this.srs);
        }
        if (!this.store) {
            this.store = new Ext.data.JsonStore({
                root: null,
                fields: [
                    {name: "name", mapping: "display_name"},
                    {name: "bounds", convert: function(v, rec) {
                        var bbox = rec.boundingbox;
                        return [bbox[2], bbox[0], bbox[3], bbox[1]];
                    }},
                    {name: "lonlat", convert: function(v, rec) {
                        return [rec.lon, rec.lat];
                    }}
                ],
                proxy: new Ext.data.ScriptTagProxy({
                    url: this.url,
                    callbackParam: "json_callback"
                })
            });
        }
        
        this.on({
            added: this.handleAdded,
            select: this.handleSelect,
            focus: function() {
                this.clearValue();
                this.removeLocationFeature();
            },
            scope: this
        });
        
        return GeoExt.form.GeocoderComboBox.superclass.initComponent.apply(this, arguments);
    },
    
    /** private: method[handleAdded]
     *  When this component is added to a container, see if it has a parent
     *  MapPanel somewhere and set the map
     */
    handleAdded: function() {
        var mapPanel = this.findParentBy(function(cmp) {
            return cmp instanceof GeoExt.MapPanel;
        });
        if (mapPanel) {
            this.setMap(mapPanel);
        }
    },
    
    /** private: method[handleSelect]
     *  Zoom to the selected location, and also set a location marker if this
     *  component was configured with an :obj:`layer`.
     */
    handleSelect: function(combo, rec) {                
        var value = this.getValue();
        if (Ext.isArray(value)) {
            var mapProj = this.map.getProjectionObject();
            delete this.center;
            delete this.locationFeature;
            if (value.length === 4) {
                this.map.zoomToExtent(
                    OpenLayers.Bounds.fromArray(value)
                        .transform(this.srs, mapProj)
                );
            } else {
                this.map.setCenter(
                    OpenLayers.LonLat.fromArray(value)
                        .transform(this.srs, mapProj),
                    Math.max(this.map.getZoom(), this.zoom)
                );
            }
            this.center = this.map.getCenter();

            var lonlat = rec.get(this.locationField);
            if (this.layer && lonlat) {
                var geom = new OpenLayers.Geometry.Point(
                    lonlat[0], lonlat[1]).transform(this.srs, mapProj);
                this.locationFeature = new OpenLayers.Feature.Vector(geom, rec.data);
                this.layer.addFeatures([this.locationFeature]);
            }
        }
        // blur the combo box
        //TODO Investigate if there is a more elegant way to do this.
        (function() {
            this.triggerBlur();
            this.el.blur();
        }).defer(100, this);
    },
    
    /** private: method[removeLocationFeature]
     *  Remove the location marker from the :obj:`layer` and destroy the
     *  :obj:`locationFeature`.
     */
    removeLocationFeature: function() {
        if (this.locationFeature) {
            this.layer.destroyFeatures([this.locationFeature]);
        }
    },
    
    /** private: method[clearResult]
     *  Handler for the map's moveend event. Clears the selected location
     *  when the map center has changed.
     */
    clearResult: function() {
        if (this.center && !this.map.getCenter().equals(this.center)) {
            this.clearValue();
        }
    },
    
    /** private: method[setMap]
     *  :param map: ``GeoExt.MapPanel||OpenLayers.Map``
     *
     *  Set the :obj:`map` for this instance.
     */
    setMap: function(map) {
        if (map instanceof GeoExt.MapPanel) {
            map = map.map;
        }
        this.map = map;
        map.events.on({
            "moveend": this.clearResult,
            "click": this.removeLocationFeature,
            scope: this
        });
    },
    
    /** private: method[addToMapPanel]
     *  :param panel: :class:`GeoExt.MapPanel`
     *  
     *  Called by a MapPanel if this component is one of the items in the panel.
     */
    addToMapPanel: Ext.emptyFn,
    
    /** private: method[beforeDestroy]
     */
    beforeDestroy: function() {
        this.map.events.un({
            "moveend": this.clearResult,
            "click": this.removeLocationFeature,
            scope: this
        });
        this.removeLocationFeature();
        delete this.map;
        delete this.layer;
        delete this.center;
        GeoExt.form.GeocoderComboBox.superclass.beforeDestroy.apply(this, arguments);
    }
});

/** api: xtype = gx_geocodercombo */
Ext.reg("gx_geocodercombo", GeoExt.form.GeocoderComboBox);
