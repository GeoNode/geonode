Ext.namespace("GeoNode");

GeoNode.BoundingBoxWidget = Ext.extend(Ext.util.Observable, {

    /**
     * Property: viewerConfig
     * Options such as background layers configuration to be passed to the
     * gxp.Viewer instance enclosed by this BoundingBoxWidget.
     */
    viewerConfig: null,
    height: 300,
    isEnabled: false,
    useGxpViewer: false,

    constructor: function(config, vanillaViewer) {
        Ext.apply(this, config);
        this.doLayout();
        var heatmap = new GeoNode.HeatmapModel({bbox_widget: this});
    },

    doLayout: function() {

        var el = Ext.get(this.renderTo);

        var viewerConfig = {
            proxy: this.proxy,
            useCapabilities: false,
            useBackgroundCapabilities: false,
            useToolbar: false,
            useMapOverlay: false,
            portalConfig: {
                collapsed: false,
                border: false,
                height: this.height,
                renderTo: el.query('.bbox-expand')[0]
            },
            listeners: {
                "ready": function() {
                    this._ready = true;
                },
                scope: this
            }
        }

        viewerConfig = Ext.apply(viewerConfig, this.viewerConfig)

        /* Use regular gxp.Viewer if displaying in window on map page, to avoid confusion/conflict with main GeoExplorer instance */
        if (this.useGxpViewer)
        {
            viewerConfig.mapItems = [{
                xtype: "gx_zoomslider",
                vertical: true,
                height: 100
            }];
            this.viewer = new gxp.Viewer(viewerConfig);
        }

        else{
            this.viewer = new GeoExplorer.Viewer(viewerConfig);
        }

    },

    updateBBox: function(bounds) {
        if (bounds && bounds != null)
        {
            var bbmap = this.viewer.mapPanel.map;
            bbmap.zoomToExtent(bounds);
        }
    },

    isActive: function() {
        return true; 
    },
    
    hasConstraint: function() {
        return this.isActive()
    },
    
    applyConstraint: function(query) {
        /* set parameters in the search query to limit the search to the 
         * displayed bounding box.
         */
        if (this.hasConstraint()) {
            var bounds = this.viewer.mapPanel.map.getExtent();
            bounds.transform(
                new OpenLayers.Projection(this.viewerConfig.map.projection),
                new OpenLayers.Projection("EPSG:4326"));
            query.bbox = bounds.toBBOX();
        }
        else if (this._ready) {
            // no constraint, don't include.
            delete query.bbox;
        }
    },
    
    initFromQuery: function(grid, query) {
        if (query.bbox) {
            var bounds = OpenLayers.Bounds.fromString(query.bbox);
            if (bounds) {
                bounds.transform(
                    new OpenLayers.Projection("EPSG:4326"),
                    new OpenLayers.Projection(this.viewerConfig.map.projection)
                );
                var setMapExtent = function() {
                    var map = this.viewer.mapPanel.map;
                    // when zooming to extent (rather than zoom+center), we
                    // need to wait until the map has its target size
                    map.events.register("moveend", this, function() {
                        map.events.unregister("moveend", this, arguments.callee);
                        map.zoomToExtent(bounds, true);
                    });
                };
                if (this._ready) {
                    setMapExtent.call(this);
                } else {
                    this.viewer.on("ready", setMapExtent, this)
                }
            }
        }
    }
});
