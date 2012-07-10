/**
 * Created with PyCharm.
 * User: mbertrand
 * Date: 6/21/12
 * Time: 2:43 PM
 * To change this template use File | Settings | File Templates.
 */

/**
 * Created with PyCharm.
 * User: mbertrand
 * Date: 6/18/12
 * Time: 1:55 PM
 * To change this template use File | Settings | File Templates.
 */


Ext.namespace("gxp.plugins");


gxp.plugins.HGLFeedSource = Ext.extend(gxp.plugins.FeedSource, {

    /** api: ptype = gx_hglfeedsource */
    ptype: "gx_hglfeedsource",


    url: "/hglpoint",

    defaultFormat: "OpenLayers.Format.GeoRSS",

    /** Title for source **/
    title: 'HGL Feed Source',


    createLayerRecord: function(config) {
        if (config.params["q"] == null) {
            config.params["q"] == ""
        }
        config.url = this.url;

        var record = gxp.plugins.HGLFeedSource.superclass.createLayerRecord.apply(this, arguments);
        return record;
    },

    configureInfoPopup: function(layer) {
        layer.events.on({
            "featureselected": function(featureObject) {
                var feature = featureObject.feature;
                var pos = feature.geometry;

                if (this.target.selectControl.popup) {
                    this.target.mapPanel.map.removePopup(this.target.selectControl.popup);
                }

                var content = document.createElement("div");
                content.innerHTML = feature.attributes.content;
                this.target.selectControl.popup = new OpenLayers.Popup.FramedCloud("popup",
                    new OpenLayers.LonLat(pos.x, pos.y),
                    new OpenLayers.Size(300,300),
                    "<a target='_blank' href=" +
                        feature.attributes.link + "\">" +  feature.attributes.title +"</a><p>"+ feature.attributes.description + "</p>",
                    null, true);
                this.target.selectControl.popup.closeOnMove = true;
                this.target.selectControl.popup.panMapIfOutOfView = false;
                this.target.selectControl.popup.autoSize = true;
                this.target.mapPanel.map.addPopup(this.target.selectControl.popup);
            },

            "featureunselected" : function(featureObject) {
                this.target.mapPanel.map.removePopup(this.target.selectControl.popup);
                this.target.selectControl.popup = null;
            },

            "moveend" :  function(evt) {
                if (this.target.selectControl) {
                    this.target.selectControl.popup = null;
                }
            },

            scope: this
        });
    },

    getStyleMap: function(config) {
        return new OpenLayers.StyleMap({})
    }

});

Ext.preg(gxp.plugins.HGLFeedSource.prototype.ptype, gxp.plugins.HGLFeedSource);