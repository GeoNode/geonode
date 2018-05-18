/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = FeatureToField
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: FeatureToField(config)
 *
 *    Plugin for serializing the currently selected feature to the form field
 *    of a :class:`gxp.form.ViewerField`. Requires a
 *    :class:`gxp.plugins.FeatureManager` and a tool that selects features
 *    (e.g. :class:`gxp.plugins.FeatureEditor`).
 */   
gxp.plugins.FeatureToField = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_featuretofield */
    ptype: "gxp_featuretofield",
    
    /** api: config[featureManager]
     *  ``String`` :class:`FeatureManager` to use for this tool.
     */
     
    /** api: config[format]
     *  ``String`` The format to use for encoding the feature. Defaults to
     *  "GeoJSON", which means ``OpenLayers.Format.GeoJSON``. All
     *  OpenLayers.Format.* formats that can serialize a single feature can be
     *  used here.
     */
    format: "GeoJSON",
    
    /** api: method[addActions]
     */
    addActions: function() {
        var featureManager = this.target.tools[this.featureManager];
        var featureInField;
        var format = new OpenLayers.Format[this.format];
        featureManager.featureLayer.events.on({
            "featureselected": function(evt) {
                this.target.field.setValue(format.write(evt.feature));
                featureInField = evt.feature;
            },
            "featureunselected": function() {
                this.target.field.setValue("");
                featureInField = null;
            },
            scope: this
        });
        featureManager.on("layerchange", function() {
            featureManager.featureStore && featureManager.featureStore.on("save", function(store, batch, data) {
                if (data.create) {
                    var i, feature;
                    for (i=data.create.length-1; i>=0; --i) {
                        //TODO check why the WFSFeatureStore returns an object
                        // here instead of a record
                        feature = data.create[i].feature;
                        if (feature == featureInField) {
                            this.target.field.setValue(format.write(feature));
                        }
                    }
                }
            }, this);
        });
        
        return gxp.plugins.FeatureToField.superclass.addActions.apply(this, arguments);
    }
        
});

Ext.preg(gxp.plugins.FeatureToField.prototype.ptype, gxp.plugins.FeatureToField);
