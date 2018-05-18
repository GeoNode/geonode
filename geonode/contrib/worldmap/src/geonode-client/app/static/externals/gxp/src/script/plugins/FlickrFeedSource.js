/**
 * Created with PyCharm.
 * User: mbertrand
 * Date: 6/18/12
 * Time: 1:55 PM
 * To change this template use File | Settings | File Templates.
 */


Ext.namespace("gxp.plugins");

OpenLayers.Format.Flickr = OpenLayers.Class(OpenLayers.Format.JSON, {

    defaultFormat: "OpenLayers.Format.JSON",
    defaultThumbnail: "url_q",
    defaultContent: "title",

    read: function(json, filter) {
        var responseJSON = OpenLayers.Format.JSON.prototype.read.apply(this, arguments);
        var photos = responseJSON.photos.photo;
        var response = this.parseResponse(photos);
        return response;
    },


    parseResponse: function(items){
        var features = [items.length];
        for (var i = 0; i < items.length; i++) {
            var photo = items[i];
            var fpoint = new  OpenLayers.Geometry.Point (photo.longitude, photo.latitude);
            var  attributes = {};
            for (var property in photo) {
                attributes[property] = photo[property];
            }
            attributes["thumbnail"] = photo[this.defaultThumbnail];
            attributes["content"] = photo[this.defaultContent];
            attributes["link"] = "http://www.flickr.com/photos/"
                + attributes["owner"] + "/"
                + attributes["id"];
            features[i] = new  OpenLayers.Feature.Vector (fpoint, attributes);

        }
        return features;
    }
});

gxp.plugins.FlickrFeedSource = Ext.extend(gxp.plugins.FeedSource, {

    /** api: ptype = gxp_rsssource */
    ptype: "gx_flickrsource",


    url: "/flickr",

    defaultFormat: "OpenLayers.Format.Flickr",

    /** Title for source **/
    title: 'Flickr Source',


    createLayerRecord: function(config) {
        if (config.params == null) {
            config.params = {"max-results":500, "q":""};
        }
        if (config.params["max-results"] == "") {
            config.params["max-results"] = 500;
        }
        if (config.params["q"] == null) {
            config.params["q"] == "";
        }
        config.url = this.url;

        var record = gxp.plugins.FlickrFeedSource.superclass.createLayerRecord.apply(this, arguments);
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
                content.innerHTML = feature.attributes.description;
                this.target.selectControl.popup = new OpenLayers.Popup("popup",
                    new OpenLayers.LonLat(pos.x, pos.y),
                    new OpenLayers.Size(150,150),
                    "<a target='_blank' href=" +
                        feature.attributes.link +"><img title='" +
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

Ext.preg(gxp.plugins.FlickrFeedSource.prototype.ptype, gxp.plugins.FlickrFeedSource);