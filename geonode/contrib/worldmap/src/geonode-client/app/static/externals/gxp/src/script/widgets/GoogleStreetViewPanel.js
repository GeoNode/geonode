/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp
 *  class = GoogleStreetViewPanel
 *  base_link = `Ext.Panel <http://dev.sencha.com/deploy/dev/docs/?class=Ext.Panel>`_
 */
Ext.namespace("gxp");

gxp.GoogleStreetViewPanel = Ext.extend(Ext.Panel, {

    /** private: property[panorama]
     *  ``google.maps.StreetViewPanorama``  The panorama object.
     */
    panorama: null,

    /** api: config[heading]
     *  ``Number``  The camera heading in degrees relative to true north. True north 
     *  is 0 degrees, east is 90 degrees, south is 180 degrees, west is 270 
     *  degrees.
     */
    /** private: property[heading]
     *  ``Number``  Camera heading.
     */
    heading: 0,

    /** api: config[pitch]
     *  ``Number``  The camera pitch in degrees, relative to the street view 
     *  vehicle. Ranges from 90 degrees (directly upwards) to -90 degrees 
     *  (directly downwards).
     */
    /** private: property[pitch]
     *  ``Number``  Camery pitch
     */
    pitch: 0,

    /** api: config[zoom]
     *  ``Number``  The zoom level. Fully zoomed-out is level 0, zooming in 
     *  increases the zoom level.
     */
    /** private: property[zoom]
     *  ``Number``  Panorama zoom level
     */
    zoom: 0,

    /** api: config[location]
     *  ``OpenLayers.LonLat``  The panorama location
     */
    /** private: property[location]
     *  ``OpenLayers.LonLat``  Panorama location
     */
    location: null,

    /** private: method[initComponent]
     *  Private initComponent override.
     */
    initComponent : function() {
        var defConfig = {
            plain: true,
            border: false
        };

        Ext.applyIf(this, defConfig);
        return gxp.GoogleStreetViewPanel.superclass.initComponent.call(this);
    },

    /** private: method[afterRender]
     *  Private afterRender override.
     */
    afterRender : function() {
        var owner = this.ownerCt;
        if (owner) {
            var size = owner.getSize();
            Ext.applyIf(this, size);
            if (!this.location) {
                // try to derive location from owner (e.g. popup)
                if (GeoExt.Popup) {
                    this.bubble(function(cmp) {
                        if (cmp instanceof GeoExt.Popup) {
                            this.location = cmp.location.clone().transform(
                                cmp.map.getProjectionObject(),
                                new OpenLayers.Projection("EPSG:4326")
                            );
                            return false;
                        }
                    }, this);
                }
            }
        }
        gxp.GoogleStreetViewPanel.superclass.afterRender.call(this);
        
        // Configure panorama and associate methods and parameters to it
        var options = {
            position: new google.maps.LatLng(this.location.lat, this.location.lon),
            pov: {
                heading: this.heading,
                pitch: this.pitch,
                zoom: this.zoom
            }
        };
        this.panorama = new google.maps.StreetViewPanorama(
            this.body.dom, options
        );

    },

    /** private: method[beforeDestroy]
     *  Destroy Street View Panorama instance and navigation tools
     *
     */
    beforeDestroy: function() {
        delete this.panorama;
        gxp.GoogleStreetViewPanel.superclass.beforeDestroy.apply(this, arguments);
    },

    /** private: method[onResize]
     *  Resize Street View Panorama
     *  :param w: ``Number`` Width
     *  :param h: ``Number`` Height
     */
    onResize : function(w, h) {
        gxp.GoogleStreetViewPanel.superclass.onResize.apply(this, arguments);
        if (this.panorama) {
            if (typeof this.panorama == "object") {
                google.maps.event.trigger(this.panorama, "resize");
            }
        }
    },

    /** private: method[setSize]
     *  Set size of Street View Panorama
     */
    setSize : function(width, height, animate) {
        gxp.GoogleStreetViewPanel.superclass.setSize.apply(this, arguments);
        if (this.panorama) {
            if (typeof this.panorama == "object") {
                google.maps.event.trigger(this.panorama, "resize");
            }
        }
    }
});

/** api: xtype = gxp_googlestreetviewpanel */
Ext.reg("gxp_googlestreetviewpanel", gxp.GoogleStreetViewPanel);
