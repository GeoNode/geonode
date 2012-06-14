/**
 * Created with PyCharm.
 * User: mbertrand
 * Date: 6/13/12
 * Time: 12:41 PM
 * To change this template use File | Settings | File Templates.
 */

Ext.namespace("gxp.plugins");

gxp.plugins.GeoRssSource = Ext.extend(gxp.plugins.OLSource, {

    /** api: ptype = gxp_hglsource */
    ptype: "gx_rsssource",


    url: null,

    /** Title for source **/
    title: 'GeoRSS Source',


    /** api: method[createLayerRecord]
     *  :arg config:  ``Object``  The application config for this layer.
     *  :returns: ``GeoExt.data.LayerRecord``
     *
     *  Create a layer record given the config.
     */
    createLayerRecord: function(config) {
        var record;

        this.url = "/proxy?url=" + escape(config.url);


        Ext.apply(config, {
            name: config.name,
            group:("group" in config) ? config.group : "General",
            buffer: ("buffer" in config) ? config.buffer : 0,
            type:"OpenLayers.Layer.Vector",
            args: [config.title,
                {   projection: new OpenLayers.Projection("EPSG:4326"),
                    displayInLayerSwitcher: true,
                    strategies:[new OpenLayers.Strategy.Fixed()],
                    protocol: new OpenLayers.Protocol.HTTP({
                        url:"http://picasaweb.google.com/data/feed/base/all",
                        params:{'KIND': 'photo', 'MAX-RESULTS':'50', 'Q' : "of"},
                        format:new OpenLayers.Format.GeoRSS({
                            internalProjection: "EPSG:900913",
                            externalProjection: "EPSG:4326"
                        })
                    }),
                    styleMap: new OpenLayers.StyleMap({
                        "default": new OpenLayers.Style({pointRadius: 5}),
                        "select": new OpenLayers.Style({pointRadius: 5})
                    })
                }]
        });

        var record = gxp.plugins.GeoRssSource.superclass.createLayerRecord(config);
        return record;

    }

});

Ext.preg(gxp.plugins.GeoRssSource.prototype.ptype, gxp.plugins.GeoRssSource);