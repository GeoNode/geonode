/** api: (define)
 *  module = GeoExplorer
 *  class = Embed
 *  base_link = GeoExplorer
 */

/** api: constructor
 *  ..class:: GeoExplorer.Embed(config)
 *
 *  Create a GeoExplorer that knows how to preview a single layer with switchable styles etc.
 */
LayerPreview = Ext.extend(GeoExplorer, {

    zoomLevelText: "UT:Zoom Level: {zoom}",

    useToolbar: true,

    /**
     * api: method[createLayout]
     * Create the various parts that compose the layout.
     */
    createLayout: function() {
        // create the map
        // TODO: check this.initialConfig.map for any map options
        this.map = new OpenLayers.Map({
            allOverlays: true,
            projection: new OpenLayers.Projection("EPSG:900913"),
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            units: "m",
            maxResolution: 156543.0339,
            maxExtent: new OpenLayers.Bounds(
                -20037508.34, -20037508.34,
                 20037508.34,  20037508.34
            ),
            controls: [
                new OpenLayers.Control.PanPanel(),
                new OpenLayers.Control.ZoomPanel()
            ]
        });

        //** Remove this code when OpenLayers #2069 is closed **
        var onDoubleClick = function(ctrl, evt) { 
 	        OpenLayers.Event.stop(evt ? evt : window.event); 
        };
        var controls = this.map.controls[0].controls;
        for(var i = 0; i < controls.length; i++){
            OpenLayers.Event.observe(controls[i].panel_div, "dblclick",  
 	                             OpenLayers.Function.bind(onDoubleClick, this.map.controls[0], controls[i])); 
        }        
        //******************************************************

        //TODO: make this more configurable
        this.map.events.on({
            "preaddlayer" : function(evt){
                if(evt.layer.mergeNewParams){
                    var maxExtent = evt.layer.maxExtent;
                    if (maxExtent) evt.layer.mergeNewParams({
                        transparent: true,
                        format: "image/png",
                        tiled: true,
                        tilesorigin: [maxExtent.left, maxExtent.bottom]
                    });
                }
            },
            scope : this
        });
        

        // place map in panel
        var mapConfig = this.initialConfig.map || {};
        var center = mapConfig.center && 
            new OpenLayers.LonLat(mapConfig.center[0], mapConfig.center[1]).transform(
                new OpenLayers.Projection("EPSG:4326"),
                new OpenLayers.Projection("EPSG:900913")
            ); 
        this.mapPanel = new GeoExt.MapPanel({
            layout: "anchor",
            border: true,
            region: "center",
            map: this.map,
            // TODO: update the OpenLayers.Map constructor to accept an initial center
            center: center,
            // TODO: update the OpenLayers.Map constructor to accept an initial zoom
            zoom: mapConfig.zoom,
            items: [
                {
                    xtype: "gx_zoomslider",
                    vertical: true,
                    height: 100,
                    plugins: new GeoExt.ZoomSliderTip({
                        template: "<div>"+this.zoomLevelText+"</div>"
                    })
                },
                this.createMapOverlay()
            ]
        });
        
        // create layer store
        this.layers = this.mapPanel.layers;
        
        var toolbar;
        if(this.useToolbar){
            toolbar = new Ext.Toolbar({
                xtype: "toolbar",
                region: "north",
                disabled: true,
                items: this.createTools()
            });

            this.on("ready", function() {
                toolbar.enable();
            });
        } else {
            this.mapPanel.map.addControl(new OpenLayers.Control.Navigation());
        }
        
        var viewport = new Ext.Panel({
            renderTo: this.renderTo,
            height: this.height,
            layout: "fit",
            hideBorders: true,
            items: {
                layout: "border",
                deferredRender: false,
                items: (toolbar ? [toolbar] : []).concat([this.mapPanel])
            }
        });    
    },

    setPreviewStyle: function(stylename) {
        function isPreviewedLayer(rec) {
            var index = this.layerSources.find("identifier", rec.get("source_id"))
            return index != -1; // the previewed layer is the only one that is not a background layer
        }

        var layerIndex = this.layers.findBy(isPreviewedLayer, this);
        if (layerIndex != -1) {
            this.layers.getAt(layerIndex).get("layer").mergeNewParams({"styles": stylename});
        }
    }
});
