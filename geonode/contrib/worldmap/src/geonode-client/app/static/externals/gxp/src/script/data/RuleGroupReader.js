/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @require GeoExt/data/StyleReader.js
 */

/** api: (define)
 *  module = gxp.data
 *  class = RuleGroupReader
 *  base_link = `GeoExt.data.StyleReader <http://dev.geoext.org/docs/lib/GeoExt/data/StyleReader.html>`_
 */
Ext.ns("gxp.data");

/** api: constructor
 *  .. class:: RuleGroupReader(config)
 *
 *  A ``StyleReader`` for reading rule groups of vector styles.
 */   
gxp.data.RuleGroupReader = Ext.extend(GeoExt.data.StyleReader, {
    
    /** private: method[constructor]
     *  :arg meta: ``Object``
     *  :arg recordType: ``Ext.data.Record``
     */
    constructor: function(meta, recordType) {
        meta = meta || {
            fields: [
                "symbolizers", "filter",
                {name: "label", mapping: "title"},
                {name: "name", convert: function(v, re) {
                    var obj;
                    try {
                        obj = Ext.util.JSON.decode(v);
                    } catch(e) {
                        obj = {group: "Custom", name: v};
                    }
                    re.group = obj.group;
                    return obj;
                }},
                "group", "description", "elseFilter",
                "minScaleDenominator", "maxScaleDenominator"
            ],
            storeToData: function(store) {
                var rules = GeoExt.data.StyleReader.metaData.rules.storeToData(store),
                    rule, i;
                for (i=rules.length-1; i>=0; --i) {
                    rule = rules[i];
                    if (typeof rule.name === "object") {
                        if (rule.group === "Custom") {
                            rule.name = rule.name.name;
                        } else {
                            rule.name = Ext.util.JSON.encode(rule.name);
                        }
                        delete rule.group;
                    }
                }
                return rules;
            }
        };
        gxp.data.RuleGroupReader.superclass.constructor.apply(this, [meta, recordType]);
    }
    
});