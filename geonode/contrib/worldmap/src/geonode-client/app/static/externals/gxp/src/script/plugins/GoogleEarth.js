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
/** api: example
 *  This tool can only be used if ``portalItems`` of :class:`gxp.Viewer` is set up 
 *  in the following way (or similar, the requirement is to have a panel with a card
 *  layout which has 2 items: the map and the Google Earth panel):
 *
 *  .. code-block:: javascript
 *
 *      portalItems: [{
 *          region: "center",
 *          layout: "border",
 *          border: false,
 *           items: [{
 *               xtype: "panel", 
 *               id: "panel", 
 *               tbar: [], 
 *               layout: "card", 
 *               region: "center", 
 *               activeItem: 0, 
 *               items: [
 *               "map", {
 *                   xtype: 'gxp_googleearthpanel', 
 *                   mapPanel: "map"
 *               }
 *           ]
 *      } 
 *
 * Then make sure the tools go into the tbar of the panel, instead of the
 * "map.tbar" which is the default, an example is:
 *
 *  .. code-block:: javascript
 *
 *    tools: [
 *        {
 *            actionTarget: "panel.tbar",
 *            ptype: "gxp_googleearth",
 *        }
 *    ] 
 */
gxp.plugins.GoogleEarth = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_googleearth */
    ptype: "gxp_googleearth",

    /** config: config[timeout]
     *  ``Number``
     *  The time (in milliseconds) to wait before giving up on the Google API
     *  script loading.  This layer source will not be availble if the script
     *  does not load within the given timeout.  Default is 7000 (seven seconds).
     */
    timeout: 7000,

    //i18n
    menuText: "3D Viewer",
    tooltip: "Switch to 3D Viewer",
    tooltipMap: "Switch back to normal map view",
    iconCls: "gxp-icon-googleearth",
    text: null,

    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.plugins.GoogleEarth.superclass.constructor.apply(this, arguments);
    },
    
    /** api: method[addActions]
     */
    addActions: function() {
        var actions = [{
            menuText: this.menuText,
            enableToggle: true,
            iconCls: this.iconCls,
            text: this.text,
            tooltip: this.tooltip,
            toggleHandler: function(button, state) {
                // we unpress the button so that it will only show pressed
                // on successful display
                this.actions[0].each(function(cmp) {
                    if (cmp.toggle) {
                        cmp.toggle(false, true);
                    }
                });
                this.togglePanelDisplay(state);
            },
            scope: this
        }];

        return gxp.plugins.GoogleEarth.superclass.addActions.apply(this, [actions]);
    },

    /** private: method[togglePanelDisplay]
     *  :arg displayed: ``Boolean`` Display the Google Earth panel.
     */
    togglePanelDisplay: function(displayed) {
        // TODO: this split between the tool and the panel needs work
        var ownerCt = this.target.mapPanel.ownerCt;
        var layout = ownerCt && ownerCt.getLayout();
        if (layout && layout instanceof Ext.layout.CardLayout) {
            if (displayed === true) {
                gxp.plugins.GoogleEarth.loader.onLoad({
                    callback: function() {
                        // display the panel
                        layout.setActiveItem(1);
                        // enable action press any buttons associated with the action
                        this.actions[0].enable();
                        this.actions[0].items[0].setTooltip(this.tooltipMap);
                        this.actions[0].each(function(cmp) {
                            if (cmp.toggle) {
                                cmp.toggle(true, true);
                            }
                        });
                    },
                    // TODO: add errback for handling load failures
                    scope: this
                });
            } else {
                // hide the panel
                layout.setActiveItem(0);
                this.actions[0].items[0].setTooltip(this.tooltip);
            }
        }
    },

    /** private: method[getHost]
     *  :returns: ``String`` The current host name and port.
     * 
     *  This method is here mainly for mocking in tests.
     */
    getHost: function() {
        var name = window.location.host.split(":").shift();
        var port = window.location.port || "80";
        return name + ":" + port;
    }

});


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
        
        // The google loader accesses document.body, so we don't add the loader
        // script before the document is ready.
        function append() {
            document.getElementsByTagName("head")[0].appendChild(script);
        }
        if (document.body) {
            append();
        } else {
            Ext.onReady(append);
        }
        
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
