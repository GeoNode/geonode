var field;
Ext.onReady(function() {
    viewerField = new gxp.form.ViewerField({
        name: "state",
        fieldLabel: "Select your state",
        allowBlank: false,
        viewer: {
            portalConfig: {border: false},
            // configuration of all tool plugins for this application
            tools: [{
                // shared FeatureManager for feature editing, grid and querying
                ptype: "gxp_featuremanager",
                id: "featuremanager",
                paging: false
            }, {
                ptype: "gxp_featureeditor",
                featureManager: "featuremanager",
                readOnly: true,
                autoLoadFeature: true,
                actionTarget: false,
                defaultAction: 1,
                outputConfig: {panIn: false, height: 220}
            }, {
                ptype: "gxp_featuretofield",
                featureManager: "featuremanager"
            }],

            // layer sources
            defaultSourceType: "gxp_wmssource",
            sources: {
                local: {
                    url: "/geoserver/wms"
                },
                google: {
                    ptype: "gxp_googlesource"
                }
            },

            // map and layers
            map: {
                border: false,
                projection: "EPSG:900913",
                units: "m",
                maxResolution: 156543.0339,
                center: [-10764594.758211, 4523072.3184791],
                zoom: 3,
                layers: [{
                    source: "google",
                    name: "TERRAIN",
                    group: "background"
                }, {
                    source: "local",
                    name: "usa:states",
                    selected: true
                }]
            }
        }
    });

    new Ext.FormPanel({
        border: false,
        width: 530,
        labelWidth: 120,
        items: [{
            name: "name",
            xtype: "textfield",
            fieldLabel: "Your name",
            allowBlank: false
        }, viewerField, {
            name: "sport",
            fieldLabel: "Your favorite sport",
            xtype: "combo",
            store: new Ext.data.ArrayStore({
                fields: ["Sport"],
                data: [["Football"], ["Snowboarding"], ["Surfing"]],
                id: 0
            }),
            mode: "local",
            valueField: "Sport",
            displayField: "Sport",
            allowBlank: false
        }],
        buttons: [{
            text: "Submit",
            handler: function() {
                var fp = this.ownerCt.ownerCt,
                    form = fp.getForm();
                if (form.isValid()) {
                    var values = form.getFieldValues();
                    alert("Name: "+values.name+"\nState: "+Ext.decode(values.state).id+"\nSport: "+values.sport);
                } else {
                    alert("Form does not validate");
                }
            }
        }],
        renderTo: document.body
    });
});
