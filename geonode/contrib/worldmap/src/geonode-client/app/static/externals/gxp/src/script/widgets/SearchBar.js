Ext.namespace("gxp");

/** api: constructor
 *  Create a tool to search all searchable layers (layers with searchable columns) for user-specified text.
 *  target: GeoExplorer instance
 */
gxp.SearchBar = Ext.extend(Ext.Toolbar,{

    emptyText: 'Enter search...',
    searchText: 'Search',
    noSearchableLayersTitle: 'No Searchable Layers',
    noSearchableLayersMsg: 'There are currently no searchable layers on the map.  You must have at least one visible layer with searchable fields on the map.',
    searchTermTitle: "Search Term Required",
    searchTermText: "Please enter a search term",
    resetText: "Reset",

    initComponent: function () {
        var target = this.target;

        var getQueryableLayers = function () {
            return target.mapPanel.layers.queryBy(function (x) {
                return x.get("queryable");
            });
        };

        var searchTB = new Ext.form.TextField({
            id: 'search-tb',
            width: 150,
            emptyText: this.emptyText,
            handleMouseEvents: true,
            enableKeyEvents: true,
            listeners: {
                render: function (el) {
                    el.getEl().on('keypress', function (e) {
                        var charpress = e.keyCode;
                        if (charpress == 13) {
                            performSearch();
                        }
                    });
                }
            }
        });

        var psHandler = function () {
            performSearch(this.noSearchableLayersTitle,
                this.noSearchableLayersMsg);
        };




        var performSearch = function (title,message) {

            // Find queryable layers (visible with searchable fields)
            var searchCount = 0;
            var queryableLayers = getQueryableLayers();
            queryableLayers.each(function (x) {
                dl = x.getLayer();
                if (!dl.getVisibility() || !dl.attributes) {
                    queryableLayers.remove(x, true);
                }
            });
            if (queryableLayers.length == 0) {
                Ext.MessageBox.alert(title, message);
                return;

            }

            try {
                //Get rid of any existing highlight layers
                removeHighlightLayers();

                //search term manipulation code, copied verbatim from existing WorldMap
                var searchTerm = searchTB.getValue();
                var layers = [];

                if (searchTerm == null || searchTerm.length == 0) {
                    Ext.Msg.alert(this.searchTermTitle, this.searchTermText);
                    return;
                }

                //Create a WMS search results layer for each searchable layer
                queryableLayers.each(function (x) {
                    dl = x.getLayer();
                    if (dl.getVisibility()) {
                        if (dl.attributes) {
                            var wms_url = dl.url;
                            var queryFields = [];
                            for (f = 0; f < dl.attributes.length; f++) {
                                field = dl.attributes[f]
                                if (field.searchable) {
                                    queryFields.push(field.id);
                                }
                            }


                            var featureQuery = "";

                            var sld = ''; //'<?xml version="1.0" encoding="utf-8"?>';
                            sld +=
                                '<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0">';
                            sld += '<sld:NamedLayer><sld:Name>' + dl.params.LAYERS +
                                '</sld:Name><sld:UserStyle><sld:Name>query</sld:Name><sld:FeatureTypeStyle><sld:Rule><ogc:Filter>';
                            for (i = 0; i < queryFields.length; i++) {
                                if (queryFields[i] != "")
                                    featureQuery = featureQuery + '<ogc:PropertyIsLike wildCard="*" singleChar="." escapeChar="!"><ogc:PropertyName>' +
                                        queryFields[i] + '</ogc:PropertyName><ogc:Literal>*' + searchTerm + '*</ogc:Literal></ogc:PropertyIsLike>';
                            }
                            if (queryFields.length > 1) {
                                featureQuery = "<ogc:Or>" + featureQuery + "</ogc:Or>";
                            }
                            if (featureQuery.length > 0) {
                                sld += featureQuery;
                                sld += '</ogc:Filter>';

                                //Points
                                sld +=
                                    '<PointSymbolizer><Graphic><Mark><WellKnownName>circle</WellKnownName><Fill><CssParameter name="fill">#FFFF00</CssParameter></Fill></Mark><Size>8</Size></Graphic></PointSymbolizer>';
                                //Lines
                                sld +=
                                    '<LineSymbolizer><sld:Stroke><sld:CssParameter name="stroke">#FFFF00</sld:CssParameter><sld:CssParameter name="stroke-opacity">1.0</sld:CssParameter><sld:CssParameter name="stroke-width">2</sld:CssParameter></sld:Stroke></LineSymbolizer>';
                                //Polygons
                                //sld += '<sld:PolygonSymbolizer> <sld:Fill><sld:GraphicFill> <sld:Graphic><sld:Mark> <sld:WellKnownName>shape://times</sld:WellKnownName> <sld:Stroke><sld:CssParameter name="stroke">#FFFF00</sld:CssParameter>';
                                //sld += '<sld:CssParameter name="stroke-width">1</sld:CssParameter> </sld:Stroke></sld:Mark><sld:Size>16</sld:Size> </sld:Graphic></sld:GraphicFill> </sld:Fill></sld:PolygonSymbolizer>';
                                sld += '</sld:Rule></sld:FeatureTypeStyle></sld:UserStyle></sld:NamedLayer></sld:StyledLayerDescriptor>';

                                var wmsHighlight = new OpenLayers.Layer.WMS(
                                    "HighlightWMS_" + dl.params.LAYERS.substr(8),
                                    wms_url, {
                                        'layers': dl.params.LAYERS,
                                        'format': 'image/png',
                                        'SLD_BODY': sld,
                                        'TILED': false,
                                        'TRANSPARENT': true
                                    }, {
                                        'isBaseLayer': false,
                                        'displayInLayerSwitcher': false,
                                        'singleTile': true
                                    }
                                );

                                //target.registerEvents(wmsHighlight);
                                layers.push(wmsHighlight);
                            }
                        }
                    }
                });
                target.mapPanel.map.addLayers(layers);
            } catch (e) {
                throw e;
            } finally {

            }


        };

        var searchBtn = new Ext.Button({
            text: '<span class="x-btn-text">' + this.searchText + '</span>',
            handler: psHandler,
            scope: this
        });

        var reset = function () {
            searchTB.setValue('');
            removeHighlightLayers();
            if (target.busyMask) {
                target.busyMask.hide();
            }

        };

        var removeHighlightLayers = function () {
            var theLayers = target.mapPanel.map.layers;
            var hLayers = [];
            for (l = 0; l < theLayers.length; l++) {
                if (theLayers[l].name && (theLayers[l].name.toString().indexOf("HighlightWMS") > -1 || theLayers[l].name == "hilites")) {
                    hLayers.push(theLayers[l]);

                }

            }

            for (h = 0; h < hLayers.length; h++) {
                target.mapPanel.map.removeLayer(hLayers[h], true);
            }

        }

        this.id = "tlbr";
        this.items = [searchTB,
            ' ', searchBtn, ' ', {
                xtype: 'button',
                text: '<span class="x-btn-text">' + this.resetText + '</span>',
                handler: function (brn, e) {
                    reset();
                }
            }
        ];

        gxp.SearchBar.superclass.initComponent.call(this);

    }

});

/** api: xtype = gxp_newsourcedialog */
Ext.reg('gxp_searchbar', gxp.SearchBar);