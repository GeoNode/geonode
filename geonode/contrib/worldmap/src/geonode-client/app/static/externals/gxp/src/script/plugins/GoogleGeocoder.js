/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @requires widgets/form/GoogleGeocoderComboBox.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = GoogleGeocoder
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: GoogleGeocoder(config)
 *
 *    Plugin for adding a GoogleGeocoderComboBox to a viewer.  The underlying
 *    GoogleGeocoderComboBox can be configured by setting this tool's 
 *    ``outputConfig`` property. The gxp.form.GoogleGeocoderComboBox requires 
 *    the gxp.plugins.GoogleSource or the Google Maps V3 API to be loaded.
 */
gxp.plugins.GoogleGeocoder = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_googlegeocoder */
    ptype: "gxp_googlegeocoder",

    /** api: config[updateField]
     *  ``String``
     *  If value is specified, when an item is selected in the combo, the map
     *  will be zoomed to the corresponding field value in the selected record.
     *  If ``null``, no map navigation will occur.  Valid values are the field
     *  names described for the :class:`gxp.form.GoogleGeocoderComboBox`.
     *  Default is "viewport".
     */
    updateField: "viewport",
    
    init: function(target) {

        var combo = new gxp.form.GoogleGeocoderComboBox(Ext.apply({
            listeners: {
                select: this.onComboSelect,
                scope: this
            }
        }, this.outputConfig));
        
        var bounds = target.mapPanel.map.restrictedExtent;
        if (bounds && !combo.bounds) {
            target.on({
                ready: function() {
                    combo.bounds = bounds.clone().transform(
                        target.mapPanel.map.getProjectionObject(),
                        new OpenLayers.Projection("EPSG:4326")
                    );
                }
            });
        }
        this.combo = combo;
        
        return gxp.plugins.GoogleGeocoder.superclass.init.apply(this, arguments);

    },

    /** api: method[addOutput]
     */
    addOutput: function(config) {
        return gxp.plugins.GoogleGeocoder.superclass.addOutput.call(this, this.combo);
    },
    
    /** private: method[onComboSelect]
     *  Listener for combo's select event.
     */
    onComboSelect: function(combo, record) {
        if (this.updateField) {
            var map = this.target.mapPanel.map;
            var location = record.get(this.updateField).clone().transform(
                new OpenLayers.Projection("EPSG:4326"),
                map.getProjectionObject()
            );
            if (location instanceof OpenLayers.Bounds) {
                map.zoomToExtent(location, true);
            } else {
                map.setCenter(location);
            }
        }
    }

});

Ext.preg(gxp.plugins.GoogleGeocoder.prototype.ptype, gxp.plugins.GoogleGeocoder);
