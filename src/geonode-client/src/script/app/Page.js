
var Page = Ext.extend(Ext.util.Observable, {
    
    constructor: function(config) {
        this.initialConfig = config;
        Ext.apply(this, this.initialConfig);
        
        // add any custom application events
        this.addEvents(
            /**
             * Event: ready
             * Fires when application is ready for user interaction.
             */
            "ready"
        );

        this.load();
    },
    
    /**
     * Method: load
     * Called at the end of construction.  This initiates the sequence that
     *     prepares the application for use.
     */
    load: function() {
	GeoExplorer.util.dispatch(
	    [
		// create layout as soon as Ext says ready
		function(done) {
		    Ext.onReady(function() {
                        this.createLayout();
                        done();
		    }, this);
                } 
            ],
	    // activate app when the above are both done
	    this.activate, this
	);
    },
   
    /**
	 * Method: createLayout
	 * Create the various parts that compose the layout.
	 */
    createLayout: function() {
        this.populateContent();
    },

    /**
     * Method: activate
     * Activate the application.  Call after application is configured.
     */
    activate: function() {
        this.fireEvent("ready");
    }
});
