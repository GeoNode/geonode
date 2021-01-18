/*global define */
'use strict';

define(function (require, exports) {
    var make_request,
          logStatus,
          logError,
          parseQueryString;

    function progressTemplate(options) {
        var template =  _.template($('#progressTemplate').html());
        return template(options);
    };

    /** We have a different notion of success and failure for GeoNode's
     * urls this function allows the user to define two functions, success
     * and failure and have the failure function called when an bad
     * http response is returns and also when there is not success
     * property define in the response.
     */
    make_request = exports.make_request = (function () {
        return function (options) {
            options.mode ="queue";
            var success = options.success,
                failure = options.failure;

            delete options.success;
            delete options.failure;

            $.ajax(options).done(function (resp, status, obj) {
               if (typeof resp === "object" && resp.success === true) {
                    success(resp, status);
               } else if (typeof resp === "string"){
                    success({status:'incomplete', input_required: true, url: options.url, resp_string:resp, redirect_to:''}, status);
                } else {
                    failure(resp, status);
                }
            }).fail(failure);
        };
    }());

    /** Function to log to the upload-status element
     *
     * options required:
     * message - the message
     * alertLevel - class to inject
     *
     * optional options:
     * empty - clear the status
     * element - us this element instead of the default
     *
     *  @params {options} options
     */
    logStatus = function (options) {
        var status = options.element || $('#upload-status'),
            empty = options.empty;

        if (empty) {
            status.empty();
        }
        status.append(progressTemplate({
            message: options.msg,
            alertLevel: options.level
        }));
    };

    /** Function to mark errors in the the status
     *
     *  @params {error} string or response object
     *  @params {element} optional element to append to
     */
    logError = function (error, element) {
        if (error.responseText) {
            var parsed_errors = null;
            var error_message = 'No error message supplied';
            try {
                parsed_errors = $.parseJSON(error.responseText);
            } catch (exception) {
                // in case the response is not json
                error_message = error.responseText;
            }

            // Support the two different syntax used in GeoNode.
            // TODO(Ariel): Agree on one of those server side and
            // simplify this code. It can be either 'errormsgs' or 'error'.
            if (parsed_errors !== null) {
                if(parsed_errors.hasOwnProperty("errormsgs")){
                    error_message = parsed_errors.errormsgs;
                } else {
                    error_message = parsed_errors.errors;
                }
            }
            error = error_message;
        }
        logStatus({msg: error, level: 'alert-warning', empty:true, element:element});
    };

    parseQueryString = function (url){
        var query_dict = {};
        var url = url || '';

        var pos = url.indexOf("?") + 1;

        $.each(url.substr(pos).split('&'),function(c,kvp){
            var parts = kvp.split('=');
            if (parts[0] && parts[1]) {
                var key = parts[0].toString().toLowerCase();
                var val = parts[1].toString();
                query_dict[key] = val;
            }
        });

        return query_dict;
    };

    exports.logStatus = logStatus;
    exports.logError = logError;
    exports.parseQueryString = parseQueryString;
});
