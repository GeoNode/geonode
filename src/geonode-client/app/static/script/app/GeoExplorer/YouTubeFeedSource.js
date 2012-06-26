/**
 * Created with PyCharm.
 * User: mbertrand
 * Date: 6/18/12
 * Time: 1:55 PM
 * To change this template use File | Settings | File Templates.
 */


Ext.namespace("gxp.plugins");

OpenLayers.Format.YouTube = OpenLayers.Class(OpenLayers.Format.GeoRSS, {
    createFeatureFromItem: function(item) {
        var feature = OpenLayers.Format.GeoRSS.prototype.createFeatureFromItem.apply(this, arguments);
        feature.attributes.thumbnail = this.getElementsByTagNameNS(item, "http://search.yahoo.com/mrss/", "thumbnail")[4].getAttribute("url");
        feature.attributes.content = OpenLayers.Util.getXmlNodeValue(this.getElementsByTagNameNS(item, "*","summary")[0]);
        return feature;
    }
});

gxp.plugins.YouTubeFeedSource = Ext.extend(gxp.plugins.FeedSource, {

    /** api: ptype = gxp_rsssource */
    ptype: "gx_youtubesource",


    url: "/youtube",

    defaultFormat: "OpenLayers.Format.YouTube",

    /** Title for source **/
    title: 'YouTube Source',


    createLayerRecord: function(config) {
        if (config.params == null) {
            config.params = {"max-results":50, "q":""}
        }
        if (config.params["max-results"] == "") {
            config.params["max-results"] = 50;
        }
        if (config.params["q"] == "") {
            config.params["q"] == ""
        }
        config.url = this.url;

        var record = gxp.plugins.YouTubeFeedSource.superclass.createLayerRecord.apply(this, arguments);
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
                    new OpenLayers.Size(240, 180),
                    "<a target='_blank' href=" +
                        feature.attributes.link + "><img height='180', width='240' title='" +
                        feature.attributes.title + "' src='" + feature.attributes.thumbnail + "' /></a>",
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
            "default":new OpenLayers.Style({externalGraphic:"${thumbnail}", pointRadius:24}),
            "select":new OpenLayers.Style({pointRadius:30})
        });
    }

});

Ext.preg(gxp.plugins.YouTubeFeedSource.prototype.ptype, gxp.plugins.YouTubeFeedSource);