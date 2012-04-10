Ext.namespace("GeoExplorer")

/*
 *  Create a tool to display YouTube Feeds in GeoExplorer based on 1 or more keywords
 *  target: GeoExplorer instance
 */

// TODO: Use JSON, override read instead of createFeatureFromItem, see http://openlayers.org/dev/examples/strategy-bbox.html



OpenLayers.Format.YouTube = OpenLayers.Class(OpenLayers.Format.GeoRSS, {
    createFeatureFromItem: function(item) {
        var feature = OpenLayers.Format.GeoRSS.prototype.createFeatureFromItem.apply(this, arguments);
        feature.attributes.thumbnail = this.getElementsByTagNameNS(item, "http://search.yahoo.com/mrss/", "thumbnail")[4].getAttribute("url");
        feature.attributes.content = OpenLayers.Util.getXmlNodeValue(this.getElementsByTagNameNS(item, "*","summary")[0]);
        return feature;
    }
});



GeoExplorer.YouTubeFeedOverlay = function (target) {

    this.youtubeRecord = null;

    this.popupControl = null;

    this.popup = null;

    this.createOverlay = function () {
        var keywords = target.about["keywords"] ? target.about["keywords"] : "of";
        var youtubeConfig = {name:"YouTube", source:"0", group:"Overlays", buffer:"0", type:"OpenLayers.Layer.Vector",
            args:["YouTube Videos",
                {
                    projection:new OpenLayers.Projection("EPSG:4326"),
                    displayInLayerSwitcher:false,
                    strategies:[new OpenLayers.Strategy.Fixed()],
                    protocol:new OpenLayers.Protocol.HTTP({
                        url:"/youtube/",
                        params:{  'MAX-RESULTS':'50', 'Q':keywords, 'BBOX':target.mapPanel.map.getExtent().transform(target.mapPanel.map.getProjectionObject(), new OpenLayers.Projection("EPSG:4326")).toBBOX()},
                        format:new OpenLayers.Format.YouTube()
                    }),
                    styleMap:new OpenLayers.StyleMap({
                        "default":new OpenLayers.Style({externalGraphic:"${thumbnail}", pointRadius:24}),
                        "select":new OpenLayers.Style({pointRadius:30})
                    })
                }
            ]
        };

        feedSource = Ext.ComponentMgr.createPlugin(
            youtubeConfig, "gx_olsource"
        );
        this.youtubeRecord = feedSource.createLayerRecord(youtubeConfig);
        this.youtubeRecord.group = youtubeConfig.group;

        this.popupControl = new OpenLayers.Control.SelectFeature(this.youtubeRecord.getLayer(), {
            //hover:true,
            clickout:true,
            onSelect:function (feature) {

                var pos = feature.geometry;
                this.popup = new OpenLayers.Popup("popup",
                    new OpenLayers.LonLat(pos.x, pos.y),
                    new OpenLayers.Size(240, 180),
                    "<a target='_blank' href=" +
                        feature.attributes.link + "><img height='180', width='240' title='" +
                        feature.attributes.title + "' src='" + feature.attributes.thumbnail + "' /></a>",
                    false);
                this.popup.closeOnMove = true;
                this.popup.keepInMap = true;
                target.mapPanel.map.addPopup(this.popup);
            },

            onUnselect:function (feature) {
                target.mapPanel.map.removePopup(this.popup);
                this.popup = null;
            }
        });

        target.mapPanel.map.addControl(this.popupControl);
        this.popupControl.activate();
        target.mapPanel.layers.insert(target.mapPanel.layers.data.items.length, [this.youtubeRecord]);
    }

    this.removeOverlay = function () {
        target.mapPanel.layers.remove(this.youtubeRecord, true);
        this.youtubeRecord = null;
        this.popupControl = null;
    }

};