/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the GPL license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp
 *  class = NewSourceDialog
 *  base_link = `Ext.Panel <http://extjs.com/deploy/dev/docs/?class=Ext.Container>`_
 */
Ext.namespace("gxp");

/** api: constructor
 * .. class:: gxp.NewSourceDialog(config)
 *
 *     An Ext.Panel with some defaults that better lend themselves toward use 
 *     as a quick query to get a service URL from a user.
 *
 */
gxp.NewSourceDialog = Ext.extend(Ext.Panel, {

    /** api: config[title]
     *  ``String``
     *  Dialog title (i18n).
     */
    title: "Add New Server...",

    /** api: config[cancelText]
     *  ``String``
     *  Text for cancel button (i18n).
     */
    cancelText: "Cancel",
    
    /** api: config[addServerText]
     *  ``String``
     *  Text for add server button (i18n).
     */
    addServerText: "Add WMS Server",

    /** api: config[wmsText]
     *  ``String``
     *  Text for WMS radio-button(i18n).
     */
    addWMSText: "WMS",

    /** api: config[arcText]
     *  ``String``
     *  Text for ArcGIS REST radio-button(i18n).
     */
    addArcText: "ArcGIS REST",
    
    /** api: config[invalidURLText]
     *  ``String``
     *  Message to display when an invalid URL is entered (i18n).
     */
    invalidURLText: "Enter a valid URL to a WMS endpoint (e.g. http://example.com/geoserver/wms)",

    /** api: config[contactingServerText]
     *  ``String``
     *  Text for server contact (i18n).
     */
    contactingServerText: "Contacting Server...",
    
    /** api: config[bodyStyle]
     * The default bodyStyle sets the padding to 0px
     */
    bodyStyle: "padding: 0px",

    /** api: property[error]
     * ``String``
     * The error message set (for example, when adding the source failed)
     */
    error: null,

    /** api: event[urlselected]
     *  Fired with a reference to this instance and the URL that the user
     *  provided as a parameters when the form is submitted.
     */     
     
    /** private: method[initComponent]
     */
    initComponent: function() {

        this.addEvents("urlselected");

        this.urlTextField = new Ext.form.TextField({
            fieldLabel: "URL",
            allowBlank: false,
            width: 240,
            msgTarget: "under",
            validator: this.urlValidator.createDelegate(this)
        });

        this.sourceTypeRadioList = new Ext.form.RadioGroup({
            fieldLabel: 'Type',
            columns: [50, 190],
            items: [
                {name: 'source_type', inputValue: 'gxp_wmscsource', boxLabel: this.addWMSText, checked: true},
                {name: 'source_type', inputValue: 'gxp_arcrestsource', boxLabel: this.addArcText}
            ]
        });

        this.form = new Ext.form.FormPanel({
            items: [
                this.urlTextField,
                this.sourceTypeRadioList
            ],
            border: false,
            labelWidth: 30,
            bodyStyle: "padding: 5px",
            autoWidth: true,
            autoHeight: true
        });

        this.bbar = [
            new Ext.Button({
                text: this.cancelText,
                handler: this.hide,
                scope: this
            }),
            new Ext.Toolbar.Fill(),
            new Ext.Button({
                text: this.addServerText,
                iconCls: "add",
                handler: function() {
                    // Clear validation before trying again.
                    this.error = null;
                    if (this.urlTextField.validate()) {
                        this.fireEvent("urlselected", this, this.urlTextField.getValue(), this.sourceTypeRadioList.getValue().inputValue);
                    }
                },
                scope: this
            })
        ];

        this.items = this.form;

        gxp.NewSourceDialog.superclass.initComponent.call(this);

        this.form.on("render", function() {
            this.loadMask = new Ext.LoadMask(this.form.getEl(), {msg:this.contactingServerText});
        }, this);

        this.on({
            hide: this.reset,
            removed: this.reset,
            scope: this
        });

        this.on("urlselected", function(cmp, url) {
            this.setLoading();
            var failure = function() {
                this.setError(this.sourceLoadFailureMessage);
            };

            // this.explorer.addSource(url, null, success, failure, this);
            //this.addSource(url, this.hide, failure, this);
            this.addSource(url, sourceType, this.hide, failure, this);
        }, this);

    },
    
    /** API: method[reset]
     *  Resets the form and hides any load mask.
     */
    reset: function() {
        // Reset values so it looks right the next time it pops up.
        this.error = null;
        this.urlTextField.reset();
        this.loadMask.hide();
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
    },

    /** private: method[setLoading]
     * Visually signify to the user that we're trying to load the service they 
     * requested, for example, by activating a loadmask.
     */
    setLoading: function() {
        this.loadMask.show();
    },

    /** private: method[setError] 
     * :param: error the message to display
     *
     * Display an error message to the user indicating a failure occurred while
     * trying to load the service.
     */
    setError: function(error) {
        this.loadMask.hide();
        this.error = error;
        this.urlTextField.validate();
    },

    /** api: config[addSource]
     * A callback function to be called when the user submits the form in the 
     * NewSourceDialog.
     *
     * TODO this can probably be extracted to an event handler
     */
    addSource: function(url, success, failure, scope) {
    }
});

/** api: xtype = gxp_newsourcedialog */
Ext.reg('gxp_newsourcedialog', gxp.NewSourceDialog);
