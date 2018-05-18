/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp.form
 *  class = FontComboBox
 *  base_link = `Ext.form.ComboBox <http://extjs.com/deploy/dev/docs/?class=Ext.form.ComboBox>`_
 */
Ext.namespace("gxp.form");

/** api: constructor
 *  .. class:: FontComboBox(config)
 *   
 *      A combo box for selecting a font.
 */
gxp.form.FontComboBox = Ext.extend(Ext.form.ComboBox, {
    
    /** api: property[fonts]
     *  ``Array``
     *  List of font families to choose from.  Default is ["Arial",
     *  "Courier New", "Tahoma", "Times New Roman", "Verdana"].
     */
    fonts: [
        "Arial Unicode MS",
        "Serif",
        "SansSerif",
        "Arial",
        "Courier New",
        "Tahoma",
        "Times New Roman",
        "Verdana"
    ],
    
    /** api: property[defaultFont]
     *  ``String``
     *  The ``fonts`` item to select by default.
     */
    defaultFont: "Serif",

    allowBlank: false,

    mode: "local",

    triggerAction: "all",

    editable: false,
  
    initComponent: function() {
        var fonts = this.fonts || gxp.form.FontComboBox.prototype.fonts;
        var defaultFont = this.defaultFont;
        if (fonts.indexOf(this.defaultFont) === -1) {
            defaultFont = fonts[0];
        }
        var defConfig = {
            displayField: "field1",
            valueField: "field1",
            store: fonts,
            value: defaultFont,
            tpl: new Ext.XTemplate(
                '<tpl for=".">' +
                    '<div class="x-combo-list-item">' +
                    '<span style="font-family: {field1};">{field1}</span>' +
                '</div></tpl>'
            )
        };
        Ext.applyIf(this, defConfig);
        
        gxp.form.FontComboBox.superclass.initComponent.call(this);
    }
});

/** api: xtype = gxp_fontcombo */
Ext.reg("gxp_fontcombo", gxp.form.FontComboBox);
