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
 *  class = AutoCompleteReader
 *  extends = GeoExt.data.FeatureReader
 */

/** api: constructor
 *  .. class:: AutoCompleteReader(config)
 *
 *    A feature reader which filters out duplicates. Used for autocomplete
 *    search fields.
 */
gxp.data.AutoCompleteReader = Ext.extend(GeoExt.data.FeatureReader, {

    /** private: method[read]
     *  :param response: ``OpenLayers.Protocol.Response``
     *  :return: ``Object`` An object with two properties. The value of the
     *      ``records`` property is the array of records corresponding to
     *      the features. The value of the ``totalRecords" property is the
     *      number of records in the array.
     *      
     *  This method is only used by a DataProxy which has retrieved data.
     */
    read: function(response) {
        // since we cannot do a distinct query on a WFS, filter out duplicates here
        var field = this.meta.uniqueField;
        this.features = [];
        for (var i=0,ii=response.features.length;i<ii;++i) {
            var feature = response.features[i];
            var value = feature.attributes[field];
            if (this.isDuplicate(field, value) === false) {
                this.features.push(feature);
            } else {
                feature.destroy();
            }
        }
        response.features = this.features;
        return gxp.data.AutoCompleteReader.superclass.read.apply(this, arguments);
    },

    /** private: method[isDuplicate]
     *  :param field: ``String`` The name of the field for which to check duplicates.
     *  :param value: ``String`` The value for which to check if it is already in the
     *      list of features.
     *  :return: ``Boolean`` True if the value was already present.
     *      
     *  Check if the value of a certain value is a duplicate.
     */
    isDuplicate: function(field, value) {
        for (var i=0,ii=this.features.length;i<ii;++i) {
            if (this.features[i].attributes[field] === value) {
                return true;
            }
        }
        return false;
    }

});
