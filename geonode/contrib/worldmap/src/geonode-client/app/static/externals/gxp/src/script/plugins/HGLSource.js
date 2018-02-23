/**
 * Created by PyCharm.
 * User: mbertrand
 * Date: 9/20/11
 * Time: 7:56 PM
 * To change this template use File | Settings | File Templates.
 */

Ext.namespace("gxp.plugins");

gxp.plugins.HGLSource = Ext.extend(gxp.plugins.WMSSource, {

    /** api: ptype = gxp_hglsource */
    ptype: "gxp_hglsource",


    /** api: config[baseParams]
     *  ``Object`` Base parameters to use on the HGL layer
     *  request.
     */
    baseParams: null,


    /** Title for source **/
    title: 'Harvard Geospatial Library Source',

    /** i18n */
    noCompatibleSRSTitle: "Warning",
    noCompatibleSRSText: "This layer cannot be added to the map since it is not available in any projection that is compatible with the map projection",

    /** private: property[format]
     *  ``OpenLayers.Format`` Optional custom format to use on the
     *  HGL store instead of the default.
     */
    format: null,

    /** api: config[url]
     *  ``String``  URL for Harvard Geospatial Library
     */
    url: null,

    /** api: method[createLayerRecord]
     *  :arg config:  ``Object``  The application config for this layer.
     *  :returns: ``GeoExt.data.LayerRecord``
     *
     *  Create a layer record given the config.
     */
    createLayerRecord: function(config) {
        //HGL Feed doesn't include bboxes, so just make global bbox
        config.bbox =  [-20037508.34, -20037508.34, 20037508.34, 20037508.34];
        return gxp.plugins.HGLSource.superclass.createLayerRecord.apply(this, arguments);

    },

    /** private: method[initDescribeLayerStore]
     *  creates a WMSDescribeLayer store for layer descriptions of all layers
     *  created from this source.
     */
    initDescribeLayerStore: function() {
        var version = "1.1.1";
        this.describeLayerStore = new GeoExt.data.WMSDescribeLayerStore({
            url: this.url,
            baseParams: {
                VERSION: version,
                REQUEST: "DescribeLayer"
            }
        });

    },

    /** api: method[createStore]
     *
     *  Creates a store of layer records.  Not necessary for this case,
     *  so create a fake store to avoid the wrath of WMSSource.
     */
    createStore: function() {
        this.store = {
            reader: {
                raw: null
            },
            findExact: function(attribute, value) {
                return -1;
            },
            getCount: function(){
                return 1;
            }
        };

        this.fireEvent("ready", this);
    }

});

Ext.preg(gxp.plugins.HGLSource.prototype.ptype, gxp.plugins.HGLSource);
