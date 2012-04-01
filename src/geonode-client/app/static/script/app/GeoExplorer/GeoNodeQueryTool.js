/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the BSD license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = GeoNodeQueryTool
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp");
/** api: constructor
 *  .. class:: GeoNodeQueryTool(config)
 *
 *    This plugins provides an action which, when active, will issue a
 *    GetFeatureInfo request to the WMS of all layers on the map. The output
 *    will be displayed in a popup.
 */
gxp.plugins.GeoNodeQueryTool = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = geo_getfeatureinfo */
    ptype: "gxp_geonodequerytool",

    /** api: config[outputTarget]
     *  ``String`` Popups created by this tool are added to the map by default.
     */
    outputTarget: "map",

    /** private: property[popupCache]
     *  ``Object``
     */
    popupCache: null,

    /** api: config[infoActionTip]
     *  ``String``
     *  Text for feature info action tooltip (i18n).
     */
    infoActionTip: "Get Feature Info",

    /** api: config[popupTitle]
     *  ``String``
     *  Title for info popup (i18n).
     */
    popupTitle: "Feature Info",

    toolText: null,
    iconCls: "gxp-icon-getfeatureinfo",
    proj_merc : new OpenLayers.Projection("EPSG:900913"),

    featurePanel: "",
    attributePanel: "",
    gridResultsPanel: 'gridResultsPanel',

    /** api: config[vendorParams]
     *  ``Object``
     *  Optional object with properties to be serialized as vendor specific
     *  parameters in the requests (e.g. {buffer: 10}).
     */

    /** api: config[paramsFromLayer]
     *  ``Array`` List of param names that should be taken from the layer and
     *  added to the GetFeatureInfo request (e.g. ["CQL_FILTER"]).
     */

    /** api: method[addActions]
     */
    addActions: function() {
        //console.log('addActions');
        this.popupCache = {};

        var tool = this;

        var actions = gxp.plugins.GeoNodeQueryTool.superclass.addActions.call(this, [
            {
                tooltip: this.infoActionTip,
                iconCls: this.iconCls,
                text: this.toolText,
                id: this.id,
                pressed: true,
                toggleGroup: this.toggleGroup,
                enableToggle: true,
                allowDepress: true,
                toggleHandler: function(button, pressed) {
                    for (var i = info.controls.length; i --;) {
                        if (pressed) {
                            info.controls[i].activate();
                        } else {
                            info.controls[i].deactivate();
                            tool.reset(true);
                        }
                    }
                }
            }
        ]);
        var infoButton = this.actions[0].items[0];

        var info = {controls: []};
        var updateInfo = function() {
            var queryableLayers = this.target.mapPanel.layers.queryBy(function(x) {
                return (x.get("queryable") && x.getLayer().getVisibility() && x.getLayer().displayInLayerSwitcher === true && x.getLayer() instanceof OpenLayers.Layer.WMS);
            });


            var localUrl = this.target.localGeoServerBaseUrl;
            //console.log('LCOAL URL: ' + localUrl);

            var map = this.target.mapPanel.map;
            var control;
            for (var i = 0, len = info.controls.length; i < len; i++) {
                control = info.controls[i];
                control.deactivate();  // TODO: remove when http://trac.openlayers.org/ticket/2130 is closed
                control.destroy();
            }

            var count = queryableLayers.length, successCount = 0, featureCount = 0;
            var features = [];
            var featureMeta = [];

            info.controls = [];
            queryableLayers.each(function(x) {
                var layer = x.getLayer();


                //console.log(layer.name +":" + layer.srs);
                var vendorParams = Ext.apply({}, this.vendorParams), param;
                if (this.layerParams) {
                    for (var i = this.layerParams.length - 1; i >= 0; --i) {
                        param = this.layerParams[i].toUpperCase();
                        vendorParams[param] = layer.params[param];
                    }
                }
                vendorParams['buffer'] = 25;

                /* Use OpenLayers.Control.GetFeature for local layers only */
                if (layer.url.indexOf(localUrl) > -1) {
                    //console.log(layer.name + 'IS LOCAL?' );
                    var control = new OpenLayers.Control.GetFeature({
                        protocol: OpenLayers.Protocol.WFS.fromWMSLayer(layer),
                        clickTolerance:25,
                        layer: layer,
                        box: false,
                        hover: false,
                        single: true,
                        eventListeners: {
                            clickout: function() {
                                if (successCount === 0)
                                    features = [];
                                successCount++;
                                //console.log('Nada:' + layer.name +  ":" + count + ":" + successCount);
                                if (successCount == count) {
                                    successCount = 0;
                                    if (features.length == 0) {
                                        Ext.Msg.alert('Map Results', 'No features found at this location.');
                                    } else {
                                        this.displayXYResults(features, featureMeta);
                                    }
                                    OpenLayers.Element.removeClass(control.map.viewPortDiv, "olCursorWait");
                                }
                            },
                            featuresselected: function(evt) {
                                if (successCount === 0)
                                    features = [];
                                successCount++;
                                //console.log('control getfeatureinfo ' + layer.name+ ':' + evt.features.length  + ":" + count + ":" + successCount);

                                if (evt.features) {
                                    //console.log('Process features');
                                    try {
                                        var featureInfo = evt.features;
                                        if (featureInfo) {
                                            if (featureInfo.constructor != Array) {
                                                featureInfo = [featureInfo];
                                            }


                                            featureInfo.title = x.get("title");
                                            //console.log('datalayers?:' + this.target.dataLayers[layer.params.LAYERS]);
                                            if (layer.attributes) {
                                                featureInfo.queryfields = layer.attributes;
                                                featureInfo.nameField = featureInfo.queryfields[0].id;
                                            } else if (featureInfo.length > 0) {
                                                var qfields = [];
                                                for (var fname in evt.features[0].attributes) {
                                                    qfields.push(fname.toString());
                                                }

                                                featureInfo.queryfields = qfields;

                                                if (featureInfo.queryfields.length > 0)
                                                    featureInfo.nameField = featureInfo.queryfields[0];
                                            }
                                            for (var f = evt.features.length; f--;) {
                                                feature = featureInfo[f];
                                                feature.wm_layer_id = featureCount;
                                                feature.wm_layer_title = featureInfo.title;
                                                feature.wm_layer_name = feature.attributes[featureInfo.nameField];
                                                feature.wm_layer_type = layer.params.LAYERS;
                                                featureCount++;
                                                features = features.concat(feature);
                                            }

                                            featureMeta[layer.params.LAYERS] = featureInfo.queryfields;

                                        }  //end if(featureInfo)
                                    } catch (err) {
                                        Ext.Msg.alert("Error", err)
                                    }
                                }  //end if (resp.responseText)


                                if (successCount == count) {
                                    successCount = 0;
                                    if (features.length == 0) {
                                        Ext.Msg.alert('Map Results', 'No features found at this location.');
                                    } else {
                                        this.displayXYResults(features, featureMeta);
                                    }
                                    OpenLayers.Element.removeClass(control.map.viewPortDiv, "olCursorWait");
                                }


                            },
                            scope: this
                        }
                    });

                    OpenLayers.Util.extend(control, {
                        request: function(bounds, options) {
                            options = options || {};
                            var filter = new OpenLayers.Filter.Spatial({
                                type: this.filterType,
                                value: bounds
                            });

                            // Set the cursor to "wait" to tell the user we're working.
                            OpenLayers.Element.addClass(this.map.viewPortDiv, "olCursorWait");

                            var control = this;
                            var wfs_layer = this.layer;
                            var wfs_url = wfs_layer.url;
                            if (wfs_url.indexOf("?") > -1)
                                wfs_url = wfs_url.substring(0, wfs_url.indexOf("?"));

                            wfs_url += "?service=WFS&request=GetFeature&version=1.0.0&srsName=EPSG:900913&outputFormat=GML2&typeName=" + wfs_layer.params.LAYERS + "&BBOX=" + bounds.toBBOX() + ",EPSG:900913";
                            Ext.Ajax.request({
                                'url':wfs_url,
                                'success':function(resp, opts) {
                                    var features = new OpenLayers.Format.GML().read(resp.responseText);
                                    if (features && features.length > 0) {
                                        if (options.single == true) {
                                            control.selectBestFeature(features,
                                                    bounds.getCenterLonLat(), options);
                                        } else {
                                            control.select(features);
                                        }
                                    } else {
                                        control.events.triggerEvent("clickout");
                                        if (control.clickout) {
                                            control.unselectAll();
                                        }
                                    }
                                    //OpenLayers.Element.removeClass(control.map.viewPortDiv, "olCursorWait");
                                },
                                'failure': function(resp, opts) {
                                    control.events.triggerEvent("clickout");
                                    //OpenLayers.Element.removeClass(control.map.viewPortDiv, "olCursorWait");
                                }
                            });
                        },
                        selectBestFeature: function(features, clickPosition, options) {
                            options = options || {};
                            if (features.length) {
                                var point = new OpenLayers.Geometry.Point(clickPosition.lon,
                                        clickPosition.lat);
                                var feature,  dist;
                                var resultFeature = [];
                                var minDist = Number.MAX_VALUE;
                                for (var i = 0, max = features.length; i < max; ++i) {
                                    feature = features[i];
                                    if (feature.geometry) {
                                        if (feature.geometry.CLASS_NAME.indexOf('Point') > -1) {
                                            resultFeature = features;
                                            break;
                                        }
                                        else {
                                                    dist = point.distanceTo(feature.geometry, {edge: false});
                                                    if (dist < minDist) {
                                                        minDist = dist;
                                                        resultFeature = feature;
                                                        if (minDist == 0) {
                                                            break;
                                                        }
                                                    }
                                        }
                                    }
                                }

                                if (options.hover == true) {
                                    this.hoverSelect(resultFeature);
                                } else {
                                    this.select(resultFeature || features);
                                }
                            }
                        }
                    });
                }
                else {
                    var control = new OpenLayers.Control.WMSGetFeatureInfo({
                        url: layer.url,
                        queryVisible: true,
                        infoFormat: 'application/vnd.ogc.gml',
                        layers: [layer],
                        vendorParams: vendorParams,
                        eventListeners: {
                            getfeatureinfo: function(evt) {
                                if (successCount === 0)
                                    features = [];
                                successCount++;

                                if (evt.text != '') {

                                    if (evt.text.indexOf('<FeatureInfoResponse') > -1) {

                                        var coords = map.getLonLatFromPixel(evt.xy);
                                        var point = new OpenLayers.Geometry.Point(coords.lon, coords.lat)


                                        var dq = Ext.DomQuery;
                                        var xmlObject = new OpenLayers.Format.XML().read(evt.text);
                                        var featureInfo = new Object();
                                        //var title =  x.get("title");
                                        //featureInfo.title = x.get("title");
                                        var nodes = dq.select('FIELDS', xmlObject);

                                        if (nodes.length > 0) {
                                            var qfields = [];

                                            for (var attr = 0, max = nodes[0].attributes.length; attr < max; attr++) {
                                                qfields.push(nodes[0].attributes[attr].name);
                                            }

                                            featureInfo['queryfields'] = qfields;

                                            if (qfields.length > 0)
                                                featureInfo['nameField'] = featureInfo['queryfields'][0];

                                            for (var it =nodes.length; it--;) {
                                                node = nodes[it];
                                                var feature = new OpenLayers.Feature.Vector(point);

//                                                for (attribute in node.attributes)
//                                                {
//                                                    qfields.push(node.attributes[attribute].name);
//                                                }

                                                //feature.attributes = node.attributes;
                                                for (var at = node.attributes.length; at--;) {
                                                    feature.attributes[node.attributes[at].name] = node.attributes[at].value;
                                                }

                                                feature.wm_layer_id = featureCount;
                                                feature.wm_layer_title = x.get("title");
                                                feature.wm_layer_name = feature.attributes[featureInfo.nameField];
                                                feature.wm_layer_type = layer.params.LAYERS;
                                                featureCount++;
                                                features = features.concat(feature);


                                            }

                                            featureMeta[layer.params.LAYERS] = featureInfo.queryfields;
                                        }
                                    }
                                    else {
                                        var featureInfo = new OpenLayers.Format.GML().read(evt.text);

                                        if (featureInfo && featureInfo.length > 0) {
                                            if (featureInfo.constructor != Array) {
                                                featureInfo = [featureInfo];
                                            }

                                            featureInfo.title = x.get("title");
                                            if (featureInfo.length > 0) {

                                                var qfields = [];
                                                for (var fname in featureInfo[0].attributes) {
                                                    qfields.push(fname.toString());
                                                }

                                                featureInfo.queryfields = qfields;

                                                if (featureInfo.queryfields.length > 0)
                                                    featureInfo.nameField = featureInfo.queryfields[0];
                                            }
                                            for (var f = featureInfo.length; f--;) {
                                                var feature = featureInfo[f];


                                                var featureBounds = feature.geometry.getBounds();
                                                //console.log('featureBounds:' + featureBounds.toBBOX());
                                                var wgs84Bounds = new OpenLayers.Bounds(-180, -90, 180, 90);

                                                //console.log('Is 4326? ' + wgs84Bounds.containsBounds(featureBounds, true));
                                                if (wgs84Bounds.containsBounds(featureBounds, true)) {
                                                    var inFormat = new OpenLayers.Format.GeoJSON({
                                                        'internalProjection': new OpenLayers.Projection("EPSG:4326"),
                                                        'externalProjection': new OpenLayers.Projection("EPSG:900913")
                                                    });

                                                    var outFormat = new OpenLayers.Format.GeoJSON({
                                                        'projection': new OpenLayers.Projection("EPSG:900913")
                                                    });

                                                    var json = inFormat.write(feature);
                                                    feature = outFormat.read(json)[0];

                                                } else {

                                                    var coords = map.getLonLatFromPixel(evt.xy);
                                                    var point = new OpenLayers.Geometry.Point(coords.lon, coords.lat)
                                                    var newFeature = new OpenLayers.Feature.Vector(point);
                                                    newFeature.attributes = feature.attributes;
                                                    feature = newFeature;
                                                }


                                                feature.wm_layer_id = featureCount;
                                                feature.wm_layer_title = featureInfo.title;
                                                feature.wm_layer_name = feature.attributes[featureInfo.nameField];
                                                feature.wm_layer_type = layer.params.LAYERS;


                                                featureCount++;
                                                features = features.concat(feature);
                                            }

                                            featureMeta[layer.params.LAYERS] = featureInfo.queryfields;

                                        }
                                    }//end if(featureInfo)

                                }  //end if (resp.responseText)


                                if (successCount == count) {
                                    successCount = 0;
                                    if (features.length == 0) {
                                        Ext.Msg.alert('Map Results', 'No features found at this location.');
                                    } else {
                                        this.displayXYResults(features, featureMeta);
                                    }
                                    OpenLayers.Element.removeClass(control.map.viewPortDiv, "olCursorWait");
                                }


                            },
                            scope: this
                        }
                    });

                }

                map.addControl(control);
                info.controls.push(control);
                if (infoButton && infoButton.pressed) {
                    control.activate();
                }
            }, this);
        };

        this.target.mapPanel.layers.on("update", updateInfo, this);
        this.target.mapPanel.layers.on("add", updateInfo, this);
        this.target.mapPanel.layers.on("remove", updateInfo, this);

        return actions;
    },

    /* Clear out any previous results */
    reset:  function(clearPanel) {

        if (clearPanel === true) {
            Ext.getCmp(this.attributePanel).removeAll(true);
            Ext.getCmp(this.gridResultsPanel).removeAll(true);
            Ext.getCmp(this.featurePanel).hide();

        }
        var theLayers = this.target.mapPanel.map.layers;
        var hLayers = [];
        for (l = theLayers.length; l--;) {
            //console.log('Remve? ' + theLayers[l].name);
            if (theLayers[l].name == "hilites") {
                //console.log('Removing highlight layer');
                this.target.mapPanel.map.removeLayer(theLayers[l], true);
                break;
            }

        }
    },

    /* Set up display of results in two panels */
    displayXYResults:  function(featureInfo, featureMeta) {
        var ep = Ext.getCmp(this.featurePanel);
        var gp = Ext.getCmp(this.attributePanel);

        if (ep.hidden) {
            ep.show();
            ep.alignTo(document, 'tr-tr');
        }
        gp.removeAll(true);

        var currentFeatures = featureInfo;
        //console.log('display # features:' + featureInfo.length);
        var reader = new Ext.data.JsonReader({}, [
            {name: 'wm_layer_title'},
            {name: 'wm_layer_name'},
            {name: 'wm_layer_id'},
            {name: 'wm_layer_type'}
        ]);

        var tool = this;
        var gridPanel = new Ext.grid.GridPanel({
            tbar:[
                {
                    xtype:'button',
                    text:'<span class="x-btn-text">Reset</span>',
                    qtip: 'Clear all features',
                    handler: function(brn, e) {
                        tool.reset(true);
                    },
                    text: 'Reset'
                }
            ],
            id: 'getFeatureInfoGrid',
            header: false,
            store:new Ext.data.GroupingStore({
                reader: reader,
                data: currentFeatures,
                groupField:'wm_layer_title',
                sortInfo:{field: 'wm_layer_id', direction: "DESC"}
            }),
            columns:[
                { id:'wm_layer_id', sortable:false, header:'FID', dataIndex:'wm_layer_id', hidden:true},
                { header: 'Name', sortable:true, dataIndex:'wm_layer_name', width:190 },
                { header:'Feature Type', dataIndex:'wm_layer_type', width:0, hidden:true },
                { header:'Layer', sortable:false, dataIndex:'wm_layer_title', width:0, hidden:true }
            ],
            view: new Ext.grid.GroupingView({
                //forceFit:true,
                groupTextTpl: '{group}',
                style: 'width: 425px'
            }),
            sm: new Ext.grid.RowSelectionModel({
                singleSelect: true,
                listeners: {
                    rowselect: {
                        fn: function(sm, rowIndex, rec) {
                            //console.log('displaySingleResult call');
                            tool.displaySingleResult(currentFeatures, rowIndex, rec.data, featureMeta[rec.data.wm_layer_type]);
                        }
                    }
                }
            }),
            layout: 'fit',
            frame:false,
            collapsible: true,
            iconCls: 'icon-grid',
            autoHeight:true,
            style: 'width: 425px',
            width: '400'

            //autoExpandColumn:'name',
        });


        gp.add(gridPanel);
        gp.doLayout();
        //gridPanel.addListener( 'afterlayout', function(){this.getSelectionModel().selectFirstRow()});
        //var t = setTimeout(function(){gridPanel.getSelectionModel().selectFirstRow()},1000);

        gridPanel.getSelectionModel().selectFirstRow();
        //var recordId = gridPanel.store.find('wm_layer_id', currentFeatures.length - 1);
        //gridPanel.getSelectionModel().selectRow(recordId);


    },

    /* Display details for individual feature*/
    displaySingleResult: function(currentFeatures, rowIndex, gridFeature, metaColumns) {

        var dp = Ext.getCmp(this.gridResultsPanel);
        dp.removeAll();

        var feature = null;
        // Look for the feature in the full collection of features (the grid store only has simplified objects)
        for (var i = currentFeatures.length; i--;) {
            if (currentFeatures[i].wm_layer_id == gridFeature.wm_layer_id) {
                feature = currentFeatures[i];
            }
        }

        //console.log('Feature:' + feature);

        if (!feature) {
            return;
        }

        this.addVectorQueryLayer(feature);


        var featureHtml = this.createHTML(feature, metaColumns);
        dp.update(featureHtml);
        dp.doLayout();

    },

    /* Create rows of attributes */
    createHTML:  function(feature, metaColumns) {
        html = '<ul class="featureDetailList" id="featureDetailList">';

        for (c = 0, max = metaColumns.length; c < max; c++) {
            column = metaColumns[c];


            featureValue = '' + (column.header ? feature.attributes[column.id] : feature.attributes[column])
            if (featureValue == 'undefined' || featureValue == 'null')
                featureValue = '';


            if (featureValue.indexOf("http") == 0) {
                featureValue = '<a target="_blank" href="' + featureValue + '">' + featureValue + '</a>'
            }


            html += "<li><label>" + (column.header ? column.header : column) + "</label><span>" + featureValue + "</span></li>";

        }

        html += "</ul>";
        return html;
    },


    /* Highlight the selected feature in red */
    addVectorQueryLayer: function(feature) {
        var highlight_style = {
            strokeColor: 'Red',
            strokeWidth: 4,
            strokeOpacity: 1,
            fillOpacity: 0.0,
            pointRadius: 10

        };

        var hilites = new OpenLayers.Layer.Vector("hilites", {
            isBaseLayer: false,
            projection: new OpenLayers.Projection("EPSG:900913"),
            visibility: true,
            style: highlight_style,
            displayInLayerSwitcher : false
        });


        //Add highlight vector layer for selected features


        hilites.addFeatures(feature);
        hilites.setVisibility(true);

        this.target.mapPanel.layers.suspendEvents();
        try {
            this.reset(false);
            this.target.mapPanel.map.addLayer(hilites);
        } finally {
            this.target.mapPanel.layers.resumeEvents();
        }
        return hilites;

    }
});


Ext.preg(gxp.plugins.GeoNodeQueryTool.prototype.ptype, gxp.plugins.GeoNodeQueryTool);
