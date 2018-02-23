var panel;
Ext.onReady(function() {
    
    panel = new Ext.Panel({
        renderTo: "panel",
        border: false,
        items: [{
            xtype: "gxp_scalelimitpanel",
            scaleSliderTemplate: "{scaleType} Zoom Level: {zoom}<br>{scaleType} Scale 1:{scale}"
        }]
    });
    
});
