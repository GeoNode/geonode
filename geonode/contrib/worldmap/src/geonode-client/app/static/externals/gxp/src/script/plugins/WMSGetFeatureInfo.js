/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @requires plugins/FeatureEditorGrid.js
 * @requires GeoExt/widgets/Popup.js
 * @requires OpenLayers/Control/WMSGetFeatureInfo.js
 * @requires OpenLayers/Format/WMSGetFeatureInfo.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = WMSGetFeatureInfo
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: WMSGetFeatureInfo(config)
 *
 *    This plugins provides an action which, when active, will issue a
 *    GetFeatureInfo request to the WMS of all layers on the map. The output
 *    will be displayed in a popup.
 */   
gxp.plugins.WMSGetFeatureInfo = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_wmsgetfeatureinfo */
    ptype: "gxp_wmsgetfeatureinfo",
    
    /** api: config[outputTarget]
     *  ``String`` Popups created by this tool are added to the map by default.
     */
    outputTarget: "map",

    /** private: property[popupCache]
     *  ``Object``
     */
    popupCache: null,

    /** api: config[infoActionTip]
     *  ``String``
     *  Text for feature info action tooltip (i18n).
     */
    infoActionTip: "Get Feature Info",

    /** api: config[popupTitle]
     *  ``String``
     *  Title for info popup (i18n).
     */
    popupTitle: "Feature Info",
    
    /** api: config[text]
     *  ``String`` Text for the GetFeatureInfo button (i18n).
     */
    buttonText: "Identify",
    
    /** api: config[format]
     *  ``String`` Either "html" or "grid". If set to "grid", GML will be
     *  requested from the server and displayed in an Ext.PropertyGrid.
     *  Otherwise, the html output from the server will be displayed as-is.
     *  Default is "html".
     */
    format: "html",
    
    /** api: config[vendorParams]
     *  ``Object``
     *  Optional object with properties to be serialized as vendor specific
     *  parameters in the requests (e.g. {buffer: 10}).
     */
    
    /** api: config[layerParams]
     *  ``Array`` List of param names that should be taken from the layer and
     *  added to the GetFeatureInfo request (e.g. ["CQL_FILTER"]).
     */
     
    /** api: config[itemConfig]
     *  ``Object`` A configuration object overriding options for the items that
     *  get added to the popup for each server response or feature. By default,
     *  each item will be configured with the following options:
     *
     *  .. code-block:: javascript
     *
     *      xtype: "propertygrid", // only for "grid" format
     *      title: feature.fid ? feature.fid : title, // just title for "html" format
     *      source: feature.attributes, // only for "grid" format
     *      html: text, // responseText from server - only for "html" format
     */

    /** api: method[addActions]
     */
    addActions: function() {
        this.popupCache = {};
        
        var actions = gxp.plugins.WMSGetFeatureInfo.superclass.addActions.call(this, [{
            tooltip: this.infoActionTip,
            iconCls: "gxp-icon-getfeatureinfo",
            buttonText: this.buttonText,
            toggleGroup: this.toggleGroup,
            enableToggle: true,
            allowDepress: true,
            toggleHandler: function(button, pressed) {
                for (var i = 0, len = info.controls.length; i < len; i++){
                    if (pressed) {
                        info.controls[i].activate();
                    } else {
                        info.controls[i].deactivate();
                    }
                }
             }
        }]);
        var infoButton = this.actions[0].items[0];

        var info = {controls: []};
        var updateInfo = function() {
            var queryableLayers = this.target.mapPanel.layers.queryBy(function(x){
                return x.get("queryable");
            });

            var map = this.target.mapPanel.map;
            var control;
            for (var i = 0, len = info.controls.length; i < len; i++){
                control = info.controls[i];
                control.deactivate();  // TODO: remove when http://trac.openlayers.org/ticket/2130 is closed
                control.destroy();
            }

            info.controls = [];
            queryableLayers.each(function(x){
                var layer = x.getLayer();
                var vendorParams = Ext.apply({}, this.vendorParams), param;
                if (this.layerParams) {
                    for (var i=this.layerParams.length-1; i>=0; --i) {
                        param = this.layerParams[i].toUpperCase();
                        vendorParams[param] = layer.params[param];
                    }
                }
                var infoFormat = x.get("infoFormat");
                if (infoFormat === undefined) {
                    // TODO: check if chosen format exists in infoFormats array
                    // TODO: this will not work for WMS 1.3 (text/xml instead for GML)
                    infoFormat = this.format == "html" ? "text/html" : "application/vnd.ogc.gml";
                }
                var control = new OpenLayers.Control.WMSGetFeatureInfo(Ext.applyIf({
                    url: layer.url,
                    queryVisible: true,
                    layers: [layer],
                    infoFormat: infoFormat,
                    vendorParams: vendorParams,
                    eventListeners: {
                        getfeatureinfo: function(evt) {
                            var title = x.get("title") || x.get("name");
                            if (infoFormat == "text/html") {
                                var match = evt.text.match(/<body[^>]*>([\s\S]*)<\/body>/);
                                if (match && !match[1].match(/^\s*$/)) {
                                    this.displayPopup(evt, title, match[1]);
                                }
                            } else if (infoFormat == "text/plain") {
                                this.displayPopup(evt, title, '<pre>' + evt.text + '</pre>');
                            } else if (evt.features && evt.features.length > 0) {
                                this.displayPopup(evt, title, null,  x.get("getFeatureInfo"));
                            }
                        },
                        scope: this
                    }
                }, this.controlOptions));
                map.addControl(control);
                info.controls.push(control);
                if(infoButton.pressed) {
                    control.activate();
                }
            }, this);

        };
        
        this.target.mapPanel.layers.on("update", updateInfo, this);
        this.target.mapPanel.layers.on("add", updateInfo, this);
        this.target.mapPanel.layers.on("remove", updateInfo, this);
        
        return actions;
    },

    /** private: method[displayPopup]
     * :arg evt: the event object from a 
     *     :class:`OpenLayers.Control.GetFeatureInfo` control
     * :arg title: a String to use for the title of the results section 
     *     reporting the info to the user
     * :arg text: ``String`` Body text.
     */
    displayPopup: function(evt, title, text, featureinfo) {
        var popup;
        var popupKey = evt.xy.x + "." + evt.xy.y;
        featureinfo = featureinfo || {};
        if (!(popupKey in this.popupCache)) {
            popup = this.addOutput({
                xtype: "gx_popup",
                title: this.popupTitle,
                layout: "accordion",
                fill: false,
                autoScroll: true,
                location: evt.xy,
                map: this.target.mapPanel,
                width: 250,
                height: 300,
                defaults: {
                    layout: "fit",
                    autoScroll: true,
                    autoHeight: true,
                    autoWidth: true,
                    collapsible: true
                },
                listeners: {
                    close: (function(key) {
                        return function(panel){
                            delete this.popupCache[key];
                        };
                    })(popupKey),
                    scope: this
                }
            });
            this.popupCache[popupKey] = popup;
        } else {
            popup = this.popupCache[popupKey];
        }

        var features = evt.features, config = [];
        if (!text && features) {
            var feature;
            for (var i=0,ii=features.length; i<ii; ++i) {
                feature = features[i];
                config.push(Ext.apply({
                    xtype: "gxp_editorgrid",
                    readOnly: true,
                    listeners: {
                        'beforeedit': function (e) {
                            return false;
                        }
                    },
                    title: feature.fid ? feature.fid : title,
                    feature: feature,
                    fields: featureinfo.fields,
                    propertyNames: featureinfo.propertyNames
                }, this.itemConfig));
            }
        } else if (text) {
            config.push(Ext.apply({
                title: title,
                html: text
            }, this.itemConfig));
        }
        popup.add(config);
        popup.doLayout();
    }
    
});

Ext.preg(gxp.plugins.WMSGetFeatureInfo.prototype.ptype, gxp.plugins.WMSGetFeatureInfo);
