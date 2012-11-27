function pollProgress(redirectTo, progressEndpoint, form) {
    var progress = Ext.MessageBox.progress("Please wait","Ingesting data"),
    formDom = form.dom;
    function success(response,redirectTo) {
        var state, msg;
        response = Ext.decode(response.responseText);
        // response will contain state, one of :
        // PENDING, READY, RUNNING, NO_CRS, NO_BOUNDS, ERROR, COMPLETE
        // though RUNNING, ERROR or COMPLETE are what we expect
        // and possibly progress and total
        if (response.state == 'COMPLETE') {
            Ext.MessageBox.wait("Finishing Ingest...");
            // don't just open a GET on the location, ensure a POST occurs
            formDom.action = redirectTo;
            formDom.submit();
            return;
        } else if ('progress' in response) {
            msg = 'Ingested ' + response.progress + " of " + response.total;
            progress.updateProgress( response.progress/response.total, msg );
        } else {
            switch (response.state) {
                // give it a chance to start running or return complete
                case 'PENDING': case 'RUNNING':
                    break;
                case 'ERROR':
                    msg = 'message' in response ? response.message :
                    "An unknown error occurred during the ingest."
                    Ext.MessageBox.show({
                        icon : Ext.MessageBox.ERROR,
                        msg : msg
                    });
                    return;
                default:
                    Ext.MessageBox.show({
                        icon : Ext.MessageBox.ERROR,
                        msg : 'Expected a status other than ' + response.state
                    });
                    return;
            }
        }
        setTimeout(poll,500);
    }
    function poll() {
        Ext.Ajax.request({
            url : progressEndpoint,
            success: function(response) {
                success(response,redirectTo);
            }
        });
    }
    poll();
}

function enableUploadProgress(uploadFormID) {
    Ext.onReady(function() {
        if (typeof(uploadFormID) == 'string') {
            // AJAX submit form
            var form = Ext.get(uploadFormID), extForm = new Ext.form.BasicForm(form);
            form.on('submit',function(ev) {
                ev.preventDefault();
                extForm.on('actioncomplete',function(form,xhrlike) {
                    var resp = Ext.decode(xhrlike.response.responseText);
                    pollProgress(resp.redirect_to, resp.progress, Ext.get(uploadFormID));
                });
                extForm.on('actionfailed',function(form,xhrlike) {
                    var msg = "result" in xhrlike ? 
                        xhrlike.result.errors.join("\n") : 
                        xhrlike.response.responseText;
                    Ext.MessageBox.show({
                        icon : Ext.MessageBox.ERROR,
                        msg : msg
                    });
                });
                extForm.submit();
            });
        }
    });
}