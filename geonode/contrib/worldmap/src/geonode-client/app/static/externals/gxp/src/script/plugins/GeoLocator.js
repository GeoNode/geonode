/**
 * @requires plugins/Tool.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = GeoLocator
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: GeoLocator(config)
 *
 *    This plugin will display the user's location
 *    using the OpenLayers.Control.Geolocate control
 *
 */
gxp.plugins.GeoLocator = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_geolocator */
    ptype: "gxp_geolocator",

    /** api: config[maxZoom]
     *  ``Integer``
     *  Maximum zoom when centering map on location
     */
    maxZoom: 21,

    /** api: config[infoActionTip]
     *  ``String``
     *  Text for feature info action tooltip (i18n).
     */
    infoActionTip: "Get My Location",
    
    locationFailedText: "Location detection failed",

    iconCls: "gxp-icon-geolocate",
    

    /** api: method[addActions]
     */
    addActions: function() {
        this.popupCache = {};
        var map = this.target.mapPanel.map;
        var firstGeolocation = true;
        var vector = new OpenLayers.Layer.Vector('vector');
        var style = {
            fillColor: '#000',
            fillOpacity: 0.1,
            strokeWidth: 0
        };
        var geolocate = new OpenLayers.Control.Geolocate({
            bind: false,
            geolocationOptions: {
                enableHighAccuracy: true,
                maximumAge: 0,
                timeout: 7000
            }
        });
        var maxZoom = this.maxZoom;


        /*
         * Special effects for initial geolocation
         */
        var pulsate = function(feature) {
            var point = feature.geometry.getCentroid(),
                bounds = feature.geometry.getBounds(),
                radius = Math.abs((bounds.right - bounds.left) / 2),
                count = 0,
                grow = 'up';

            var resize = function() {
                if (count > 16) {
                    clearInterval(window.resizeInterval);
                }
                var interval = radius * 0.03;
                var ratio = interval / radius;
                switch (count) {
                    case 4:
                    case 12:
                        grow = 'down';
                        break;
                    case 8:
                        grow = 'up';
                        break;
                }
                if (grow !== 'up') {
                    ratio = - Math.abs(ratio);
                }
                feature.geometry.resize(1 + ratio, point);
                vector.drawFeature(feature);
                count++;
            };
            window.resizeInterval = window.setInterval(resize, 50, point, radius);
        };

        /*
         * Redraw the location vector whenever the user's location is updated
         */
        geolocate.events.register("locationupdated", geolocate, function(e) {
            vector.removeAllFeatures();
            var circle = new OpenLayers.Feature.Vector(
                OpenLayers.Geometry.Polygon.createRegularPolygon(
                    new OpenLayers.Geometry.Point(e.point.x, e.point.y),
                    e.position.coords.accuracy / 2,
                    40,
                    0
                ),
                {},
                style
            );
            vector.addFeatures([
                new OpenLayers.Feature.Vector(
                    e.point,
                    {},
                    {
                        graphicName: 'cross',
                        strokeColor: '#f00',
                        strokeWidth: 2,
                        fillOpacity: 0,
                        pointRadius: 10
                    }
                ),
                circle
            ]);
            if (firstGeolocation) {
                map.zoomToExtent(vector.getDataExtent());
                pulsate(circle);
                if (map.getZoom() > maxZoom) {
                    map.zoomTo(maxZoom);
                }
                firstGeolocation = false;
                this.bind = true;
            }
        });

        geolocate.events.register("locationfailed", this, function() {
            OpenLayers.Console.log(this.locationFailedText);
        });

        // Add OpenLayers.Control.Geolocate to the mao
        map.addControl(geolocate);

        var actions = gxp.plugins.GeoLocator.superclass.addActions.call(this, [
            {
                tooltip: this.infoActionTip,
                iconCls: this.iconCls,
                text: this.toolText,
                toggleGroup: this.toggleGroup,
                enableToggle: true,
                allowDepress: true,
                toggleHandler: function(button, pressed) {
                    if (pressed) {
                        map.addLayer(vector);
                        geolocate.watch = true;
                        firstGeolocation = true;
                        geolocate.activate();
                    } else {
                        vector.removeAllFeatures();
                        geolocate.deactivate();
                        geolocate.watch = false;
                        map.removeLayer(vector);
                    }

                }
            }
        ]);

    }
});

Ext.preg(gxp.plugins.GeoLocator.prototype.ptype, gxp.plugins.GeoLocator);