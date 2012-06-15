/**
 * Created with PyCharm.
 * User: mbertrand
 * Date: 6/13/12
 * Time: 12:41 PM
 * To change this template use File | Settings | File Templates.
 */

Ext.namespace("gxp.plugins");

gxp.plugins.GeoRssSource = Ext.extend(gxp.plugins.LayerSource, {

    /** api: ptype = gxp_hglsource */
    ptype: "gx_rsssource",


    url: null,

    /** Title for source **/
    title: 'GeoRSS Source',


    internalProjection: "EPSG:900913",

    /** api: method[createLayerRecord]
     *  :arg config:  ``Object``  The application config for this layer.
     *  :returns: ``GeoExt.data.LayerRecord``
     *
     *  Create a layer record given the config.
     */
    createLayerRecord: function(config) {
        var record;


        var layer = new OpenLayers.Layer.Vector(config.title, {
            projection: "projection" in config? config.projection : "EPSG:4326",
            strategies: [new OpenLayers.Strategy.BBOX({resFactor: 1, ratio: 1})],
            protocol: new OpenLayers.Protocol.HTTP({
                url: config.url,
                params: config.params,
                format:new OpenLayers.Format.GeoRSS()
            }),
            styleMap: new OpenLayers.StyleMap({
                "default": new OpenLayers.Style("defaultStyle" in config ? config.defaultStyle : {graphicName: "circle", pointRadius: 5, fillOpacity: 0.7, fillColor: 'Red'}),
                "select": new OpenLayers.Style("selectStyle" in config ? config.selectStyle : {graphicName: "circle", pointRadius: 10, fillOpacity: 1.0, fillColor: "Yellow"})
            })
        });



        // create a layer record for this layer
        var Record = GeoExt.data.LayerRecord.create([
            {name: "title", type: "string"},
            {name: "source", type: "string"},
            {name: "group", type: "string"},
            {name: "fixed", type: "boolean"},
            {name: "selected", type: "boolean"},
            {name: "type", type: "string"},
            {name: "defaultStyle"},
            {name: "selectStyle"},
            {name: "params"}
        ]);



        var data = {
            layer: layer,
            title: config.title,
            source: config.source,
            group: config.group,
            fixed: ("fixed" in config) ? config.fixed : false,
            selected: ("selected" in config) ? config.selected : false,
            params: ("params" in config) ? config.params : {},
            defaultStyle: "defaultStyle" in config ? config.defaultStyle : {},
            selectStyle: "selectStyle" in config ? config.selectStyle : {}
        };

        if (this.target.selectControl == null) {
            this.target.selectControl = new OpenLayers.Control.SelectFeature([layer], {
                //hover:true,
                clickout: true,
                scope: this
            });

            this.target.mapPanel.map.addControl(this.target.selectControl);
            this.target.selectControl.activate();
        } else {
            this.target.selectControl.layers.push(layer);
        }


        layer.events.on({
            "featureselected": function(feature) {

                var pos = feature.feature.geometry;
                if (this.target.selectControl.popup != null) {
                    this.target.mapPanel.map.removePopup(this.target.selectControl.popup);
                }
                this.target.selectControl.popup = new OpenLayers.Popup.FramedCloud("popup",
                    feature.feature.geometry.getBounds().getCenterLonLat(),
                    new OpenLayers.Size(300,300),
                    "<a target='_blank' href=\"" +
                        feature.feature.attributes.link + "\">" +  feature.feature.attributes.title +"</a><p>"+ feature.feature.attributes.description + "</p>",
                    //"<p><a target='_blank' href=\"javascript:onClick=app.addHGL('" +  feature.attributes.guid + "');return false;\">Display on map</a></p>",
                    null, true);
                this.target.selectControl.popup.closeOnMove = false;
                this.target.selectControl.popup.minSize = new OpenLayers.Size(300,150);
                this.target.selectControl.popup.keepInMap = false;
                this.target.mapPanel.map.addPopup(this.target.selectControl.popup);
            },

            "featureunselected" : function(feature) {
                this.target.mapPanel.map.removePopup(this.target.selectControl.popup);
                this.target.selectControl.popup = null;
            },
            scope: this
        });

        record = new Record(data, layer.id);

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
        return Ext.apply(config, {
            title: record.get("title"),
            group: record.get("group"),
            fixed: record.get("fixed"),
            selected: record.get("selected"),
            params: record.get("params"),
            defaultStyle: record.getLayer().styleMap.styles.default.defaultStyle,
            selectStyle: record.getLayer().styleMap.styles.select.defaultStyle
        });
    }



});




Ext.preg(gxp.plugins.GeoRssSource.prototype.ptype, gxp.plugins.GeoRssSource);