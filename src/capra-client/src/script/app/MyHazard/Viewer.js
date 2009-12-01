Ext.namespace("MyHazard");
MyHazard.Viewer = Ext.extend(Ext.util.Observable, {
    reportService: "/hazard/report",
    popup: null,
    mapPanel: null,
    appPanel: null,
    sidebar: null,
    hazardConfig: null,

    pdfButtonText: "UT: PDF Report",
    
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
                }, this);
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

    createLayers: function(){
        var layers = [];
        var hazard;
        for(var i = 0; i < this.hazardConfig.length; i++){
            hazard = this.hazardConfig[i];

            var periods = hazard.periods;
            periods.sort(function(period){return period.length;});
            var layersParam = [];
            for(var j = 0; j < periods.length; j++){
                layersParam.push(periods[j].typename);
            }
            
            layers.unshift(new OpenLayers.Layer.WMS(hazard.hazard,
 	                             this.GEONODE_WMS, {
 	                                 layers: layersParam,
 	                                 transparent: true,
 	                                 format: "image/gif"
 	                             }, {
 	                                 isBaseLayer: false,
 	                                 buffer: 0, 
 	                                 // exclude this layer from layer container nodes
 	                                 displayInLayerSwitcher: false,
 	                                 visibility: false
 	                             }));
            
        }

        return layers;
    },

    createLayout: function(){
        this.map = new OpenLayers.Map(
            {allOverlays: false,
             controls: [new OpenLayers.Control.Navigation(),
                       new OpenLayers.Control.PanPanel(),
                       new OpenLayers.Control.ZoomPanel()]
            });

        var baseLayers = [
            new OpenLayers.Layer.WMS(
                "Global Imagery",
                "http://sigma.openplans.org/geoserver/wms",
                {layers: 'bluemarble'}
            ),
            new OpenLayers.Layer.Google(
                "Google Hybrid", 
                {numZoomLevels: 20,
                 type: G_HYBRID_MAP}
            )
        ];

        var layers = this.createLayers();

        this.map.addLayers(layers.concat(baseLayers));

        this.mapPanel = new GeoExt.MapPanel({
            region: "center",
            center: new OpenLayers.LonLat(-87, 13),
            zoom: 5,
            map: this.map,
            items: [
                {
                    xtype: "gx_zoomslider",
                    vertical: true,
                    height: 100,
                    plugins: new GeoExt.ZoomSliderTip({
			template: "<div>"+this.zoomSliderTipText+": {zoom}<div>"
                    })
                },
                this.createMapOverlay()
            ]
        });

        var toolGroup = "toolGroup";

        var activeIndex = 0;
        var reportSplit = new Ext.SplitButton({
            iconCls: "icon-point",
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
                            control: this.createReporter(OpenLayers.Handler.Point)
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
                            control: this.createReporter(OpenLayers.Handler.Path)
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
                            control: this.createReporter(OpenLayers.Handler.Polygon)
                        }))
                ]                
            })
        });

        reportSplit.menu.items.each(function(item, index) {
            item.on({checkchange: function(item, checked) {
                reportSplit.toggle(checked);
                if(checked) {
                    activeIndex = index;
                    reportSplit.setIconClass(item.iconCls);
                }
            }});
        });
        
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
            }),
            new Ext.Button({
                tooltip: this.transparencyMenuText,
                iconCls: "icon-visibility",
                menu: {
                    minWidth: 10,
                    items: [
                        new MyHazard.LayerGroupOpacitySlider({
                            layers: layers,
                            vertical: true,
                            height: 150
                        })
                    ]
                }
            })
        ];

        treeConfig = [];

        for(var i = 0; i < layers.length; i++){
            treeConfig.push({
                nodeType: "gx_layer",
                layer: layers[i].name,
                allowDrop: false,
                isLead: false,
                loader: new GeoExt.tree.LayerParamLoader({
                    param: "LAYERS",
                    baseAttrs: {
                        draggable: false,
                        allowDrop: false // this should be a default
                    }
                }),
                listeners : {
                    "move" : function(tree, node, oldParent, newParent, index){
                        this.map.setLayerIndex(node.layer, index);
                    },
                    scope: this
                }
            });
        }

        treeConfig.push({
            nodeType: "gx_baselayercontainer",
            draggable: false,
            allowDrop: false,
            isTarget: false
        });

        this.sidebar = new Ext.tree.TreePanel({
            region: "west",
            width: 250,
            tbar: tools,
            loader: new Ext.tree.TreeLoader({
                applyLoader: false
            }),
            enableDD: true,
            rootVisible: false,
            root: {
                nodeType: "async",
                children: treeConfig
            }
        });
        

        this.appPanel = new Ext.Panel({
            renderTo: "app",
            width: 950,
            height: 400,
            layout: "border",
            items: [this.sidebar, this.mapPanel]
        });

    },

    activate: function(){
        Ext.QuickTips.init();
        //populate the map and layer tree according to the
        //hazard configuration

        //activate the reporting controls.
    },

    createReporter: function(handlerType) {
        return new MyHazard.Reporter(handlerType, {
            eventListeners: {
                report: this.report,
                activate: this.clearPopup,
                deactivate: this.clearPopup,
                scope: this
            }
        });
    },

    clearPopup: function() {
        if (this.popup) {
            this.popup.close();
            delete this.popup;

            // If we still have a transient geometry from one of the draw tools, kill it.
            var controls = this.mapPanel.map.controls;
            for (var i = 0, len = controls.length; i < len; i++) {
                var c = controls[i];
                if (c.active && c.handler && c.handler.cancel) {
                    c.handler.cancel();
                }
            }
        }
    },

    report: function(evt) {
        var geom = evt.geom;
        var geojson = new OpenLayers.Format.GeoJSON();
        var json = new OpenLayers.Format.JSON();
        var request = {
            geometry: json.read(geojson.write(geom)),
            scale: this.mapPanel.map.getScale(),
            datalayers: [],
            politicalLayer: 'base:distrits',
            politicalLayerAttributes: ['CANTON', 'DISTRITO', 'PROVINCIA']
        };

        request.geometry.crs = { 
            "type": "name",
            "properties": { "name": "EPSG:4326" }
        };

        this.mapPanel.layers.each(function(rec) {
            var layer = rec.get("layer");
            if (!layer.displayInLayerSwitcher && layer.params) {
                request.datalayers = request.datalayers.concat(layer.params.LAYERS);
            }
        });
        this.clearPopup();

        request = json.write(request);

        Ext.Ajax.request({
            url: this.reportService + '.html',
            xmlData: request,
            method: "POST",
            success: function(response, options) {
                this.popup = new GeoExt.Popup({
                    feature: new OpenLayers.Feature.Vector(geom),
                    title: "UT:MyHazard Report",
                    html: response.responseText,
                    maximizable: true,
                    height: 350,
                    width: 275,
                    map: this.mapPanel,
                    bbar: [
                        '<a class="download pdf" href="' + this.reportService + '.pdf?' + 
                        Ext.urlEncode({ q: request }) + '"> ' +
                        this.pdfButtonText + '</a>'
                    ],
                    listeners: {
                       hide: this.clearPopup,
                       scope: this
                    }
                });
                this.mapPanel.add(this.popup);
                this.popup.show();
            },
            failure: function() {
                alert("Failure while retrieving report...");
            },
            scope: this
        });
    },


    createMapOverlay: function() {
        var scaleLinePanel = new Ext.Panel({
            cls: 'olControlScaleLine overlay-element overlay-scaleline',
            border: false
        });

        scaleLinePanel.on('render', function(){
            var scaleLine = new OpenLayers.Control.ScaleLine({
                div: scaleLinePanel.body.dom
            });

            this.map.addControl(scaleLine);
            scaleLine.activate();
        }, this);

        var zoomStore = new GeoExt.data.ScaleStore({
            map: this.map
        });

        var zoomSelector = new Ext.form.ComboBox({
		emptyText: this.zoomSelectorText,
            tpl: '<tpl for="."><div class="x-combo-list-item">1 : {[parseInt(values.scale)]}</div></tpl>',
            editable: false,
            triggerAction: 'all',
            mode: 'local',
            store: zoomStore,
            width: 110
        });

        zoomSelector.on('click', function(evt){evt.stopEvent();});
        zoomSelector.on('mousedown', function(evt){evt.stopEvent();});

        zoomSelector.on('select', function(combo, record, index) {
                this.map.zoomTo(record.data.level);
            },
            this);

        var zoomSelectorWrapper = new Ext.Panel({
            items: [zoomSelector],
            cls: 'overlay-element overlay-scalechooser',
            border: false });

        this.map.events.register('zoomend', this, function() {
            var scale = zoomStore.queryBy(function(record){
                return this.map.getZoom() == record.data.level;
            });

            if (scale.length > 0) {
                scale = scale.items[0];
                zoomSelector.setValue("1 : " + parseInt(scale.data.scale, 10));
            } else {
                if (!zoomSelector.rendered) return;
                zoomSelector.clearValue();
            }
        });

        var mapOverlay = new Ext.Panel({
            // title: "Overlay",
            cls: 'map-overlay',
            items: [
                scaleLinePanel,
                zoomSelectorWrapper
            ]
        });


        mapOverlay.on("afterlayout", function(){
            scaleLinePanel.body.dom.style.position = 'relative';
            scaleLinePanel.body.dom.style.display = 'inline';

            mapOverlay.getEl().on("click", function(x){x.stopEvent();});
            mapOverlay.getEl().on("mousedown", function(x){x.stopEvent();});
        }, this);

        return mapOverlay;
    }

});
