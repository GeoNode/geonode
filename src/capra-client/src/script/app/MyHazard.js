var MyHazard = Ext.extend(Ext.util.Observable, {

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

        var toolGroup = "toolGroup";

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

        this.sidebar = 
            this.mapPanel = new Ext.Panel({
                region: "west",
                width: 250,
                tbar: tools

            });

        this.map = new OpenLayers.Map();

        //dummy layers for development standin
        var layer = new OpenLayers.Layer.WMS(
            "Global Imagery",
            "http://demo.opengeo.org/geoserver/wms",
            {layers: 'bluemarble'}
        );
        this.map.addLayer(layer);


        this.mapPanel = new GeoExt.MapPanel({
            region: "center",
            center: new OpenLayers.LonLat(5, 45),
            zoom: 4,
            map: this.map
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

    }
});
