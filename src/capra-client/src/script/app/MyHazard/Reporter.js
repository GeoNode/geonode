Ext.namespace("MyHazard");

MyHazard.Reporter = OpenLayers.Class(OpenLayers.Control, {
    format: null,

    initialize: function(handler, options) {
        handler = handler || OpenLayers.Handler.Point;
        this.format = (options && options.format) || new OpenLayers.Format.GeoJSON();
        OpenLayers.Control.prototype.initialize.apply(this, [options]);
        this.callbacks = OpenLayers.Util.extend(
            {done: this.report},
            this.callbacks
        );

        this.handlerOptions = OpenLayers.Util.extend(
            {persist: this.persist}, this.handlerOptions
        );
        this.handler = new handler(this, this.callbacks, this.handlerOptions);
    },

    report: function(geom) {
        alert(this.format.write(geom));
    }
});
