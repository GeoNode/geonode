/**
 * Copyright (c) 2008-2012 The Open Source Geospatial Foundation
 * 
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = GeoExt
 *  class = LegendImage
 *  base_link = `Ext.BoxComponent <http://dev.sencha.com/deploy/dev/docs/?class=Ext.BoxComponent>`_
 */

Ext.namespace('GeoExt');

/** api: constructor
 *  .. class:: LegendImage(config)
 *
 *      Show a legend image in a BoxComponent and make sure load errors are 
 *      dealt with.
 */
GeoExt.LegendImage = Ext.extend(Ext.BoxComponent, {

    /** api: config[url]
     *  ``String``  The url of the image to load
     */
    url: null,
    
    /** api: config[defaultImgSrc]
     *  ``String`` Path to image that will be used if the legend image fails
     *  to load.  Default is Ext.BLANK_IMAGE_URL.
     */
    defaultImgSrc: null,

    /** api: config[imgCls]
     *  ``String``  Optional css class to apply to img tag
     */
    imgCls: null,
    
    /** private: config[noImgCls]
     *  ``String`` CSS class applied to img tag when no image is available or
     *  the default image was loaded.
     */
    noImgCls: "gx-legend-noimage",
    
    /** private: method[initComponent]
     *  Initializes the legend image component. 
     */
    initComponent: function() {
        GeoExt.LegendImage.superclass.initComponent.call(this);
        if(this.defaultImgSrc === null) {
            this.defaultImgSrc = Ext.BLANK_IMAGE_URL;
        }
        this.autoEl = {
            tag: "img",
            "class": (this.imgCls ? this.imgCls + " " + this.noImgCls : this.noImgCls),
            src: this.defaultImgSrc
        };
    },

    /** api: method[setUrl]
     *  :param url: ``String`` The new URL.
     *  
     *  Sets the url of the legend image.
     */
    setUrl: function(url) {
        this.url = url;
        var el = this.getEl();
        if (el) {
            el.un("load", this.onImageLoad, this);
            el.on("load", this.onImageLoad, this, {single: true});
            el.un("error", this.onImageLoadError, this);
            el.on("error", this.onImageLoadError, this, {single: true});
            el.dom.src = url;
        }
    },

    /** private: method[onRender]
     *  Private method called when the legend image component is being
     *  rendered.
     */
    onRender: function(ct, position) {
        GeoExt.LegendImage.superclass.onRender.call(this, ct, position);
        if(this.url) {
            this.setUrl(this.url);
        }
    },

    /** private: method[onDestroy]
     *  Private method called during the destroy sequence.
     */
    onDestroy: function() {
        var el = this.getEl();
        if(el) {
            el.un("load", this.onImageLoad, this);
            el.un("error", this.onImageLoadError, this);
        }
        GeoExt.LegendImage.superclass.onDestroy.apply(this, arguments);
    },
    
    /** private: method[onImageLoadError]
     *  Private method called if the legend image fails loading.
     */
    onImageLoadError: function() {
        var el = this.getEl();
        el.addClass(this.noImgCls);
        el.dom.src = this.defaultImgSrc;
    },
    
    /** private: method[onImageLoad]
     *  Private method called after the legend image finished loading.
     */
    onImageLoad: function() {
        var el = this.getEl();
        if (!OpenLayers.Util.isEquivalentUrl(el.dom.src, this.defaultImgSrc)) {
            el.removeClass(this.noImgCls);
        }
    }

});

/** api: xtype = gx_legendimage */
Ext.reg('gx_legendimage', GeoExt.LegendImage);
