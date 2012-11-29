/**
 * Created by PyCharm.
 * User: mbertrand
 * Date: 8/15/11
 * Time: 10:03 AM
 * To change this template use File | Settings | File Templates.
 */


StreetViewPopup = OpenLayers.Class(OpenLayers.Control, {

     popup: null,
     mapPanel: null,
     titleHeader: 'Street View',
     popupHeight: 300,
     popupWidth: 300,

    defaults: {
        pixelTolerance: 1,
        stopSingle: true
    },

    initialize: function(options) {
        this.handlerOptions = OpenLayers.Util.extend(
            {}, this.defaults
        );
        OpenLayers.Control.prototype.initialize.apply(this, arguments);
        this.handler = new OpenLayers.Handler.Click(
            this, {click: this.trigger}, this.handlerOptions
        );
    },

    trigger: function(event) {
            this.openPopup(this.map.getLonLatFromViewPortPx(event.xy));
    },


     openPopup: function(location) {
            if (!location) {
                location = this.mapPanel.map.getCenter();
            }
            if (this.popup && this.popup.anc) {
                this.popup.close();
            }

            this.popup = new GeoExt.Popup({
                title: this.titleHeader,
                location: location,
                width: this.popupWidth,
                height: this.popupHeight,
                collapsible: true,
                map: this.mapPanel,
                items: [new gxp.GoogleStreetViewPanel()]
            });
            this.popup.show();
        }

});

