/**
 * Copyright (c) 2008-2012 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires widgets/tree/SymbolizerLoader.js
 * @requires GeoExt/widgets/FeatureRenderer.js
 */

/** api: (define)
 *  module = gxp.grid
 *  class = SymbolizerGrid
 */
Ext.namespace("gxp.grid");

/** api: constructor
 *  .. class:: SymbolizerGrid(config)
 *
 *      Create a new grid displaying the symbolizers of a style and its subtypes.
 */
gxp.grid.SymbolizerGrid = Ext.ux && Ext.ux.tree && Ext.ux.tree.TreeGrid && Ext.extend(Ext.ux.tree.TreeGrid, {

    /** api: config[symbolizers]
     *  ``Array`` Array of OpenLayers symbolizer objects which will be
     *  displayed by the grid.
     */
    symbolizers: null,

    /** private overrides */
    enableHdMenu: false,
    enableSort: false,
    useArrows: false,
    columnResize: false,
    cls: "gxp-symbolgrid",

    /** i18n */
    typeTitle: "Symbolizer Type",
    previewTitle: "Preview",

    /** api: method[initComponent]
     *  Initializes the SymbolizerGrid.
     */
    initComponent: function() {
        this.on('checkchange', this.onCheckChange, this);
        this.loader = new gxp.tree.SymbolizerLoader({
            symbolizers: this.symbolizers
        });
        this.columns = [{
            header: this.typeTitle,
            dataIndex: 'type',
            width: 200
        }, {
            header: this.previewTitle,
            width: 100,
            dataIndex: 'preview'
        }];
        gxp.grid.SymbolizerGrid.superclass.initComponent.call(this);
    },

    /** api: method[getSymbolizers]
     *  :returns: ``Array`` Array of symbolizers.
     *
     *  Get the current state of the symbolizers array. Symbolizers who don't
     *  have any visible children will be filtered out.
     */
    getSymbolizers: function() {
        var symbolizers = [];
        this.root.eachChild(function(n){
            var childVisible = false;
            n.eachChild(function(c) {
                var type = c.attributes.type.toLowerCase();
                if (type !== "label") {
                    n.attributes.originalSymbolizer[type] = c.attributes.checked;
                }
                if (c.attributes.checked === true) {
                    childVisible = true;
                }
            });
            if (childVisible) {
                symbolizers.push(n.attributes.originalSymbolizer);
            }
        });
        return symbolizers;
    },

    /** private: method[beforeDestroy]
     *  Clean up.
     */
    beforeDestroy : function(){
        this.root.cascade(function(node) {
            if (node.attributes.featureRenderer) {
                node.attributes.featureRenderer.destroy();
                node.attributes.featureRenderer = null;
            }
        });
        gxp.grid.SymbolizerGrid.superclass.onDestroy.call(this);
    },

    /** private: method[onCheckChange]
     *  :arg node: ``Ext.data.Node``
     *  :arg checked: ``Boolean``
     *
     *  Handle the check change event. Update the symbolizers and their
     *  swatches.
     */
    onCheckChange: function(node, checked) {
        var a = node.attributes;
        var r = a.featureRenderer;
        var type = a.type.toLowerCase();
        var symbolizer = a.symbolizer;
        var fullSymbolizer = node.parentNode.attributes.symbolizer;
        if (type !== "label") {
            // special handling for graphic, can only be turned on if label is on
            if (type === 'graphic') {
                var label = node.parentNode.findChild('type', 'Label');
                if (label !== null) {
                    var labelChecked = label.attributes.checked;
                    if ((labelChecked && checked) || !checked) {
                        fullSymbolizer[type] = symbolizer[type] = checked;
                    } else {
                        node.getUI().toggleCheck(false);
                    }
                }
            } else {
                fullSymbolizer[type] = symbolizer[type] = checked;
            }
        } else {
            if (!checked) {
                symbolizer[type] = fullSymbolizer[type] = "";
                var graphic = node.parentNode.findChild('type', 'Graphic');
                if (graphic !== null) {
                    graphic.getUI().toggleCheck(false);
                }
            } else {
                symbolizer[type] = fullSymbolizer[type] = "Ab";
            }
        }
        if (node.parentNode.attributes.featureRenderer) {
            node.parentNode.attributes.featureRenderer.update({
                symbolizers: [fullSymbolizer]
            });
        }
        r.update({symbolizers: [symbolizer]});
    },

    /** private: method[afterRender]
     *  Create the swatches.
     */
    afterRender: function() {
        gxp.grid.SymbolizerGrid.superclass.afterRender.call(this);
        this.root.cascade(function(node) {
            if (node.attributes.rendererId) {
                var ct = Ext.get(node.attributes.rendererId);
                if (ct) {
                    node.attributes.featureRenderer = new GeoExt.FeatureRenderer({
                        symbolizers: [node.attributes.symbolizer],
                        renderTo: ct, 
                        width:21, 
                        height: 21
                    });
                }
            }
        });
    }

});

/** api: xtype = gxp_symbolgrid */
gxp.grid.SymbolizerGrid && Ext.reg('gxp_symbolgrid', gxp.grid.SymbolizerGrid);
