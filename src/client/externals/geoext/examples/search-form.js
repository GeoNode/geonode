/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

var formPanel;

Ext.onReady(function() {

    // create a protocol, this protocol is used by the form
    // to send the search request, this protocol's read
    // method received an OpenLayers.Filter instance,
    // which is derived from the content of the form
    var protocol = new OpenLayers.Protocol({
        read: function(options) {
            var f; html = [];

            f = options.filter;
            html.push([f.CLASS_NAME, ",", f.type, "<br />"].join(" "));

            f = options.filter.filters[0];
            html.push([f.CLASS_NAME, ",", f.type, ",",
                       f.property, ":", f.value, "<br />"].join(" "));

            f = options.filter.filters[1];
            html.push([f.CLASS_NAME, ",", f.type, ", ",
                       f.property, ": ", f.value].join(" "));

            Ext.get("filter").update(html.join(""));

        }
    });

    // create a GeoExt form panel (configured with an OpenLayers.Protocol
    // instance)
    formPanel = new GeoExt.form.FormPanel({
        width: 300,
        height: 200,
        protocol: protocol,
        items: [{
            xtype: "textfield",
            name: "name__like",
            value: "foo",
            fieldLabel: "name"
        }, {
            xtype: "textfield",
            name: "elevation__ge",
            value: "1200",
            fieldLabel: "maximum elevation"
        }],
        listeners: {
            actioncomplete: function(form, action) {
                // this listener triggers when the search request
                // is complete, the OpenLayers.Protocol.Response
                // resulting from the request is available
                // through "action.response"
            }
        }
    });

    formPanel.addButton({
        text: "search",
        handler: function() {
            // trigger search request, the options passed to doAction
            // are passed to the protocol's read method, so one
            // can register a read callback here
            var o = {
                callback: function(response) {
                }
            };
            this.search(o);
        },
        scope: formPanel
    });

    formPanel.render("formpanel");
});
