/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/**
 * @require OpenLayers/Format/CSWGetRecords/v2_0_2.js
 */

/** api: (define)
 *  module = GeoExt.data
 *  class = CSWRecordsReader
 *  base_link = `Ext.data.JsonReader <http://extjs.com/deploy/dev/docs/?class=Ext.data.JsonReader>`_
 */

Ext.namespace("GeoExt.data");

/** api: example
 *  Typical usage in a store:
 * 
 *  .. code-block:: javascript
 *     
 *      var store = new Ext.data.Store({
 *          proxy: new GeoExt.data.ProtocolProxy({
 *              protocol: new OpenLayers.Protocol.CSW({
 *                  url: "http://demo.geonode.org/geonetwork/srv/en/csw"
 *              })
 *          }),
 *          reader: new GeoExt.data.CSWRecordsReader({
 *             fields: ['title', 'subject', 'URI', 'bounds', 'projection']
 *          })
 *      });
 *      
 */

/** api: constructor
 *  .. class:: CSWRecordsReader(meta, recordType)
 *  
 *      :param meta: ``Object`` Reader configuration.
 *      :param recordType: ``Array | Ext.data.Record`` An array of field
 *          configuration objects or a record object.  Default is
 *          :class:`Ext.data.Record`.
 *   
 *      Data reader class to create an array of records from a CSW
 *      GetRecords response. The raw response from the OpenLayers parser
 *      is available through the jsonData property.
 */
GeoExt.data.CSWRecordsReader = function(meta, recordType) {
    meta = meta || {};
    if(!meta.format) {
        meta.format = new OpenLayers.Format.CSWGetRecords();
    }
    if(!meta.root) {
        meta.root = 'records';
    }
    GeoExt.data.CSWRecordsReader.superclass.constructor.call(
        this, meta, recordType
    );
};

Ext.extend(GeoExt.data.CSWRecordsReader, Ext.data.JsonReader, {

    /** private: method[read]
     *  :param data: ``XMLHttpRequest | OpenLayers.Protocol.Response`` If a
     *  ProtocolProxy is configured with OpenLayers.Protocol.CSW data will be
     *  ``OpenLayers.Protocol.Response``. Otherwise data will be the 
     * ``XMLHttpRequest`` object.
     *  :return: ``Object`` A data block which is used by an
     *      ``Ext.data.Store`` as a cache of ``Ext.data.Record``
     *      objects.
     */
    read: function(data) {
        var o = data.data;
        if (!o) {
            o = data.responseXML;
            if(!o || !o.documentElement) {
                o = data.responseText;
            }
        }
        return this.readRecords(o);
    },

    /** private: method[readRecords]
     *  :param data: ``DOMElement | String | Object`` A document
     *      element or XHR response string.
     *  :return: ``Object`` A data block which is used by an
     *      ``Ext.data.Store`` as a cache of ``Ext.data.Record``
     *      objects.
     */
    readRecords: function(data) {
        if(typeof data === "string" || data.nodeType) {
            data = this.meta.format.read(data);
        }
        var result = GeoExt.data.CSWRecordsReader.superclass.readRecords.call(
            this, data
        );
        // post-process so we flatten simple objects with a value property
        Ext.each(result.records, function(record) {
            for (var key in record.data) {
                var value = record.data[key];
                if (value instanceof Array) {
                    for (var i=0, ii=value.length; i<ii; ++i) {
                        if (value[i] instanceof Object) {
                            value[i] = value[i].value;
                        }
                    }
                }
            }
        });
        if (data.SearchResults) {
            result.totalRecords = data.SearchResults.numberOfRecordsMatched;
        }
        return result;
    }
});
