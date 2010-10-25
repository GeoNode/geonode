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
Ext.namespace("GeoExplorer");

/** api: constructor
 *  ..class:: GeoExplorer.Viewer(config)
 *
 *  Create a GeoExplorer application suitable for embedding in larger pages.
 */
GeoExplorer.Viewer = Ext.extend(GeoExplorer, {

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
                autoHeight: true,
                disabled: true,
                items: this.createTools()
            });
            this.on("ready", function() {this.toolbar.enable();}, this);
        }

        this.mapPanelContainer = new Ext.Panel({
            layout: "card",
            region: "center",
            tbar: this.toolbar,
            defaults: {
                border: false
            },
            items: [
                this.mapPanel,
                new gxp.GoogleEarthPanel({
                    mapPanel: this.mapPanel,
                    listeners: {
                        beforeadd: function(record) {
                            return record.get("group") !== "background";
                        }
                    }
                })
            ],
            activeItem: 0
        });

        this.portalItems = [
            this.mapPanelContainer
        ];
        
        GeoExplorer.superclass.initPortal.apply(this, arguments);        

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
            iconCls: 'icon-layer-switcher',
            menu: new gxp.menu.LayerMenu({
                layers: this.mapPanel.layers
            })
        });

        tools.unshift("-");
        tools.unshift(layerChooser);

        var aboutButton = new Ext.Button({
            tooltip: "About this map",
            iconCls: "icon-about",
            handler: this.displayAppInfo,
            scope: this
        });

        tools.push("->");
        tools.push(aboutButton);

        return tools;
    }
});








