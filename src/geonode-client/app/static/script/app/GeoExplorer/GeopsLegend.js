/**
 * Published under the GNU General Public License.
 * Copyright 2011-2012 © The President and Fellows of Harvard College
 */

Ext.namespace('GeoExt');

GeoExt.GeopsLegend = Ext.extend(GeoExt.WMSLegend, {

    initComponent: function() {
        GeoExt.GeopsLegend.superclass.initComponent.call(this);
        var layer = this.layerRecord.getLayer();
        this._noMap = !layer.map;
        layer.events.register("moveend", this, this.onLayerMoveend);
        layer.events.register("update", this, this.onLayerMoveend);
        this.update();
    },

    /** private: method[onLayerMoveend]
     *  :param e: ``Object``
     */
    onLayerMoveend: function(e) {
        if ((e.zoomChanged === true && this.useScaleParameter === true) ||
            this._noMap) {
            delete this._noMap;
            this.update();
        }
    },


    getLegendUrl: function(layerName, layerNames) {
        var rec = this.layerRecord;
        var layer = rec.getLayer();

        if (layer.getVisibility() === true) {
            return  rec.get("url") +
                "?TRANSPARENT=TRUE&TILED=false&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetLegendGraphic&EXCEPTIONS=application%2Fvnd.ogc.se_xml" +
                "&LAYER=heatmap&FORMAT=image%2Fgif&SQL=" + layer.params["SQL"] + "&MAXVAL=" +  Ext.getCmp("slider_maxval").getValue() +
                "&BLUR=" + Ext.getCmp("slider_blur").getValue() + "&MIN=" + Ext.getCmp("slider_blur").getValue() +
                "&RND=" + layer.params["RND"];
        } else return "";
    }

});

/** private: method[supports]
 *  Private override
 */
GeoExt.GeopsLegend.supports = function(layerRecord) {
    return layerRecord.getLayer() instanceof OpenLayers.Layer.WMS ? 1 : 0;
};

/** api: legendtype = gx_wmslegend */
GeoExt.LayerLegend.types["gx_geopslegend"] = GeoExt.GeopsLegend;

/** api: xtype = gx_wmslegend */
Ext.reg('gx_geopslegend', GeoExt.GeopsLegend);
