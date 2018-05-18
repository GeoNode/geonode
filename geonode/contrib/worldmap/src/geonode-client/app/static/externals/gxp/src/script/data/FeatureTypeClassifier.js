/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @require OpenLayers.Format.WPSExecute.js
 * @require util/style.js
 */

/** api: (define)
 *  module = gxp.data
 *  class = FeatureTypeClassifier
 *  base_link = `Ext.util.Observable <http://extjs.com/deploy/dev/docs/?class=Ext.util.Observable>`_
 */

Ext.ns("gxp.data");

/** api: constructor
 *  .. class:: FeatureTypeClassifier(config)
 *
 *  Utility class for creating classifications of vector styles
 */   
gxp.data.FeatureTypeClassifier = Ext.extend(Ext.util.Observable, {
    
    /** api: config[store]
     *  ``Ext.data.Store`` Store of style rules, read from GetStyles response
     *  using GeoExt.data.StyleReader. Classification operations will be
     *  performed on the layer denoted as ``layerName`` in the ``namedLayer``
     *  object of the raw SLD.
     */
    store: null,
    
    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.data.FeatureTypeClassifier.superclass.constructor.apply(this, arguments);
        Ext.apply(this, config);
    },
    
    /** api: method[classify]
     *  :arg group: ``String`` Name of the group to classify
     *  :method: ``String`` Name of one of the classification methods from
     *      :obj:`methods`
     *  :args: ``Array`` Arguments to pass to the classification method
     *
     *  Creates a classification for a :obj:`group`. If there are already rules
     *  for the selected group, the class breaks will be replaced with the new
     *  classification and linear stretching will be applied to the existing
     *  symbolizers to match the number of new classes.
     */
    classify: function(group, method, args, callback, scope) {
        this.store.filter("group", group);
        var start, end, count = this.store.getCount();
        if (count > 0) {
            start = this.store.getAt(0).get("symbolizers");
            end = this.store.getAt(count - 1).get("symbolizers");
        }
        var targetArgs = [function(store) {
            var fraction, i = 0, count = store.getCount(), data;
            store.each(function(rec) {
                fraction = i / count;
                var targetRec = this.store.getAt(i);
                if (!targetRec) {
                    // add rule if new classification has more classes
                    targetRec = new this.store.recordType(Ext.apply({}, data));
                    this.store.add([targetRec]);
                }
                data = targetRec.data;
                var filter = rec.get("filter");
                if (start && end) {
                    targetRec.set("symbolizers", gxp.util.style.interpolateSymbolizers(start, end, fraction));
                }
                targetRec.set("filter", filter);
                //TODO Use a template for this
                targetRec.set("label", filter.lowerBoundary + "-" + filter.upperBoundary);
                targetRec.set("group", group);
                targetRec.set("name", Ext.applyIf({
                    group: group,
                    method: method,
                    args: args
                }, targetRec.get("name")));
                i++;
            }, this);
            // remove rules if new classification has less classes
            var rec;
            while(rec = this.store.getAt(i)) {
                this.store.remove(rec);
                i++;
            }
            this.store.clearFilter();
            if (callback) {
                callback.call(scope);
            }
        }];
        targetArgs.unshift.apply(targetArgs, args);
        this.methods[method].apply(this, targetArgs);
    },
    
    /** api: property[methods]
     *  ``Object`` Classification methods for use with ``classify``:
     *
     *  * ``graduated(attribute, classes, method)`` Uses GeoServer's
     *    ``gs:getFeatureClassStats`` WPS process. ``attribute`` is the
     *    field of the layer to create the classification from; ``classes``
     *    is the number of classes to create, and ``method`` is one of
     *    "EQUAL_INTERVL", "NATURAL_BREAKS", "QUANTILE".
     */
    methods: {
        graduated: function(attribute, classes, method, callback) {
            var process = {
                identifier: "gs:FeatureClassStats", 
                dataInputs: [{
                    identifier: "features",
                    reference: {
                        mimeType: "text/xml; subtype=wfs-collection/1.0", 
                        href: "http://geoserver/wfs", 
                        method: "POST",
                        body: {
                            wfs: {
                                version: "1.0.0",
                                outputFormat: "GML2",
                                featureType: this.store.reader.raw.layerName
                            }
                        }
                    }
                }, {
                    identifier: "attribute",
                    data: {
                        literalData: {
                            value: attribute
                        }
                    }
                }, {
                    identifier: "classes",
                    data: {
                        literalData: {
                            value: classes
                        }
                    }
                }, {
                    identifier: "method",
                    data: {
                        literalData: {
                            value: method
                        }
                    }
                }],
                responseForm: {
                    rawDataOutput: {
                        mimeType: "text/xml",
                        identifier: "results"
                    }
                }
            };
            var store = new Ext.data.XmlStore({
                record: "Class",
                fields: [
                    {name: "count", mapping: "@count"},
                    {name: "filter", convert: function(v, re) {
                        return new OpenLayers.Filter.Comparison({
                            type: OpenLayers.Filter.Comparison.BETWEEN,
                            property: attribute,
                            lowerBoundary: parseFloat(re.getAttribute("lowerBound")),
                            upperBoundary: parseFloat(re.getAttribute("upperBound"))
                        });
                    }}
                ],
                proxy: new Ext.data.HttpProxy({
                    url: "/geoserver/wps",
                    method: "POST",
                    xmlData: new OpenLayers.Format.WPSExecute().write(process)
                }),
                autoLoad: true,
                listeners: {
                    load: callback,
                    scope: this
                }
            });
            return store;
        }
    }
    
});