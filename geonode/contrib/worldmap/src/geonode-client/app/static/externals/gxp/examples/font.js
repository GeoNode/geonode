
var panel;
Ext.onReady(function() {

    panel = new Ext.FormPanel({
        title: "Font Picker",
        renderTo: "panel",
        width: 270,
        labelWidth: 40,
        bodyStyle: {padding: 10},
        items: [{
            xtype: "gxp_fontcombo",
            fieldLabel: "Font",
            anchor: "90%"
        }]
    });

});
