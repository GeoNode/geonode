/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/WMSSource.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = CatalogueSource
 */

/** api: (extends)
 *  plugins/WMSSource.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: CatalogueSource(config)
 *
 *    Base class for catalogue sources uses for search.
 */
gxp.plugins.CatalogueSource = Ext.extend(gxp.plugins.WMSSource, {

    /** api: config[url]
     *  ``String`` Online resource of the catalogue service.
     */
    url: null,

    /** api: config[title]
     *  ``String`` Optional title for this source.
     */
    title: null,

    /** private: property[lazy]
     *  ``Boolean`` This source always operates lazy so without GetCapabilities
     */
    lazy: true,

    /** api: config[proxyOptions]
     *  ``Object``
     *  An optional object to pass to the constructor of the ProtocolProxy.
     *  This can be used e.g. to set listeners.
     */
    proxyOptions: null,

    /** api: method[describeLayer]
     *  :arg rec: ``GeoExt.data.LayerRecord`` the layer to issue a WMS
     *      DescribeLayer request for
     *  :arg callback: ``Function`` Callback function. Will be called with
     *      an ``Ext.data.Record`` from a ``GeoExt.data.DescribeLayerStore``
     *      as first argument, or false if the WMS does not support
     *      DescribeLayer.
     *  :arg scope: ``Object`` Optional scope for the callback.
     *
     *  Get a DescribeLayer response from this source's WMS.
     */
    describeLayer: function(rec, callback, scope) {
        // it makes no sense to keep a describeLayerStore since
        // everything is lazy and layers can come from different WMSs.
        var recordType = Ext.data.Record.create(
            [
                {name: "owsType", type: "string"},
                {name: "owsURL", type: "string"},
                {name: "typeName", type: "string"}
            ]
        );
        var record = new recordType({
            owsType: "WFS",
            owsURL: rec.get('url'),
            typeName: rec.get('name')
        });
        callback.call(scope, record);
    },

    /** private: method[destroy]
     */
    destroy: function() {
        this.store && this.store.destroy();
        this.store = null;
        gxp.plugins.CatalogueSource.superclass.destroy.apply(this, arguments);
    }

    /** api: method[getPagingParamNames]
     *  :return: ``Object`` with keys start and limit.
     *
     *  Get the names of the parameters to use for paging.
     *
     *  To be implemented by subclasses
     */

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
     *
     *  To be implemented by subclasses
     */

});
