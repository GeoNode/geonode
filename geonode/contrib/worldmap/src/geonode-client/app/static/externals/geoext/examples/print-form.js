 /**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[print-form]
 *  Print Configuration with a Form
 *  -------------------------------
 *  Use form field plugins to control print output.
 */

var mapPanel, printPage;

Ext.onReady(function() {
    // The printProvider that connects us to the print service
    var printProvider = new GeoExt.data.PrintProvider({
        method: "GET", // "POST" recommended for production use
        capabilities: printCapabilities, // from the info.json script in the html
        customParams: {
            mapTitle: "Printing Demo"
        }
    });
    // Our print page. Stores scale, center and rotation and gives us a page
    // extent feature that we can add to a layer.
    printPage = new GeoExt.data.PrintPage({
        printProvider: printProvider
    });
    // A layer to display the print page extent
    var pageLayer = new OpenLayers.Layer.Vector();
    pageLayer.addFeatures(printPage.feature);

    // The map we want to print
    mapPanel = new GeoExt.MapPanel({
        region: "center",
        map: {
            eventListeners: {
                // recenter/resize page extent after pan/zoom
                "moveend": function(){ printPage.fit(this, {mode: "screen"}); }
            }
        },
        layers: [
            new OpenLayers.Layer.WMS("Tasmania", "http://demo.opengeo.org/geoserver/wms",
                {layers: "topp:tasmania_state_boundaries"}, {singleTile: true}),
            pageLayer
        ],
        center: [146.56, -41.56],
        zoom: 6
    });
    // The form with fields controlling the print output
    var formPanel = new Ext.form.FormPanel({
        region: "west",
        width: 150,
        bodyStyle: "padding:5px",
        labelAlign: "top",
        defaults: {anchor: "100%"},
        items: [{
            xtype: "textarea",
            name: "comment",
            value: "",
            fieldLabel: "Comment",
            plugins: new GeoExt.plugins.PrintPageField({
                printPage: printPage
            })
        }, {
            xtype: "combo",
            store: printProvider.layouts,
            displayField: "name",
            fieldLabel: "Layout",
            typeAhead: true,
            mode: "local",
            triggerAction: "all",
            plugins: new GeoExt.plugins.PrintProviderField({
                printProvider: printProvider
            })
        }, {
            xtype: "combo",
            store: printProvider.dpis,
            displayField: "name",
            fieldLabel: "Resolution",
            tpl: '<tpl for="."><div class="x-combo-list-item">{name} dpi</div></tpl>',
            typeAhead: true,
            mode: "local",
            triggerAction: "all",
            plugins: new GeoExt.plugins.PrintProviderField({
                printProvider: printProvider
            }),
            // the plugin will work even if we modify a combo value
            setValue: function(v) {
                v = parseInt(v) + " dpi";
                Ext.form.ComboBox.prototype.setValue.apply(this, arguments);
            }
        }, {
            xtype: "combo",
            store: printProvider.scales,
            displayField: "name",
            fieldLabel: "Scale",
            typeAhead: true,
            mode: "local",
            triggerAction: "all",
            plugins: new GeoExt.plugins.PrintPageField({
                printPage: printPage
            })
        }, {
            xtype: "textfield",
            name: "rotation",
            fieldLabel: "Rotation",
            plugins: new GeoExt.plugins.PrintPageField({
                printPage: printPage
            })
        }],
        buttons: [{
            text: "Create PDF",
            handler: function() {
                printProvider.print(mapPanel, printPage);
            }
        }]
    });
     
    // The main panel
    new Ext.Panel({
        renderTo: "content",
        layout: "border",
        width: 700,
        height: 420,
        items: [mapPanel, formPanel]
    });
});
