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

    internalProjection: "EPSG:900913",

    externalProjection: "EPSG:4326",

    /** api: method[createLayerRecord]
     *  :arg config:  ``Object``  The application config for this layer.
     *  :returns: ``GeoExt.data.LayerRecord``
     *
     *  Create a layer record given the config.
     */
    createLayerRecord: function(config) {
        var record;

        this.url = config.url +"?q=of&kind=photo&max-results=50";

        Ext.apply(config, {
            name: config.name,
            group:("group" in config) ? config.group : "General",
            buffer: ("buffer" in config) ? config.buffer : 0,
            type:"OpenLayers.Layer.Vector",
            args: [config.title,
                {   projection: "projection" in config ? config.projection : this.externalProjection,
                    displayInLayerSwitcher: true,
                    strategies: [new OpenLayers.Strategy.BBOX({resFactor: 1.1})],
                    protocol: new OpenLayers.Protocol.HTTP({
                        url: config.url,
                        params:"params" in config ? config.params : {},
                        format:new OpenLayers.Format.GeoRSS({
                            internalProjection: this.internalProjection,
                            externalProjection: "projection" in config ? config.projection : this.externalProjection
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

    },

    /** api: method[getConfigForRecord]
     *  :arg record: :class:`GeoExt.data.LayerRecord`
     *  :returns: ``Object``
     *
     *  Create a config object that can be used to recreate the given record.
     */
    getConfigForRecord: function(record) {
        // get general config
        var config = gxp.plugins.GeoRssSource.superclass.getConfigForRecord.apply(this, arguments);
        // add config specific to this source
        var layer = record.getLayer();
        return Ext.apply(config, {
            params: record.get("args").get("protocol").get("params"),
            group: record.get("group"),
            args: {}
        });
    }

});

Ext.preg(gxp.plugins.GeoRssSource.prototype.ptype, gxp.plugins.GeoRssSource);