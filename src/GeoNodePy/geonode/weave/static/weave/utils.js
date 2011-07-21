var setWeaveDashboard = function (sessionstate) {
/*
 * Hides menubar and activates dashboard mode
 */
	Ext.each(sessionstate, function(object){
		// manipulate "WeaveProperties"
		if (this.objectName === "WeaveProperties") {
			this.sessionState.dashboardMode = true;
			this.sessionState.enableMenuBar = false;
			// exit the iterator
			return false;
		}
	});
	// return modified sessionstate
	return sessionstate;
}