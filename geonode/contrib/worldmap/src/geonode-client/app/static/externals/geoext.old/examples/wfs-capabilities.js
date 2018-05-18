/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */


/** api: example[wfs-capabilities]
 *  WFS Capabilities Store
 *  ----------------------
 *  Create layer records from WFS capabilities documents.
 */

var store;

Ext.onReady(function() {

    // create a new WFS capabilities store
    store = new GeoExt.data.WFSCapabilitiesStore({
        url: "data/wfscap_tiny_100.xml",
        // set as a function that returns a hash of layer options.  This allows
        // to have new objects created upon each new OpenLayers.Layer.Vector
        // object creations.
        layerOptions: function() {
            return {
                visibility: false,
                displayInLayerSwitcher: false,
                strategies: [new OpenLayers.Strategy.BBOX({ratio: 1})]
            };
        }
    });
    // load the store with records derived from the doc at the above url
    store.load();

    // create a grid to display records from the store
    var grid = new Ext.grid.GridPanel({
        title: "WFS Capabilities",
        store: store,
        columns: [
            {header: "Title", dataIndex: "title", sortable: true, width: 250},
            {header: "Name", dataIndex: "name", sortable: true},
            {header: "Namespace", dataIndex: "namespace", sortable: true, width: 150},
            {id: "description", header: "Description", dataIndex: "abstract"}
        ],
        renderTo: "capgrid",
        height: 300,
        width: 650
    });
});
