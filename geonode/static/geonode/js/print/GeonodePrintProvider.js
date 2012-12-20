/**
 * Copyright (c) 2008-2012 OpenPlans
 *
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/**
 * @requires GeoExplorer/TemplateStore.js
 */

/** api: (define)
 *  module = GeoExplorer
 *  class = GeoNodePrintProvider
 */
Ext.namespace("GeoExplorer");

GeoExplorer.GeonodePrintProvider = Ext.extend(Ext.util.Observable, {
    /** api: config[printService]
     *  ``String``
     *  URL of the GeoNode print service.
     *  Defaults to 'printing/print/'
     */
    printService: '/printing/preview',
    //'/printing/print/',
    /** api: config[templateService]
     *  ``String``
     *  URL of the GeoNode print template source.
     *  Do NOT include a trailing slash
     *  Defaults to 'printing/templates'
     */
    templateService: '/printing/templates',

    /** api: config[previewService]
     *  ``String``
     *  URL of the GeoNode print preview service.
     *  Defaults to 'printing/preview/'
     */
    previewService: '/printing/preview/',

    pageUnits: 'mm',

    pageSize: 'A4',

    pageOrientation: 'landscape',

    pageMargins: null,

    activeTemplate: null,

    templates: null,

    legend: null,

    constructor: function(config) {
        this.initialConfig = config;
        Ext.apply(this, config);

        if(!this.customParams) {
            this.customParams = {};
        }

        this.addEvents(
            /** api: event[loadtemplates]
             *  Triggered when the template store has finished loading.
             *
             *  Listener arguments:
             *
             *  * printProvider - :class:`GeoExplorer.GeonodePrintProvider` this
             *    PrintProvider
             *  * templates - ``Array[Ext.data.Record]`` the cache of template records
             */
            "loadtemplates",

            /** api: event[optionschange]
             *  Triggered when the print options are changed.
             *  Only triggered when using `setOptions` or other accessor method. Will
             *  NOT be triggered if you directly modify an option attribute
             *
             *  Listener arguments:
             *
             *  * printProvider - :class:`GeoExplorer.GeonodePrintProvider` this
             *    PrintProvider
             *  * option - ``Object`` the modified print option key:value pairs
             */
            "optionschange",

            /** api: event[beforeprint]
             *  Triggered when the print method is called.
             *
             *  Listener arguments:
             *
             *  * printProvider - :class:`GeoExplorer.GeonodePrintProvider` this
             *    PrintProvider
             *  * map - ``OpenLayers.Map`` the map being printed
             *  * options - ``Object`` the options to the print command
             */
            "beforeprint",

            /** api: event[printexception]
             *  Triggered when when the print
             *  backend returns an exception.
             *
             *  Listener arguments:
             *
             *  * printProvider - :class:`GeoExplorer.GeonodePrintProvider` this
             *    PrintProvider
             *  * response - ``Object`` the response object of the XHR
             */
            "printexception",

            /** api: events[beforedownload]
             *  Triggered before the PDF is downloaded. By returning false from
             *  a listener, the default handling of the PDF can be cancelled
             *  and applications can take control over downloading the PDF.
             *  TODO: rename to beforeprint after the current beforeprint event
             *  has been renamed to beforeencode.
             *
             *  Listener arguments:
             *  * printProvider - :class:`GeoExplorer.GeonodePrintProvider` this
             *    PrintProvider
             *  * url - ``String`` the url of the print document
             */
            "beforedownload"

        );

        GeoExplorer.GeonodePrintProvider.superclass.constructor.apply(this, arguments);

        if(this.templateService && this.initialConfig.autoLoad !== false) {
            this.loadTemplates();
        }
    },

    print: function(map, options) {
        var self = this,
            printCb = this.download.createDelegate(this);

        if (options) {
            printCb = options.callback || options.success || printCb;
            delete options.callback;
            delete options.success;
            this.setOptions(options);
        } else {
            options = {};
        }
        if(this.fireEvent('beforeprint', this, map, options) !== false) {
            var legend_html = undefined;
            if (options.includeLegend) {
                if (this.legend) {
                    legend_html = '';
                    if (this.legend.ptype === "gxp_layermanager") {
                        var output = this.legend.output;
                        output[0].getRootNode().cascade(function(node) {
                            if (node.component && !node.component.hidden) {
                                var cmp = node.component;
                                legend_html += '<div>' + cmp.layerRecord.get('title') + '</div>';
                                legend_html += '<div>' + cmp.items.get(1).url + '</div>';
                            }
                        });
                    } else if (this.legend.ptype === "gxp_legend") {
                        // TODO: this is not ideal, it requires someone to open up
                        // the legend before printing with include legend
                        var lp = this.legend.getLegendPanel();
                        if (lp && lp.items) {
                            lp.items.each(function(cmp) {
                                if(!cmp.hidden) {
                                    legend_html += '<div>' + cmp.layerRecord.get('title') + '</div>';
                                    legend_html += '<div>' + cmp.items.get(1).url + '</div>'; 
                                }
                            });
                        }
                    }
                }
            }
            var mapId = options.mapId,
                rulesTxt = this.buildPageStyle() + this.buildStylesText(),
                styleEl = Ext.DomHelper.createDom({
                    tag: 'style',
                    type: 'text/css',
                    cn: rulesTxt
                }),
                mapEl = (map.getEl) ? map.getEl() : map;

            Ext.Ajax.request({
                url: this.printService + this.activeTemplate.id + '/' + mapId,
                success: function (response) {
                    var url = Ext.decode(response.responseText).getURL;
                    printCb(response, url);
                },
                failure: function (response) {
                    this.fireEvent("printexception", this, response);
                },
                method: 'POST',
                params: {
                    styles: styleEl.outerHTML,
                    map_html: mapEl.dom.outerHTML,
                    legend_html: legend_html,
                    width: options.width ? options.width : mapEl.getWidth() || undefined,
                    height: options.height ? options.height : mapEl.getHeight() || undefined
                },
                scope: this
            });
        }

    },

    download: function(resp, url){

        if(this.fireEvent('beforedownload', this, url) !== false) {
            //Requires user to un-block popups for this site to work properly

            // FIX ME The GeoServer url is hard coded here
            window.open('http://localhost:8080' + url);
        }
    },

    loadTemplates: function() {
        this.templates = new GeoExplorer.TemplateStore({
            url: this.templateService,
            listeners: {
                load: function(store, recs) {
                    this.fireEvent('loadtemplates', this, recs);
                    this.activeTemplate = this.templates.getAt(1);
                },
                scope: this
            }
        });
        this.templates.load();
    },
    setOptions: function(options) {
        Ext.apply(this, options);
        this.fireEvent('optionschange', this, Ext.apply({}, options));
    },
    buildStylesText: function() {
        var rulesTxt = '';
        /*Ext.iterate(Ext.util.CSS.getRules(), function(k, v) {
            rulesTxt += ' ' + v.cssText;
        });*/
        return rulesTxt;
    },
    buildPageStyle: function(options) {
        if(options) {
            this.setOptions(options);
        }
        var units = this.pageUnits;
        var size = this.pageSize;
        var orientation = this.pageOrientation;
        var margins = this.pageMargins;
        if(Ext.isArray(size)) {
            size = '' + size[0] + units + ' ' + size[1] + units;
        }
        if(Ext.isArray(margins)) {
            for(var mtxt = '', i = margins.length - 1; i >= 0; i--) {
                if(Ext.isString(margins[i])) {
                    mtxt += margins[i] + ' ';
                } else {
                    mtxt += margins[i] + units + ' ';
                }
            }
            margins = mtxt;
        }
        var pageStyle = '@page{ size:' + size + /*' ' + orientation +*/ '; ';
        pageStyle += 'fit: meet; fit-position: center; page-break-after: avoid; page-break-inside: avoid; ';
        if(margins) {
            pageStyle += 'margins: ' + margins + '; ';
        }
        pageStyle += ' }';
        return pageStyle;
    }
});
