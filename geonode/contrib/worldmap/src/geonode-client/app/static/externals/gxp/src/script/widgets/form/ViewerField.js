/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp.form
 *  class = ViewerField
 *  base_link = `Ext.form.Field <http://extjs.com/deploy/dev/docs/?class=Ext.form.TextArea>`_
 */
Ext.namespace("gxp.form");

/** api: constructor
 *  .. class:: ViewerField(config)
 *   
 *    A form field that holds an entire :class:`gxp.Viewer`. This field is used
 *    to process geospatial information in forms. By itself, this field does
 *    nothing but showing a map viewer in a form element, aligned with field
 *    label and suited for an ``Ext.layouts.FormLayout``.
 *
 *    To actually have this field's textarea populated with information, a
 *    plugin accessing the additional ``field`` property that this component
 *    adds to its :class:`gxp.Viewer` instance is required.
 *    See :class:`gxp.plugins.FeatureToField` for a basic plugin that does
 *    this.
 */
gxp.form.ViewerField = Ext.extend(Ext.form.TextArea, {

    /** api: config[width]
     *  ``Number`` Width of the map viewer. Default is 350.
     */
    
    /** api: config[height]
     *  ``Number`` Height of the map viewer. Default is 220.
     */
    
    /** api: config[viewer]
     *  ``Object`` Configuration passed to the :class:`gxp.Viewer` constructor.
     *  The ``portalConfig`` will be extended to make sure that the portal is
     *  rendered into this field.
     */

    /** api: property[viewer]
     *  :class:`gxp.Viewer` The viewer wrapped by this field. This component
     *  adds an additional ``field`` (``Ext.form.TextArea``) property to the
     *  viewer, which is to be populated by a viewer plugin to actually give
     *  this field a value.
     */
    viewer: null,

    /** private: method[initComponent]
     *  Override
     */
    initComponent: function() {
        this.width = this.width || 350;
        this.height = this.height || 220;
        gxp.form.ViewerField.superclass.initComponent.call(this);
    },
    
    /** private: method[onRender]
     *  Override
     */
    onRender: function() {
        if(!this.el){
            this.defaultAutoCreate = {
                tag: "textarea",
                style: {
                    color: "transparent",
                    background: "none"
                }
            };
        }
        gxp.form.ViewerField.superclass.onRender.apply(this, arguments);
        
        this.viewerEl = Ext.get(document.createElement("div"));
        this.viewerEl.setStyle("position", "absolute");
        // keep focussed while working with the map viewer
        this.viewerEl.on({
            "mouseenter": function() {
                this.hasFocus || this.el.focus();
            },
            "mousemove": function() {
                this.hasFocus || this.el.focus();
            },
            "mouseleave": function() {
                this.hasFocus && this.el.blur();
            },
            scope: this
        });
        this.el.dom.parentNode.appendChild(this.viewerEl.dom);
        // align the viewer with the textarea and keep it anchored
        this.viewerEl.anchorTo(this.el, "tl-tl");
        
        var portalConfig = {
            border: false,
            renderTo: this.viewerEl,
            width: this.width,
            height: this.height,
            // transparent border so we can see the textarea's border, which
            // indicates focus
            style: "border: 1px solid transparent"
        };
        var config = Ext.applyIf(this.initialConfig.viewer || {}, {
            field: this,
            portalConfig: portalConfig
        });
        Ext.apply(config.portalConfig, portalConfig);
        this.viewer = new gxp.Viewer(config);
    }
    
});

Ext.reg("gxp_viewerfield", gxp.form.ViewerField);
