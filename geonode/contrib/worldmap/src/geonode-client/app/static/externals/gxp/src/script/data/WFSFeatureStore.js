/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires data/WFSProtocolProxy.js
 * @requires GeoExt/data/FeatureStore.js
 */

/** api: (define)
 *  module = gxp.data
 *  class = WFSFeatureStore
 *  base_link = `Ext.data.Store <http://extjs.com/deploy/dev/docs/?class=Ext.data.Store>`_
 */
Ext.namespace("gxp.data");

gxp.data.WFSFeatureStore = Ext.extend(GeoExt.data.FeatureStore, {
    
    /** api: config[maxFeatures]
     *  ``Number``
     *  Optional limit for number of features requested in a read.  No limit
     *  set by default.
     */
    
    /** api: config[ogcFilter]
     *  ``OpenLayers.Filter``
     *  Optional filter to set on the WFSProtocolProxy.
     */
    
    /** api: config[multi]
     *  ``Boolean`` If set to true, geometries will be casted to Multi
     *  geometries before writing. No casting will be done for reading.
     */

    /** api: method[setOgcFilter]
     *  :arg ogcFilter: ``OpenLayers.Filter`` Update the filter used by the
     *      protocol proxy.  You must manually call load or reload to trigger
     *      loading.
     */
    setOgcFilter: function(ogcFilter) {
        this.proxy.setFilter(ogcFilter);
    },
    
    /** private */
    constructor: function(config) {
        if(!(config.proxy && config.proxy instanceof GeoExt.data.ProtocolProxy)) {
            config.proxy = new gxp.data.WFSProtocolProxy(Ext.apply({
                srsName: config.srsName,
                url: config.url,
                featureType: config.featureType,
                featureNS:  config.featureNS,
                geometryName: config.geometryName,
                schema: config.schema,
                filter: config.ogcFilter,
                maxFeatures: config.maxFeatures,
                multi: config.multi
            }, config.proxy));
        }
        if(!config.writer) {
            // a writer is not used, but is required by store.save
            config.writer = new Ext.data.DataWriter({
                write: Ext.emptyFn
            });
        }
        gxp.data.WFSFeatureStore.superclass.constructor.apply(this, arguments);
        
        /**
         * TODO: Determine what needs to be done to the feature reader to
         * properly fit the 3.0 DataReader inteface.
         *
         * This method gets called with the data that goes to the reader.realize
         * method.  This method requires that the data has a property with the
         * same name as reader.meta.idProperty.  The WFSProtocolProxy prepares
         * a data object for each feature, with a fid and feature property.  The
         * return from this method will be applied to record.data.  So it makes
         * sense that it looks very much like what reader.readRecords does.
         */
        this.reader.extractValues = (function(data, items, length) {
            var obj = this.readRecords([data.feature]);
            return obj.records[0].data;
        }).createDelegate(this.reader);
        
        /**
         * TODO: Determine the appropriate meta.idProperty value.
         * If this is set to fid, then we can't use store.getById given a feature
         * until after the feature has been saved.  If this is set to id, then
         * we better never have to create a new feature that represents the
         * same record.
         */
        this.reader.meta.idProperty = "id";
        
        /**
         * TODO: Same as above, but it seems that the getId method is responsible
         * for determining the id in Ext > 3.0. This is crucial after changes
         * are committed (see WFSProtocolProxy::onProtocolCommit), because the
         * callback there does an isData check, which involves an attempt to get
         * the id through this method.
         */
        this.reader.getId = function(data) {
            return data.id;
        };
        
        
        
    }
    
});
