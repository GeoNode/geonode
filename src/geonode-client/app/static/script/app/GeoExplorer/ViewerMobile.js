/**
 * Copyright (c) 2009-2010 The Open Planning Project
 *
 * @requires GeoExplorer.js
 */

/** api: (define)
 *  module = GeoExplorer
 *  class = Embed
 *  base_link = GeoExplorer
 */
Ext.namespace("gxp");

/** api: constructor
 *  ..class:: GeoExplorer.Viewer(config)
 *
 *  Create a GeoExplorer application suitable for embedding in larger pages.
 */
GeoExplorer.ViewerMobile = Ext.extend(GeoExplorer, {
    
    /** api: config[useCapabilities]
     *  ``Boolean`` If set to false, no Capabilities document will be loaded.
     */
    
    /** api: config[useToolbar]
     *  ``Boolean`` If set to false, no top toolbar will be rendered.
     */

	
    initMapPanel: function() {
        this.mapItems = [];

        OpenLayers.IMAGE_RELOAD_ATTEMPTS = 5;
        OpenLayers.Util.onImageLoadErrorColor = "transparent";

        GeoExplorer.superclass.initMapPanel.apply(this, arguments);

        var incrementLayerStats = function(layer) {
            Ext.Ajax.request({
                url: "/data/layerstats/",
                method: "POST",
                params: {layername:layer.params.LAYERS}
            });
        }
        this.mapPlugins = [{
            ptype: "gxp_loadingindicator",
            onlyShowOnFirstLoad: true
        }];

        this.mapPanel.map.events.register("preaddlayer", this, function(e) {
            var layer = e.layer;
            if (layer instanceof OpenLayers.Layer.WMS) {
                layer.events.on({
                    "loadend": function() {
                        incrementLayerStats(layer);
                        layer.events.unregister("loadend", this, arguments.callee);
                    },
                    scope: this
                });
            }
        });
        
        this.westPanel = new Ext.Panel({
            layout: "fit",
            id: "westpanel",
            border: false,
            collapsed: true,
            split: true,
            region: "west",
            autoScroll:true,
            width: "90%",
            title: "Layers",
            plugins: {
                init: function (p) {
                    if (p.collapsed) {
                        var r = p.region;
                        if ((r == 'east') || (r == 'west')) {
                            p.on('render', function () {
                                var ct = p.ownerCt;
                                ct.on('afterlayout', function () {
                                    p.collapsedTitleEl = ct.layout[r].collapsedEl.createChild({
                                        tag: 'span',
                                        cls: 'css-vertical-text',
                                        html: p.title
                                    });
                                    p.setTitle = Ext.Panel.prototype.setTitle.createSequence(function (t) {
                                        p.collapsedTitleEl.dom.innerHTML = t;
                                    });
                                }, false, {
                                    single: true
                                });
                            });
                        }
                    }
                }
            }
        });        

    },	
	
	
    loadConfig: function(config) {
        var source;
        for (var s in config.sources) {
            source = config.sources[s];
            if (!source.ptype || /wmsc?source/.test(source.ptype)) {
                source.forceLazy = config.useCapabilities === false;
            }
            if (config.useToolbar === false) {
                var remove = true, layer;
                for (var i=config.map.layers.length-1; i>=0; --i) {
                    layer = config.map.layers[i];
                    if (layer.source == s) {
                        if (layer.visibility === false) {
                            config.map.layers.remove(layer);
                        } else {
                            remove = false;
                        }
                    }
                }
                if (remove) {
                    delete config.sources[s];
                }
            }
        }
        if (config.useToolbar !== false) {
            config.tools = (config.tools || []).concat({
                ptype: "gxp_styler",
                id: "styler",
                rasterStyling: true,
                actionTarget: undefined
            },{
                ptype: "gxp_layermanager",
                groups: (config.map.groups || config.treeconfig),
                id: "treecontentmgr",
                autoScroll: true,
                outputConfig: {
                    id: "treecontent",
		            width: "100%",
                    autoScroll: true
                },
                outputTarget: "westpanel"
            });
        }
        

        
        
        // load the super's super, because we don't want the default tools from
        // GeoExplorer
        GeoExplorer.superclass.loadConfig.apply(this, arguments);
    },

    
    initInfoTextWindow: function() {
        this.infoTextPanel = new Ext.FormPanel({
        	layout: 'fit',
            bodyStyle: {padding: "5px"},
            labelAlign: "top",
            preventBodyReset: true,
            autoScroll:false,
            autoWidth: true,
            html: this.about['introtext']
        });




        this.infoTextWindow = new Ext.Window({
            title: this.about.title,
            closeAction: 'hide',
            items: this.infoTextPanel,
            modal: true,
            width: "100%",
            autoHeight: true,
            autoScroll: true,
            bbar: [{
                text: 'Close',
                width: "100%",
                handler: function(){
                	this.infoTextWindow.close(); 
                },
                scope: this
                }]
        });
    },
    
    
    /** private: method[initPortal]
     * Create the various parts that compose the layout.
     */
    initPortal: function() {

        // TODO: make a proper component out of this
        if (this.useMapOverlay !== false) {
            this.mapPanel.add(this.createMapOverlay());
        }

        if(this.useToolbar !== false) {
            this.toolbar = new Ext.Toolbar({
                xtype: "toolbar",
                region: "north",
                autoHeight: false,
                height: '50px',
                disabled: true,
                items: this.createTools()
            });
            this.on("ready", function() {this.toolbar.enable();}, this);
        }


        
        this.mapPanelContainer = new Ext.Panel({
            layout: "card",
            region: "center",
            ref: "../main",
            tbar: this.toolbar,
            defaults: {
                border: false
            },
            items: [
                this.mapPanel
            ],
            ref: "../main",
            activeItem: 0
        });


        this.portalItems = [
            this.mapPanelContainer,
            this.westPanel
        ];
        
        var gridWinPanel = new Ext.Panel({
            id: 'gridWinPanel',
            collapseMode: "mini",
            title: 'Identify Results',
            region: "west",
            autoScroll: true,
            split: true,
            items: []
        });

        var gridResultsPanel = new Ext.Panel({
            id: 'gridResultsPanel',
            title: 'Feature Details',
            region: "center",
            collapseMode: "mini",
            autoScroll: true,
            split: true,
            items: []
        });


        var identifyWindow = new Ext.Window({
            id: 'queryPanel',
            layout: "border",
            closeAction: "hide",
            items: [gridWinPanel, gridResultsPanel],
            width: "100%",
            height: 400
        });
        
        
        this.about["introtext"] = "Hello";
        
        GeoExplorer.superclass.initPortal.apply(this, arguments);
        
        
        //Show the info window if it's the first time here
        if (this.config.first_visit_mobile) {
        	this.about["introtext"] = Ext.get("mobile_intro").dom.innerHTML;
            if (!this.infoTextWindow) {
                this.initInfoTextWindow();
            }
            this.infoTextWindow.show();  	
            this.infoTextWindow.alignTo(document, 'tl-tl');
        }


    },
    
    /**
     * private: method[addLayerSource]
     */
    addLayerSource: function(options) {
        // use super's super instead of super - we don't want to issue
        // DescribeLayer requests because we neither need to style layers
        // nor to show a capabilities grid.
        var source = GeoExplorer.superclass.addLayerSource.apply(this, arguments);
    },

    /**
     * api: method[createTools]
     * Create the various parts that compose the layout.
     */
    createTools: function() {
        var tools = GeoExplorer.Viewer.superclass.createTools.apply(this, arguments);

        var layerChooser = new Ext.Button({
            tooltip: 'Layer Switcher',
            //iconCls: 'icon-layer-switcher',
            text: "Layers",
            menu: new gxp.menu.LayerMenu({
                layers: this.mapPanel.layers
            })
        });

        tools.unshift("-");
        tools.unshift(layerChooser);

        var aboutButton = new Ext.Button({
            tooltip: "About this map",
            //iconCls: "icon-about",
            text: "About",
            handler: this.displayAppInfo,
            scope: this
        });

        tools.push("->");
        tools.push(aboutButton);

        return tools;
    }
});
