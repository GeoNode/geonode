Ext.QuickTips.init();

var form = new gxp.LayerUploadPanel({
    renderTo: "container",
    url: "/geoserver/rest",
    width: 350,
    frame: true,
    title: "Upload Layer Data",
    autoHeight: true,
    bodyStyle: "padding: 10px 10px 0 10px;",
    labelWidth: 65,
    defaults: {
        anchor: "95%",
        allowBlank: false,
        msgTarget: "side"
    },
    listeners: {
        uploadcomplete: function(panel, detail) {
            var layers = detail.layers;
            var names = [];
            for (var i=0, len=layers.length; i<len; ++i) {
                names.push(layers[i].name);
            }
            Ext.Msg.show({
                title: "Success",
                msg: "Added new layer" + (len !== 1 ? "s" : "") + ": " + names.join(", "),
                minWidth: 200,
                icon: Ext.Msg.INFO,
                buttons: Ext.Msg.OK
            });
        }
    }
});
