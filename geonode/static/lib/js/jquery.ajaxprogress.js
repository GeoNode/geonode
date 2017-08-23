/*!
 * jQuery ajaxProgress Plugin v0.5.0
 * Requires jQuery v1.5.0 or later
 * 
 * http://www.kpozin.net/ajaxprogress
 *
 * (c) 2011, Konstantin Pozin
 * Licensed under MIT license.
 */
(function($) {

    // Test whether onprogress is supported
    var support = $.support.ajaxProgress = ("onprogress" in $.ajaxSettings.xhr());

    // If it's not supported, we can't do anything
    if (!support) {
        return;
    }

    var NAMESPACE = ".ajaxprogress";

    // Create global "ajaxProgress" event
    $.fn.ajaxProgress = function (f) {
        return this.bind("ajaxProgress", f);
    };

    // Hold on to a reference to the jqXHR object so that we can pass it to the progress callback.
    // Namespacing the handler with ".ajaxprogress"
    $("html").bind("ajaxSend" + NAMESPACE, function(event, jqXHR, ajaxOptions) {
        ajaxOptions.__jqXHR = jqXHR;
    });

    /**
     * @param {XMLHttpRequestProgressEvent} evt
     * @param {Object} options jQuery AJAX options
     */
    function handleOnProgress(evt, options) {

        // Trigger the global event.
        // function handler(jqEvent, progressEvent, jqXHR) {}
        if (options.global) {
            $.event.trigger("ajaxProgress", [evt, options.__jqXHR]);
        }

        // Trigger the local event.
        // function handler(jqXHR, progressEvent)
        if (typeof options.progress === "function") {
            options.progress(options.__jqXHR, evt);
        }
    }


    // We'll work with the original factory method just in case
    var makeOriginalXhr = $.ajaxSettings.xhr.bind($.ajaxSettings);

    // Options to be passed into $.ajaxSetup;
    var newOptions = {};

    // Wrap the XMLHttpRequest factory method
    newOptions.xhr = function () {

        // Reference to the extended options object
        var s = this;

        var newXhr = makeOriginalXhr();
        if (newXhr) {
            newXhr.addEventListener("progress", function(evt) {
                handleOnProgress(evt, s);
            });
        }
        return newXhr;
    };

    $.ajaxSetup(newOptions);

})(jQuery);