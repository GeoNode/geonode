/**
 * Copyright (c) 2008-2010 The Open Source Geospatial Foundation
 *
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[feature-editing]
 */

var mapPanel, editingContainer, selectFeature;

function closeEditing() {
    // avoid reentrance
    if(!arguments.callee._in) {
        arguments.callee._in = true;
        editingContainer.removeAll(true);
        selectFeature.unselectAll();
        delete arguments.callee._in;
    }
}

function createVectorLayer() {

    var styleDefault = Ext.applyIf({
        graphicName: "${symbol}",
        pointRadius: "${size}"
    }, OpenLayers.Feature.Vector.style["default"]);

    var styleSelect = Ext.applyIf({
        graphicName: "${symbol}",
        pointRadius: "${size}"
    }, OpenLayers.Feature.Vector.style["select"]);

    return new OpenLayers.Layer.Vector("vector", {
        styleMap: new OpenLayers.StyleMap({
            "default": styleDefault,
            "select": styleSelect
        }),
        eventListeners: {
            beforefeatureadded: function(e) {
                closeEditing();
                selectFeature.select(e.feature);
            },
            beforefeatureselected: function(e) {
                addEditorGrid(e.feature);
            },
            featureunselected: function(e) {
                closeEditing();
            }
        }
    });
}

function addEditorGrid(feature) {

    var store = new GeoExt.data.AttributeStore({
        feature: feature,
        fields: ["name", "type", "restriction", "label"],
        data: [{
            name: "symbol",
            label: "Symbol",
            type: {
                xtype: "combo",
                store: new Ext.data.ArrayStore({
                    fields: ['symbol'],
                    data: [['star'], ['square'], ['circle']]
                }),
                displayField: 'symbol',
                valueField: 'symbol',
                mode: 'local',
                editable: false,
                forceSelection: true,
                triggerAction: 'all',
                selectOnFocus: true
            },
            value: "star"
        }, {
            name: "size",
            label: "Size",
            type: "number",
            value: 6,
            restriction: {
                "minInclusive": 0,
                "maxInclusive": 10
            }
        }]
    });

    var editorGrid = new GeoExt.ux.FeatureEditorGrid({
        nameField: "label",
        store: store,
        forceValidation: true,
        allowSave: true,
        allowCancel: true,
        allowDelete: true,
        border: false,
        hideHeaders: true,
        viewConfig: {
            forceFit: true,
            scrollOffset: 2 // the grid will never have scrollbars
        },
        listeners: {
            done: function(panel, e) {
                closeEditing();
                var feature = e.feature, modified = e.modified;
                if(feature.state != null) {
                    // simulate save to server
                    setTimeout(function() {
                        if(feature.state === OpenLayers.State.DELETE) {
                            feature.layer.destroyFeatures([feature]);
                        } else {
                            feature.state = null;
                        }
                    }, 1);
                }
            },
            cancel: function(panel, e) {
                var feature = e.feature, modified = e.modified;
                panel.cancel();
                closeEditing();
                if(feature.state === OpenLayers.State.INSERT) {
                    feature.layer.destroyFeatures([feature]);
                }
                // we call cancel() ourselves so return false here
                return false;
            }
        }
    });

    editingContainer.add(editorGrid);
    editingContainer.doLayout();

    feature.layer.drawFeature(feature, "select");
}

Ext.onReady(function() {

    var map = new OpenLayers.Map({controls: []});

    var wmsLayer = new OpenLayers.Layer.WMS(
        "vmap0",
        "http://vmap0.tiles.osgeo.org/wms/vmap0",
        {layers: 'basic'}
    );
    var vecLayer = createVectorLayer();

    map.addLayers([wmsLayer, vecLayer]);

    var drawFeature = new OpenLayers.Control.DrawFeature(
        vecLayer, OpenLayers.Handler.Point, {
            eventListeners: {
                deactivate: closeEditing
            }
    });

    selectFeature = new OpenLayers.Control.SelectFeature(vecLayer, {
        eventListeners: {
            deactivate: closeEditing
        }
    });

    var tools = [
        "->",
        new GeoExt.Action({
            control: new OpenLayers.Control.Navigation(),
            map: map,
            toggleGroup: "edit",
            pressed: true,
            allowDepress: false,
            text: "Navigate"
        }),
        new GeoExt.Action({
            control: drawFeature,
            map: map,
            toggleGroup: "edit",
            pressed: false,
            allowDepress: false,
            text: "Add feature"
        }),
        new GeoExt.Action({
            control: selectFeature,
            map: map,
            toggleGroup: "edit",
            pressed: false,
            allowDepress: false,
            text: "Edit feature"
        })
    ];

    mapPanel = new GeoExt.MapPanel({
        title: "Map",
        region: "center",
        height: 400,
        width: 600,
        map: map,
        center: new OpenLayers.LonLat(5, 45),
        zoom: 6,
        tbar: tools
    });

    editingContainer = new Ext.Panel({
        title: "Editing",
        region: "east",
        layout: "fit",
        width: 320
    });

    new Ext.Panel({
        renderTo: "panel",
        layout: "border",
        height: 400,
        width: 920,
        items: [mapPanel, editingContainer]
    });
});
