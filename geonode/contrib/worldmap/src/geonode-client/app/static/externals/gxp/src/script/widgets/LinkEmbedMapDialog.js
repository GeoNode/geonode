/**
 * Copyright (c) 2010 OpenPlans
 */

/**
 */

Ext.namespace("gxp");

/** api: (define)
 *  module = GeoExplorer
 *  class = LinkEmbedMapDialog
 *  base_link = `Ext.Container <http://extjs.com/deploy/dev/docs/?class=Ext.Container>`_
 */

/** api: example
 *  Show a :class:`gxp.LinkEmbedMapDialog` in a window, using "viewer.html" in the
 *  current path as url:
 * 
 *  .. code-block:: javascript
 *      new Ext.Window({
 *           title: "Export Map",
 *           layout: "fit",
 *           width: 380,
 *           autoHeight: true,
 *           items: [{
 *               xtype: "gx_embedmapdialog",
 *               url: "viewer.html" 
 *           }]
 *       }).show();
 */
 
/** api: constructor
 *  .. class:: LinkEmbedMapDialog(config)
 *   
 *  A dialog for configuring a map iframe to embed on external web pages.
 */
gxp.LinkEmbedMapDialog = Ext.extend(gxp.EmbedMapDialog, {
    

	linkMessage: 'Paste link in email or IM',
	linkUrl : '',
	linkBox : null,
    
    /** private: method[initComponent]
     */
    initComponent: function() {
        Ext.apply(this, this.getConfig());
        gxp.LinkEmbedMapDialog.superclass.initComponent.call(this);
    },
    
    /** private: method[updateSnippetAndLink]
     */
    updateSnippetAndLink: function() {
        this.snippetArea.setValue(
            '<iframe height="' + this.heightField.getValue() +
            '" width="' + this.widthField.getValue() +'" src="' + 
            gxp.util.getAbsoluteUrl(this.url) + '"></iframe>'
        );
		this.linkBox.focus(true, 100);
		
    },

    /** private: method[getConfig]
     */
    getConfig: function() {
    	
    	var absoluteUrl = gxp.util.getAbsoluteUrl(this.linkUrl);
    	        
        this.snippetArea = new Ext.form.TextArea({
            height: 70,
            selectOnFocus: true,
            readOnly: true
        });
        
        var numFieldListeners = {
            "change": this.updateSnippet,
            "specialkey": function(f, e) {
                e.getKey() == e.ENTER && this.updateSnippet();
            },
            scope: this
        };

        this.heightField = new Ext.form.NumberField({
            width: 50,
            value: 400,
            listeners: numFieldListeners
        });
        this.widthField = new Ext.form.NumberField({
            width: 50,
            value: 600,
            listeners: numFieldListeners
        });        

        this.linkBox = new Ext.form.TextField({
        	value: absoluteUrl,
        	listeners: {
        		"focus": function() {
        			this.selectText();
        		}
        	}
        });
        
        var adjustments = new Ext.Container({
            layout: "column",
            defaults: {
                border: false,
                xtype: "box"
            },
            items: [
                {autoEl: {cls: "gx-field-label", html: this.mapSizeLabel}},
                new Ext.form.ComboBox({
                    editable: false,
                    width: 75,
                    store: new Ext.data.SimpleStore({
                        fields: ["name", "height", "width"],
                        data: [
                            [this.miniSizeLabel, 100, 100],
                            [this.smallSizeLabel, 200, 300],
                            [this.largeSizeLabel, 400, 600],
                            [this.premiumSizeLabel, 600, 800]
                        ]
                    }),
                    triggerAction: 'all',
                    displayField: 'name',
                    value: this.largeSizeLabel,
                    mode: 'local',
                    listeners: {
                        "select": function(combo, record, index) {
                            this.widthField.setValue(record.get("width"));
                            this.heightField.setValue(record.get("height"));
                            this.updateSnippet();
                        },
                        scope: this
                    }
                }),
                {autoEl: {cls: "gx-field-label", html: this.heightLabel}},
                this.heightField,
                {autoEl: {cls: "gx-field-label", html: this.widthLabel}},
                this.widthField
            ]
        });


        
        return {
            border: false,
            defaults: {
                border: false,
                cls: "gx-export-section",
                xtype: "container",
                layout: "fit"
            },
            items: [{
                xtype: "box",
                autoEl: {
                    tag: "div",
                    html: this.linkMessage
                }
            },{
            	items: [this.linkBox]
            }, {
                xtype: "box",
                autoEl: {
                    tag: "div",
                    html: this.publishMessage
                }
            }, {
                items: [this.snippetArea]
            }, {
                items: [adjustments]
            }],
            listeners: {
                "afterrender": this.updateSnippetAndLink,
                scope: this
            }
        }
    }
});

/** api: xtype = gx_linkembedmapdialog */
Ext.reg('gx_linkembedmapdialog', gxp.LinkEmbedMapDialog);