/**
 * Copyright (c) 2008-2009 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */
Ext.namespace("GeoExt.ux");

/** api: (define)
 *  module = GeoExt.ux
 *  class = PrintPreview
 *  base_link = `Ext.Container <http://dev.sencha.com/deploy/dev/docs/?class=Ext.Container>`_
 */

/** api: constructor
 *  .. class:: PrintPreview
 * 
 *  A print preview with an interactive map. Requires a server-side print
 *  module configuration with two custom fields (by default ``mapTitle`` and
 *  ``comment``).
 */
GeoExt.ux.PrintPreview = Ext.extend(Ext.Container, {
    
    /* begin i18n */
    /** api: config[paperSizeText] ``String`` i18n */
    paperSizeText: "Paper size:",
    /** api: config[resolutionText] ``String`` i18n */
    resolutionText: "Resolution:",
    /** api: config[printText] ``String`` i18n */
    printText: "Print",
    /** api: config[emptyTitleText] ``String`` i18n */
    emptyTitleText: "Enter map title here.",
    /** api: config[includeLegendText] ``String`` i18n */
    includeLegendText: "Include legend?",
    /** api: config[emptyCommentText] ``String`` i18n */
    emptyCommentText: "Enter comments here.",
    /** api: config[creatingPdfText] ``String`` i18n */
    creatingPdfText: "Creating PDF...",
    /* end i18n */
    
    /** api: config[printProvider]
     *  :class:`GeoExt.data.PrintProvider`|``Object`` Instance or
     *  configuration for the PrintProvider that this dialog will use. Not
     *  required if provided with the
     *  :ref:`GeoExt.ux.PrintPreview.printMapPanel`.
     */
    
    /** private: property[printProvider]
     *  :class:`GeoExt.data.PrintProvider`
     */
    printProvider: null,
    
    /** api: config[sourceMap]
     *  :class:`GeoExt.MapPanel`|``OpenLayers.Map`` The map to copy layers and
     *  extent from for printing. Not required if provided with the
     *  :ref:`GeoExt.ux.PrintPreview.printMapPanel`.
     */

    /** private: property[sourceMap]
     *  ``OpenLayers.Map`` The map to copy layers and extent from for printing.
     */
    sourceMap: null,
    
    /** api: config[printMapPanel]
     *  :class:`GeoExt.PrintMapPanel`:``Object`` Optional. Useful e.g.
     *  for adding a ZoomSlider (via ``items``) or setting map options (like
     *  configuring custom controls or filtering out unsupported layers with
     *  a preaddlayer listener via ``map``).
     *  
     *  .. note:: If provided as :class:`GeoExt.PrintMapPanel`, this has to be
     *       configured with ``printProvider`` and ``sourceMap``.
     */
    
    /** api: property[printMapPanel]
     *  class:`GeoExt.PrintMapPanel` The print preview map. Read-only.
     */
    printMapPanel: null,
    
    /** api: config[mapTitleField]
     *  ``String`` The custom field of the print service for the map title
     */
    mapTitleField: "mapTitle",
    
    /** api: config[commentField]
     *  ``String`` The custom field of the print service for the comment
     */
    commentField: "comment",
    
    /** api: config[legend]
     *  ref:`GeoExt.LegendPanel` The legend to include. If not provided, the
     *  dialog won't have an option to include the legend.
     */
    legend: null,
    
    /** api: config[includeLegend]
     *  ``Boolean`` Initial status of the "Include legend?" checkbox. Will be
     *  ignored if :ref:`GeoExt.ux.PrintPreview.legend` is not provided.
     */
    includeLegend: false,
    
    /** api: config[mapTitle]
     *  ``String`` An optional title to set for the mapTitle field when
     *  creating the dialog.
     */
    mapTitle: null,
    
    /** api: config[comment]
     *  ``String`` An optional comment to set for the comment field when
     *  creating the dialog.
     */
    comment: null,
    
    /** api: config[addMapOverlay]
     *  ``Boolean`` Set to false if no map overlay with scale, scale selector
     *  and north arrow should be added. Default is true.
     */
    addMapOverlay: true,
    
    /** api: config[busyMask]
     *  ``Ext.LoadMask`` A LoadMask to use while the print document is
     *  prepared. Optional, will be auto-created with ``creatingPdfText` if
     *  not provided.
     */
    
    /** private: property[busyMask]
     *  ``Ext.LoadMask``
     */
    busyMask: null,

    /** private: property[form]
     *  ``Ext.form.FormPanel`` The form for this dialog.
     */
    form: null,
    
    /** private: property[autoEl]
     *  override
     */
    autoEl: "center",

    /** private: property[cls]
     *  override
     */
    cls: "x-panel-body x-panel-body-noheader",
    
    /** private: method[initComponent]
     */
    initComponent: function() {
        var printMapPanelOptions = {
            sourceMap: this.sourceMap,
            printProvider: this.printProvider
        };
        if(this.printMapPanel) {
            if(!(this.printMapPanel instanceof GeoExt.PrintMapPanel)) {
                printMapPanelOptions.xtype = "gx_printmappanel"
                this.printMapPanel = new GeoExt.PrintMapPanel(
                    Ext.applyIf(this.printMapPanel, printMapPanelOptions));
            }
        } else {
            this.printMapPanel = new GeoExt.PrintMapPanel(
                printMapPanelOptions);
        }
        this.sourceMap = this.printMapPanel.sourceMap;
        this.printProvider = this.printMapPanel.printProvider;
        
        this.form = this.createForm();

        if (!this.items) {
            this.items = [];
        }
        this.items.push(this.createToolbar(), {
            xtype: "container",
            cls: "gx-printpreview",
            autoHeight: this.autoHeight,
            autoWidth: this.autoWidth,
            items: [
                this.form,
                this.printMapPanel
            ]
        });

        GeoExt.ux.PrintPreview.superclass.initComponent.call(this);
        
        this.addMapOverlay && this.printMapPanel.add(this.createMapOverlay());

        this.printMapPanel.on({
            "resize": this.updateSize,
            scope: this
        });
        this.on({
            "render": function() {
                if (!this.busyMask) {
                    this.busyMask = new Ext.LoadMask(this.getEl(), {
                        msg: this.creatingPdfText
                    });
                }
                this.printProvider.on({
                    "beforeprint": this.busyMask.show,
                    "print": this.busyMask.hide,
                    "printexception": this.busyMask.hide,
                    scope: this.busyMask
                });
            },
            scope: this
        });
    },
    
    /** private: method[createToolbar]
     *  :return: ``Ext.Toolbar``
     */
    createToolbar: function() {
        var items = [];
        this.printProvider.layouts.getCount() > 1 && items.push(this.paperSizeText, {
            xtype: "combo",
            width: 98,
            plugins: new GeoExt.plugins.PrintProviderField({
                printProvider: this.printProvider
            }),
            store: this.printProvider.layouts,
            displayField: "name",
            typeAhead: true,
            mode: "local",
            forceSelection: true,
            triggerAction: "all",
            selectOnFocus: true
        }, "&nbsp;");
        this.printProvider.dpis.getCount() > 1 && items.push(this.resolutionText, {
            xtype: "combo",
            width: 62,
            plugins: new GeoExt.plugins.PrintProviderField({
                printProvider: this.printProvider
            }),
            store: this.printProvider.dpis,
            displayField: "name",
            tpl: '<tpl for="."><div class="x-combo-list-item">{name} dpi</div></tpl>',
            typeAhead: true,
            mode: "local",
            forceSelection: true,
            triggerAction: "all",
            selectOnFocus: true,
            setValue: function(v){
                v = parseInt(v) + " dpi";
                Ext.form.ComboBox.prototype.setValue.apply(this, arguments);
            }
        }, "&nbsp;");
        items.push("->", {
            text: this.printText,
            iconCls: "icon-print",
            handler: function(){
                this.printMapPanel.print(this.includeLegend &&
                    {legend: this.legend});
            },
            scope: this
        });
        return {
            xtype: "toolbar",
            items: items
        };
    },
    
    /** private: method[createForm]
     *  :return: ``Ext.form.FormPanel``
     */
    createForm: function() {
        var titleCfg = {
            xtype: "textfield",
            name: this.mapTitleField,
            value: this.mapTitle,
            emptyText: this.emptyTitleText,
            margins: "0 5 0 0",
            flex: 1,
            anchor: "100%",
            hideLabel: true,
            plugins: new GeoExt.plugins.PrintProviderField({
                printProvider: this.printProvider
            })
        };
        
        if(this.legend) {
            var legendCheckbox = new Ext.form.Checkbox({
                name: "legend",
                checked: this.includeLegend,
                boxLabel: this.includeLegendText,
                hideLabel: true,
                ctCls: "gx-item-nowrap",
                handler: function(cb, checked) {
                    this.includeLegend = checked;
                },
                scope: this
            });
        }
        
        return new Ext.form.FormPanel({
            autoHeight: true,
            border: false,
            defaults: {
                anchor: "100%"
            },
            items: [
                this.legend ? {
                    xtype: "container",
                    layout: "hbox",
                    cls: "x-form-item",
                    items: [
                        titleCfg,
                        legendCheckbox
                    ]
                } : titleCfg, {
                    xtype: "textarea",
                    name: this.commentField,
                    value: this.comment,
                    emptyText: this.emptyCommentText,
                    hideLabel: true,
                    plugins: new GeoExt.plugins.PrintProviderField({
                        printProvider: this.printProvider
                    })
                }
            ]
        });
    },

    /** private: method[createMapOverlay]
     *  :return: ``Ext.Panel``
     */
    createMapOverlay: function() {
        var scaleLine = new OpenLayers.Control.ScaleLine();
        this.printMapPanel.map.addControl(scaleLine);
        scaleLine.activate();
        return new Ext.Panel({
            cls: "gx-map-overlay",
            layout: "column",
            width: 235,
            bodyStyle: "padding:5px",
            items: [{
                xtype: "box",
                el: scaleLine.div,
                width: scaleLine.maxWidth
            }, {
                xtype: "container",
                layout: "form",
                style: "padding: .2em 5px 0 0;",
                columnWidth: 1,
                cls: "x-small-editor x-form-item",
                items: {
                    xtype: "combo",
                    name: "scale",
                    anchor: "100%",
                    hideLabel: true,
                    store: this.printMapPanel.previewScales,
                    displayField: "name",
                    typeAhead: true,
                    mode: "local",
                    forceSelection: true,
                    triggerAction: "all",
                    selectOnFocus: true,
                    getListParent: function() {
                        return this.el.up(".x-window") || document.body;
                    },
                    plugins: new GeoExt.plugins.PrintPageField({
                        printPage: this.printMapPanel.printPage
                    })
                }
            }, {
                xtype: "box",
                autoEl: {
                    tag: "div",
                    cls: "gx-northarrow"
                }
            }],
            listeners: {
                "render": function() {
                    function stop(evt){evt.stopPropagation();}
                    this.getEl().on({
                        "click": stop,
                        "dblclick": stop,
                        "mousedown": stop
                    });
                }
            }
        });
    },

    /** private: method[updateSize]
     *  sync the form's width with the map with, and make sure that the window
     *  shadow is updated if this dialog is added to an ``Ext.Window``
     */
    updateSize: function() {
        this.suspendEvents();
        var mapWidth = this.printMapPanel.getWidth();
        // sync form and toolbar width with map width
        this.form.setWidth(mapWidth);
        // the line with title and legend needs an extra invitation
        this.form.items.get(0).setWidth(mapWidth);
        var minWidth = this.initialConfig.minWidth || 0;
        this.items.get(0).setWidth(
            this.form.ownerCt.el.getPadding("lr") + Math.max(mapWidth, minWidth)
        );
        // shadow does not sync, so do it manually
        var parent = this.ownerCt;
        if (parent && parent instanceof Ext.Window) {
            this.ownerCt.syncShadow();
        }
        this.resumeEvents();
    },
    
    /** private: method[beforeDestroy]
     */
    beforeDestroy: function() {
        if (this.busyMask) {
            this.printProvider.un("beforeprint", this.busyMask.show, this.busyMask);
            this.printProvider.un("print", this.busyMask.hide, this.busyMask);
        }
        this.printMapPanel.un("resize", this.updateSize, this);
        GeoExt.ux.PrintPreview.superclass.beforeDestroy.apply(this, arguments);
    }
    
});

/** api: xtype = gxux_printpreview */
Ext.reg("gxux_printpreview", GeoExt.ux.PrintPreview);
