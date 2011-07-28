// weave.setSessionState(["WeaveProperties"], { backgroundColor: "16777215" });

var applyDefaultStyle = function (sessionstate) {
/*
* Sets default styling for Weave
*/
	Ext.each(sessionstate, function(object){
		// manipulate "WeaveProperties"
		if (this.objectName === "WeaveProperties") {
			this.sessionState.backgroundColor = "16777215";
			// exit the iterator
			return false;
		}
	});
	// return modified sessionstate
	return sessionstate
}

var embedWeave = function (sessionstate) {
	/*
	 * Hides menubar
	 */
		Ext.each(sessionstate, function(object){
			// manipulate "WeaveProperties"
			if (this.objectName === "WeaveProperties") {
				this.sessionState.enableMenuBar = false;
				// exit the iterator
				return false;
			}
		});
		// return modified sessionstate
		return sessionstate;
}

var setWeaveDashboard = function (sessionstate) {
/*
 * Hides menubar and activates dashboard mode
 */
	Ext.each(sessionstate, function(object){
		// manipulate "WeaveProperties"
		if (this.objectName === "WeaveProperties") {
			this.sessionState.dashboardMode = true;
			this.sessionState.enableMenuBar = false;
			this.sessionState.enableToolControls = false;
			// exit the iterator
			return false;
		}
	});
	// return modified sessionstate
	return sessionstate;
}
