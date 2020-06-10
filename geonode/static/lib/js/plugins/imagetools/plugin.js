/**
 * Copyright (c) Tiny Technologies, Inc. All rights reserved.
 * Licensed under the LGPL or a commercial license.
 * For LGPL see License.txt in the project root for license information.
 * For commercial licenses see https://www.tiny.cloud/
 *
 * Version: 5.3.1 (2020-05-27)
 */
(function (domGlobals) {
    'use strict';

    var Cell = function (initial) {
      var value = initial;
      var get = function () {
        return value;
      };
      var set = function (v) {
        value = v;
      };
      return {
        get: get,
        set: set
      };
    };

    var global = tinymce.util.Tools.resolve('tinymce.PluginManager');

    var global$1 = tinymce.util.Tools.resolve('tinymce.util.Tools');

    var noop = function () {
    };
    var constant = function (value) {
      return function () {
        return value;
      };
    };
    var never = constant(false);
    var always = constant(true);

    var none = function () {
      return NONE;
    };
    var NONE = function () {
      var eq = function (o) {
        return o.isNone();
      };
      var call = function (thunk) {
        return thunk();
      };
      var id = function (n) {
        return n;
      };
      var me = {
        fold: function (n, _s) {
          return n();
        },
        is: never,
        isSome: never,
        isNone: always,
        getOr: id,
        getOrThunk: call,
        getOrDie: function (msg) {
          throw new Error(msg || 'error: getOrDie called on none.');
        },
        getOrNull: constant(null),
        getOrUndefined: constant(undefined),
        or: id,
        orThunk: call,
        map: none,
        each: noop,
        bind: none,
        exists: never,
        forall: always,
        filter: none,
        equals: eq,
        equals_: eq,
        toArray: function () {
          return [];
        },
        toString: constant('none()')
      };
      return me;
    }();
    var some = function (a) {
      var constant_a = constant(a);
      var self = function () {
        return me;
      };
      var bind = function (f) {
        return f(a);
      };
      var me = {
        fold: function (n, s) {
          return s(a);
        },
        is: function (v) {
          return a === v;
        },
        isSome: always,
        isNone: never,
        getOr: constant_a,
        getOrThunk: constant_a,
        getOrDie: constant_a,
        getOrNull: constant_a,
        getOrUndefined: constant_a,
        or: self,
        orThunk: self,
        map: function (f) {
          return some(f(a));
        },
        each: function (f) {
          f(a);
        },
        bind: bind,
        exists: bind,
        forall: bind,
        filter: function (f) {
          return f(a) ? me : NONE;
        },
        toArray: function () {
          return [a];
        },
        toString: function () {
          return 'some(' + a + ')';
        },
        equals: function (o) {
          return o.is(a);
        },
        equals_: function (o, elementEq) {
          return o.fold(never, function (b) {
            return elementEq(a, b);
          });
        }
      };
      return me;
    };
    var from = function (value) {
      return value === null || value === undefined ? NONE : some(value);
    };
    var Option = {
      some: some,
      none: none,
      from: from
    };

    function create(width, height) {
      return resize(domGlobals.document.createElement('canvas'), width, height);
    }
    function clone(canvas) {
      var tCanvas = create(canvas.width, canvas.height);
      var ctx = get2dContext(tCanvas);
      ctx.drawImage(canvas, 0, 0);
      return tCanvas;
    }
    function get2dContext(canvas) {
      return canvas.getContext('2d');
    }
    function resize(canvas, width, height) {
      canvas.width = width;
      canvas.height = height;
      return canvas;
    }

    function getWidth(image) {
      return image.naturalWidth || image.width;
    }
    function getHeight(image) {
      return image.naturalHeight || image.height;
    }

    var promise = function () {
      var Promise = function (fn) {
        if (typeof this !== 'object') {
          throw new TypeError('Promises must be constructed via new');
        }
        if (typeof fn !== 'function') {
          throw new TypeError('not a function');
        }
        this._state = null;
        this._value = null;
        this._deferreds = [];
        doResolve(fn, bind(resolve, this), bind(reject, this));
      };
      var asap = Promise.immediateFn || typeof window.setImmediate === 'function' && window.setImmediate || function (fn) {
        domGlobals.setTimeout(fn, 1);
      };
      function bind(fn, thisArg) {
        return function () {
          return fn.apply(thisArg, arguments);
        };
      }
      var isArray = Array.isArray || function (value) {
        return Object.prototype.toString.call(value) === '[object Array]';
      };
      function handle(deferred) {
        var me = this;
        if (this._state === null) {
          this._deferreds.push(deferred);
          return;
        }
        asap(function () {
          var cb = me._state ? deferred.onFulfilled : deferred.onRejected;
          if (cb === null) {
            (me._state ? deferred.resolve : deferred.reject)(me._value);
            return;
          }
          var ret;
          try {
            ret = cb(me._value);
          } catch (e) {
            deferred.reject(e);
            return;
          }
          deferred.resolve(ret);
        });
      }
      function resolve(newValue) {
        try {
          if (newValue === this) {
            throw new TypeError('A promise cannot be resolved with itself.');
          }
          if (newValue && (typeof newValue === 'object' || typeof newValue === 'function')) {
            var then = newValue.then;
            if (typeof then === 'function') {
              doResolve(bind(then, newValue), bind(resolve, this), bind(reject, this));
              return;
            }
          }
          this._state = true;
          this._value = newValue;
          finale.call(this);
        } catch (e) {
          reject.call(this, e);
        }
      }
      function reject(newValue) {
        this._state = false;
        this._value = newValue;
        finale.call(this);
      }
      function finale() {
        for (var _i = 0, _a = this._deferreds; _i < _a.length; _i++) {
          var deferred = _a[_i];
          handle.call(this, deferred);
        }
        this._deferreds = [];
      }
      function Handler(onFulfilled, onRejected, resolve, reject) {
        this.onFulfilled = typeof onFulfilled === 'function' ? onFulfilled : null;
        this.onRejected = typeof onRejected === 'function' ? onRejected : null;
        this.resolve = resolve;
        this.reject = reject;
      }
      function doResolve(fn, onFulfilled, onRejected) {
        var done = false;
        try {
          fn(function (value) {
            if (done) {
              return;
            }
            done = true;
            onFulfilled(value);
          }, function (reason) {
            if (done) {
              return;
            }
            done = true;
            onRejected(reason);
          });
        } catch (ex) {
          if (done) {
            return;
          }
          done = true;
          onRejected(ex);
        }
      }
      Promise.prototype.catch = function (onRejected) {
        return this.then(null, onRejected);
      };
      Promise.prototype.then = function (onFulfilled, onRejected) {
        var me = this;
        return new Promise(function (resolve, reject) {
          handle.call(me, new Handler(onFulfilled, onRejected, resolve, reject));
        });
      };
      Promise.all = function () {
        var values = [];
        for (var _i = 0; _i < arguments.length; _i++) {
          values[_i] = arguments[_i];
        }
        var args = Array.prototype.slice.call(values.length === 1 && isArray(values[0]) ? values[0] : values);
        return new Promise(function (resolve, reject) {
          if (args.length === 0) {
            return resolve([]);
          }
          var remaining = args.length;
          function res(i, val) {
            try {
              if (val && (typeof val === 'object' || typeof val === 'function')) {
                var then = val.then;
                if (typeof then === 'function') {
                  then.call(val, function (val) {
                    res(i, val);
                  }, reject);
                  return;
                }
              }
              args[i] = val;
              if (--remaining === 0) {
                resolve(args);
              }
            } catch (ex) {
              reject(ex);
            }
          }
          for (var i = 0; i < args.length; i++) {
            res(i, args[i]);
          }
        });
      };
      Promise.resolve = function (value) {
        if (value && typeof value === 'object' && value.constructor === Promise) {
          return value;
        }
        return new Promise(function (resolve) {
          resolve(value);
        });
      };
      Promise.reject = function (reason) {
        return new Promise(function (resolve, reject) {
          reject(reason);
        });
      };
      Promise.race = function (values) {
        return new Promise(function (resolve, reject) {
          for (var _i = 0, values_1 = values; _i < values_1.length; _i++) {
            var value = values_1[_i];
            value.then(resolve, reject);
          }
        });
      };
      return Promise;
    };
    var Promise = window.Promise ? window.Promise : promise();

    function imageToBlob(image) {
      var src = image.src;
      if (src.indexOf('data:') === 0) {
        return dataUriToBlob(src);
      }
      return anyUriToBlob(src);
    }
    function blobToImage(blob) {
      return new Promise(function (resolve, reject) {
        var blobUrl = domGlobals.URL.createObjectURL(blob);
        var image = new domGlobals.Image();
        var removeListeners = function () {
          image.removeEventListener('load', loaded);
          image.removeEventListener('error', error);
        };
        function loaded() {
          removeListeners();
          resolve(image);
        }
        function error() {
          removeListeners();
          reject('Unable to load data of type ' + blob.type + ': ' + blobUrl);
        }
        image.addEventListener('load', loaded);
        image.addEventListener('error', error);
        image.src = blobUrl;
        if (image.complete) {
          loaded();
        }
      });
    }
    function anyUriToBlob(url) {
      return new Promise(function (resolve, reject) {
        var xhr = new domGlobals.XMLHttpRequest();
        xhr.open('GET', url, true);
        xhr.responseType = 'blob';
        xhr.onload = function () {
          if (this.status === 200) {
            resolve(this.response);
          }
        };
        xhr.onerror = function () {
          var _this = this;
          var corsError = function () {
            var obj = new Error('No access to download image');
            obj.code = 18;
            obj.name = 'SecurityError';
            return obj;
          };
          var genericError = function () {
            return new Error('Error ' + _this.status + ' downloading image');
          };
          reject(this.status === 0 ? corsError() : genericError());
        };
        xhr.send();
      });
    }
    function dataUriToBlobSync(uri) {
      var data = uri.split(',');
      var matches = /data:([^;]+)/.exec(data[0]);
      if (!matches) {
        return Option.none();
      }
      var mimetype = matches[1];
      var base64 = data[1];
      var sliceSize = 1024;
      var byteCharacters = domGlobals.atob(base64);
      var bytesLength = byteCharacters.length;
      var slicesCount = Math.ceil(bytesLength / sliceSize);
      var byteArrays = new Array(slicesCount);
      for (var sliceIndex = 0; sliceIndex < slicesCount; ++sliceIndex) {
        var begin = sliceIndex * sliceSize;
        var end = Math.min(begin + sliceSize, bytesLength);
        var bytes = new Array(end - begin);
        for (var offset = begin, i = 0; offset < end; ++i, ++offset) {
          bytes[i] = byteCharacters[offset].charCodeAt(0);
        }
        byteArrays[sliceIndex] = new Uint8Array(bytes);
      }
      return Option.some(new domGlobals.Blob(byteArrays, { type: mimetype }));
    }
    function dataUriToBlob(uri) {
      return new Promise(function (resolve, reject) {
        dataUriToBlobSync(uri).fold(function () {
          reject('uri is not base64: ' + uri);
        }, resolve);
      });
    }
    function canvasToBlob(canvas, type, quality) {
      type = type || 'image/png';
      if (domGlobals.HTMLCanvasElement.prototype.toBlob) {
        return new Promise(function (resolve, reject) {
          canvas.toBlob(function (blob) {
            if (blob) {
              resolve(blob);
            } else {
              reject();
            }
          }, type, quality);
        });
      } else {
        return dataUriToBlob(canvas.toDataURL(type, quality));
      }
    }
    function canvasToDataURL(canvas, type, quality) {
      type = type || 'image/png';
      return canvas.toDataURL(type, quality);
    }
    function blobToCanvas(blob) {
      return blobToImage(blob).then(function (image) {
        revokeImageUrl(image);
        var canvas = create(getWidth(image), getHeight(image));
        var context = get2dContext(canvas);
        context.drawImage(image, 0, 0);
        return canvas;
      });
    }
    function blobToDataUri(blob) {
      return new Promise(function (resolve) {
        var reader = new domGlobals.FileReader();
        reader.onloadend = function () {
          resolve(reader.result);
        };
        reader.readAsDataURL(blob);
      });
    }
    function revokeImageUrl(image) {
      domGlobals.URL.revokeObjectURL(image.src);
    }

    var blobToImage$1 = function (blob) {
      return blobToImage(blob);
    };
    var imageToBlob$1 = function (image) {
      return imageToBlob(image);
    };

    function create$1(getCanvas, blob, uri) {
      var initialType = blob.type;
      var getType = constant(initialType);
      function toBlob() {
        return Promise.resolve(blob);
      }
      var toDataURL = constant(uri);
      function toBase64() {
        return uri.split(',')[1];
      }
      function toAdjustedBlob(type, quality) {
        return getCanvas.then(function (canvas) {
          return canvasToBlob(canvas, type, quality);
        });
      }
      function toAdjustedDataURL(type, quality) {
        return getCanvas.then(function (canvas) {
          return canvasToDataURL(canvas, type, quality);
        });
      }
      function toAdjustedBase64(type, quality) {
        return toAdjustedDataURL(type, quality).then(function (dataurl) {
          return dataurl.split(',')[1];
        });
      }
      function toCanvas() {
        return getCanvas.then(clone);
      }
      return {
        getType: getType,
        toBlob: toBlob,
        toDataURL: toDataURL,
        toBase64: toBase64,
        toAdjustedBlob: toAdjustedBlob,
        toAdjustedDataURL: toAdjustedDataURL,
        toAdjustedBase64: toAdjustedBase64,
        toCanvas: toCanvas
      };
    }
    function fromBlob(blob) {
      return blobToDataUri(blob).then(function (uri) {
        return create$1(blobToCanvas(blob), blob, uri);
      });
    }
    function fromCanvas(canvas, type) {
      return canvasToBlob(canvas, type).then(function (blob) {
        return create$1(Promise.resolve(canvas), blob, canvas.toDataURL());
      });
    }

    function rotate(ir, angle) {
      return ir.toCanvas().then(function (canvas) {
        return applyRotate(canvas, ir.getType(), angle);
      });
    }
    function applyRotate(image, type, angle) {
      var canvas = create(image.width, image.height);
      var context = get2dContext(canvas);
      var translateX = 0;
      var translateY = 0;
      angle = angle < 0 ? 360 + angle : angle;
      if (angle === 90 || angle === 270) {
        resize(canvas, canvas.height, canvas.width);
      }
      if (angle === 90 || angle === 180) {
        translateX = canvas.width;
      }
      if (angle === 270 || angle === 180) {
        translateY = canvas.height;
      }
      context.translate(translateX, translateY);
      context.rotate(angle * Math.PI / 180);
      context.drawImage(image, 0, 0);
      return fromCanvas(canvas, type);
    }
    function flip(ir, axis) {
      return ir.toCanvas().then(function (canvas) {
        return applyFlip(canvas, ir.getType(), axis);
      });
    }
    function applyFlip(image, type, axis) {
      var canvas = create(image.width, image.height);
      var context = get2dContext(canvas);
      if (axis === 'v') {
        context.scale(1, -1);
        context.drawImage(image, 0, -canvas.height);
      } else {
        context.scale(-1, 1);
        context.drawImage(image, -canvas.width, 0);
      }
      return fromCanvas(canvas, type);
    }

    var findUntil = function (xs, pred, until) {
      for (var i = 0, len = xs.length; i < len; i++) {
        var x = xs[i];
        if (pred(x, i)) {
          return Option.some(x);
        } else if (until(x, i)) {
          break;
        }
      }
      return Option.none();
    };
    var find = function (xs, pred) {
      return findUntil(xs, pred, never);
    };

    var flip$1 = function (ir, axis) {
      return flip(ir, axis);
    };
    var rotate$1 = function (ir, angle) {
      return rotate(ir, angle);
    };

    var blobToImageResult = function (blob) {
      return fromBlob(blob);
    };

    var global$2 = tinymce.util.Tools.resolve('tinymce.util.Delay');

    var global$3 = tinymce.util.Tools.resolve('tinymce.util.Promise');

    var global$4 = tinymce.util.Tools.resolve('tinymce.util.URI');

    var getToolbarItems = function (editor) {
      return editor.getParam('imagetools_toolbar', 'rotateleft rotateright flipv fliph editimage imageoptions');
    };
    var getProxyUrl = function (editor) {
      return editor.getParam('imagetools_proxy');
    };
    var getCorsHosts = function (editor) {
      return editor.getParam('imagetools_cors_hosts', [], 'string[]');
    };
    var getCredentialsHosts = function (editor) {
      return editor.getParam('imagetools_credentials_hosts', [], 'string[]');
    };
    var getFetchImage = function (editor) {
      return Option.from(editor.getParam('imagetools_fetch_image', null, 'function'));
    };
    var getApiKey = function (editor) {
      return editor.getParam('api_key', editor.getParam('imagetools_api_key', '', 'string'), 'string');
    };
    var getUploadTimeout = function (editor) {
      return editor.getParam('images_upload_timeout', 30000, 'number');
    };
    var shouldReuseFilename = function (editor) {
      return editor.getParam('images_reuse_filename', false, 'boolean');
    };

    function getImageSize(img) {
      var width, height;
      function isPxValue(value) {
        return /^[0-9\.]+px$/.test(value);
      }
      width = img.style.width;
      height = img.style.height;
      if (width || height) {
        if (isPxValue(width) && isPxValue(height)) {
          return {
            w: parseInt(width, 10),
            h: parseInt(height, 10)
          };
        }
        return null;
      }
      width = img.width;
      height = img.height;
      if (width && height) {
        return {
          w: parseInt(width, 10),
          h: parseInt(height, 10)
        };
      }
      return null;
    }
    function setImageSize(img, size) {
      var width, height;
      if (size) {
        width = img.style.width;
        height = img.style.height;
        if (width || height) {
          img.style.width = size.w + 'px';
          img.style.height = size.h + 'px';
          img.removeAttribute('data-mce-style');
        }
        width = img.width;
        height = img.height;
        if (width || height) {
          img.setAttribute('width', size.w);
          img.setAttribute('height', size.h);
        }
      }
    }
    function getNaturalImageSize(img) {
      return {
        w: img.naturalWidth,
        h: img.naturalHeight
      };
    }

    var isValue = function (obj) {
      return obj !== null && obj !== undefined;
    };
    var traverse = function (json, path) {
      var value;
      value = path.reduce(function (result, key) {
        return isValue(result) ? result[key] : undefined;
      }, json);
      return isValue(value) ? value : null;
    };
    var requestUrlAsBlob = function (url, headers, withCredentials) {
      return new global$3(function (resolve) {
        var xhr;
        xhr = new domGlobals.XMLHttpRequest();
        xhr.onreadystatechange = function () {
          if (xhr.readyState === 4) {
            resolve({
              status: xhr.status,
              blob: this.response
            });
          }
        };
        xhr.open('GET', url, true);
        xhr.withCredentials = withCredentials;
        global$1.each(headers, function (value, key) {
          xhr.setRequestHeader(key, value);
        });
        xhr.responseType = 'blob';
        xhr.send();
      });
    };
    var readBlob = function (blob) {
      return new global$3(function (resolve) {
        var fr = new domGlobals.FileReader();
        fr.onload = function (e) {
          var data = e.target;
          resolve(data.result);
        };
        fr.readAsText(blob);
      });
    };
    var parseJson = function (text) {
      var json;
      try {
        json = JSON.parse(text);
      } catch (ex) {
      }
      return json;
    };

    var friendlyHttpErrors = [
      {
        code: 404,
        message: 'Could not find Image Proxy'
      },
      {
        code: 403,
        message: 'Rejected request'
      },
      {
        code: 0,
        message: 'Incorrect Image Proxy URL'
      }
    ];
    var friendlyServiceErrors = [
      {
        type: 'key_missing',
        message: 'The request did not include an api key.'
      },
      {
        type: 'key_not_found',
        message: 'The provided api key could not be found.'
      },
      {
        type: 'domain_not_trusted',
        message: 'The api key is not valid for the request origins.'
      }
    ];
    var isServiceErrorCode = function (code) {
      return code === 400 || code === 403 || code === 500;
    };
    var getHttpErrorMsg = function (status) {
      var message = find(friendlyHttpErrors, function (error) {
        return status === error.code;
      }).fold(constant('Unknown ImageProxy error'), function (error) {
        return error.message;
      });
      return 'ImageProxy HTTP error: ' + message;
    };
    var handleHttpError = function (status) {
      var message = getHttpErrorMsg(status);
      return global$3.reject(message);
    };
    var getServiceErrorMsg = function (type) {
      return find(friendlyServiceErrors, function (error) {
        return error.type === type;
      }).fold(constant('Unknown service error'), function (error) {
        return error.message;
      });
    };
    var getServiceError = function (text) {
      var serviceError = parseJson(text);
      var errorType = traverse(serviceError, [
        'error',
        'type'
      ]);
      var errorMsg = errorType ? getServiceErrorMsg(errorType) : 'Invalid JSON in service error message';
      return 'ImageProxy Service error: ' + errorMsg;
    };
    var handleServiceError = function (status, blob) {
      return readBlob(blob).then(function (text) {
        var serviceError = getServiceError(text);
        return global$3.reject(serviceError);
      });
    };
    var handleServiceErrorResponse = function (status, blob) {
      return isServiceErrorCode(status) ? handleServiceError(status, blob) : handleHttpError(status);
    };

    var appendApiKey = function (url, apiKey) {
      var separator = url.indexOf('?') === -1 ? '?' : '&';
      if (/[?&]apiKey=/.test(url) || !apiKey) {
        return url;
      } else {
        return url + separator + 'apiKey=' + encodeURIComponent(apiKey);
      }
    };
    var requestServiceBlob = function (url, apiKey) {
      var headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'tiny-api-key': apiKey
      };
      return requestUrlAsBlob(appendApiKey(url, apiKey), headers, false).then(function (result) {
        return result.status < 200 || result.status >= 300 ? handleServiceErrorResponse(result.status, result.blob) : global$3.resolve(result.blob);
      });
    };
    function requestBlob(url, withCredentials) {
      return requestUrlAsBlob(url, {}, withCredentials).then(function (result) {
        return result.status < 200 || result.status >= 300 ? handleHttpError(result.status) : global$3.resolve(result.blob);
      });
    }
    var getUrl = function (url, apiKey, withCredentials) {
      return apiKey ? requestServiceBlob(url, apiKey) : requestBlob(url, withCredentials);
    };

    var fromHtml = function (html, scope) {
      var doc = scope || domGlobals.document;
      var div = doc.createElement('div');
      div.innerHTML = html;
      if (!div.hasChildNodes() || div.childNodes.length > 1) {
        domGlobals.console.error('HTML does not have a single root node', html);
        throw new Error('HTML must have a single root node');
      }
      return fromDom(div.childNodes[0]);
    };
    var fromTag = function (tag, scope) {
      var doc = scope || domGlobals.document;
      var node = doc.createElement(tag);
      return fromDom(node);
    };
    var fromText = function (text, scope) {
      var doc = scope || domGlobals.document;
      var node = doc.createTextNode(text);
      return fromDom(node);
    };
    var fromDom = function (node) {
      if (node === null || node === undefined) {
        throw new Error('Node cannot be null or undefined');
      }
      return { dom: constant(node) };
    };
    var fromPoint = function (docElm, x, y) {
      var doc = docElm.dom();
      return Option.from(doc.elementFromPoint(x, y)).map(fromDom);
    };
    var Element = {
      fromHtml: fromHtml,
      fromTag: fromTag,
      fromText: fromText,
      fromDom: fromDom,
      fromPoint: fromPoint
    };

    var ELEMENT = 1;

    var ELEMENT$1 = ELEMENT;
    var is = function (element, selector) {
      var dom = element.dom();
      if (dom.nodeType !== ELEMENT$1) {
        return false;
      } else {
        var elem = dom;
        if (elem.matches !== undefined) {
          return elem.matches(selector);
        } else if (elem.msMatchesSelector !== undefined) {
          return elem.msMatchesSelector(selector);
        } else if (elem.webkitMatchesSelector !== undefined) {
          return elem.webkitMatchesSelector(selector);
        } else if (elem.mozMatchesSelector !== undefined) {
          return elem.mozMatchesSelector(selector);
        } else {
          throw new Error('Browser lacks native selectors');
        }
      }
    };

    var Global = typeof domGlobals.window !== 'undefined' ? domGlobals.window : Function('return this;')();

    var child = function (scope, predicate) {
      var pred = function (node) {
        return predicate(Element.fromDom(node));
      };
      var result = find(scope.dom().childNodes, pred);
      return result.map(Element.fromDom);
    };

    var child$1 = function (scope, selector) {
      return child(scope, function (e) {
        return is(e, selector);
      });
    };

    var count = 0;
    var getFigureImg = function (elem) {
      return child$1(Element.fromDom(elem), 'img');
    };
    var isFigure = function (editor, elem) {
      return editor.dom.is(elem, 'figure');
    };
    var getEditableImage = function (editor, elem) {
      var isImage = function (imgNode) {
        return editor.dom.is(imgNode, 'img:not([data-mce-object],[data-mce-placeholder])');
      };
      var isEditable = function (imgNode) {
        return isImage(imgNode) && (isLocalImage(editor, imgNode) || isCorsImage(editor, imgNode) || editor.settings.imagetools_proxy);
      };
      if (isFigure(editor, elem)) {
        var imgOpt = getFigureImg(elem);
        return imgOpt.map(function (img) {
          return isEditable(img.dom()) ? Option.some(img.dom()) : Option.none();
        });
      }
      return isEditable(elem) ? Option.some(elem) : Option.none();
    };
    var displayError = function (editor, error) {
      editor.notificationManager.open({
        text: error,
        type: 'error'
      });
    };
    var getSelectedImage = function (editor) {
      var elem = editor.selection.getNode();
      if (isFigure(editor, elem)) {
        return getFigureImg(elem);
      } else {
        return Option.some(Element.fromDom(elem));
      }
    };
    var extractFilename = function (editor, url) {
      var m = url.match(/\/([^\/\?]+)?\.(?:jpeg|jpg|png|gif)(?:\?|$)/i);
      if (m) {
        return editor.dom.encode(m[1]);
      }
      return null;
    };
    var createId = function () {
      return 'imagetools' + count++;
    };
    var isLocalImage = function (editor, img) {
      var url = img.src;
      return url.indexOf('data:') === 0 || url.indexOf('blob:') === 0 || new global$4(url).host === editor.documentBaseURI.host;
    };
    var isCorsImage = function (editor, img) {
      return global$1.inArray(getCorsHosts(editor), new global$4(img.src).host) !== -1;
    };
    var isCorsWithCredentialsImage = function (editor, img) {
      return global$1.inArray(getCredentialsHosts(editor), new global$4(img.src).host) !== -1;
    };
    var defaultFetchImage = function (editor, img) {
      var src = img.src, apiKey;
      if (isCorsImage(editor, img)) {
        return getUrl(img.src, null, isCorsWithCredentialsImage(editor, img));
      }
      if (!isLocalImage(editor, img)) {
        src = getProxyUrl(editor);
        src += (src.indexOf('?') === -1 ? '?' : '&') + 'url=' + encodeURIComponent(img.src);
        apiKey = getApiKey(editor);
        return getUrl(src, apiKey, false);
      }
      return imageToBlob$1(img);
    };
    var imageToBlob$2 = function (editor, img) {
      return getFetchImage(editor).fold(function () {
        return defaultFetchImage(editor, img);
      }, function (customFetchImage) {
        return customFetchImage(img);
      });
    };
    var findBlob = function (editor, img) {
      var blobInfo;
      blobInfo = editor.editorUpload.blobCache.getByUri(img.src);
      if (blobInfo) {
        return global$3.resolve(blobInfo.blob());
      }
      return imageToBlob$2(editor, img);
    };
    var startTimedUpload = function (editor, imageUploadTimerState) {
      var imageUploadTimer = global$2.setEditorTimeout(editor, function () {
        editor.editorUpload.uploadImagesAuto();
      }, getUploadTimeout(editor));
      imageUploadTimerState.set(imageUploadTimer);
    };
    var cancelTimedUpload = function (imageUploadTimerState) {
      global$2.clearTimeout(imageUploadTimerState.get());
    };
    var updateSelectedImage = function (editor, ir, uploadImmediately, imageUploadTimerState, selectedImage, size) {
      return ir.toBlob().then(function (blob) {
        var uri, name, blobCache, blobInfo;
        blobCache = editor.editorUpload.blobCache;
        uri = selectedImage.src;
        if (shouldReuseFilename(editor)) {
          blobInfo = blobCache.getByUri(uri);
          if (blobInfo) {
            uri = blobInfo.uri();
            name = blobInfo.name();
          } else {
            name = extractFilename(editor, uri);
          }
        }
        blobInfo = blobCache.create({
          id: createId(),
          blob: blob,
          base64: ir.toBase64(),
          uri: uri,
          name: name
        });
        blobCache.add(blobInfo);
        editor.undoManager.transact(function () {
          function imageLoadedHandler() {
            editor.$(selectedImage).off('load', imageLoadedHandler);
            editor.nodeChanged();
            if (uploadImmediately) {
              editor.editorUpload.uploadImagesAuto();
            } else {
              cancelTimedUpload(imageUploadTimerState);
              startTimedUpload(editor, imageUploadTimerState);
            }
          }
          editor.$(selectedImage).on('load', imageLoadedHandler);
          if (size) {
            editor.$(selectedImage).attr({
              width: size.w,
              height: size.h
            });
          }
          editor.$(selectedImage).attr({ src: blobInfo.blobUri() }).removeAttr('data-mce-src');
        });
        return blobInfo;
      });
    };
    var selectedImageOperation = function (editor, imageUploadTimerState, fn, size) {
      return function () {
        var imgOpt = getSelectedImage(editor);
        return imgOpt.fold(function () {
          displayError(editor, 'Could not find selected image');
        }, function (img) {
          return editor._scanForImages().then(function () {
            return findBlob(editor, img.dom());
          }).then(blobToImageResult).then(fn).then(function (imageResult) {
            return updateSelectedImage(editor, imageResult, false, imageUploadTimerState, img.dom(), size);
          }, function (error) {
            displayError(editor, error);
          });
        });
      };
    };
    var rotate$2 = function (editor, imageUploadTimerState, angle) {
      return function () {
        var imgOpt = getSelectedImage(editor);
        var flippedSize = imgOpt.fold(function () {
          return null;
        }, function (img) {
          var size = getImageSize(img.dom());
          return size ? {
            w: size.h,
            h: size.w
          } : null;
        });
        return selectedImageOperation(editor, imageUploadTimerState, function (imageResult) {
          return rotate$1(imageResult, angle);
        }, flippedSize)();
      };
    };
    var flip$2 = function (editor, imageUploadTimerState, axis) {
      return function () {
        return selectedImageOperation(editor, imageUploadTimerState, function (imageResult) {
          return flip$1(imageResult, axis);
        })();
      };
    };
    var handleDialogBlob = function (editor, imageUploadTimerState, img, originalSize, blob) {
      return blobToImage$1(blob).then(function (newImage) {
        var newSize = getNaturalImageSize(newImage);
        if (originalSize.w !== newSize.w || originalSize.h !== newSize.h) {
          if (getImageSize(img)) {
            setImageSize(img, newSize);
          }
        }
        domGlobals.URL.revokeObjectURL(newImage.src);
        return blob;
      }).then(blobToImageResult).then(function (imageResult) {
        return updateSelectedImage(editor, imageResult, true, imageUploadTimerState, img);
      }, function () {
      });
    };

    var saveState = 'save-state';
    var disable = 'disable';
    var enable = 'enable';

    var createState = function (blob) {
      return {
        blob: blob,
        url: domGlobals.URL.createObjectURL(blob)
      };
    };
    var makeOpen = function (editor, imageUploadTimerState) {
      return function () {
        var getLoadedSpec = function (currentState) {
          return {
            title: 'Edit Image',
            size: 'large',
            body: {
              type: 'panel',
              items: [{
                  type: 'imagetools',
                  name: 'imagetools',
                  label: 'Edit Image',
                  currentState: currentState
                }]
            },
            buttons: [
              {
                type: 'cancel',
                name: 'cancel',
                text: 'Cancel'
              },
              {
                type: 'submit',
                name: 'save',
                text: 'Save',
                primary: true,
                disabled: true
              }
            ],
            onSubmit: function (api) {
              var blob = api.getData().imagetools.blob;
              originalImgOpt.each(function (originalImg) {
                originalSizeOpt.each(function (originalSize) {
                  handleDialogBlob(editor, imageUploadTimerState, originalImg.dom(), originalSize, blob);
                });
              });
              api.close();
            },
            onCancel: function () {
            },
            onAction: function (api, details) {
              switch (details.name) {
              case saveState:
                if (details.value) {
                  api.enable('save');
                } else {
                  api.disable('save');
                }
                break;
              case disable:
                api.disable('save');
                api.disable('cancel');
                break;
              case enable:
                api.enable('cancel');
                break;
              }
            }
          };
        };
        var originalImgOpt = getSelectedImage(editor);
        var originalSizeOpt = originalImgOpt.map(function (origImg) {
          return getNaturalImageSize(origImg.dom());
        });
        var imgOpt = getSelectedImage(editor);
        imgOpt.each(function (img) {
          getEditableImage(editor, img.dom()).each(function (_) {
            findBlob(editor, img.dom()).then(function (blob) {
              var state = createState(blob);
              editor.windowManager.open(getLoadedSpec(state));
            });
          });
        });
      };
    };

    var register = function (editor, imageUploadTimerState) {
      global$1.each({
        mceImageRotateLeft: rotate$2(editor, imageUploadTimerState, -90),
        mceImageRotateRight: rotate$2(editor, imageUploadTimerState, 90),
        mceImageFlipVertical: flip$2(editor, imageUploadTimerState, 'v'),
        mceImageFlipHorizontal: flip$2(editor, imageUploadTimerState, 'h'),
        mceEditImage: makeOpen(editor, imageUploadTimerState)
      }, function (fn, cmd) {
        editor.addCommand(cmd, fn);
      });
    };

    var setup = function (editor, imageUploadTimerState, lastSelectedImageState) {
      editor.on('NodeChange', function (e) {
        var lastSelectedImage = lastSelectedImageState.get();
        if (lastSelectedImage && lastSelectedImage.src !== e.element.src) {
          cancelTimedUpload(imageUploadTimerState);
          editor.editorUpload.uploadImagesAuto();
          lastSelectedImageState.set(null);
        }
        getEditableImage(editor, e.element).each(lastSelectedImageState.set);
      });
    };

    var register$1 = function (editor) {
      var cmd = function (command) {
        return function () {
          return editor.execCommand(command);
        };
      };
      editor.ui.registry.addButton('rotateleft', {
        tooltip: 'Rotate counterclockwise',
        icon: 'rotate-left',
        onAction: cmd('mceImageRotateLeft')
      });
      editor.ui.registry.addButton('rotateright', {
        tooltip: 'Rotate clockwise',
        icon: 'rotate-right',
        onAction: cmd('mceImageRotateRight')
      });
      editor.ui.registry.addButton('flipv', {
        tooltip: 'Flip vertically',
        icon: 'flip-vertically',
        onAction: cmd('mceImageFlipVertical')
      });
      editor.ui.registry.addButton('fliph', {
        tooltip: 'Flip horizontally',
        icon: 'flip-horizontally',
        onAction: cmd('mceImageFlipHorizontal')
      });
      editor.ui.registry.addButton('editimage', {
        tooltip: 'Edit image',
        icon: 'edit-image',
        onAction: cmd('mceEditImage'),
        onSetup: function (buttonApi) {
          var setDisabled = function () {
            var elementOpt = getSelectedImage(editor);
            elementOpt.each(function (element) {
              var disabled = getEditableImage(editor, element.dom()).isNone();
              buttonApi.setDisabled(disabled);
            });
          };
          editor.on('NodeChange', setDisabled);
          return function () {
            editor.off('NodeChange', setDisabled);
          };
        }
      });
      editor.ui.registry.addButton('imageoptions', {
        tooltip: 'Image options',
        icon: 'image-options',
        onAction: cmd('mceImage')
      });
      editor.ui.registry.addContextMenu('imagetools', {
        update: function (element) {
          return getEditableImage(editor, element).fold(function () {
            return [];
          }, function (_) {
            return [{
                text: 'Edit image',
                icon: 'edit-image',
                onAction: cmd('mceEditImage')
              }];
          });
        }
      });
    };

    var register$2 = function (editor) {
      editor.ui.registry.addContextToolbar('imagetools', {
        items: getToolbarItems(editor),
        predicate: function (elem) {
          return getEditableImage(editor, elem).isSome();
        },
        position: 'node',
        scope: 'node'
      });
    };

    function Plugin () {
      global.add('imagetools', function (editor) {
        var imageUploadTimerState = Cell(0);
        var lastSelectedImageState = Cell(null);
        register(editor, imageUploadTimerState);
        register$1(editor);
        register$2(editor);
        setup(editor, imageUploadTimerState, lastSelectedImageState);
      });
    }

    Plugin();

}(window));
