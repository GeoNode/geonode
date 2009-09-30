var ExportWizard = Ext.extend(Ext.Window, {

    exportDialogMessage: '<p> UT: Your map is ready to be published to the web! </p>' +
            '<p> Simply copy the following HTML to embed the map in your website: </p>',
    publishActionText: 'UT:Publish Map',
    heightLabel: 'UT: Height',
    widthLabel: 'UT: Width',
    mapSizeLabel: 'UT: Map Size',
    miniSizeLabel: 'UT: Mini',
    smallSizeLabel: 'UT: Small',
    largeSizeLabel: 'UT: Large',
    premiumSizeLabel: 'UT: Premium',

    initComponent: function(config) {
        var description = new Ext.Panel({
            cls: 'gx-wizard-description',
            html: this.exportDialogMessage,
            border: false
        });

        var snippetArea = new Ext.form.TextArea({
            height: '100',
            selectOnFocus: true,
            enableKeyEvents: true,
            listeners: {
                keypress: function(area, evt) {
                    evt.stopEvent();
                }
            }
        });
 
        var heightField = new Ext.form.NumberField({width: 50, value: 400});
        var widthField = new Ext.form.NumberField({width: 50, value: 600});

        var updateSnippet = function() {
            var query = Ext.urlEncode({map: this.map}); 

            // TODO: configurablize!!!1!!!!!111!!!!!!
            var pathname = window.location.pathname.replace(/\/[^\/]*$/, '/embed.html'); 
            var url = 
                window.location.protocol + "//" +
                window.location.host +
                pathname + "?" + query;

            snippetArea.setValue('<iframe height="' + heightField.getValue() +
                ' " width="' + widthField.getValue() + '" src="' + url +
                '"> </iframe>');
        };

        heightField.on("change", updateSnippet, this);
        widthField.on("change", updateSnippet, this);

        var snippet = new Ext.Panel({
            border: false,
            layout: 'fit',
            cls: 'gx-snippet-area',
            items: [snippetArea]
        });

        var adjustments = new Ext.Panel({
            layout: "column",
            items: [
                new Ext.Panel({
                border: false, 
                width: 90,
                items: [
                    new Ext.form.ComboBox({
                    editable: false,
                    width: 70,
                    store: new Ext.data.SimpleStore({
                        fields: ["name", "height", "width"],
                        data: [
                            [this.miniSizeLabel, 100, 100],
                            [this.smallSizeLabel, 200, 300],
                            [this.largeSizeLabel, 400, 600],
                            [this.premiumSizeLabel, 600, 800]
                        ]}),
                    triggerAction: 'all',
                    displayField: 'name',
                    value: this.largeSizeLabel,
                    mode: 'local',
                    listeners: {
                        'select': function(combo, record, index) {
                                widthField.setValue(record.get("width"));
                                heightField.setValue(record.get("height"));
                                updateSnippet.call(this);
                            },
                        scope: this
                        }
                    })
                ]}),
                {cls: 'gx-field-label', html: this.heightLabel, border: false},
                heightField,
                {cls: 'gx-field-label', html: this.widthLabel, border: false},
                widthField
            ],
            border: false
        });

        Ext.apply(this, {
            cls: 'gx-wizard-pane',
            border: false,
            modal: true,
            title: this.publishActionText,
            height: 'auto',
            width: 500,
            items: [
                description, 
                snippet, 
                {cls: 'gx-field-label', html: this.mapSizeLabel, border: false},
                adjustments]
        });

        ExportWizard.superclass.initComponent.call(this);       
        this.on('show', updateSnippet);
    }
});
