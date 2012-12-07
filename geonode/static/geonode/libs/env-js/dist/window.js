
/**
 * @todo: document
 */
var Window,
    Screen,
    History,
    Navigator;


/*
 * Envjs window.1.2.13 
 * Pure JavaScript Browser Environment
 * By John Resig <http://ejohn.org/> and the Envjs Team
 * Copyright 2008-2010 John Resig, under the MIT License
 */

//CLOSURE_START
(function(){





/**
 * @author john resig
 */
// Helper method for extending one object with another.
function __extend__(a,b) {
    for ( var i in b ) {
        var g = b.__lookupGetter__(i), s = b.__lookupSetter__(i);
        if ( g || s ) {
            if ( g ) { a.__defineGetter__(i, g); }
            if ( s ) { a.__defineSetter__(i, s); }
        } else {
            a[i] = b[i];
        }
    } return a;
}

/**
 * @todo: document
 */

__extend__(HTMLFrameElement.prototype,{

    get contentDocument(){
        return this.contentWindow?
            this.contentWindow.document:
            null;
    },
    set src(value){
        var event;
        this.setAttribute('src', value);
        if (this.parentNode && value && value.length > 0){
            //console.log('loading frame %s', value);
            Envjs.loadFrame(this, Envjs.uri(value));

            //console.log('event frame load %s', value);
            event = this.ownerDocument.createEvent('HTMLEvents');
            event.initEvent("load", false, false);
            this.dispatchEvent( event, false );
        }
    }

});

/*
 *       history.js
 *
 */

History = function(owner) {
    var $current = 0,
        $history = [null],
        $owner = owner;

    return {
        go : function(target) {
            if (typeof target === "number") {
                target = $current + target;
                if (target > -1 && target < $history.length){
                    if ($history[target].type === "hash") {
                        if ($owner.location) {
                            $owner.location.hash = $history[target].value;
                        }
                    } else {
                        if ($owner.location) {
                            $owner.location = $history[target].value;
                        }
                    }
                    $current = target;
                }
            } else {
                //TODO: walk through the history and find the 'best match'?
            }
        },

        get length() {
            return $history.length;
        },

        back : function(count) {
            if (count) {
                this.go(-count);
            } else {
                this.go(-1);
            }
        },

        get current() {
            return this.item($current);
        },

        get previous() {
            return this.item($current-1);
        },

        forward : function(count) {
            if (count) {
                this.go(count);
            } else {
                this.go(1);
            }
        },

        item: function(idx) {
            if (idx >= 0 && idx < $history.length) {
                return $history[idx];
            } else {
                return null;
            }
        },

        add: function(newLocation, type) {
            //not a standard interface, we expose it to simplify
            //history state modifications
            if (newLocation !== $history[$current]) {
                $history.slice(0, $current);
                $history.push({
                    type: type || 'href',
                    value: newLocation
                });
            }
        }
    }; /* closes 'return {' */
};


/*
 *      navigator.js
 *  Browser Navigator
 */
Navigator = function(){

    return {
        get appCodeName(){
            return Envjs.appCodeName;
        },
        get appName(){
            return Envjs.appName;
        },
        get appVersion(){
            return Envjs.version +" ("+
                this.platform +"; "+
                "U; "+//?
                Envjs.os_name+" "+Envjs.os_arch+" "+Envjs.os_version+"; "+
                (Envjs.lang?Envjs.lang:"en-US")+"; "+
                "rv:"+Envjs.revision+
                ")";
        },
        get cookieEnabled(){
            return true;
        },
        get mimeTypes(){
            return [];
        },
        get platform(){
            return Envjs.platform;
        },
        get plugins(){
            return [];
        },
        get userAgent(){
            return this.appCodeName + "/" + this.appVersion + " Resig/20070309 PilotFish/1.2.13";
        },
        javaEnabled : function(){
            return Envjs.javaEnabled;
        }
    };
};


/**
 * Screen
 * @param {Object} __window__
 */

Screen = function(__window__){

    var $availHeight  = 600,
        $availWidth   = 800,
        $colorDepth   = 16,
        $pixelDepth   = 24,
        $height       = 600,
        $width        = 800,
        $top          = 0,
        $left         = 0,
        $availTop     = 0,
        $availLeft    = 0;

    __extend__( __window__, {
        moveBy : function(dx,dy){
            //TODO - modify $locals to reflect change
        },
        moveTo : function(x,y) {
            //TODO - modify $locals to reflect change
        },
        /*print : function(){
            //TODO - good global to modify to ensure print is not misused
        };*/
        resizeBy : function(dw, dh){
            __window__resizeTo($width + dw, $height + dh);
        },
        resizeTo : function(width, height){
            $width = (width <= $availWidth) ? width : $availWidth;
            $height = (height <= $availHeight) ? height : $availHeight;
        },
        scroll : function(x,y){
            //TODO - modify $locals to reflect change
        },
        scrollBy : function(dx, dy){
            //TODO - modify $locals to reflect change
        },
        scrollTo : function(x,y){
            //TODO - modify $locals to reflect change
        }
    });

    return {
        get top(){
            return $top;
        },
        get left(){
            return $left;
        },
        get availTop(){
            return $availTop;
        },
        get availLeft(){
            return $availLeft;
        },
        get availHeight(){
            return $availHeight;
        },
        get availWidth(){
            return $availWidth;
        },
        get colorDepth(){
            return $colorDepth;
        },
        get pixelDepth(){
            return $pixelDepth;
        },
        get height(){
            return $height;
        },
        get width(){
            return $width;
        }
    };
};

/*
 * Copyright (c) 2010 Nick Galbreath
 * http://code.google.com/p/stringencoders/source/browse/#svn/trunk/javascript
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use,
 * copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following
 * conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 */

/* base64 encode/decode compatible with window.btoa/atob
 *
 * window.atob/btoa is a Firefox extension to convert binary data (the "b")
 * to base64 (ascii, the "a").
 *
 * It is also found in Safari and Chrome.  It is not available in IE.
 *
 * if (!window.btoa) window.btoa = base64.encode
 * if (!window.atob) window.atob = base64.decode
 *
 * The original spec's for atob/btoa are a bit lacking
 * https://developer.mozilla.org/en/DOM/window.atob
 * https://developer.mozilla.org/en/DOM/window.btoa
 *
 * window.btoa and base64.encode takes a string where charCodeAt is [0,255]
 * If any character is not [0,255], then an DOMException(5) is thrown.
 *
 * window.atob and base64.decode take a base64-encoded string
 * If the input length is not a multiple of 4, or contains invalid characters
 *   then an DOMException(5) is thrown.
 */
var base64 = {};
base64.PADCHAR = '=';
base64.ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

base64.makeDOMException = function() {
    // sadly in FF,Safari,Chrome you can't make a DOMException
    var e, tmp;

    try {
        return new DOMException(DOMException.INVALID_CHARACTER_ERR);
    } catch (tmp) {
        // not available, just passback a duck-typed equiv
        // https://developer.mozilla.org/en/Core_JavaScript_1.5_Reference/Global_Objects/Error
        // https://developer.mozilla.org/en/Core_JavaScript_1.5_Reference/Global_Objects/Error/prototype
        var ex = new Error("DOM Exception 5");

        // ex.number and ex.description is IE-specific.
        ex.code = ex.number = 5;
        ex.name = ex.description = "INVALID_CHARACTER_ERR";

        // Safari/Chrome output format
        ex.toString = function() { return 'Error: ' + ex.name + ': ' + ex.message; };
        return ex;
    }
};

base64.getbyte64 = function(s,i) {
    // This is oddly fast, except on Chrome/V8.
    //  Minimal or no improvement in performance by using a
    //   object with properties mapping chars to value (eg. 'A': 0)
    var idx = base64.ALPHA.indexOf(s.charAt(i));
    if (idx === -1) {
        throw base64.makeDOMException();
    }
    return idx;
};

base64.decode = function(s) {
    // convert to string
    s = '' + s;
    var getbyte64 = base64.getbyte64;
    var pads, i, b10;
    var imax = s.length;
    if (imax === 0) {
        return s;
    }

    if (imax % 4 !== 0) {
        throw base64.makeDOMException();
    }

    pads = 0;
    if (s.charAt(imax - 1) === base64.PADCHAR) {
        pads = 1;
        if (s.charAt(imax - 2) === base64.PADCHAR) {
            pads = 2;
        }
        // either way, we want to ignore this last block
        imax -= 4;
    }

    var x = [];
    for (i = 0; i < imax; i += 4) {
        b10 = (getbyte64(s,i) << 18) | (getbyte64(s,i+1) << 12) |
            (getbyte64(s,i+2) << 6) | getbyte64(s,i+3);
        x.push(String.fromCharCode(b10 >> 16, (b10 >> 8) & 0xff, b10 & 0xff));
    }

    switch (pads) {
    case 1:
        b10 = (getbyte64(s,i) << 18) | (getbyte64(s,i+1) << 12) | (getbyte64(s,i+2) << 6);
        x.push(String.fromCharCode(b10 >> 16, (b10 >> 8) & 0xff));
        break;
    case 2:
        b10 = (getbyte64(s,i) << 18) | (getbyte64(s,i+1) << 12);
        x.push(String.fromCharCode(b10 >> 16));
        break;
    }
    return x.join('');
};

base64.getbyte = function(s,i) {
    var x = s.charCodeAt(i);
    if (x > 255) {
        throw base64.makeDOMException();
    }
    return x;
};

base64.encode = function(s) {
    if (arguments.length !== 1) {
        throw new SyntaxError("Not enough arguments");
    }
    var padchar = base64.PADCHAR;
    var alpha   = base64.ALPHA;
    var getbyte = base64.getbyte;

    var i, b10;
    var x = [];

    // convert to string
    s = '' + s;

    var imax = s.length - s.length % 3;

    if (s.length === 0) {
        return s;
    }
    for (i = 0; i < imax; i += 3) {
        b10 = (getbyte(s,i) << 16) | (getbyte(s,i+1) << 8) | getbyte(s,i+2);
        x.push(alpha.charAt(b10 >> 18));
        x.push(alpha.charAt((b10 >> 12) & 0x3F));
        x.push(alpha.charAt((b10 >> 6) & 0x3f));
        x.push(alpha.charAt(b10 & 0x3f));
    }
    switch (s.length - imax) {
    case 1:
        b10 = getbyte(s,i) << 16;
        x.push(alpha.charAt(b10 >> 18) + alpha.charAt((b10 >> 12) & 0x3F) +
               padchar + padchar);
        break;
    case 2:
        b10 = (getbyte(s,i) << 16) | (getbyte(s,i+1) << 8);
        x.push(alpha.charAt(b10 >> 18) + alpha.charAt((b10 >> 12) & 0x3F) +
               alpha.charAt((b10 >> 6) & 0x3f) + padchar);
        break;
    }
    return x.join('');
};
//These descriptions of window properties are taken loosely David Flanagan's
//'JavaScript - The Definitive Guide' (O'Reilly)

var __windows__ = {};

var __top__ = function(_scope){
    var _parent = _scope.parent;
    while (_scope && _parent && _scope !== _parent) {
        if (_parent === _parent.parent) {
            break;
        }
        _parent = _parent.parent;
        //console.log('scope %s _parent %s', scope, _parent);
    }
    return _parent || null;
};

/**
 * Window
 * @param {Object} scope
 * @param {Object} parent
 * @param {Object} opener
 */
Window = function(scope, parent, opener){

    // the window property is identical to the self property and to this obj
    //var proxy = new Envjs.proxy(scope, parent);
    //scope.__proxy__ = proxy;
    scope.__defineGetter__('window', function(){
        return scope;
    });

    var $uuid = new Date().getTime()+'-'+Math.floor(Math.random()*1000000000000000);
    __windows__[$uuid] = scope;
    //console.log('opening window %s', $uuid);

    // every window has one-and-only-one .document property which is always
    // an [object HTMLDocument].  also, only window.document objects are
    // html documents, all other documents created by the window.document are
    // [object XMLDocument]
    var $htmlImplementation =  new DOMImplementation();
    $htmlImplementation.namespaceAware = true;
    $htmlImplementation.errorChecking = false;

    // read only reference to the Document object
    var $document = new HTMLDocument($htmlImplementation, scope);

    // A read-only reference to the Window object that contains this window
    // or frame.  If the window is a top-level window, parent refers to
    // the window itself.  If this window is a frame, this property refers
    // to the window or frame that contains it.
    var $parent = parent;

    /**> $cookies - see cookie.js <*/
    // read only boolean specifies whether the window has been closed
    var $closed = false;

    // a read/write string that specifies the default message that
    // appears in the status line
    var $defaultStatus = "Done";

    // IE only, refers to the most recent event object - this maybe be
    // removed after review
    var $event = null;

    // a read-only reference to the History object
    var $history = new History();

    // a read-only reference to the Location object.  the location object does
    // expose read/write properties
    var $location = new Location('about:blank', $document, $history);

    // The name of window/frame. Set directly, when using open(), or in frameset.
    // May be used when specifying the target attribute of links
    var $name = null;

    // a read-only reference to the Navigator object
    var $navigator = new Navigator();

    // a read/write reference to the Window object that contained the script
    // that called open() to open this browser window.  This property is valid
    // only for top-level window objects.
    var $opener = opener?opener:null;

    // read-only properties that specify the height and width, in pixels
    var $innerHeight = 600, $innerWidth = 800;

    // Read-only properties that specify the total height and width, in pixels,
    // of the browser window. These dimensions include the height and width of
    // the menu bar, toolbars, scrollbars, window borders and so on.  These
    // properties are not supported by IE and IE offers no alternative
    // properties;
    var $outerHeight = $innerHeight,
        $outerWidth = $innerWidth;

    // Read-only properties that specify the number of pixels that the current
    // document has been scrolled to the right and down.  These are not
    // supported by IE.
    var $pageXOffset = 0, $pageYOffset = 0;

    // a read-only reference to the Screen object that specifies information
    // about the screen: the number of available pixels and the number of
    // available colors.
    var $screen = new Screen(scope);

    // read only properties that specify the coordinates of the upper-left
    // corner of the screen.
    var $screenX = 1,
        $screenY = 1;
    var $screenLeft = $screenX,
        $screenTop = $screenY;

    // a read/write string that specifies the current status line.
    var $status = '';

    __extend__(scope, EventTarget.prototype);

    return __extend__( scope, {
        get closed(){
            return $closed;
        },
        get defaultStatus(){
            return $defaultStatus;
        },
        set defaultStatus(defaultStatus){
            $defaultStatus = defaultStatus;
        },
        get document(){
            return $document;
        },
        set document(doc){
            $document = doc;
        },
        /*
        deprecated ie specific property probably not good to support
        get event(){
            return $event;
        },
        */
        get frames(){
        return new HTMLCollection($document.getElementsByTagName('frame'));
        },
        get length(){
            // should be frames.length,
            return this.frames.length;
        },
        get history(){
            return $history;
        },
        get innerHeight(){
            return $innerHeight;
        },
        get innerWidth(){
            return $innerWidth;
        },
        get clientHeight(){
            return $innerHeight;
        },
        get clientWidth(){
            return $innerWidth;
        },
        get location(){
            return $location;
        },
        set location(uri){
            uri = Envjs.uri(uri);
            //new Window(this, this.parent, this.opener);
            if($location.href == uri){
                $location.reload();
            }else if($location.href == 'about:blank'){
                $location.assign(uri);
            }else{
                $location.replace(uri);
            }
        },
        get name(){
            return $name;
        },
        set name(newName){
            $name = newName;
        },
        get navigator(){
            return $navigator;
        },
        get opener(){
            return $opener;
        },
        get outerHeight(){
            return $outerHeight;
        },
        get outerWidth(){
            return $outerWidth;
        },
        get pageXOffest(){
            return $pageXOffset;
        },
        get pageYOffset(){
            return $pageYOffset;
        },
        get parent(){
            return $parent;
        },
        get screen(){
            return $screen;
        },
        get screenLeft(){
            return $screenLeft;
        },
        get screenTop(){
            return $screenTop;
        },
        get screenX(){
            return $screenX;
        },
        get screenY(){
            return $screenY;
        },
        get self(){
            return scope;
        },
        get status(){
            return $status;
        },
        set status(status){
            $status = status;
        },
        // a read-only reference to the top-level window that contains this window.
        // If this window is a top-level window it is simply a reference to itself.
        // If this window is a frame, the top property refers to the top-level
        // window that contains the frame.
        get top(){
            return __top__(scope);
        },
        get window(){
            return this;
        },
        toString : function(){
            return '[Window]';
        },

        /**
         * getComputedStyle
         *
         * Firefox 3.6:
         *  - Requires both elements to be present else an
         *    exception is thrown.
         *  - Returns a 'ComputedCSSStyleDeclaration' object.
         *    while a raw element.style returns a 'CSSStyleDeclaration' object.
         *  - Bogus input also throws exception
         *
         * Safari 4:
         *  - Requires one argument (second can be MIA)
         *  - Returns a CSSStyleDeclaration object
         *  - if bad imput, returns null
         *
         * getComputedStyle should really be an "add on" from the css
         * modules.  Unfortunately, 'window' comes way after the 'css'
         * so css can't add it.
         */
        getComputedStyle: function(element, pseudoElement) {
            return element.style;
        },

        open: function(url, name, features, replace){
            if (features) {
                console.log("'features argument not yet implemented");
            }
            var _window = Envjs.proxy({}),
                open;
            if(replace && name){
                for(open in __windows__){
                    if(open.name === name) {
                        _window = open;
                    }
                }
            }
            new Window(_window, _window, this);
            if(name) {
                _window.name = name;
            }
            _window.document.async = false;
            _window.location.assign(Envjs.uri(url));
            return _window;
        },
        close: function(){
            //console.log('closing window %s', __windows__[$uuid]);
            try{
                delete __windows__[$uuid];
            }catch(e){
                console.log('%s',e);
            }
        },
        alert : function(message){
            Envjs.alert(message);
        },
        confirm : function(question){
            Envjs.confirm(question);
        },
        prompt : function(message, defaultMsg){
            Envjs.prompt(message, defaultMsg);
        },
        btoa: function(binary){
            return base64.encode(binary);
        },
        atob: function(ascii){
            return base64.decode(ascii);
        },
        onload: function(){},
        onunload: function(){},
        get guid(){
            return $uuid;
        }
    });

};


//finally pre-supply the window with the window-like environment
//console.log('Default Window');
new Window(__this__, __this__);
console.log('[ %s ]',window.navigator.userAgent);
/**
 *
 * @param {Object} event
 */
__extend__(Envjs.defaultEventBehaviors,{

    'submit': function(event) {
        var target = event.target;
        while (target && target.nodeName !== 'FORM') {
            target = target.parentNode;
        }
        if (target && target.nodeName === 'FORM') {
            target.submit();
        }
    },
    'click': function(event) {
        // console.log('handling event target default behavior for click');
    }

});
/**
 * @author john resig & the envjs team
 * @uri http://www.envjs.com/
 * @copyright 2008-2010
 * @license MIT
 */
//CLOSURE_END
}());
