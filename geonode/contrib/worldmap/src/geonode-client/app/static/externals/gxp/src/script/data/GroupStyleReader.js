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
 *  class = GroupStyleReader
 *  extends = GeoExt.data.StyleReader
 */

/** api: constructor
 *  .. class:: GroupStyleReader(config)
 *
 *    A subclass of ``GeoExt.data.StyleReader`` that adds rule group specific
 *    features:
 *
 *    * For classified groups, the filters of neighboring classes will be
 *      updated, to make sure that classes always align with each other.
 */
gxp.data.GroupStyleReader = Ext.extend(GeoExt.data.StyleReader, {

    /** private: method[onMetaChange]
     *  Override to intercept the set method of the record prototype used
     *  by the reader, so it makes sure that filters are always stored as
     *  ``OpenLayers.Filter`` instances, and neighboring classes are aligned
     *  to each other by making them share class boundaries.
     */
    onMetaChange: function() {
        gxp.data.GroupStyleReader.superclass.onMetaChange.apply(this, arguments);
        var recordType = this.recordType,
            aligning = false;
        recordType.prototype.set = Ext.createInterceptor(this.recordType.prototype.set, function(name, value) {
            if (!aligning && name === "filter") {
                aligning = true;
                var store = this.store,
                    modified = this.get("filter");
                    BETWEEN = OpenLayers.Filter.Comparison.BETWEEN;
                if (modified instanceof OpenLayers.Filter && typeof value === "string") {
                    value = OpenLayers.Format.CQL.prototype.read(value);
                }
                var prop, index = store.indexOf(this);
                if (index < store.getCount() - 1) {
                    prop = value.type === BETWEEN ? "upperBoundary" : "value";
                    if (value[prop] !== modified[prop]) {
                        var nextRec = store.getAt(index + 1),
                            nextFilter = nextRec.get("filter").clone(),
                            nextProp = nextFilter.type === BETWEEN ? "lowerBoundary" : "value";
                        nextFilter[nextProp] = value[prop];
                        nextRec.set("filter", nextFilter);
                    }
                }
                if (index > 0) {
                    prop = value.type === BETWEEN ? "lowerBoundary" : "value";
                    if (value[prop] !== modified[prop]) {
                        var prevRec = store.getAt(index - 1),
                            prevFilter = prevRec.get("filter").clone(),
                            prevProp = prevFilter.type === BETWEEN ? "upperBoundary" : "value";
                        prevFilter[prevProp] = value[prop];
                        prevRec.set("filter", prevFilter);
                    }
                }
                recordType.prototype.set.apply(this, [name, value]);
                aligning = false;
                return false;
            }
        });
    }

});
