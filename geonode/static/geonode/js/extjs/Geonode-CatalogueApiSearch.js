/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/CatalogueSource.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = GeoNodeAPICatalogueSource
 */

/** api: (extends)
 *  plugins/CatalogueSource.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: GeoNodeCatalogueSource(config)
 *
 */
gxp.plugins.GeoNodeAPICatalogueSource = Ext.extend(gxp.plugins.CatalogueSource, {

    /** api: ptype = gxp_geonodeapicataloguesource */
    ptype: "gxp_geonodeapicataloguesource",

    /** api: config[rootProperty]
     *  ``String`` Root property in the JSON response. Defaults to 'objects'.
     */
    rootProperty: 'objects',

    /** api: config[rootProperty]
     *  ``String`` Total Object Count property in the JSON response. Defaults to 'meta.total_count'.
     */
    totalProperty : 'meta.total_count',

    /** api: config[baseParams]
     *  ``Object`` Optional additional params to send in the requests.
     */
    baseParams: null,

    /** api: config[fields]
     *  ``Array`` Fields to use for the JsonReader. By default the following
     *  fields are provided: title, abstract, bounds and URI. Optionally this 
     *  can be overridden by applications to provide different or additional
     *  mappings.
     */
    fields: [
        {name: "title", convert: function(v) {
            return [v];
        }},
        {name: "abstract", mapping: "description"},
        {name: "bounds", mapping: "csw_wkt_geometry", convert: function(v) {
            var wkt = new OpenLayers.Format.WKT();
            var features = wkt.read(v);
            var bounds = features.geometry.getBounds();
            return {
                left: bounds.left,
                right: bounds.right,
                bottom: bounds.bottom,
                top: bounds.top
            };
        }},
        {name: "URI", mapping: "detail_url", convert: function(v) {
            var result = [];
            for (var key in v) {
                result.push({value: app.localGeoServerBaseUrl + "wms", protocol:"OGC:WMS", name: decodeURIComponent(v.substr(8))});
            }
            return result;
        }}
    ],

    /** api: method[createStore]
     *  Create the store that will be used for the GeoNode searches.
     */
    createStore: function() {
        this.store = new Ext.data.Store({
            proxy: new Ext.data.HttpProxy(Ext.apply({
                url: this.url, 
                method: 'GET'
            }, this.proxyOptions || {})),
            reader: new Ext.data.JsonReader({
                root: this.rootProperty,
                totalProperty: this.totalProperty
            }, this.fields)
        });
        gxp.plugins.LayerSource.prototype.createStore.apply(this, arguments);
    },

    /** api: method[getPagingStart]
     *  :return: ``Integer`` Where does paging start at?
     */
    getPagingStart: function() {
        return 0;
    },

    /** api: method[getPagingParamNames]
     *  :return: ``Object`` with keys start and limit.
     *
     *  Get the names of the parameters to use for paging.
     */
    getPagingParamNames: function() {
        return {
            start: 'offset',
            limit: 'limit'
        };
    },

    /** api: method[filter]
     *  Filter the store by querying the catalogue service.
     *  :param options: ``Object`` An object with the following keys:
     *
     * .. list-table::
     *     :widths: 20 80
     * 
     *     * - ``queryString``
     *       - the search string
     *     * - ``limit`` 
     *       - the maximum number of records to retrieve
     *     * - ``filters``
     *       - additional filters to include in the query
     */
    filter: function(options) {
        var bbox = undefined;

        // check for the filters property before using it
        if (options.filters !== undefined) {
            for (var i=0, ii=options.filters.length; i<ii; ++i) {
                var f = options.filters[i];
                if (f instanceof OpenLayers.Filter.Spatial) {
                    bbox = f.value.toBBOX();
                    break;
                }
            }
        }
        Ext.apply(this.store.baseParams, {
            'title__icontains': options.queryString
        });
        if (options.limit !== undefined) {
            Ext.apply(this.store.baseParams, {
                'limit': options.limit
            });
        }
        if (bbox !== undefined) {
            Ext.apply(this.store.baseParams, {
                'bbox': bbox
            });
        } else {
            delete this.store.baseParams.bbox;
        }
        this.store.load();
    },

    createLayerRecord: function(layerConfig) {
        layerConfig.restUrl = this.restUrl;
        layerConfig.queryable = true;
        return gxp.plugins.GeoNodeAPICatalogueSource.superclass.createLayerRecord.apply(this, arguments);
    }

});

Ext.preg(gxp.plugins.GeoNodeAPICatalogueSource.prototype.ptype, gxp.plugins.GeoNodeAPICatalogueSource);
