Ext.namespace("MyHazard");

MyHazard.Reporter = OpenLayers.Class(OpenLayers.Control, {
    format: null,
    persist: true,

    EVENT_TYPES: ["report"],

    initialize: function(handler, options) {
        this.EVENT_TYPES = MyHazard.Reporter.prototype.EVENT_TYPES.concat(
            OpenLayers.Control.prototype.EVENT_TYPES
        );
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
        this.events.triggerEvent("report", {geom: geom});
    }
});
