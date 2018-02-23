/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/CatalogueSource.js
 * @requires GeoExt/data/CSWRecordsReader.js
 * @requires GeoExt/data/ProtocolProxy.js
 * @requires OpenLayers.Protocol.CSW/v2_0_2.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = CSWCatalogueSource
 */

/** api: (extends)
 *  plugins/CatalogueSource.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: CSWCatalogueSource(config)
 *
 *    Plugin for creating WMS layers lazily. The difference with the WMSSource
 *    is that the url is configured on the layer not on the source. This means
 *    that this source can create WMS layers for any url. This is particularly
 *    useful when working against a Catalogue Service, such as a OGC:CS-W.
 */
gxp.plugins.CSWCatalogueSource = Ext.extend(gxp.plugins.CatalogueSource, {

    /** api: ptype = gxp_cataloguesource */
    ptype: "gxp_cataloguesource",

    /** api: method[createStore]
     *  Create the store that will be used for the CS-W searches.
     */
    createStore: function() {
        this.store = new Ext.data.Store({
            proxy: new GeoExt.data.ProtocolProxy(Ext.apply({
                setParamsAsOptions: true,
                protocol: new OpenLayers.Protocol.CSW({
                    url: this.url
                })
            }, this.proxyOptions || {})),
            reader: new GeoExt.data.CSWRecordsReader({
                fields: ['title', 'abstract', 'URI', 'bounds', 'projection', 'references']
            })
        });
        gxp.plugins.LayerSource.prototype.createStore.apply(this, arguments);
    },

    /** api: method[getPagingParamNames]
     *  :return: ``Object`` with keys start and limit.
     *
     *  Get the names of the parameters to use for paging.
     */
    getPagingParamNames: function() {
        return {
            start: 'startPosition',
            limit: 'maxRecords'
        };
    },

    /** private: method[getFullFilter]
     *  :arg filter: ``OpenLayers.Filter`` The filter to add to the other existing 
     *  filters. This is normally the free text search filter.
     *  :arg otherFilters: ``Array``
     *  :returns: ``OpenLayers.Filter`` The combined filter.
     *
     *  Get the filter to use in the CS-W query.
     */
    getFullFilter: function(filter, otherFilters) {
        var filters = [];
        if (filter !== undefined) {
            filters.push(filter);
        }
        filters = filters.concat(otherFilters);
        if (filters.length <= 1) {
            return filters[0];
        } else {
            return new OpenLayers.Filter.Logical({
                type: OpenLayers.Filter.Logical.AND,
                filters: filters
            });
        }
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
        var filter = undefined;
        if (options.queryString !== "") {
            filter = new OpenLayers.Filter.Comparison({
                type: OpenLayers.Filter.Comparison.LIKE,
                matchCase: false,
                property: 'csw:AnyText',
                value: '*' + options.queryString + '*'
            });
        }
        var data = {
            "resultType": "results",
            "maxRecords": options.limit,
            "Query": {
                "typeNames": "gmd:MD_Metadata",
                "ElementSetName": {
                    "value": "full"
                }
            }
        };
        var fullFilter = this.getFullFilter(filter, options.filters);
        if (fullFilter !== undefined) {
            Ext.apply(data.Query, {
                "Constraint": {
                    version: "1.1.0",
                    Filter: fullFilter
                }
            });
        }
        Ext.apply(this.store.baseParams, data);
        this.store.load();
    }

});

Ext.preg(gxp.plugins.CSWCatalogueSource.prototype.ptype, gxp.plugins.CSWCatalogueSource);
