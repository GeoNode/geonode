/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: example[style-grid]
 *  Style Reader
 *  ----------------
 *  Rendering and basic editing of SLD rules or an SLD ColorMap with a store
 *  created using GeoExt.data.StyleReader.
 */

var rasterSld = '<?xml version="1.0" encoding="ISO-8859-1"?><StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd"><NamedLayer><Name>rain</Name><UserStyle><Name>rain</Name><Title>Rain distribution</Title><FeatureTypeStyle><Rule><RasterSymbolizer><Opacity>1.0</Opacity><ColorMap><ColorMapEntry color="#FF0000" quantity="0" /><ColorMapEntry color="#FFFFFF" quantity="100"/><ColorMapEntry color="#00FF00" quantity="2000"/><ColorMapEntry color="#0000FF" quantity="5000"/></ColorMap></RasterSymbolizer></Rule></FeatureTypeStyle></UserStyle></NamedLayer></StyledLayerDescriptor>';
var vectorSld = '<?xml version="1.0" encoding="ISO-8859-1"?><StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:gml="http://www.opengis.net/gml" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd"><NamedLayer><Name>USA states population</Name><UserStyle><Name>population</Name><Title>Population in the United States</Title><Abstract>A sample filter that filters the United States into threecategories of population, drawn in different colors</Abstract><FeatureTypeStyle><Rule><Title>&lt; 2M</Title><ogc:Filter><ogc:PropertyIsLessThan> <ogc:PropertyName>PERSONS</ogc:PropertyName> <ogc:Literal>2000000</ogc:Literal></ogc:PropertyIsLessThan></ogc:Filter><PolygonSymbolizer> <Fill><!-- CssParameters allowed are fill (the color) and fill-opacity --><CssParameter name="fill">#4DFF4D</CssParameter><CssParameter name="fill-opacity">0.7</CssParameter> </Fill> </PolygonSymbolizer></Rule><Rule><Title>2M - 4M</Title><ogc:Filter><ogc:PropertyIsBetween><ogc:PropertyName>PERSONS</ogc:PropertyName><ogc:LowerBoundary><ogc:Literal>2000000</ogc:Literal></ogc:LowerBoundary><ogc:UpperBoundary><ogc:Literal>4000000</ogc:Literal></ogc:UpperBoundary></ogc:PropertyIsBetween></ogc:Filter><PolygonSymbolizer> <Fill><!-- CssParameters allowed are fill (the color) and fill-opacity --><CssParameter name="fill">#FF4D4D</CssParameter><CssParameter name="fill-opacity">0.7</CssParameter> </Fill> </PolygonSymbolizer></Rule><Rule><Title>&gt; 4M</Title><!-- like a linesymbolizer but with a fill too --><ogc:Filter><ogc:PropertyIsGreaterThan> <ogc:PropertyName>PERSONS</ogc:PropertyName> <ogc:Literal>4000000</ogc:Literal></ogc:PropertyIsGreaterThan></ogc:Filter><PolygonSymbolizer> <Fill><!-- CssParameters allowed are fill (the color) and fill-opacity --><CssParameter name="fill">#4D4DFF</CssParameter><CssParameter name="fill-opacity">0.7</CssParameter> </Fill> </PolygonSymbolizer></Rule><Rule><Title>Boundary</Title><LineSymbolizer><Stroke><CssParameter name="stroke-width">0.2</CssParameter></Stroke></LineSymbolizer><TextSymbolizer><Label><ogc:PropertyName>STATE_ABBR</ogc:PropertyName></Label><Font><CssParameter name="font-family">Times New Roman</CssParameter><CssParameter name="font-style">Normal</CssParameter><CssParameter name="font-size">14</CssParameter></Font><LabelPlacement><PointPlacement><AnchorPoint><AnchorPointX>0.5</AnchorPointX><AnchorPointY>0.5</AnchorPointY></AnchorPoint></PointPlacement></LabelPlacement></TextSymbolizer></Rule> </FeatureTypeStyle></UserStyle></NamedLayer></StyledLayerDescriptor>';

var format = new OpenLayers.Format.SLD({multipleSymbolizers: true});

var vectorStyle = format.read(vectorSld).namedLayers["USA states population"].userStyles[0];
var rasterStyle = format.read(rasterSld).namedLayers["rain"].userStyles[0];

var vectorGrid, rasterGrid;

Ext.onReady(function() {
    
    var columns = [
        {dataIndex: "symbolizers", width: 26, xtype: "gx_symbolizercolumn"},
        {header: "Label", dataIndex: "label", editor: {xtype: "textfield"}},
        {header: "Filter", dataIndex: "filter", editor: {xtype: "textfield"}}
    ];
        
    vectorGrid = new Ext.grid.EditorGridPanel({
        width: 220,
        height: 115,
        columns: columns.concat(),
        viewConfig: {autoFill: true},
        store: {
            reader: new GeoExt.data.StyleReader(),
            data: vectorStyle
        },
        renderTo: "vectorgrid",
        enableDragDrop: true,
        sm: new Ext.grid.RowSelectionModel(),
        ddGroup: "vgrid",
        listeners: {
            afteredit: function(e) {e.grid.store.commitChanges();},
            render: function makeDD(grid) {
                store = grid.store;
                new Ext.dd.DropTarget(grid.getView().mainBody, {
                    ddGroup : "vgrid",
                    notifyDrop: function(dd, e, data){
                        var sm = grid.getSelectionModel();
                        var rows = sm.getSelections();
                        var cindex = dd.getDragData(e).rowIndex;
                        if (sm.hasSelection()) {
                            for (var i=0, ii=rows.length; i<ii; ++i) {
                                store.remove(store.getById(rows[i].id));
                                store.insert(cindex,rows[i]);
                                store.commitChanges();
                            }
                            sm.selectRecords(rows);
                        }  
                    }
                });
            },
            scope: this
        }
    });
    rasterGrid = new Ext.grid.EditorGridPanel({
        width: 220,
        height: 115,
        columns: columns.concat(),
        viewConfig: {autoFill: true},
        store: {
            reader: new GeoExt.data.StyleReader(),
            data: rasterStyle.rules[0].symbolizers[0]
        },
        renderTo: "rastergrid",
        listeners: {
            afteredit: function(e) {e.grid.store.commitChanges();}
        }
    });
});
