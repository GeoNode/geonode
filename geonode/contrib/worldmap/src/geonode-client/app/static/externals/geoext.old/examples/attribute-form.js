/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 *
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[attribute-form]
 *  Attribute Form
 *  --------------
 *  Create a form with fields from attributes read from a WFS
 *  DescribeFeatureType response
 */

var form;

Ext.onReady(function() {
    Ext.QuickTips.init();

    // create attributes store
    var attributeStore = new GeoExt.data.AttributeStore({
        url: "data/describe_feature_type.xml"
    });

    form = new Ext.form.FormPanel({
        renderTo: document.body,
        autoScroll: true,
        height: 300,
        width: 350,
        defaults: {
            width: 120,
            maxLengthText: "too long",
            minLengthText: "too short"
        },
        plugins: [
            new GeoExt.plugins.AttributeForm({
                attributeStore: attributeStore,
                recordToFieldOptions: {
                    labelTpl: new Ext.XTemplate(
                        '{name}{[this.getStar(values)]}', {
                            compiled: true,
                            disableFormats: true,
                            getStar: function(v) {
                                return v.nillable ? '' : ' *';
                            }
                        }
                    )
                }
            })
        ]
    });

    attributeStore.load();
});
