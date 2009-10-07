Ext.namespace("MyHazard");
MyHazard.Viewer = Ext.extend(Ext.util.Observable, {
    reportService: "/hazard/report.html",
    mapPanel: null,
    sidebar: null,
    
    constructor: function (config) {
        this.initialConfig = config;
        Ext.apply(this, this.initialConfig);
        this.addEvents(
            "ready"
        );

        this.load();
    },

    load: function() {
        var dispatchQueue = [
            // create layout as soon as Ext says ready
            function(done) {
                Ext.onReady(function() {
                    this.createLayout();
                    done();
                }, this)
            },
            function(done) {
                //TODO: Get hazard configuration from django
                //app and store it
                done();
            }
        ];
 
        GeoExplorer.util.dispatch(
            dispatchQueue,
            this.activate, 
            this);
    },

    createLayout: function(){
        this.map = new OpenLayers.Map({allOverlays: false});

        //dummy layers for development standin
        var layers = [
            new OpenLayers.Layer.WMS(
                "Global Imagery",
                "http://demo.opengeo.org/geoserver/wms",
                {layers: 'bluemarble'}
            ),
            new OpenLayers.Layer.Google(
                "Google Hybrid", 
                {numZoomLevels: 20,
                 type: G_HYBRID_MAP}
            )
        ];

        this.map.addLayers(layers);

        this.mapPanel = new GeoExt.MapPanel({
            region: "center",
            center: new OpenLayers.LonLat(5, 45),
            zoom: 4,
            map: this.map
        });

        var toolGroup = "toolGroup";

        var reportSplit = new Ext.SplitButton({
            iconCls: "icon-getfeatureinfo",
            tooltip: "TODO: Tooltip here",
            enableToggle: true,
            toggleGroup: toolGroup, // Ext doesn't respect this, registered with ButtonToggleMgr below
            allowDepress: false, // Ext doesn't respect this, handler deals with it
            handler: function(button, event) {
                // allowDepress should deal with this first condition
                if(!button.pressed) {
                    button.toggle();
                } else {
                    button.menu.items.itemAt(activeIndex).setChecked(true);
                }
            },
            listeners: {
                toggle: function(button, pressed) {
                    // toggleGroup should handle this
                    if(!pressed) {
                        button.menu.items.each(function(i) {
                            i.setChecked(false);
                        });
                    }
                },
                render: function(button) {
                    // toggleGroup should handle this
                    Ext.ButtonToggleMgr.register(button);
                }
            },
            menu: new Ext.menu.Menu({
                items: [
                    new Ext.menu.CheckItem(
                        new GeoExt.Action({
                            text: "TODO: Point reporter",
                            iconCls: "icon-point",
                            map: this.map,
                            toggleGroup: toolGroup,
                            group: toolGroup,
                            allowDepress: false,
                            map: this.map,
                            control: new MyHazard.Reporter(OpenLayers.Handler.Point, {
                                eventListeners: {
                                    report: this.report,
                                    scope: this
                                }
                            })
                        })),
                    new Ext.menu.CheckItem(
                        new GeoExt.Action({
                            text: "TODO: Line reporter",
                            iconCls: "icon-line",
                            map: this.map,
                            toggleGroup: toolGroup,
                            group: toolGroup,
                            allowDepress: false,
                            map: this.map,
                            control: new MyHazard.Reporter(OpenLayers.Handler.Path, {
                                eventListeners: {
                                    report: this.report,
                                    scope: this
                                }
                            })
                        })),
                    new Ext.menu.CheckItem(
                        new GeoExt.Action({
                            text: "TODO: Polygon reporter",
                            iconCls: "icon-polygon",
                            map: this.map,
                            toggleGroup: toolGroup,
                            group: toolGroup,
                            allowDepress: false,
                            map: this.map,
                            control: new MyHazard.Reporter(OpenLayers.Handler.Polygon, {
                                eventListeners: {
                                    report: this.report,
                                    scope: this
                                }
                            })
                        }))
                ]                
            })
        });
/*        reportSplit.menu.items.each(function(item, index) {
            item.on({checkchange: function(item, checked) {
                reportSplit.toggle(checked);
                if(checked) {
                    activeIndex = index;
                    reportSplit.setIconClass(item.iconCls);
                }
            }});
        }); */
        
        var tools = [
            new GeoExt.Action({
                tooltip: this.navActionTipText,
                iconCls: "icon-pan",
                enableToggle: true,
                pressed: true,
                allowDepress: false,
                control: new OpenLayers.Control.Navigation(),
                map: this.map,
                toggleGroup: toolGroup
            }),
            reportSplit,
            "-",
            new Ext.Button({
                handler: function(){
                    this.map.zoomIn();
                },
                tooltip: this.zoomInActionText,
                iconCls: "icon-zoom-in",
                scope: this
            }),
            new Ext.Button({
		    tooltip: this.zoomOutActionText,
                handler: function(){
                    this.map.zoomOut();
                },
                iconCls: "icon-zoom-out",
                scope: this
            })
        ];

        this.sidebar = new Ext.tree.TreePanel({
            region: "west",
            width: 250,
            tbar: tools,
            loader: new Ext.tree.TreeLoader({
                applyLoader: false
            }),
            rootVisible: false,
            root: {
                nodeType: "async",
                children: [
                    {nodeType: "gx_baselayercontainer"}
                ]
            }
        });
        

        var appPanel = new Ext.Panel({
            renderTo: "app",
            width: 950,
            height: 400,
            layout: "border",
            items: [this.sidebar, this.mapPanel]
        });

    },

    activate: function(){
        //populate the map and layer tree according to the
        //hazard configuration

        //activate the reporting controls.
    },

    report: function(evt) {
        var geom = evt.geom;
        var format = new OpenLayers.Format.GeoJSON();

        Ext.Ajax.request({
            url: this.reportService,
            xmlData: format.write(geom),
            method: "POST",
            success: function(response, options) {
                var popup = new GeoExt.Popup({
                    lonlat: geom.getCentroid(),
                    html: response.responseText,
                    map: this.mapPanel
                });
                this.mapPanel.add(popup);
                popup.show();
            },
            failure: function() {
                alert("Failure while retrieving report...");
            },
            scope: this
        });
    }
});
