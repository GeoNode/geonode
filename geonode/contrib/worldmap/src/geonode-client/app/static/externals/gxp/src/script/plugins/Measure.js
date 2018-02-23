/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @requires OpenLayers/StyleMap.js
 * @requires OpenLayers/Rule.js
 * @requires OpenLayers/Control/Measure.js
 * @requires OpenLayers/Renderer/SVG.js
 * @requires OpenLayers/Renderer/VML.js
 * @requires OpenLayers/Renderer/Canvas.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = Measure
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: Measure(config)
 *
 *    Provides two actions for measuring length and area.
 */
gxp.plugins.Measure = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_measure */
    ptype: "gxp_measure",

    /** api: config[outputTarget]
     *  ``String`` Popups created by this tool are added to the map by default.
     */
    outputTarget: "map",

    /** api: config[buttonText]
     *  ``String``
     *  Text for the Measure button (i18n).
     */
    buttonText: "Measure",

    /** api: config[lengthMenuText]
     *  ``String``
     *  Text for measure length menu item (i18n).
     */
    lengthMenuText: "Length",

    /** api: config[areaMenuText]
     *  ``String``
     *  Text for measure area menu item (i18n).
     */
    areaMenuText: "Area",

    /** api: config[lengthTooltip]
     *  ``String``
     *  Text for measure length action tooltip (i18n).
     */
    lengthTooltip: "Measure length",

    /** api: config[areaTooltip]
     *  ``String``
     *  Text for measure area action tooltip (i18n).
     */
    areaTooltip: "Measure area",

    /** api: config[measureTooltip]
     *  ``String``
     *  Text for measure action tooltip (i18n).
     */
    measureTooltip: "Measure",

    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.plugins.Measure.superclass.constructor.apply(this, arguments);
    },

    /** private: method[destroy]
     */
    destroy: function() {
        this.button = null;
        gxp.plugins.Measure.superclass.destroy.apply(this, arguments);
    },

    /** private: method[createMeasureControl]
     * :param: handlerType: the :class:`OpenLayers.Handler` for the measurement
     *     operation
     * :param: title: the string label to display alongside results
     *
     * Convenience method for creating a :class:`OpenLayers.Control.Measure`
     * control
     */
    createMeasureControl: function(handlerType, title) {

        var styleMap = new OpenLayers.StyleMap({
            "default": new OpenLayers.Style(null, {
                rules: [new OpenLayers.Rule({
                    symbolizer: {
                        "Point": {
                            pointRadius: 4,
                            graphicName: "square",
                            fillColor: "white",
                            fillOpacity: 1,
                            strokeWidth: 1,
                            strokeOpacity: 1,
                            strokeColor: "#333333"
                        },
                        "Line": {
                            strokeWidth: 3,
                            strokeOpacity: 1,
                            strokeColor: "#666666",
                            strokeDashstyle: "dash"
                        },
                        "Polygon": {
                            strokeWidth: 2,
                            strokeOpacity: 1,
                            strokeColor: "#666666",
                            fillColor: "white",
                            fillOpacity: 0.3
                        }
                    }
                })]
            })
        });
        var cleanup = function() {
            if (measureToolTip) {
                measureToolTip.destroy();
            }
        };

        var makeString = function(metricData) {
            var metric = metricData.measure;
            var metricUnit = metricData.units;

            measureControl.displaySystem = "english";

            var englishData = metricData.geometry.CLASS_NAME.indexOf("LineString") > -1 ?
            measureControl.getBestLength(metricData.geometry) :
            measureControl.getBestArea(metricData.geometry);

            var english = englishData[0];
            var englishUnit = englishData[1];

            measureControl.displaySystem = "metric";
            var dim = metricData.order == 2 ?
            '<sup>2</sup>' :
            '';

            return metric.toFixed(2) + " " + metricUnit + dim + "<br>" +
                english.toFixed(2) + " " + englishUnit + dim;
        };

        var measureToolTip;
        var controlOptions = Ext.apply({}, this.initialConfig.controlOptions);
        Ext.applyIf(controlOptions, {
            geodesic: true,
            persist: true,
            handlerOptions: {layerOptions: {styleMap: styleMap}},
            eventListeners: {
                measurepartial: function(event) {
                    cleanup();
                    measureToolTip = this.addOutput({
                        xtype: 'tooltip',
                        html: makeString(event),
                        title: title,
                        autoHide: false,
                        closable: true,
                        draggable: false,
                        mouseOffset: [0, 0],
                        showDelay: 1,
                        listeners: {hide: cleanup}
                    });
                    if(event.measure > 0) {
                        var px = measureControl.handler.lastUp;
                        var p0 = this.target.mapPanel.getPosition();
                        measureToolTip.targetXY = [p0[0] + px.x, p0[1] + px.y];
                        measureToolTip.show();
                    }
                },
                deactivate: cleanup,
                scope: this
            }
        });
        var measureControl = new OpenLayers.Control.Measure(handlerType,
            controlOptions);

        return measureControl;
    },

    /** api: method[addActions]
     */
    addActions: function() {
        this.activeIndex = 0;
        this.button = new Ext.SplitButton({
            iconCls: "gxp-icon-measure-length",
            text: "Measure",
            tooltip: this.measureTooltip,
            buttonText: this.buttonText,
            enableToggle: true,
            toggleGroup: this.toggleGroup,
            allowDepress: true,
            handler: function(button, event) {
                if(button.pressed) {
                    button.menu.items.itemAt(this.activeIndex).setChecked(true);
                }
            },
            scope: this,
            listeners: {
                toggle: function(button, pressed) {
                    // toggleGroup should handle this
                    if(!pressed) {
                        button.menu.items.each(function(i) {
                            i.setChecked(false);
                        });
                    }
                },
                render: function(button) {
                    // toggleGroup should handle this
                    Ext.ButtonToggleMgr.register(button);
                }
            },
            menu: new Ext.menu.Menu({
                items: [
                    new Ext.menu.CheckItem(
                        new GeoExt.Action({
                            text: this.lengthMenuText,
                            iconCls: "gxp-icon-measure-length",
                            toggleGroup: this.toggleGroup,
                            group: this.toggleGroup,
                            listeners: {
                                checkchange: function(item, checked) {
                                    this.activeIndex = 0;
                                    this.button.toggle(checked);
                                    if (checked) {
                                        this.button.setIconClass(item.iconCls);
                                    }
                                },
                                scope: this
                            },
                            map: this.target.mapPanel.map,
                            control: this.createMeasureControl(
                                OpenLayers.Handler.Path, this.lengthTooltip
                            )
                        })
                    ),
                    new Ext.menu.CheckItem(
                        new GeoExt.Action({
                            text: this.areaMenuText,
                            iconCls: "gxp-icon-measure-area",
                            toggleGroup: this.toggleGroup,
                            group: this.toggleGroup,
                            allowDepress: false,
                            listeners: {
                                checkchange: function(item, checked) {
                                    this.activeIndex = 1;
                                    this.button.toggle(checked);
                                    if (checked) {
                                        this.button.setIconClass(item.iconCls);
                                    }
                                },
                                scope: this
                            },
                            map: this.target.mapPanel.map,
                            control: this.createMeasureControl(
                                OpenLayers.Handler.Polygon, this.areaTooltip
                            )
                        })
                    )
                ]
            })
        });

        return gxp.plugins.Measure.superclass.addActions.apply(this, [this.button]);
    }

});

Ext.preg(gxp.plugins.Measure.prototype.ptype, gxp.plugins.Measure);
