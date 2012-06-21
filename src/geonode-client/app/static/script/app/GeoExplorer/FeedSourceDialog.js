/**
 * Created with PyCharm.
 * User: mbertrand
 * Date: 6/18/12
 * Time: 3:45 PM
 * To change this template use File | Settings | File Templates.
 */

Ext.namespace("gxp");

gxp.FeedSourceDialog = Ext.extend(Ext.Window, {

    addPicasaText: "Picasa Photos",

    addYouTubeText: "YouTube Videos",

    addHGLText: "Harvard Geospatial Library",

    addRSSText: "Other GeoRSS Feed",

    addFeedText: "Add to Map",

    titleText: "Feed Title",

    keywordText: "Keyword",

    /** config: config[mapPanel]
     *  ``GeoExt.MapPanel``
     *  GeoExplorer object to which layers can be added.
     */
    target : null,


    /** private: method[initComponent]
     */
    initComponent: function() {

        this.addEvents("feed-added");

        this.sourceTypeRadioList = new Ext.form.RadioGroup({
            fieldLabel: 'Type',
            columns: [500],
            labelWidth: 100,
            items: [
                {name: 'source_type', inputValue: 'gx_picasasource', boxLabel: this.addPicasaText, checked: true},
                {name: 'source_type', inputValue: 'gx_youtubesource', boxLabel: this.addYouTubeText},
                {name: 'source_type', inputValue: 'gx_hglfeedsource', boxLabel: this.addHGLText},
                {name: 'source_type', inputValue: 'gx_feedsource', boxLabel: this.addRSSText}
            ],
            listeners: {
                "change": function(radiogroup, radio) {
                    if (radio && radio.inputValue == "gx_feedsource") {
                        this.urlTextField.show();
                        this.keywordTextField.hide();
                        this.maxResultsField.hide();
                        this.symbolizerField.show();
                    } else {
                        this.urlTextField.hide();
                        this.keywordTextField.show();
                        this.maxResultsField.show();
                        this.symbolizerField.hide();
                    }
                },
                scope: this
            }
        });

        this.urlTextField = new Ext.form.TextField({
            fieldLabel: "URL",
            allowBlank: false,
            hidden: true,
            width: 240,
            msgTarget: "right",
            validator: this.urlValidator.createDelegate(this)
        });

        this.keywordTextField = new Ext.form.TextField({
            fieldLabel: this.keywordText,
            allowBlank: true,
            width: 150,
            msgTarget: "right"
        });

        this.titleTextField = new Ext.form.TextField({
            fieldLabel: this.titleText,
            allowBlank: true,
            width: 150,
            msgTarget: "right"
        });

        this.maxResultsField = new Ext.form.ComboBox({
            fieldLabel: 'Maximum # Results',
            hiddenName: 'max-results',
            store: new Ext.data.ArrayStore({
                fields: ['max-results'],
                data : [[10],[25],[50],[100]]
            }),
            displayField: 'max-results',
            mode: 'local',
            triggerAction: 'all',
            emptyText:'Choose number...',
            labelWidth: 100,
            defaults: {
                labelWidth: 100,
                width:100
            }
        });


        this.symbolizerField = new gxp.PointSymbolizer({
            bodyStyle: {padding: "10px"},
            border: false,
            hidden: true,
            labelWidth: 70,
            defaults: {
                labelWidth: 70
            },
            symbolizer: {pointGraphics: "circle", pointRadius: "5"}
        });

        if (this.symbolType === "Point" && this.pointGraphics) {
            cfg.pointGraphics = this.pointGraphics;
        }

        this.submitButton =  new Ext.Button({
            text: this.addFeedText,
            handler: function() {
                var ptype = this.sourceTypeRadioList.getValue().inputValue;
                var config = {
                    "title" : this.titleTextField.getValue(),
                    "group" : "GeoRSS Feeds"
                };

                if (ptype != "gx_feedsource") {
                    config.params = {"q" : this.keywordTextField.getValue(), "max-results" : this.maxResultsField.getValue()}

                } else {
                    config.url = this.urlTextField.getValue();
                    var symbolizer = this.symbolizerField.symbolizer
                    config.defaultStyle = {};
                    config.selectStyle = {};
                    Ext.apply(config.defaultStyle, symbolizer);
                    Ext.apply(config.selectStyle, symbolizer);
                    Ext.apply(config.selectStyle, {
                        fillColor: "Yellow",
                        pointRadius: symbolizer["pointRadius"] + 2
                    })
                }

                this.fireEvent("feed-added", ptype, config);

            },
            scope: this
        });

        this.panel = new Ext.Panel({
            items: [
                this.sourceTypeRadioList,
                this.titleTextField,
                this.urlTextField,
                this.keywordTextField,
                this.maxResultsField,
                this.symbolizerField,
                this.submitButton
            ],
            layout: "form",
            border: false,
            labelWidth: 100,
            bodyStyle: "padding: 5px",
            autoWidth: true,
            autoHeight: true
        });

        this.items = this.panel;

        gxp.FeedSourceDialog.superclass.initComponent.call(this);

    },



    /** private: property[urlRegExp]
     *  `RegExp`
     *
     *  We want to allow protocol or scheme relative URL
     *  (e.g. //example.com/).  We also want to allow username and
     *  password in the URL (e.g. http://user:pass@example.com/).
     *  We also want to support virtual host names without a top
     *  level domain (e.g. http://localhost:9080/).  It also makes sense
     *  to limit scheme to http and https.
     *  The Ext "url" vtype does not support any of this.
     *  This doesn't have to be completely strict.  It is meant to help
     *  the user avoid typos.
     */
    urlRegExp: /^(http(s)?:)?\/\/([\w%]+:[\w%]+@)?([^@\/:]+)(:\d+)?\//i,

    /** private: method[urlValidator]
     *  :arg url: `String`
     *  :returns: `Boolean` The url looks valid.
     *
     *  This method checks to see that a user entered URL looks valid.  It also
     *  does form validation based on the `error` property set when a response
     *  is parsed.
     */
    urlValidator: function(url) {
        var valid;
        if (!this.urlRegExp.test(url)) {
            valid = this.invalidURLText;
        } else {
            valid = !this.error || this.error;
        }
        // clear previous error message
        this.error = null;
        return valid;
    }


});

/** api: xtype = gxp_embedmapdialog */
Ext.reg('gxp_feedsourcedialog', gxp.FeedSourceDialog);




