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

    var get = function (fullscreenState) {
      return {
        isFullscreen: function () {
          return fullscreenState.get() !== null;
        }
      };
    };

    var noop = function () {
    };
    var compose = function (fa, fb) {
      return function () {
        var args = [];
        for (var _i = 0; _i < arguments.length; _i++) {
          args[_i] = arguments[_i];
        }
        return fa(fb.apply(null, args));
      };
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

    var revocable = function (doRevoke) {
      var subject = Cell(Option.none());
      var revoke = function () {
        subject.get().each(doRevoke);
      };
      var clear = function () {
        revoke();
        subject.set(Option.none());
      };
      var set = function (s) {
        revoke();
        subject.set(Option.some(s));
      };
      var isSet = function () {
        return subject.get().isSome();
      };
      return {
        clear: clear,
        isSet: isSet,
        set: set
      };
    };
    var unbindable = function () {
      return revocable(function (s) {
        s.unbind();
      });
    };
    var value = function () {
      var subject = Cell(Option.none());
      var clear = function () {
        subject.set(Option.none());
      };
      var set = function (s) {
        subject.set(Option.some(s));
      };
      var on = function (f) {
        subject.get().each(f);
      };
      var isSet = function () {
        return subject.get().isSome();
      };
      return {
        clear: clear,
        set: set,
        isSet: isSet,
        on: on
      };
    };

    var typeOf = function (x) {
      var t = typeof x;
      if (x === null) {
        return 'null';
      } else if (t === 'object' && (Array.prototype.isPrototypeOf(x) || x.constructor && x.constructor.name === 'Array')) {
        return 'array';
      } else if (t === 'object' && (String.prototype.isPrototypeOf(x) || x.constructor && x.constructor.name === 'String')) {
        return 'string';
      } else {
        return t;
      }
    };
    var isType = function (type) {
      return function (value) {
        return typeOf(value) === type;
      };
    };
    var isSimpleType = function (type) {
      return function (value) {
        return typeof value === type;
      };
    };
    var isString = isType('string');
    var isArray = isType('array');
    var isBoolean = isSimpleType('boolean');
    var isFunction = isSimpleType('function');
    var isNumber = isSimpleType('number');

    var nativePush = Array.prototype.push;
    var map = function (xs, f) {
      var len = xs.length;
      var r = new Array(len);
      for (var i = 0; i < len; i++) {
        var x = xs[i];
        r[i] = f(x, i);
      }
      return r;
    };
    var each = function (xs, f) {
      for (var i = 0, len = xs.length; i < len; i++) {
        var x = xs[i];
        f(x, i);
      }
    };
    var filter = function (xs, pred) {
      var r = [];
      for (var i = 0, len = xs.length; i < len; i++) {
        var x = xs[i];
        if (pred(x, i)) {
          r.push(x);
        }
      }
      return r;
    };
    var flatten = function (xs) {
      var r = [];
      for (var i = 0, len = xs.length; i < len; ++i) {
        if (!isArray(xs[i])) {
          throw new Error('Arr.flatten item ' + i + ' was not an array, input: ' + xs);
        }
        nativePush.apply(r, xs[i]);
      }
      return r;
    };
    var bind = function (xs, f) {
      return flatten(map(xs, f));
    };

    var keys = Object.keys;
    var each$1 = function (obj, f) {
      var props = keys(obj);
      for (var k = 0, len = props.length; k < len; k++) {
        var i = props[k];
        var x = obj[i];
        f(x, i);
      }
    };

    var isSupported = function (dom) {
      return dom.style !== undefined && isFunction(dom.style.getPropertyValue);
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

    var Global = typeof domGlobals.window !== 'undefined' ? domGlobals.window : Function('return this;')();

    var DOCUMENT = 9;
    var ELEMENT = 1;
    var TEXT = 3;

    var type = function (element) {
      return element.dom().nodeType;
    };
    var isType$1 = function (t) {
      return function (element) {
        return type(element) === t;
      };
    };
    var isText = isType$1(TEXT);

    var inBody = function (element) {
      var dom = isText(element) ? element.dom().parentNode : element.dom();
      return dom !== undefined && dom !== null && dom.ownerDocument.body.contains(dom);
    };

    var rawSet = function (dom, key, value) {
      if (isString(value) || isBoolean(value) || isNumber(value)) {
        dom.setAttribute(key, value + '');
      } else {
        domGlobals.console.error('Invalid call to Attr.set. Key ', key, ':: Value ', value, ':: Element ', dom);
        throw new Error('Attribute value was not simple');
      }
    };
    var set = function (element, key, value) {
      rawSet(element.dom(), key, value);
    };
    var get$1 = function (element, key) {
      var v = element.dom().getAttribute(key);
      return v === null ? undefined : v;
    };
    var remove = function (element, key) {
      element.dom().removeAttribute(key);
    };

    var internalSet = function (dom, property, value) {
      if (!isString(value)) {
        domGlobals.console.error('Invalid call to CSS.set. Property ', property, ':: Value ', value, ':: Element ', dom);
        throw new Error('CSS value must be a string: ' + value);
      }
      if (isSupported(dom)) {
        dom.style.setProperty(property, value);
      }
    };
    var setAll = function (element, css) {
      var dom = element.dom();
      each$1(css, function (v, k) {
        internalSet(dom, k, v);
      });
    };
    var get$2 = function (element, property) {
      var dom = element.dom();
      var styles = domGlobals.window.getComputedStyle(dom);
      var r = styles.getPropertyValue(property);
      return r === '' && !inBody(element) ? getUnsafeProperty(dom, property) : r;
    };
    var getUnsafeProperty = function (dom, property) {
      return isSupported(dom) ? dom.style.getPropertyValue(property) : '';
    };

    var mkEvent = function (target, x, y, stop, prevent, kill, raw) {
      return {
        target: constant(target),
        x: constant(x),
        y: constant(y),
        stop: stop,
        prevent: prevent,
        kill: kill,
        raw: constant(raw)
      };
    };
    var fromRawEvent = function (rawEvent) {
      var target = Element.fromDom(rawEvent.target);
      var stop = function () {
        return rawEvent.stopPropagation();
      };
      var prevent = function () {
        return rawEvent.preventDefault();
      };
      var kill = compose(prevent, stop);
      return mkEvent(target, rawEvent.clientX, rawEvent.clientY, stop, prevent, kill, rawEvent);
    };

    var ELEMENT$1 = ELEMENT;
    var DOCUMENT$1 = DOCUMENT;
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
    var bypassSelector = function (dom) {
      return dom.nodeType !== ELEMENT$1 && dom.nodeType !== DOCUMENT$1 || dom.childElementCount === 0;
    };
    var all = function (selector, scope) {
      var base = scope === undefined ? domGlobals.document : scope.dom();
      return bypassSelector(base) ? [] : map(base.querySelectorAll(selector), Element.fromDom);
    };

    var eq = function (e1, e2) {
      return e1.dom() === e2.dom();
    };

    var parent = function (element) {
      return Option.from(element.dom().parentNode).map(Element.fromDom);
    };
    var parents = function (element, isRoot) {
      var stop = isFunction(isRoot) ? isRoot : never;
      var dom = element.dom();
      var ret = [];
      while (dom.parentNode !== null && dom.parentNode !== undefined) {
        var rawParent = dom.parentNode;
        var p = Element.fromDom(rawParent);
        ret.push(p);
        if (stop(p) === true) {
          break;
        } else {
          dom = rawParent;
        }
      }
      return ret;
    };
    var siblings = function (element) {
      var filterSelf = function (elements) {
        return filter(elements, function (x) {
          return !eq(element, x);
        });
      };
      return parent(element).map(children).map(filterSelf).getOr([]);
    };
    var children = function (element) {
      return map(element.dom().childNodes, Element.fromDom);
    };

    var r = function (left, top) {
      var translate = function (x, y) {
        return r(left + x, top + y);
      };
      return {
        left: constant(left),
        top: constant(top),
        translate: translate
      };
    };
    var Position = r;

    var get$3 = function (_DOC) {
      var doc = _DOC !== undefined ? _DOC.dom() : domGlobals.document;
      var x = doc.body.scrollLeft || doc.documentElement.scrollLeft;
      var y = doc.body.scrollTop || doc.documentElement.scrollTop;
      return Position(x, y);
    };

    var get$4 = function (_win) {
      var win = _win === undefined ? domGlobals.window : _win;
      return Option.from(win['visualViewport']);
    };
    var bounds = function (x, y, width, height) {
      return {
        x: x,
        y: y,
        width: width,
        height: height,
        right: x + width,
        bottom: y + height
      };
    };
    var getBounds = function (_win) {
      var win = _win === undefined ? domGlobals.window : _win;
      var doc = win.document;
      var scroll = get$3(Element.fromDom(doc));
      return get$4(win).fold(function () {
        var html = win.document.documentElement;
        var width = html.clientWidth;
        var height = html.clientHeight;
        return bounds(scroll.left(), scroll.top(), width, height);
      }, function (visualViewport) {
        return bounds(Math.max(visualViewport.pageLeft, scroll.left()), Math.max(visualViewport.pageTop, scroll.top()), visualViewport.width, visualViewport.height);
      });
    };
    var bind$1 = function (name, callback, _win) {
      return get$4(_win).map(function (visualViewport) {
        var handler = function (e) {
          return fromRawEvent(e);
        };
        visualViewport.addEventListener(name, handler);
        return {
          unbind: function () {
            return visualViewport.removeEventListener(name, handler);
          }
        };
      }).getOrThunk(function () {
        return { unbind: noop };
      });
    };

    var global$1 = tinymce.util.Tools.resolve('tinymce.dom.DOMUtils');

    var global$2 = tinymce.util.Tools.resolve('tinymce.Env');

    var global$3 = tinymce.util.Tools.resolve('tinymce.util.Delay');

    var fireFullscreenStateChanged = function (editor, state) {
      editor.fire('FullscreenStateChanged', { state: state });
    };

    var ancestors = function (scope, predicate, isRoot) {
      return filter(parents(scope, isRoot), predicate);
    };
    var siblings$1 = function (scope, predicate) {
      return filter(siblings(scope), predicate);
    };

    var all$1 = function (selector) {
      return all(selector);
    };
    var ancestors$1 = function (scope, selector, isRoot) {
      return ancestors(scope, function (e) {
        return is(e, selector);
      }, isRoot);
    };
    var siblings$2 = function (scope, selector) {
      return siblings$1(scope, function (e) {
        return is(e, selector);
      });
    };

    var attr = 'data-ephox-mobile-fullscreen-style';
    var siblingStyles = 'display:none!important;';
    var ancestorPosition = 'position:absolute!important;';
    var ancestorStyles = 'top:0!important;left:0!important;margin:0!important;padding:0!important;width:100%!important;height:100%!important;overflow:visible!important;';
    var bgFallback = 'background-color:rgb(255,255,255)!important;';
    var isAndroid = global$2.os.isAndroid();
    var matchColor = function (editorBody) {
      var color = get$2(editorBody, 'background-color');
      return color !== undefined && color !== '' ? 'background-color:' + color + '!important' : bgFallback;
    };
    var clobberStyles = function (dom, container, editorBody) {
      var gatherSibilings = function (element) {
        return siblings$2(element, '*:not(.tox-silver-sink)');
      };
      var clobber = function (clobberStyle) {
        return function (element) {
          var styles = get$1(element, 'style');
          var backup = styles === undefined ? 'no-styles' : styles.trim();
          if (backup === clobberStyle) {
            return;
          } else {
            set(element, attr, backup);
            setAll(element, dom.parseStyle(clobberStyle));
          }
        };
      };
      var ancestors = ancestors$1(container, '*');
      var siblings = bind(ancestors, gatherSibilings);
      var bgColor = matchColor(editorBody);
      each(siblings, clobber(siblingStyles));
      each(ancestors, clobber(ancestorPosition + ancestorStyles + bgColor));
      var containerStyles = isAndroid === true ? '' : ancestorPosition;
      clobber(containerStyles + ancestorStyles + bgColor)(container);
    };
    var restoreStyles = function (dom) {
      var clobberedEls = all$1('[' + attr + ']');
      each(clobberedEls, function (element) {
        var restore = get$1(element, attr);
        if (restore !== 'no-styles') {
          setAll(element, dom.parseStyle(restore));
        } else {
          remove(element, 'style');
        }
        remove(element, attr);
      });
    };

    var DOM = global$1.DOM;
    var getScrollPos = function () {
      var vp = getBounds(domGlobals.window);
      return {
        x: vp.x,
        y: vp.y
      };
    };
    var setScrollPos = function (pos) {
      domGlobals.window.scrollTo(pos.x, pos.y);
    };
    var viewportUpdate = get$4().fold(function () {
      return {
        bind: noop,
        unbind: noop
      };
    }, function (visualViewport) {
      var editorContainer = value();
      var resizeBinder = unbindable();
      var scrollBinder = unbindable();
      var refreshScroll = function () {
        domGlobals.document.body.scrollTop = 0;
        domGlobals.document.documentElement.scrollTop = 0;
      };
      var refreshVisualViewport = function () {
        domGlobals.window.requestAnimationFrame(function () {
          editorContainer.on(function (container) {
            return setAll(container, {
              top: visualViewport.offsetTop + 'px',
              left: visualViewport.offsetLeft + 'px',
              height: visualViewport.height + 'px',
              width: visualViewport.width + 'px'
            });
          });
        });
      };
      var update = global$3.throttle(function () {
        refreshScroll();
        refreshVisualViewport();
      }, 50);
      var bind = function (element) {
        editorContainer.set(element);
        update();
        resizeBinder.set(bind$1('resize'));
        scrollBinder.set(bind$1('scroll'));
      };
      var unbind = function () {
        editorContainer.on(function () {
          resizeBinder.clear();
          scrollBinder.clear();
        });
        editorContainer.clear();
      };
      return {
        bind: bind,
        unbind: unbind
      };
    });
    var toggleFullscreen = function (editor, fullscreenState) {
      var body = domGlobals.document.body;
      var documentElement = domGlobals.document.documentElement;
      var editorContainerStyle;
      var editorContainer, iframe, iframeStyle;
      editorContainer = editor.getContainer();
      var editorContainerS = Element.fromDom(editorContainer);
      var fullscreenInfo = fullscreenState.get();
      var editorBody = Element.fromDom(editor.getBody());
      var isTouch = global$2.deviceType.isTouch();
      editorContainerStyle = editorContainer.style;
      iframe = editor.getContentAreaContainer().firstChild;
      iframeStyle = iframe.style;
      if (!fullscreenInfo) {
        var newFullScreenInfo = {
          scrollPos: getScrollPos(),
          containerWidth: editorContainerStyle.width,
          containerHeight: editorContainerStyle.height,
          containerTop: editorContainerStyle.top,
          containerLeft: editorContainerStyle.left,
          iframeWidth: iframeStyle.width,
          iframeHeight: iframeStyle.height
        };
        if (isTouch) {
          clobberStyles(editor.dom, editorContainerS, editorBody);
        }
        iframeStyle.width = iframeStyle.height = '100%';
        editorContainerStyle.width = editorContainerStyle.height = '';
        DOM.addClass(body, 'tox-fullscreen');
        DOM.addClass(documentElement, 'tox-fullscreen');
        DOM.addClass(editorContainer, 'tox-fullscreen');
        viewportUpdate.bind(editorContainerS);
        editor.on('remove', viewportUpdate.unbind);
        fullscreenState.set(newFullScreenInfo);
        fireFullscreenStateChanged(editor, true);
      } else {
        iframeStyle.width = fullscreenInfo.iframeWidth;
        iframeStyle.height = fullscreenInfo.iframeHeight;
        editorContainerStyle.width = fullscreenInfo.containerWidth;
        editorContainerStyle.height = fullscreenInfo.containerHeight;
        editorContainerStyle.top = fullscreenInfo.containerTop;
        editorContainerStyle.left = fullscreenInfo.containerLeft;
        if (isTouch) {
          restoreStyles(editor.dom);
        }
        DOM.removeClass(body, 'tox-fullscreen');
        DOM.removeClass(documentElement, 'tox-fullscreen');
        DOM.removeClass(editorContainer, 'tox-fullscreen');
        setScrollPos(fullscreenInfo.scrollPos);
        fullscreenState.set(null);
        fireFullscreenStateChanged(editor, false);
        viewportUpdate.unbind();
        editor.off('remove', viewportUpdate.unbind);
      }
    };

    var register = function (editor, fullscreenState) {
      editor.addCommand('mceFullScreen', function () {
        toggleFullscreen(editor, fullscreenState);
      });
    };

    var makeSetupHandler = function (editor, fullscreenState) {
      return function (api) {
        api.setActive(fullscreenState.get() !== null);
        var editorEventCallback = function (e) {
          return api.setActive(e.state);
        };
        editor.on('FullscreenStateChanged', editorEventCallback);
        return function () {
          return editor.off('FullscreenStateChanged', editorEventCallback);
        };
      };
    };
    var register$1 = function (editor, fullscreenState) {
      editor.ui.registry.addToggleMenuItem('fullscreen', {
        text: 'Fullscreen',
        icon: 'fullscreen',
        shortcut: 'Meta+Shift+F',
        onAction: function () {
          return editor.execCommand('mceFullScreen');
        },
        onSetup: makeSetupHandler(editor, fullscreenState)
      });
      editor.ui.registry.addToggleButton('fullscreen', {
        tooltip: 'Fullscreen',
        icon: 'fullscreen',
        onAction: function () {
          return editor.execCommand('mceFullScreen');
        },
        onSetup: makeSetupHandler(editor, fullscreenState)
      });
    };

    function Plugin () {
      global.add('fullscreen', function (editor) {
        var fullscreenState = Cell(null);
        if (editor.settings.inline) {
          return get(fullscreenState);
        }
        register(editor, fullscreenState);
        register$1(editor, fullscreenState);
        editor.addShortcut('Meta+Shift+F', '', 'mceFullScreen');
        return get(fullscreenState);
      });
    }

    Plugin();

}(window));
