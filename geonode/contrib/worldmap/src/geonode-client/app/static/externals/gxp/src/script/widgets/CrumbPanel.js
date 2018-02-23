/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

Ext.namespace("gxp");

/** api: (define)
 *  module = gxp
 *  class = CrumbPanel
 *  base_link = `Ext.TabPanel <http://extjs.com/deploy/dev/docs/?class=Ext.TabPanel>`_
 */

/** api: constructor
 *  .. class:: CrumbPanel(config)
 *
 *    Panel that accommodates modal dialogs and displays their hierarchy as
 *    crumbs in tabs, from left to right. Clicking on a crumb left of the
 *    rightmost one will close all dialogs that are hosted in tabs on its
 *    right.
 *
 *    If a component has a ``shortTitle`` configured, it will be used instead
 *    of the ``title`` in the crumb path.
 *
 *    Components intended to be reused after being removed from this panel need
 *    the closeAction option set to "hide", like an ``Ext.Window``. 
 */   
gxp.CrumbPanel = Ext.extend(Ext.TabPanel, {
    
    /** private: property[widths]
     *  {Object} widths of the panel's items, keyed by item id, so they can be
     *  restored after closing an item that required a wider container. 
     */
    widths: null,
    
    enableTabScroll: true,
    
    /** private: method[initComponent]
     */
    initComponent: function() {
        gxp.CrumbPanel.superclass.initComponent.apply(this, arguments);
        this.widths = {};
    },
    
    /** private: method[onBeforeAdd]
     *  :arg cmp: ``Ext.Component``
     */
    onBeforeAdd: function(cmp) {
        gxp.CrumbPanel.superclass.onBeforeAdd.apply(this, arguments);
        if (cmp.shortTitle) {
            cmp.title = cmp.shortTitle;
        }
    },
    
    /** private: method[onAdd]
     *  :arg cmp: ``Ext.Component``
     */
    onAdd: function(cmp) {
        gxp.CrumbPanel.superclass.onAdd.apply(this, arguments);
        this.setActiveTab(this.items.getCount() - 1);
        cmp.on("hide", this.onCmpHide, this);
        //TODO investigate why hidden components are displayed again when
        // another crumb is activated - this just works around the issue
        cmp.getEl().dom.style.display = "";
    },
    
    /** private: method[onRemove]
     *  :arg cmp: ``Ext.Component``
     */
    onRemove: function(cmp) {
        gxp.CrumbPanel.superclass.onRemove.apply(this, arguments);
        cmp.un("hide", this.onCmpHide, this);
        var previousWidth = this.widths[this.get(this.items.getCount()-1).id];
        if (previousWidth && previousWidth < this.getWidth()) {
            this.setWidth(previousWidth);
            if (this.ownerCt) {
                this.ownerCt.syncSize();
            }
        }
        //TODO investigate why hidden components are displayed again when
        // another crumb is activated - this just works around the issue
        cmp.getEl().dom.style.display = "none";
    },
    
    /** private: method[onRender]
     *  :arg cmp: ``Ext.Component``
     */
    onRender: function(cmp) {
        if (!this.initialConfig.itemTpl) {
            this.itemTpl = new Ext.Template(
                 '<li class="{cls} gxp-crumb" id="{id}"><div class="gxp-crumb-separator">\u00BB</div>',
                 '<a class="x-tab-right" href="#"><em class="x-tab-left">',
                 '<span class="x-tab-strip-inner"><span class="x-tab-strip-text {iconCls}">{text}</span></span></span>',
                 '</em></a></li>'
            );
        }
        gxp.CrumbPanel.superclass.onRender.apply(this, arguments);
        this.getEl().down("div").addClass("gxp-crumbpanel-header");
    },
    
    /** private: method[onCmpHide]
     *  :arg cmp: ``Ext.Component`` The component that was hidden.
     *
     *  Listener for the "hide" event of components that were added to the
     *  CrumbPanel.
     */
    onCmpHide: function(cmp) {
        var lastIndex = this.items.getCount() - 1;
        if (this.items.indexOf(cmp) === lastIndex) {
            this.setActiveTab(this.get(--lastIndex));
        }
    },
    
    /** private: method[setActiveTab]
     *  :arg item: ``Number|Ext.Component``
     */
    setActiveTab: function(item) {
        var index;
        if (Ext.isNumber(item)) {
            index = item;
            item = this.get(index);
        } else {
            index = this.items.indexOf(item);
        }
        if (~index) {
            var cmp, i;
            for (i=this.items.getCount()-1; i>index; --i) {
                cmp = this.get(i);
                // remove, but don't destroy if component was configured with
                // {closeAction: "hide"}
                this.remove(cmp, cmp.closeAction !== "hide");
            }
        }
        var width = item.initialConfig.minWidth || item.initialConfig.width,
            previousWidth = this.getWidth();
        if (width > previousWidth) {
            this.widths[this.get(index - 1).id] = previousWidth;
            this.setWidth(width);
            if (this.ownerCt) {
                this.ownerCt.syncSize();
            }
        }
        gxp.CrumbPanel.superclass.setActiveTab.apply(this, arguments);
    }

});

/** api: xtype = gxp_crumbpanel */
Ext.reg('gxp_crumbpanel', gxp.CrumbPanel);