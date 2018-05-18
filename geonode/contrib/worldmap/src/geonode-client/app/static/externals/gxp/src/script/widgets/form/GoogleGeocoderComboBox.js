/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp.form
 *  class = GoogleGeocoderComboBox
 *  base_link = `Ext.form.ComboBox <http://extjs.com/deploy/dev/docs/?class=Ext.form.ComboBox>`_
 */
Ext.namespace("gxp.form");

/** api: constructor
 *  .. class:: GoogleGeocoderComboBox(config)
 *
 *  Creates a combo box that issues queries to the Google Maps geocoding service.
 *  If the user enters a valid address in the search box, the combo's store
 *  will be populated with records that match the address.  Records have the 
 *  following fields:
 *  
 *  * address - ``String`` The formatted address.
 *  * location - ``OpenLayers.LonLat`` Location matching address.
 *  * viewport - ``OpenLayers.Bounds`` Recommended viewing bounds.
 *
 */   
gxp.form.GoogleGeocoderComboBox = Ext.extend(Ext.form.ComboBox, {
    
    /** api: xtype = gxp_googlegeocodercombo */
    xtype: "gxp_googlegeocodercombo",

    /** api: config[queryDelay]
     *  ``Number`` Delay before the search occurs.  Default is 100ms.
     */
    queryDelay: 100,
    
    /** api: config[bounds]
     *  ``OpenLayers.Bounds | Array`` Optional bounds (in geographic coordinates)
     *  for restricting search.
     */
    
    /** api: config[valueField]
     *  ``String``
     *  Field from selected record to use when the combo's ``getValue`` method
     *  is called.  Default is "location".  Possible value's are "location",
     *  "viewport", or "address".  The location value will be an 
     * ``OpenLayers.LonLat`` object that corresponds to the geocoded address.
     *  The viewport value will be an ``OpenLayers.Bounds`` object that is 
     *  the recommended viewport for viewing the resulting location.  The
     *  address value will be a string that is the formatted address.
     */
    valueField: "viewport",

    /** private: config[displayField]
     */
    displayField: "address",

    /** private: method[initComponent]
     *  Override
     */
    initComponent: function() {
        
        // only enable when Google Maps API is available
        this.disabled = true;
        var ready = !!(window.google && google.maps);
        if (!ready) {
            if (!gxp.plugins || !gxp.plugins.GoogleSource) {
                throw new Error("The gxp.form.GoogleGeocoderComboBox requires the gxp.plugins.GoogleSource or the Google Maps V3 API to be loaded.");
            }
            gxp.plugins.GoogleSource.loader.onLoad({
                callback: this.prepGeocoder,
                errback: function() {
                    throw new Error("The Google Maps script failed to load within the given timeout.");
                },
                scope: this
            });
        } else {
            // call in the next turn to complete initialization
            window.setTimeout((function() {
                this.prepGeocoder();
            }).createDelegate(this), 0);
        }

        this.store = new Ext.data.JsonStore({
            root: "results",
            fields: [
                {name: "address", type: "string"},
                {name: "location"}, // OpenLayers.LonLat
                {name: "viewport"} // OpenLayers.Bounds
            ],
            autoLoad: false
        });
        
        this.on({
            focus: function() {
                this.clearValue();
            },
            scope: this
        });
        
        return gxp.form.GoogleGeocoderComboBox.superclass.initComponent.apply(this, arguments);

    },
    
    /** private: method[prepGeocoder]
     */
    prepGeocoder: function() {
        var geocoder = new google.maps.Geocoder();
        

        // create an async proxy for getting geocoder results
        var api = {};
        api[Ext.data.Api.actions.read] = true;
        var proxy = new Ext.data.DataProxy({api: api});
        var combo = this;
        
        // TODO: unhack this - this is due to the the tool output being generated too early
        var getBounds = (function() {
            // optional bounds for restricting search
            var bounds = this.bounds;
            if (bounds) {
                if (bounds instanceof OpenLayers.Bounds) {
                    bounds = bounds.toArray();
                }
                bounds = new google.maps.LatLngBounds(
                    new google.maps.LatLng(bounds[1], bounds[0]),
                    new google.maps.LatLng(bounds[3], bounds[2])
                );
            }
            return bounds;
        }).createDelegate(this);
        
        proxy.doRequest = function(action, rs, params, reader, callback, scope, options) {
            // Assumes all actions read.
            geocoder.geocode(
                {address: params.query, bounds: getBounds()},
                function(results, status) {
                    var readerResult;
                    if (status === google.maps.GeocoderStatus.OK || 
                        status === google.maps.GeocoderStatus.ZERO_RESULTS) {
                        try {
                            results = combo.transformResults(results);
                            readerResult = reader.readRecords({results: results});
                        } catch (err) {
                            combo.fireEvent("exception", combo, "response", action, options, status, err);
                        }
                    } else {
                        combo.fireEvent("exception", combo, "remote", action, options, status, null);
                    }
                    if (readerResult) {
                        callback.call(scope, readerResult, options, true);                        
                    } else {
                        callback.call(scope, null, options, false);                        
                    }
                }
            );
        };
        
        this.store.proxy = proxy;
        if (this.initialConfig.disabled != true) {
            this.enable();
        }
    },
        
    /** private: method[transformResults]
     *  Transform an array of results so values are OpenLayers objects.
     */
    transformResults: function(gResults) {
        var num = gResults.length;
        var olResults = new Array(num);
        var item, latLng, bounds, ne, sw;
        for (i=0; i<num; ++i) {
            item = gResults[i];
            latLng = item.geometry.location;
            bounds = item.geometry.viewport;
            ne = bounds.getNorthEast();
            sw = bounds.getSouthWest();
            olResults[i] = {
                address: item.formatted_address,
                location: new OpenLayers.LonLat(latLng.lng(), latLng.lat()),
                viewport: new OpenLayers.Bounds(sw.lng(), sw.lat(), ne.lng(), ne.lat())
            };
        }
        return olResults;
    }

});

Ext.reg(gxp.form.GoogleGeocoderComboBox.prototype.xtype, gxp.form.GoogleGeocoderComboBox);
