/*
 * jQuery Ajax Progress - Lightweight jQuery plugin that adds support of `progress` and `uploadProgress` events to $.ajax()
 * Copyright (c) 2018 Alexey Lizurchik <al.lizurchik@gmail.com> (@likerR_r)
 * Licensed under the MIT license
 * http://likerrr.mit-license.org/
 */

(function(factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD. Register as an anonymous module.
    define(['jquery'], factory);
  } else if (typeof exports === 'object') {
    // Node/CommonJS
    module.exports = factory(require('jquery'));
  } else {
    // Browser globals
    factory(jQuery);
  }
}(function($) {
  var $originalAjax = $.ajax.bind($);

  $.ajax = function (url, options) {
    if (typeof url === 'object') {
      options = url;
      url = undefined;
    }

    options = options || {
      chunking: false
    };

    // Get current xhr object
    var xmlHttpReq = options.xhr ? options.xhr() : $.ajaxSettings.xhr();
    var chunking = options.chunking || $.ajaxSettings.chunking;

    // Make it use our own.
    options.xhr = function () {
      if (typeof options.uploadProgress === 'function') {
        if (!xmlHttpReq.upload) {
          return;
        }

        // this line looks strange, but without it chrome doesn't catch `progress` event on uploading. Seems like chromium bug
        xmlHttpReq.upload.onprogress = null;

        // Upload progress listener
        xmlHttpReq.upload.addEventListener('progress', function (e) {
          options.uploadProgress.call(this, e);
        }, false);
      }

      if (typeof options.progress === 'function') {
        var lastChunkLen = 0;

        // Download progress listener
        xmlHttpReq.addEventListener('progress', function (e) {
          var params = [e],
            chunk = '';

          if (this.readyState === XMLHttpRequest.LOADING && chunking) {
            chunk = this.responseText.substr(lastChunkLen);
            lastChunkLen = this.responseText.length;
            params.push(chunk);
          }

          options.progress.apply(this, params);
        }, false);
      }

      return xmlHttpReq;
    };

    return $originalAjax(url, options);
  };
}));
