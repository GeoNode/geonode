/**
 * Copyright (c) 2008-2011 The Open Planning Project
 *
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 * @requires widgets/WMSStylesDialog.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = Styler
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: Styler(config)
 *
 *    Plugin providing a styles editing dialog for geoserver layers.
 */
gxp.plugins.Styler = Ext.extend(gxp.plugins.Tool, {

    /** api: ptype = gxp_styler */
    ptype: "gxp_styler",

    /** api: config[menuText]
     *  ``String``
     *  Text for layer properties menu item (i18n).
     */
    menuText: "Styles",

    /** api: config[tooltip]
     *  ``String``
     *  Text for layer properties action tooltip (i18n).
     */
    tooltip: "Manage layer styles",

    /** api: config[roles]
     *  ``Array`` Roles authorized to style layers. Default is
     *  ["ROLE_ADMINISTRATOR"]
     */
    roles: ["ROLE_ADMINISTRATOR"],

    /** api: config[sameOriginStyling]
     *  ``Boolean``
     *  Only allow editing of styles for layers whose sources have a URL that
     *  matches the origin of this applicaiton.  It is strongly discouraged to
     *  do styling through commonly used proxies as all authorization headers
     *  and cookies are shared with all remote sources.  Default is ``true``.
     */
    sameOriginStyling: true,

    /** api: config[rasterStyling]
     *  ``Boolean`` If set to true, single-band raster styling will be
     *  supported. Default is ``false``.
     */
    rasterStyling: false,

    /** api: config[requireDescribeLayer]
     *  ``Boolean`` If set to false, styling will be enabled for all WMS layers
     *  that have "/ows" or "/wms" at the end of their base url in case the WMS
     *  does not support DescribeLayer. Only set to false when rasterStyling is
     *  set to true. Default is true.
     */
    requireDescribeLayer: true,

    editable: false,

    constructor: function(config) {
        gxp.plugins.Styler.superclass.constructor.apply(this, arguments);

        if (!this.outputConfig) {
            this.outputConfig = {
                autoHeight: true,
                width: 335
            };
        }
        Ext.applyIf(this.outputConfig, {
            closeAction: "close"
        });
    },

    /** private: method[init]
     *  :arg target: ``Object`` The object initializing this plugin.
     */
    init: function(target) {
        gxp.plugins.Styler.superclass.init.apply(this, arguments);
        this.target.on("authorizationchange", this.enableOrDisable, this);
    },

    /** private: method[destroy]
     */
    destroy: function() {
        this.target.on("authorizationchange", this.enableOrDisable, this);
        gxp.plugins.Styler.superclass.destroy.apply(this, arguments);
    },

    /** private: method[enableOrDisable]
     *  Enable or disable the button when the login status changes.
     */
    enableOrDisable: function() {
        if (this.target && this.target.selectedLayer !== null) {
            this.handleLayerChange(this.target.selectedLayer);
        }
    },

    /** api: method[addActions]
     */
    addActions: function() {
        var layerProperties;
        var actions = gxp.plugins.Styler.superclass.addActions.apply(this, [{
            menuText: this.menuText,
            iconCls: "gxp-icon-palette",
            disabled: true,
            tooltip: this.tooltip,
            handler: function() {
                this.target.doAuthorized(this.roles, this.addOutput, this);
            },
            scope: this
        }]);

        this.launchAction = actions[0];
        this.target.on({
            layerselectionchange: this.handleLayerChange,
            scope: this
        });

        return actions;
    },

    /** private: method[handleLayerChange]
     *  :arg record: ``GeoExt.data.LayerRecord``
     *
     *  Handle changes to the target viewer's selected layer.
     */
    handleLayerChange: function(record) {
        this.launchAction.disable();
        if (record && record.get("styles")) {
            var source = this.target.getSource(record);
            if (source instanceof gxp.plugins.WMSSource) {
                source.describeLayer(record, function(describeRec) {
                    this.checkIfStyleable(record, describeRec);
                }, this);
            }
        }
    },

    /** private: method[checkIfStyleable]
     *  :arg layerRec: ``GeoExt.data.LayerRecord``
     *  :arg describeRec: ``Ext.data.Record`` Record from a
     *      `GeoExt.data.DescribeLayerStore``.
     *
     *  Given a layer record and the corresponding describe layer record,
     *  determine if the target layer can be styled.  If so, enable the launch
     *  action.
     */
    checkIfStyleable: function(layerRec, describeRec) {
        if (describeRec) {
            var owsTypes = ["WFS"];
            if (this.rasterStyling === true) {
                owsTypes.push("WCS");
            }
        }
        if (describeRec ? owsTypes.indexOf(describeRec.get("owsType")) !== -1 : !this.requireDescribeLayer) {
            var editableStyles = false;
            var source = this.target.layerSources[layerRec.get("source")];
            var url;
            // TODO: revisit this
            var restUrl = layerRec.get("restUrl");
            if (restUrl) {
                url = restUrl + "/styles";
            } else {
                url = source.url.split("?")
                    .shift().replace(/\/(wms|ows)\/?$/, "/rest/styles");
            }
            if (this.sameOriginStyling) {
                // this could be made more robust
                // for now, only style for sources with relative url
                //editableStyles = url.charAt(0) === "/";
                editableStyles = layerRec.get("local");
		// and assume that local sources are GeoServer instances with
                // styling capabilities
                if (editableStyles) {
                    this.enableEditingIfAuthorized(layerRec, url);
                    return;
                }
            } else {
                editableStyles = true;
                this.enableEditingIfAuthorized(layerRec, url);
            }
        }
    },

    /** private: method[enableActionIfAvailable]
     *  :arg url: ``String`` URL of style service
     *
     *  Enable the launch action if the service is available.
     */
    enableEditingIfAuthorized: function(layerRec, url) {
        Ext.Ajax.request({
            method: "PUT",
            url:"/data/" + layerRec.getLayer().params.LAYERS + "/ajax-edit-check",
            callback: function(options, success, response) {
                this.editable = (response.status == 200);
                this.launchAction.enable();
            },
            scope: this
        });

    },

    addOutput: function(config) {
        config = config || {};
        var record = this.target.selectedLayer;

        var origCfg = this.initialConfig.outputConfig || {};
        this.outputConfig.title = origCfg.title ||
            this.menuText + ": " + record.get("title");
        this.outputConfig.shortTitle = record.get("title");
        Ext.apply(config, gxp.WMSStylesDialog.createGeoServerStylerConfig(record));
        if (this.rasterStyling === true) {
            config.plugins.push({
                ptype: "gxp_wmsrasterstylesdialog",
                editable: this.editable
            });
        }
        Ext.applyIf(config, {style: "padding: 10px", editable: this.editable});

        var output = gxp.plugins.Styler.superclass.addOutput.call(this, config);
        if (!(output.ownerCt.ownerCt instanceof Ext.Window)) {
            output.dialogCls = Ext.Panel;
            output.showDlg = function(dlg) {
                dlg.layout = "fit";
                dlg.autoHeight = false;
                output.ownerCt.add(dlg);
            };
        }
        output.stylesStore.on("load", function() {
            if (!this.outputTarget && output.ownerCt.ownerCt instanceof Ext.Window) {
                output.ownerCt.ownerCt.center();
            }
        });
    }

});

Ext.preg(gxp.plugins.Styler.prototype.ptype, gxp.plugins.Styler);
