/**
 * Created by sdsl on 11/3/16.
 */
/** FILE: plugins/Legend.js **/
/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @requires GeoExt/widgets/LegendPanel.js
 * @requires GeoExt/widgets/WMSLegend.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = Legend
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: Legend(config)
 *
 *    Provides an action to display a legend in a new window.
 */
gxp.plugins.Legend = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_legend */
    ptype: "gxp_legend",

    /** api: config[menuText]
     *  ``String``
     *  Text for legend menu item (i18n).
     */
    menuText: "Legend",

    /** api: config[tooltip]
     *  ``String``
     *  Text for legend action tooltip (i18n).
     */
    tooltip: "Show Legend",

    /** api: config[actionTarget]
     *  ``Object`` or ``String`` or ``Array`` Where to place the tool's actions
     *  (e.g. buttons or menus)? Use null as the default since our tool has both
     *  output and action(s).
     */
    actionTarget: null,

    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.plugins.Legend.superclass.constructor.apply(this, arguments);

        if (!this.outputConfig) {
            this.outputConfig = {
                id: 'gxp-sdsl-legend',
                width: 300,
                height: 200,
                align: 'r'
            };
        }
        Ext.applyIf(this.outputConfig, {title: this.menuText});
    },

    /** api: method[addActions]
     */
    addActions: function() {
        var actions = [{
            menuText: this.menuText,
            iconCls: "gxp-icon-legend",
            tooltip: this.tooltip,
            handler: function() {
                this.removeOutput();
                this.addOutput(this.outputConfig);
            },
            scope: this
        }];
        return gxp.plugins.Legend.superclass.addActions.apply(this, [actions]);
    },

    /** api: method[getLegendPanel]
     *  :returns: ``GeoExt.LegendPanel``
     *
     *  Get the legend panel associated with this legend plugin.
     */
    getLegendPanel: function() {
        return this.output[0];
    },

    /** private: method[addOutput]
     *  :arg config: ``Object``
     */
    addOutput: function(config) {
        //console.log(legend_clolor_str || 'legend_clolor_str');
        
        if(legend_clolor_str != undefined && legend_clolor_str != null && legend_clolor_str != ''){
            this.addChartLegend(legend_clolor_str);
        }
        
        var output = gxp.plugins.Legend.superclass.addOutput.call(this, Ext.apply({
            xtype: 'gx_legendpanel',
            ascending: false,
            border: false,
            hideMode: "offsets",
            layerStore: this.target.mapPanel.layers,
            defaults: {
                cls: 'gxp-legend-item',
                baseParams: {
                    FORMAT: 'image/png',
                    LEGEND_OPTIONS: 'forceLabels:on'
                 }
            }
        }, config));
        output.ownerCt.ownerCt.alignTo(Ext.getBody(), "tr-tr", [-20, 95]);

        /*if (!(output.ownerCt.ownerCt instanceof Ext.Window)) {
            output.dialogCls = Ext.Panel;
            output.showDlg = function(dlg) {
                dlg.layout = "fit";
                dlg.autoHeight = false;
                output.ownerCt.add(dlg);
            };
        }
        output.stylesStore.on("load", function() {
            if (!this.outputTarget && output.ownerCt.ownerCt instanceof Ext.Window) {
                //output.ownerCt.ownerCt.center();
                output.ownerCt.ownerCt.alignTo(Ext.getBody(), "tr-tr", [-20, 95]);
            }
        });

        return gxp.plugins.Legend.superclass.addOutput.call(this, Ext.apply({
            xtype: 'gx_legendpanel',
            ascending: false,
            border: false,
            hideMode: "offsets",
            layerStore: this.target.mapPanel.layers,
            defaults: {cls: 'gxp-legend-item'}
        }, config));*/
    },
    addChartLegend: function (uri) {
        //console.log(uri);
        uri = uri.trim();
        uri = uri.replaceAll('&amp;', '&');
        if (uri !== '') {
            var chartLegend = '';
            var colors = getUriParameterByName('chco', uri);
            var labels = getUriParameterByName('label', uri);
            //console.log(colors,labels);
            if (colors !== undefined && colors !== '' && labels !== null && labels !== undefined && labels !== '') {
                //console.log(colors, labels);
                var colorList = colors.split(',');
                var labelList = labels.split('|');
                //console.log(colorList,labelList);
                //console.log(colorList.length, labelList.length);
                if (colorList.length == labelList.length) {
                    for (var i = 0; i < colorList.length; i++) {
                        chartLegend += '<div style="margin-bottom:5px;"><span style="background: #' + colorList[i] + '; height:5px;width:5px;margin-right: 5px; padding: 0 10px;"></span><span>' + labelList[i] + '</span></div>';
                    }
                }
            }
            //console.log(chartLegend);
            setTimeout(function(){
                $('#chart-legend-holder').html(chartLegend);
                $('#gxp-sdsl-legend .x-panel-bwrap .gxp-legend-item').append(chartLegend);
            }, 500);
            
        }
    },
    getUriParameterByName: function (name, url) {
        if (!url) {
            return '';
        }
        name = name.replace(/[\[\]]/g, "\\$&");
        var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
                results = regex.exec(url);
        if (!results)
            return null;
        if (!results[2])
            return '';
        return decodeURIComponent(results[2].replace(/\+/g, " "));
    }
});

Ext.preg(gxp.plugins.Legend.prototype.ptype, gxp.plugins.Legend);
