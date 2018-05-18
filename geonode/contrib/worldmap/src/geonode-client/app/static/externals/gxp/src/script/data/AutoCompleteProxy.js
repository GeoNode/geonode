/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

Ext.ns("gxp.data");

/** api: (define)
 *  module = gxp.data
 *  class = AutoCompleteProxy
 *  extends = GeoExt.data.ProtocolProxy
 */

/** api: constructor
 *  .. class:: AutoCompleteProxy(config)
 *
 *    A protocol proxy that will add the filter before doing the request.
 *    params.query contains the text entered by the user, when he enters more
 *    than minChars characters.
 */
gxp.data.AutoCompleteProxy = Ext.extend(GeoExt.data.ProtocolProxy, {

    /** private: method[doRequest]
     *  :param action: ``String`` The crud action type (create, read, update, 
     *      destroy)
     *  :param records: ``Ext.data.Record`` or ``Array(Ext.data.Record)``
     *  :param params: ``Object`` An object containing properties which are to
     *       be used as HTTP parameters
     *  :param reader: ``Ext.data.DataReader`` The Reader object which 
     *      converts the data object into a block of Ext.data.Records.
     *  :param callback: ``Function`` A function to be called after the request.
     *  :param scope: ``Object`` The scope in which the callback function is 
     *      executed.
     *  :param arg: ``Object`` An optional argument which is passed to the 
     *      callback as its second parameter.
     */
    doRequest: function(action, records, params, reader, callback, scope, arg) {
        if (params.query) {
            params.filter = new OpenLayers.Filter.Comparison({
                type: OpenLayers.Filter.Comparison.LIKE,
                matchCase: false,
                property: this.protocol.propertyNames[0],
                value: '*' + params.query + '*'
            });
            delete params.query;
        }
        gxp.data.AutoCompleteProxy.superclass.doRequest.apply(this, arguments);
    }

});
