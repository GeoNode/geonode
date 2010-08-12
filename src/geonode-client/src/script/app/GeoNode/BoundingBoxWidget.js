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
        this.activated = false;
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
            bounds.transform(this.viewer.mapPanel.map.getProjectionObject(),
                new OpenLayers.Projection("EPSG:4326"));
            query.bbox = bounds.toBBOX();
        }
        else {
            // no constraint, don't include.
            delete query.bbox;
        }
    },
    
    initFromQuery: function(grid, query) {  
        if (query.bbox) {
            var bounds = OpenLayers.Bounds.fromString(query.bbox);
            if (bounds) {
                bounds.transform(new OpenLayers.Projection("EPSG:4326"),
                    this.viewer.mapPanel.map.getProjectionObject());
                this.enable();
                this.viewer.mapPanel.map.zoomToExtent(bounds, true);
            }
        }
    },
    
    activate: function() {
        this.activated = true;
    },
    
    enable: function() {
        this.enabledCB.checked = true;
        this.viewer.portal.expand();
    }, 

    disable: function() {
        this.enabledCB.checked = false;
        this.viewer.portal && this.viewer.portal.collapse();
    }
});
