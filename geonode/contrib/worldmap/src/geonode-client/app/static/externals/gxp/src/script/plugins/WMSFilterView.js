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
 *  class = WMSFilterView
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: WMSFilterView(config)
 *
 *    Plugin for displaying the selection of a
 *    :class:`gxp.plugins.FeatureManager` as WMS layer. Only works with WMS
 *    services that support the CQL_FILTER and FEATUREID vendor parameters.
 *    This tool will automatically add a WMS layer to the target's mapPanel,
 *    and populate it whenever a query is processed by the FeatureManager.
 */   
gxp.plugins.WMSFilterView = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_WMSFilterView */
    ptype: "gxp_wmsfilterview",
    
    /** api: config[featureManager]
     *  ``String`` The id of the :class:`gxp.plugins.FeatureManager` to use
     *  with this tool.
     */
    featureManager: null,
    
    /** private: property[filterLayer]
     *  ``OpenLayers.Layer.WMS``
     */
    
    init: function(target) {
        gxp.plugins.WMSFilterView.superclass.init.apply(this, arguments);        
        this.createFilterLayer();
    },
    
    createFilterLayer: function() {
        this.filterLayer = new OpenLayers.Layer.WMS(this.id + "filterlayer",
            Ext.BLANK_IMAGE_URL,
            {
                format: "image/png",
                transparent: true
            }, {
                buffer: 0,
                displayInLayerSwitcher: false,
                tileOptions: {maxGetUrlLength: 2048}
            }
        );
        var map = this.target.mapPanel.map;
        map.addLayer(this.filterLayer);
        map.events.on({
            addlayer: this.raiseLayer,
            scope: this
        });
        var featureManager = this.target.tools[this.featureManager];
        var format = new OpenLayers.Format.SLD();
        var clear = (function() {
            this.filterLayer.setUrl(Ext.BLANK_IMAGE_URL);
            this.filterLayer.setVisibility(false);
        }).bind(this); 
        featureManager.on({
            "clearfeatures": clear,
            "beforelayerchange": clear,
            "beforequery": function(tool, filter) {
                this.filterLayer.setUrl(Ext.BLANK_IMAGE_URL);
                this.filterLayer.setVisibility(false);
            },
            "query": function(tool, store, filter) {
                if (!filter) {
                    return;
                }
                var rule = new OpenLayers.Rule();
                var geomType = featureManager.geometryType.replace(/^Multi/, "");
                var symbolizer = featureManager.style["all"].rules[0].symbolizer;
                rule.symbolizer[geomType] = Ext.applyIf(
                    Ext.apply({}, symbolizer[geomType] || symbolizer),
                    OpenLayers.Feature.Vector.style["default"]
                );
                var style = new OpenLayers.Style(null, {
                  rules: [rule]
                });
                var layer = tool.layerRecord.getLayer();
                this.filterLayer.setUrl(layer.url);
                
                // Remove bbox filter on 1st level (usually set by QueryForm),
                // because bbox filter and wms requests don't play together.
                if (filter instanceof OpenLayers.Filter.Logical) {
                    var filters = filter.filters;
                    for (var i=filters.length-1; i>=0; --i)  {
                        if (filters[i].type === OpenLayers.Filter.Spatial.BBOX) {
                            filters.remove(filters[i]);
                        }
                    }
                    if (filters.length == 1 && filter.type !== OpenLayers.Filter.Comparison.NOT) {
                        filter = filters[0];
                    } else if (filters.length == 0) {
                        filter = null;
                    }
                } else if (filter.type === OpenLayers.Filter.Spatial.BBOX) {
                    filter = null;
                }
                
                var params = {};
                // To avoid switching to POST requests whenever possible, we
                // encode the filter with the much more compact CQL format and
                // FEATUREID vendor param, and strip namespace prefixes and
                // declarations from the SLD
                if (filter) {
                    if (filter instanceof OpenLayers.Filter.FeatureId) {
                        params.featureid = filter.fids;
                    } else {
                        params.cql_filter = new OpenLayers.Format.CQL().write(filter);
                    }
                }
                this.filterLayer.mergeNewParams(Ext.apply(params, {
                    sld_body: format.write({
                        namedLayers: [{
                            name: featureManager.layerRecord.get("name"),
                            userStyles: [style]
                        }]
                    }).replace(/( (xmlns|xsi):[^\"]*\"[^\"]*"|sld:)/g, "")
                }));
                this.filterLayer.setVisibility(true);
            },
            scope: this
        });
    },
    
    /** private: method[raiseLayer]
     *  Called whenever a layer is added to the map to keep this layer on top.
     */
    raiseLayer: function() {
        var map = this.filterLayer.map;
        map.setLayerIndex(this.filterLayer, map.layers.length);
    }
    
});

Ext.preg(gxp.plugins.WMSFilterView.prototype.ptype, gxp.plugins.WMSFilterView);
