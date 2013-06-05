/*global define */
'use strict';

define(function (require, exports) {
    var make_request; 

    /** We have a different notion of success and failure for GeoNode's
     * urls this function allows the user to define two functions, success
     * and failure and have the failure function called when an bad
     * http response is returns and also when there is not success
     * property define in the response.
     */
    make_request = exports.make_request = (function () {
        return function (options) {
            var success = options.success,
                failure = options.failure;

            delete options.success;
            delete options.failure;

            $.ajax(options).done(function (resp, status, obj) {
               if (typeof resp === "object" && resp.success === true) {
                    success(resp, status);
               } else if (typeof resp === "string"){
                    success({status:'other', url: options.url, resp_string:resp}, status);
                } else {
                    failure(resp, status);
                }
            }).fail(failure);
        };
    }());
});
