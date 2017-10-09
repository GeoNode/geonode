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
 *  class = GoogleEarth
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: GoogleEarth(config)
 *
 *    Provides an action for switching between normal map view and 
 *    Google Earth view.
 */

 /**
 * Create a loader singleton that all plugin instances can use.
 */
gxp.plugins.GoogleEarth.loader = new (Ext.extend(Ext.util.Observable, {

    /** private: property[ready]
     *  ``Boolean``
     *  This plugin type is ready to use.
     */
    ready: !!(window.google && window.google.earth),

    /** private: property[loading]
     *  ``Boolean``
     *  The resources for this plugin type are loading.
     */
    loading: false,
    
    constructor: function() {
        this.addEvents(
            /** private: event[ready]
             *  Fires when this plugin type is ready.
             */
             "ready",

             /** private: event[failure]
              *  Fires when script loading fails.
              */
              "failure"
        );
        return Ext.util.Observable.prototype.constructor.apply(this, arguments);
    },
    
    /** private: method[onScriptLoad]
     *  Called when all resources required by this plugin type have loaded.
     */
    onScriptLoad: function() {
        // the google loader calls this in the window scope
        var monitor = gxp.plugins.GoogleEarth.loader;
        if (!monitor.ready) {
            monitor.ready = true;
            monitor.loading = false;
            monitor.fireEvent("ready");
        }
    },
    
    /** api: method[gxp.plugins.GoogleEarth.loader.onLoad]
     *  :arg options: ``Object``
     *
     *  Options:
     *
     *  * apiKey - ``String`` API key for Google Earth plugin.
     *  * callback - ``Function`` Called when script loads.
     *  * errback - ``Function`` Called if loading fails.
     *  * timeout - ``Number`` Time to wait before deciding that loading failed
     *      (in milliseconds).
     *  * scope - ``Object`` The ``this`` object for callbacks.
     */
    onLoad: function(options) {
        if (this.ready) {
            // call this in the next turn for consistent return before callback
            window.setTimeout(function() {
                options.callback.call(options.scope);
            }, 0);
        } else if (!this.loading) {
            this.loadScript(options);
        } else {
            this.on({
                ready: options.callback,
                failure: options.errback || Ext.emptyFn,
                scope: options.scope
            });
        }
    },

    /** private: method[onScriptLoad]
     *  Called when all resources required by this plugin type have loaded.
     */
    loadScript: function(options) {
        
        // remove any previous loader to ensure that the key is applied
        if (window.google) {
            delete google.loader;
        }

        var params = {
            key: 'AIzaSyBULYPrtqSg51_C-37aaHhNi6niNfY2ruw',
            autoload: Ext.encode({
                modules: [{
                    name: "earth",
                    version: "1",
                    callback: "gxp.plugins.GoogleEarth.loader.onScriptLoad"
                }]
            })
        };
        
        var script = document.createElement("script");
        script.src = "https://www.google.com/jsapi?" + Ext.urlEncode(params);

        // cancel loading if monitor is not ready within timeout
        var errback = options.errback || Ext.emptyFn;
        var timeout = options.timeout || gxp.plugins.GoogleSource.prototype.timeout;
        window.setTimeout((function() {
            if (!gxp.plugins.GoogleEarth.loader.ready) {
                this.fireEvent("failure");
                this.unload();
            }
        }).createDelegate(this), timeout);
        
        // register callback for ready
        this.on({
            ready: options.callback,
            failure: options.errback || Ext.emptyFn,
            scope: options.scope
        });

        this.loading = true;
        document.getElementsByTagName("head")[0].appendChild(script);
        this.script = script;

    },
    
    /** api: method[unload]
     *  Clean up resources created by loading.
     */
    unload: function() {
        this.purgeListeners();
        if (this.script) {
            document.getElementsByTagName("head")[0].removeChild(this.script);
            delete this.script;
        }
        this.loading = false;
        this.ready = false;
        delete google.loader;
        delete google.earth;
    }

}))();

Ext.preg(gxp.plugins.GoogleEarth.prototype.ptype, gxp.plugins.GoogleEarth);
