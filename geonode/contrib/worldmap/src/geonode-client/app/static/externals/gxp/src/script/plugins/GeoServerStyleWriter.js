/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires util.js
 * @requires plugins/StyleWriter.js
 */

Ext.namespace("gxp.plugins");

/** api: (define)
 *  module = gxp.plugins
 *  class = GeoServerStyleWriter
 */

/** api: (extends)
 *  plugins/StyleWriter.js
 */

/** api: constructor
 *  .. class:: GeoServerStyleWriter(config)
 *
 *      Save styles from :class:`gxp.WMSStylesDialog` or similar classes that
 *      have a ``layerRecord`` and a ``stylesStore`` with a ``userStyle``
 *      field. The plugin provides a save method, which will use the GeoServer
 *      RESTConfig API to persist style changes from the ``stylesStore`` to the
 *      server and associate them with the layer referenced in the target's
 *      ``layerRecord``.
 */
gxp.plugins.GeoServerStyleWriter = Ext.extend(gxp.plugins.StyleWriter, {

    /** api: config[baseUrl]
     *  ``String``
     *  The base url for the GeoServer REST API. Default is "/geoserver/rest".
     */
    baseUrl: "/geoserver/rest",

    /** private: method[constructor]
     */
    constructor: function(config) {
        this.initialConfig = config;
        Ext.apply(this, config);

        gxp.plugins.GeoServerStyleWriter.superclass.constructor.apply(this, arguments);
    },

    /** api: method[write]
     *  :arg options: ``Object``
     *
     *  Saves the styles of the target's ``layerRecord`` using GeoServer's
     *  RESTconfig API.
     *
     *  Supported options:
     *
     *  * defaultStyle - ``String`` If set, the default style will be set.
     *  * success - ``Function`` A function to call when all styles were
     *    written successfully.
     *  * scope - ``Object`` A scope to call the ``success`` function with.
     */
    write: function(options) {
        options = options || {};
        var dispatchQueue = [];
        var store = this.target.stylesStore;
        store.each(function(rec) {
            (rec.phantom || store.modified.indexOf(rec) !== -1) &&
                this.writeStyle(rec, dispatchQueue);
        }, this);
        var success = function() {
            // we don't need any callbacks for deleting styles.
            this.deleteStyles();
            var modified = this.target.stylesStore.getModifiedRecords();
            for (var i=modified.length-1; i>=0; --i) {
                // mark saved
                modified[i].phantom = false;
            }
            var target = this.target;
            target.stylesStore.commitChanges();
            options.success && options.success.call(options.scope);
            target.fireEvent("saved", target, target.selectedStyle.get("name"));
        };
        if(dispatchQueue.length > 0) {
            gxp.util.dispatch(dispatchQueue, function() {
                this.assignStyles(options.defaultStyle, success);
            }, this);
        } else {
            this.assignStyles(options.defaultStyle, success);
        }
    },

    /** private: method[writeStyle]
     *  :arg styleRec: ``Ext.data.Record`` the record from the target's
     *      ``stylesStore`` to write
     *  :arg dispatchQueue: ``Array(Function)`` the dispatch queue the write
     *      function is added to.
     *
     *  This method does not actually write styles, it just adds a function to
     *  the provided ``dispatchQueue`` that will do so.
     */
    writeStyle: function(styleRec, dispatchQueue) {
        var styleName = styleRec.get("userStyle").name;
        dispatchQueue.push(function(callback, storage) {
            Ext.Ajax.request({
                method: styleRec.phantom === true ? "POST" : "PUT",
                url: this.baseUrl + "/styles" + (styleRec.phantom === true ?
                    "" : "/" + styleName + ".xml"),
                headers: {
                    "Content-Type": "application/vnd.ogc.sld+xml; charset=UTF-8"
                },
                xmlData: this.target.createSLD({
                    userStyles: [styleName]
                }),
                success: styleRec.phantom === true ? function(){
                    Ext.Ajax.request({
                        method: "POST",
                        url: this.baseUrl + "/layers/" +
                            this.target.layerRecord.get("name") + "/styles.json",
                        jsonData: {
                            "style": {
                                "name": styleName
                            }
                        },
                        success: callback,
                        scope: this
                    });
                } : callback,
                scope: this
            });
        });
    },

    /** private: method[assignStyles]
     *  :arg defaultStyle: ``String`` The default style. Optional.
     *  :arg callback: ``Function`` The function to call when all operations
     *      succeeded. Will be called in the scope of this instance. Optional.
     */
    assignStyles: function(defaultStyle, callback) {
        var styles = [];
        this.target.stylesStore.each(function(rec) {
            if (!defaultStyle && rec.get("userStyle").isDefault === true) {
                defaultStyle = rec.get("name");
            }
            if (rec.get("name") !== defaultStyle &&
                                this.deletedStyles.indexOf(rec.id) === -1) {
                styles.push({"name": rec.get("name")});
            }
        }, this);
        Ext.Ajax.request({
            method: "PUT",
            url: this.baseUrl + "/layers/" +
                this.target.layerRecord.get("name") + ".json",
            jsonData: {
                "layer": {
                    "defaultStyle": {
                        "name": defaultStyle
                    },
                    "styles": styles.length > 0 ? {
                        "style": styles
                    } : {},
                    "enabled": true
                }
            },
            success: callback,
            scope: this
        });
    },

    /** private: method[deleteStyles]
     *  Deletes styles that are no longer assigned to the layer.
     */
    deleteStyles: function() {

        //Get rid of layers in deleteStyles that are also in the main datastore
        //How did they get there in the first place? Don't know yet.
        var store = this.target.stylesStore;
        var deletedStyles = this.deletedStyles;
        store.each(function(rec) {
            delRec = deletedStyles.indexOf(rec.data.name);
            if (delRec > -1)
            {
                deletedStyles.splice(delRec,1);
            }
        });


        for (var i=0, len=this.deletedStyles.length; i<len; ++i) {
            Ext.Ajax.request({
                method: "DELETE",
                url: this.baseUrl + "/styles/" + this.deletedStyles[i] +
                    // cannot use params for DELETE requests without jsonData
                    "?purge=true"
            });
        }
        this.deletedStyles = [];
    }

});

/** api: ptype = gxp_geoserverstylewriter */
Ext.preg("gxp_geoserverstylewriter", gxp.plugins.GeoServerStyleWriter);
