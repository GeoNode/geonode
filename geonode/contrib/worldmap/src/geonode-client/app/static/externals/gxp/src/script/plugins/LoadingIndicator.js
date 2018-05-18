/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = LoadingIndicator
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: LoadingIndicator(config)
 *
 *    Static plugin for show a loading indicator on the map.
 */   
gxp.plugins.LoadingIndicator = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_loadingindicator */
    ptype: "gxp_loadingindicator",

    /** api: config[onlyShowOnFirstLoad]
     * ``Boolean`` Set this to true to only show the loading indicator on the 
     * first load of the map. Default is false.
     */
    onlyShowOnFirstLoad: false,

    /** api: config[loadingMapMessage]
     *  ``String`` Message to show when the map is loading (i18n)
     */
    loadingMapMessage: "Loading Map...",

    /** private: property[layerCount]
     * ``Integer`` The number of layers currently loading.
     */ 
    layerCount: 0,

    /**
     * private: property[busyMask]
     * ``Ext.LoadMask`` The Ext load mask to show when busy.
     */
    busyMask: null,

    /** private: method[init]
     *  :arg target: ``Object``
     */
    init: function(target) {
        target.map.events.register("preaddlayer", this, function(e) {
            var layer = e.layer;
            if (layer instanceof OpenLayers.Layer.WMS) {
                layer.events.on({
                    "loadstart": function() {
                        this.layerCount++;
                        if (!this.busyMask) {
                            this.busyMask = new Ext.LoadMask(
                                target.map.div, {
                                    msg: this.loadingMapMessage
                                }
                            );
                        }
                        this.busyMask.show();
                        if (this.onlyShowOnFirstLoad === true) {
                            layer.events.unregister("loadstart", this, arguments.callee);
                        }
                    },
                    "loadend": function() {
                        this.layerCount--;
                        if(this.layerCount === 0) {
                            this.busyMask.hide();
                        }
                        if (this.onlyShowOnFirstLoad === true) {
                            layer.events.unregister("loadend", this, arguments.callee);
                        }
                    },
                    scope: this
                });
            } 
        });
    },

    /** private: method[destroy]
     */
    destroy : function(){
        Ext.destroy(this.busyMask);
        this.busyMask = null;
        gxp.plugins.LoadingIndicator.superclass.destroy.apply(this, arguments);
    }

});

Ext.preg(gxp.plugins.LoadingIndicator.prototype.ptype, gxp.plugins.LoadingIndicator);
