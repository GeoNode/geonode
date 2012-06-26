/**
 * Created with PyCharm.
 * User: mbertrand
 * Date: 6/18/12
 * Time: 1:55 PM
 * To change this template use File | Settings | File Templates.
 */


Ext.namespace("gxp.plugins");

OpenLayers.Format.Picasa = OpenLayers.Class(OpenLayers.Format.GeoRSS, {
    createFeatureFromItem: function(item) {
        var feature = OpenLayers.Format.GeoRSS.prototype
            .createFeatureFromItem.apply(this, arguments);
        feature.attributes.thumbnail = this.getElementsByTagNameNS(item, "http://search.yahoo.com/mrss/", "thumbnail")[0].getAttribute("url");
        feature.attributes.content = OpenLayers.Util.getXmlNodeValue(this.getElementsByTagNameNS(item, "*","summary")[0]);
        return feature;
    }
});

gxp.plugins.PicasaFeedSource = Ext.extend(gxp.plugins.FeedSource, {

    /** api: ptype = gxp_rsssource */
    ptype: "gx_picasasource",


    url: "/picasa",

    defaultFormat: "OpenLayers.Format.Picasa",

    /** Title for source **/
    title: 'Picasa Source',


    createLayerRecord: function(config) {
        if (config.params == null) {
            config.params = {"kind":"photo","max-results":50, "q":""}
        }
        if (config.params["kind"] == null) {
            config.params["kind"] = "photo";
        }
        if (config.params["max-results"] == "") {
            config.params["max-results"] = 50;
        }
        if (config.params["q"] == null) {
          config.params["q"] == ""
        }
        config.url = this.url;

        var record = gxp.plugins.PicasaFeedSource.superclass.createLayerRecord.apply(this, arguments);
        return record;
    },

    configureInfoPopup: function(layer) {
        layer.events.on({
            "featureselected": function(featureObject) {
                var feature = featureObject.feature;
                var pos = feature.geometry;

                if (this.target.selectControl.popup != null) {
                    this.target.mapPanel.map.removePopup(this.target.selectControl.popup);
                }

                var content = document.createElement("div");
                content.innerHTML = feature.attributes.content;
                this.target.selectControl.popup = new OpenLayers.Popup("popup",
                    new OpenLayers.LonLat(pos.x, pos.y),
                    new OpenLayers.Size(160,160),
                    "<a target='_blank' href=" +
                        content.getElementsByTagName('a')[0].getAttribute('href') +"><img title='" +
                        feature.attributes.title +"' src='" + feature.attributes.thumbnail +"' /></a>",
                    false);
                this.target.selectControl.popup.closeOnMove = true;
                this.target.selectControl.popup.keepInMap = true;
                this.target.mapPanel.map.addPopup(this.target.selectControl.popup);
            },

            "featureunselected" : function(featureObject) {
                this.target.mapPanel.map.removePopup(this.target.selectControl.popup);
                this.target.selectControl.popup = null;
            },
            scope: this
        });
    },

    getStyleMap: function(config) {
        return new OpenLayers.StyleMap({
            "default": new OpenLayers.Style({externalGraphic: "${thumbnail}", pointRadius: 14}),
            "select": new OpenLayers.Style({pointRadius: 20})
        });
    }

});

Ext.preg(gxp.plugins.PicasaFeedSource.prototype.ptype, gxp.plugins.PicasaFeedSource);