Ext.namespace("GeoNode");

GeoNode.BoundingBoxWidget = Ext.extend(Ext.util.Observable, {

    /**
     * Property: viewerConfig
     * Options such as background layers configuration to be passed to the
     * gxp.Viewer instance enclosed by this BoundingBoxWidget.
     */
    viewerConfig: null,

    constructor: function(config) {
        Ext.apply(this, config);
        this.doLayout();
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
                collapsed: true,
                border: false,
                height: 300,
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

        this.viewer = new GeoExplorer.Viewer(viewerConfig);

        this.enabledCB = el.query('.bbox-enabled input')[0];        
        this.disable();
         
        Ext.get(this.enabledCB).on('click', function() {
            if (this.enabledCB.checked == true) {
                this.enable();
            }
            else {
                this.disable();
            }
        }, this);

    },
    
    isActive: function() {
        return this.enabledCB.checked == true; 
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
                    this.enable();
                };
                if (this._ready) {
                    setMapExtent.call(this);
                } else {
                    this.viewer.on("ready", setMapExtent, this)
                }
            }
        }
    },
    
    enable: function() {
        this.enabledCB.checked = true;
        this.viewer.portal && this.viewer.portal.expand();
    }, 

    disable: function() {
        this.enabledCB.checked = false;
        this.viewer.portal && this.viewer.portal.collapse();
    }
});
