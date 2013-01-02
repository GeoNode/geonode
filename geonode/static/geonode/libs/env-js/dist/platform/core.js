/*
 * Envjs core-env.1.2.13
 * Pure JavaScript Browser Environment
 * By John Resig <http://ejohn.org/> and the Envjs Team
 * Copyright 2008-2010 John Resig, under the MIT License
 */

var Envjs = function(){
    var i,
        name,
        override = function(){
            for(i=0;i<arguments.length;i++){
                for ( name in arguments[i] ) {
                    var g = arguments[i].__lookupGetter__(name),
                        s = arguments[i].__lookupSetter__(name);
                    if ( g || s ) {
                        if ( g ) { Envjs.__defineGetter__(name, g); }
                        if ( s ) { Envjs.__defineSetter__(name, s); }
                    } else {
                        Envjs[name] = arguments[i][name];
                    }
                }
            }
        };
    if(arguments.length === 1 && typeof(arguments[0]) == 'string'){
        window.location = arguments[0];
    }else if (arguments.length === 1 && typeof(arguments[0]) == "object"){
        override(arguments[0]);
    }else if(arguments.length === 2 && typeof(arguments[0]) == 'string'){
        override(arguments[1]);
        window.location = arguments[0];
    }
    return;
},
__this__ = this;

//eg "Mozilla"
Envjs.appCodeName  = "Envjs";

//eg "Gecko/20070309 Firefox/2.0.0.3"
Envjs.appName      = "Netscape";

Envjs.version = "1.6";//?
Envjs.revision = '';
/*
 * Envjs core-env.1.2.13 
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
 * @author ariel flesler
 *    http://flesler.blogspot.com/2008/11/fast-trim-function-for-javascript.html
 * @param {Object} str
 */
function __trim__( str ){
    return (str || "").replace( /^\s+|\s+$/g, "" );
}


/**
 * Writes message to system out
 * @param {String} message
 */
Envjs.log = function(message){};

/**
 * Constants providing enumerated levels for logging in modules
 */
Envjs.DEBUG = 1;
Envjs.INFO = 2;
Envjs.WARN = 3;
Envjs.ERROR = 3;
Envjs.NONE = 3;

/**
 * Writes error info out to console
 * @param {Error} e
 */
Envjs.lineSource = function(e){};

    
/**
 * TODO: used in ./event/eventtarget.js
 * @param {Object} event
 */
Envjs.defaultEventBehaviors = {};


/**
 * describes which script src values will trigger Envjs to load
 * the script like a browser would
 */
Envjs.scriptTypes = {
    "text/javascript"   :false,
    "text/envjs"        :true
};

/**
 * will be called when loading a script throws an error
 * @param {Object} script
 * @param {Object} e
 */
Envjs.onScriptLoadError = function(script, e){
    console.log('error loading script %s %s', script, e);
};


/**
 * load and execute script tag text content
 * @param {Object} script
 */
Envjs.loadInlineScript = function(script){
    var tmpFile;
    tmpFile = Envjs.writeToTempFile(script.text, 'js') ;
    load(tmpFile);
};

/**
 * Should evaluate script in some context
 * @param {Object} context
 * @param {Object} source
 * @param {Object} name
 */
Envjs.eval = function(context, source, name){};


/**
 * Executes a script tag
 * @param {Object} script
 * @param {Object} parser
 */
Envjs.loadLocalScript = function(script){
    //console.log("loading script %s", script);
    var types,
    src,
    i,
    base,
    filename,
    xhr;

    if(script.type){
        types = script.type.split(";");
        for(i=0;i<types.length;i++){
            if(Envjs.scriptTypes[types[i]]){
                //ok this script type is allowed
                break;
            }
            if(i+1 == types.length){
                //console.log('wont load script type %s', script.type);
                return false;
            }
        }
    }

    try{
        //console.log('handling inline scripts');
        if(!script.src.length){
            Envjs.loadInlineScript(script);
            return true;
        }
    }catch(e){
        //Envjs.error("Error loading script.", e);
        Envjs.onScriptLoadError(script, e);
        return false;
    }


    //console.log("loading allowed external script %s", script.src);

    //lets you register a function to execute
    //before the script is loaded
    if(Envjs.beforeScriptLoad){
        for(src in Envjs.beforeScriptLoad){
            if(script.src.match(src)){
                Envjs.beforeScriptLoad[src](script);
            }
        }
    }
    base = "" + script.ownerDocument.location;
    //filename = Envjs.uri(script.src.match(/([^\?#]*)/)[1], base );
    //console.log('loading script from base %s', base);
    filename = Envjs.uri(script.src, base);
    try {
        xhr = new XMLHttpRequest();
        xhr.open("GET", filename, false/*syncronous*/);
        //console.log("loading external script %s", filename);
        xhr.onreadystatechange = function(){
            //console.log("readyState %s", xhr.readyState);
            if(xhr.readyState === 4){
                Envjs.eval(
                    script.ownerDocument.ownerWindow,
                    xhr.responseText,
                    filename
                );
            }
        };
        xhr.send(null, false);
    } catch(e) {
        console.log("could not load script %s \n %s", filename, e );
        Envjs.onScriptLoadError(script, e);
        return false;
    }
    //lets you register a function to execute
    //after the script is loaded
    if(Envjs.afterScriptLoad){
        for(src in Envjs.afterScriptLoad){
            if(script.src.match(src)){
                Envjs.afterScriptLoad[src](script);
            }
        }
    }
    return true;
};


/**
 * An 'image' was requested by the document.
 *
 * - During inital parse of a <link>
 * - Via an innerHTML parse of a <link>
 * - A modificiation of the 'src' attribute of an Image/HTMLImageElement
 *
 * NOTE: this is optional API.  If this doesn't exist then the default
 * 'loaded' event occurs.
 *
 * @param node {Object} the <img> node
 * @param node the src value
 * @return 'true' to indicate the 'load' succeed, false otherwise
 */
Envjs.loadImage = function(node, src) {
    return true;
};


/**
 * A 'link'  was requested by the document.  Typically this occurs when:
 * - During inital parse of a <link>
 * - Via an innerHTML parse of a <link>
 * - A modificiation of the 'href' attribute on a <link> node in the tree
 *
 * @param node {Object} is the link node in question
 * @param href {String} is the href.
 *
 * Return 'true' to indicate that the 'load' was successful, or false
 * otherwise.  The appropriate event is then triggered.
 *
 * NOTE: this is optional API.  If this doesn't exist then the default
 *   'loaded' event occurs
 */
Envjs.loadLink = function(node, href) {
    return true;
};

(function(){


/*
 *  cookie handling
 *  Private internal helper class used to save/retreive cookies
 */

/**
 * Specifies the location of the cookie file
 */
Envjs.cookieFile = function(){
    return 'file://'+Envjs.homedir+'/.cookies';
};

/**
 * saves cookies to a local file
 * @param {Object} htmldoc
 */
Envjs.saveCookies = function(){
    var cookiejson = JSON.stringify(Envjs.cookies.peristent,null,'\t');
    //console.log('persisting cookies %s', cookiejson);
    Envjs.writeToFile(cookiejson, Envjs.cookieFile());
};

/**
 * loads cookies from a local file
 * @param {Object} htmldoc
 */
Envjs.loadCookies = function(){
    var cookiejson,
        js;
    try{
        cookiejson = Envjs.readFromFile(Envjs.cookieFile())
        js = JSON.parse(cookiejson, null, '\t');
    }catch(e){
        //console.log('failed to load cookies %s', e);
        js = {};
    }
    return js;
};

Envjs.cookies = {
    persistent:{
        //domain - key on domain name {
            //path - key on path {
                //name - key on name {
                     //value : cookie value
                     //other cookie properties
                //}
            //}
        //}
        //expire - provides a timestamp for expiring the cookie
        //cookie - the cookie!
    },
    temporary:{//transient is a reserved word :(
        //like above
    }
};

var __cookies__;

//HTMLDocument cookie
Envjs.setCookie = function(url, cookie){
    var i,
        index,
        name,
        value,
        properties = {},
        attr,
        attrs;
    url = Envjs.urlsplit(url);
    if(cookie)
        attrs = cookie.split(";");
    else
        return;
    
    //for now the strategy is to simply create a json object
    //and post it to a file in the .cookies.js file.  I hate parsing
    //dates so I decided not to implement support for 'expires' 
    //(which is deprecated) and instead focus on the easier 'max-age'
    //(which succeeds 'expires') 
    cookie = {};//keyword properties of the cookie
    cookie['domain'] = url.hostname;
    cookie['path'] = url.path||'/';
    for(i=0;i<attrs.length;i++){
        index = attrs[i].indexOf("=");
        if(index > -1){
            name = __trim__(attrs[i].slice(0,index));
            value = __trim__(attrs[i].slice(index+1));
            if(name=='max-age'){
                //we'll have to when to check these
                //and garbage collect expired cookies
                cookie[name] = parseInt(value, 10);
            } else if( name == 'domain' ){
                if(__domainValid__(url, value)){
                    cookie['domain'] = value;
                }
            } else if( name == 'path' ){
                //not sure of any special logic for path
                cookie['path'] = value;
            } else {
                //its not a cookie keyword so store it in our array of properties
                //and we'll serialize individually in a moment
                properties[name] = value;
            }
        }else{
            if( attrs[i] == 'secure' ){
                cookie[attrs[i]] = true;
            }
        }
    }
    if(!('max-age' in cookie)){
        //it's a transient cookie so it only lasts as long as 
        //the window.location remains the same (ie in-memory cookie)
        __mergeCookie__(Envjs.cookies.temporary, cookie, properties);
    }else{
        //the cookie is persistent
        __mergeCookie__(Envjs.cookies.persistent, cookie, properties);
        Envjs.saveCookies();
    }
};

function __domainValid__(url, value){
    var i,
        domainParts = url.hostname.split('.').reverse(),
        newDomainParts = value.split('.').reverse();
    if(newDomainParts.length > 1){
        for(i=0;i<newDomainParts.length;i++){
            if(!(newDomainParts[i] == domainParts[i])){
                return false;
            }
        }
        return true;
    }
    return false;
};

Envjs.getCookies = function(url){
    //The cookies that are returned must belong to the same domain
    //and be at or below the current window.location.path.  Also
    //we must check to see if the cookie was set to 'secure' in which
    //case we must check our current location.protocol to make sure it's
    //https:
    var persisted;
    url = Envjs.urlsplit(url);
    if(!__cookies__){
        try{
            __cookies__ = true;
            try{
                persisted = Envjs.loadCookies();
            }catch(e){
                //fail gracefully
                //console.log('%s', e);
            }   
            if(persisted){
                __extend__(Envjs.cookies.persistent, persisted);
            }
            //console.log('set cookies for doc %s', doc.baseURI);
        }catch(e){
            console.log('cookies not loaded %s', e)
        };
    }
    var temporary = __cookieString__(Envjs.cookies.temporary, url),
        persistent =  __cookieString__(Envjs.cookies.persistent, url);
    //console.log('temporary cookies: %s', temporary);  
    //console.log('persistent cookies: %s', persistent);  
    return  temporary + persistent;
};

function __cookieString__(cookies, url) {
    var cookieString = "",
        domain, 
        path,
        name,
        i=0;
    for (domain in cookies) {
        // check if the cookie is in the current domain (if domain is set)
        // console.log('cookie domain %s', domain);
        if (domain == "" || domain == url.hostname) {
            for (path in cookies[domain]) {
                // console.log('cookie domain path %s', path);
                // make sure path is at or below the window location path
                if (path == "/" || url.path.indexOf(path) > -1) {
                    for (name in cookies[domain][path]) {
                        // console.log('cookie domain path name %s', name);
                        cookieString += 
                            ((i++ > 0)?'; ':'') +
                            name + "=" + 
                            cookies[domain][path][name].value;
                    }
                }
            }
        }
    }
    return cookieString;
};

function __mergeCookie__(target, cookie, properties){
    var name, now;
    if(!target[cookie.domain]){
        target[cookie.domain] = {};
    }
    if(!target[cookie.domain][cookie.path]){
        target[cookie.domain][cookie.path] = {};
    }
    for(name in properties){
        now = new Date().getTime();
        target[cookie.domain][cookie.path][name] = {
            "value":properties[name],
            "secure":cookie.secure,
            "max-age":cookie['max-age'],
            "date-created":now,
            "expiration":(cookie['max-age']===0) ? 
                0 :
                now + cookie['max-age']
        };
        //console.log('cookie is %o',target[cookie.domain][cookie.path][name]);
    }
};

})();//end cookies
/*
    http://www.JSON.org/json2.js
    2008-07-15

    Public Domain.

    NO WARRANTY EXPRESSED OR IMPLIED. USE AT YOUR OWN RISK.

    See http://www.JSON.org/js.html

   
    This code should be minified before deployment.
    See http://javascript.crockford.com/jsmin.html

    USE YOUR OWN COPY. IT IS EXTREMELY UNWISE TO LOAD CODE FROM SERVERS YOU DO
    NOT CONTROL.
*/
try{ JSON; }catch(e){ 
JSON = function () {

    function f(n) {
        // Format integers to have at least two digits.
        return n < 10 ? '0' + n : n;
    }

    Date.prototype.toJSON = function (key) {

        return this.getUTCFullYear()   + '-' +
             f(this.getUTCMonth() + 1) + '-' +
             f(this.getUTCDate())      + 'T' +
             f(this.getUTCHours())     + ':' +
             f(this.getUTCMinutes())   + ':' +
             f(this.getUTCSeconds())   + 'Z';
    };

    String.prototype.toJSON = function (key) {
        return String(this);
    };
    Number.prototype.toJSON =
    Boolean.prototype.toJSON = function (key) {
        return this.valueOf();
    };

    var cx = /[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
        escapeable = /[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
        gap,
        indent,
        meta = {    // table of character substitutions
            '\b': '\\b',
            '\t': '\\t',
            '\n': '\\n',
            '\f': '\\f',
            '\r': '\\r',
            '"' : '\\"',
            '\\': '\\\\'
        },
        rep;


    function quote(string) {
        
        escapeable.lastIndex = 0;
        return escapeable.test(string) ?
            '"' + string.replace(escapeable, function (a) {
                var c = meta[a];
                if (typeof c === 'string') {
                    return c;
                }
                return '\\u' + ('0000' +
                        (+(a.charCodeAt(0))).toString(16)).slice(-4);
            }) + '"' :
            '"' + string + '"';
    }


    function str(key, holder) {

        var i,          // The loop counter.
            k,          // The member key.
            v,          // The member value.
            length,
            mind = gap,
            partial,
            value = holder[key];

        if (value && typeof value === 'object' &&
                typeof value.toJSON === 'function') {
            value = value.toJSON(key);
        }
        if (typeof rep === 'function') {
            value = rep.call(holder, key, value);
        }

        switch (typeof value) {
        case 'string':
            return quote(value);

        case 'number':
            return isFinite(value) ? String(value) : 'null';

        case 'boolean':
        case 'null':

            return String(value);
            
        case 'object':

            if (!value) {
                return 'null';
            }
            gap += indent;
            partial = [];

            if (typeof value.length === 'number' &&
                    !(value.propertyIsEnumerable('length'))) {

                length = value.length;
                for (i = 0; i < length; i += 1) {
                    partial[i] = str(i, value) || 'null';
                }
                
                v = partial.length === 0 ? '[]' :
                    gap ? '[\n' + gap +
                            partial.join(',\n' + gap) + '\n' +
                                mind + ']' :
                          '[' + partial.join(',') + ']';
                gap = mind;
                return v;
            }

            if (rep && typeof rep === 'object') {
                length = rep.length;
                for (i = 0; i < length; i += 1) {
                    k = rep[i];
                    if (typeof k === 'string') {
                        v = str(k, value);
                        if (v) {
                            partial.push(quote(k) + (gap ? ': ' : ':') + v);
                        }
                    }
                }
            } else {

                for (k in value) {
                    if (Object.hasOwnProperty.call(value, k)) {
                        v = str(k, value);
                        if (v) {
                            partial.push(quote(k) + (gap ? ': ' : ':') + v);
                        }
                    }
                }
            }

            v = partial.length === 0 ? '{}' :
                gap ? '{\n' + gap + partial.join(',\n' + gap) + '\n' +
                        mind + '}' : '{' + partial.join(',') + '}';
            gap = mind;
            return v;
        }
    }

    return {
        stringify: function (value, replacer, space) {

            var i;
            gap = '';
            indent = '';

            if (typeof space === 'number') {
                for (i = 0; i < space; i += 1) {
                    indent += ' ';
                }

            } else if (typeof space === 'string') {
                indent = space;
            }

            rep = replacer;
            if (replacer && typeof replacer !== 'function' &&
                    (typeof replacer !== 'object' ||
                     typeof replacer.length !== 'number')) {
                throw new Error('JSON.stringify');
            }

            return str('', {'': value});
        },


        parse: function (text, reviver) {
            var j;
            function walk(holder, key) {
                var k, v, value = holder[key];
                if (value && typeof value === 'object') {
                    for (k in value) {
                        if (Object.hasOwnProperty.call(value, k)) {
                            v = walk(value, k);
                            if (v !== undefined) {
                                value[k] = v;
                            } else {
                                delete value[k];
                            }
                        }
                    }
                }
                return reviver.call(holder, key, value);
            }

            cx.lastIndex = 0;
            if (cx.test(text)) {
                text = text.replace(cx, function (a) {
                    return '\\u' + ('0000' +
                            (+(a.charCodeAt(0))).toString(16)).slice(-4);
                });
            }


            if (/^[\],:{}\s]*$/.
test(text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g, '@').
replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, ']').
replace(/(?:^|:|,)(?:\s*\[)+/g, ''))) {
        
                j = eval('(' + text + ')');

                return typeof reviver === 'function' ?
                    walk({'': j}, '') : j;
            }

            throw new SyntaxError('JSON.parse');
        }
    };
}();

}

/**
 * synchronizes thread modifications
 * @param {Function} fn
 */
Envjs.sync = function(fn){};

/**
 * sleep thread for specified duration
 * @param {Object} millseconds
 */
Envjs.sleep = function(millseconds){};

/**
 * Interval to wait on event loop when nothing is happening
 */
Envjs.WAIT_INTERVAL = 20;//milliseconds

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

/*
 * url processing in the spirit of python's urlparse module
 * see `pydoc urlparse` or
 * http://docs.python.org/library/urlparse.html
 *
 *  urlsplit: break apart a URL into components
 *  urlunsplit:  reconsistute a URL from componets
 *  urljoin: join an absolute and another URL
 *  urldefrag: remove the fragment from a URL
 *
 * Take a look at the tests in urlparse-test.html
 *
 * On URL Normalization:
 *
 * urlsplit only does minor normalization the components Only scheme
 * and hostname are lowercased urljoin does a bit more, normalizing
 * paths with "."  and "..".

 * urlnormalize adds additional normalization
 *
 *   * removes default port numbers
 *     http://abc.com:80/ -> http://abc.com/, etc
 *   * normalizes path
 *     http://abc.com -> http://abc.com/
 *     and other "." and ".." cleanups
 *   * if file, remove query and fragment
 *
 * It does not do:
 *   * normalizes escaped hex values
 *     http://abc.com/%7efoo -> http://abc.com/%7Efoo
 *   * normalize '+' <--> '%20'
 *
 * Differences with Python
 *
 * The javascript urlsplit returns a normal object with the following
 * properties: scheme, netloc, hostname, port, path, query, fragment.
 * All properties are read-write.
 *
 * In python, the resulting object is not a dict, but a specialized,
 * read-only, and has alternative tuple interface (e.g. obj[0] ==
 * obj.scheme).  It's not clear why such a simple function requires
 * a unique datastructure.
 *
 * urlunsplit in javascript takes an duck-typed object,
 *  { scheme: 'http', netloc: 'abc.com', ...}
 *  while in  * python it takes a list-like object.
 *  ['http', 'abc.com'... ]
 *
 * For all functions, the javascript version use
 * hostname+port if netloc is missing.  In python
 * hostname+port were always ignored.
 *
 * Similar functionality in different languages:
 *
 *   http://php.net/manual/en/function.parse-url.php
 *   returns assocative array but cannot handle relative URL
 *
 * TODO: test allowfragments more
 * TODO: test netloc missing, but hostname present
 */

var urlparse = {};

// Unlike to be useful standalone
//
// NORMALIZE PATH with "../" and "./"
//   http://en.wikipedia.org/wiki/URL_normalization
//   http://tools.ietf.org/html/rfc3986#section-5.2.3
//
urlparse.normalizepath = function(path)
{
    if (!path || path === '/') {
        return '/';
    }

    var parts = path.split('/');

    var newparts = [];
    // make sure path always starts with '/'
    if (parts[0]) {
        newparts.push('');
    }

    for (var i = 0; i < parts.length; ++i) {
        if (parts[i] === '..') {
            if (newparts.length > 1) {
                newparts.pop();
            } else {
                newparts.push(parts[i]);
            }
        } else if (parts[i] != '.') {
            newparts.push(parts[i]);
        }
    }

    path = newparts.join('/');
    if (!path) {
        path = '/';
    }
    return path;
};

//
// Does many of the normalizations that the stock
//  python urlsplit/urlunsplit/urljoin neglects
//
// Doesn't do hex-escape normalization on path or query
//   %7e -> %7E
// Nor, '+' <--> %20 translation
//
urlparse.urlnormalize = function(url)
{
    var parts = urlparse.urlsplit(url);
    switch (parts.scheme) {
    case 'file':
        // files can't have query strings
        //  and we don't bother with fragments
        parts.query = '';
        parts.fragment = '';
        break;
    case 'http':
    case 'https':
        // remove default port
        if ((parts.scheme === 'http' && parts.port == 80) ||
            (parts.scheme === 'https' && parts.port == 443)) {
            parts.port = null;
            // hostname is already lower case
            parts.netloc = parts.hostname;
        }
        break;
    default:
        // if we don't have specific normalizations for this
        // scheme, return the original url unmolested
        return url;
    }

    // for [file|http|https].  Not sure about other schemes
    parts.path = urlparse.normalizepath(parts.path);

    return urlparse.urlunsplit(parts);
};

urlparse.urldefrag = function(url)
{
    var idx = url.indexOf('#');
    if (idx == -1) {
        return [ url, '' ];
    } else {
        return [ url.substr(0,idx), url.substr(idx+1) ];
    }
};

urlparse.urlsplit = function(url, default_scheme, allow_fragments)
{
    var leftover;

    if (typeof allow_fragments === 'undefined') {
        allow_fragments = true;
    }

    // scheme (optional), host, port
    var fullurl = /^([A-Za-z]+)?(:?\/\/)([0-9.\-A-Za-z]*)(?::(\d+))?(.*)$/;
    // path, query, fragment
    var parse_leftovers = /([^?#]*)?(?:\?([^#]*))?(?:#(.*))?$/;

    var o = {};

    var parts = url.match(fullurl);
    if (parts) {
        o.scheme = parts[1] || default_scheme || '';
        o.hostname = parts[3].toLowerCase() || '';
        o.port = parseInt(parts[4],10) || '';
        // Probably should grab the netloc from regexp
        //  and then parse again for hostname/port

        o.netloc = parts[3];
        if (parts[4]) {
            o.netloc += ':' + parts[4];
        }

        leftover = parts[5];
    } else {
        o.scheme = default_scheme || '';
        o.netloc = '';
        o.hostname = '';
        leftover = url;
    }
    o.scheme = o.scheme.toLowerCase();

    parts = leftover.match(parse_leftovers);

    o.path =  parts[1] || '';
    o.query = parts[2] || '';

    if (allow_fragments) {
        o.fragment = parts[3] || '';
    } else {
        o.fragment = '';
    }

    return o;
};

urlparse.urlunsplit = function(o) {
    var s = '';
    if (o.scheme) {
        s += o.scheme + '://';
    }

    if (o.netloc) {
        if (s == '') {
            s += '//';
        }
        s +=  o.netloc;
    } else if (o.hostname) {
        // extension.  Python only uses netloc
        if (s == '') {
            s += '//';
        }
        s += o.hostname;
        if (o.port) {
            s += ':' + o.port;
        }
    }

    if (o.path) {
        s += o.path;
    }

    if (o.query) {
        s += '?' + o.query;
    }
    if (o.fragment) {
        s += '#' + o.fragment;
    }
    return s;
};

urlparse.urljoin = function(base, url, allow_fragments)
{
    if (typeof allow_fragments === 'undefined') {
        allow_fragments = true;
    }

    var url_parts = urlparse.urlsplit(url);

    // if url parts has a scheme (i.e. absolute)
    // then nothing to do
    if (url_parts.scheme) {
        if (! allow_fragments) {
            return url;
        } else {
            return urlparse.urldefrag(url)[0];
        }
    }
    var base_parts = urlparse.urlsplit(base);

    // copy base, only if not present
    if (!base_parts.scheme) {
        base_parts.scheme = url_parts.scheme;
    }

    // copy netloc, only if not present
    if (!base_parts.netloc || !base_parts.hostname) {
        base_parts.netloc = url_parts.netloc;
        base_parts.hostname = url_parts.hostname;
        base_parts.port = url_parts.port;
    }

    // paths
    if (url_parts.path.length > 0) {
        if (url_parts.path.charAt(0) == '/') {
            base_parts.path = url_parts.path;
        } else {
            // relative path.. get rid of "current filename" and
            //   replace.  Same as var parts =
            //   base_parts.path.split('/'); parts[parts.length-1] =
            //   url_parts.path; base_parts.path = parts.join('/');
            var idx = base_parts.path.lastIndexOf('/');
            if (idx == -1) {
                base_parts.path = url_parts.path;
            } else {
                base_parts.path = base_parts.path.substr(0,idx) + '/' +
                    url_parts.path;
            }
        }
    }

    // clean up path
    base_parts.path = urlparse.normalizepath(base_parts.path);

    // copy query string
    base_parts.query = url_parts.query;

    // copy fragments
    if (allow_fragments) {
        base_parts.fragment = url_parts.fragment;
    } else {
        base_parts.fragment = '';
    }

    return urlparse.urlunsplit(base_parts);
};

/**
 * getcwd - named after posix call of same name (see 'man 2 getcwd')
 *
 */
Envjs.getcwd = function() {
    return '.';
};

/**
 * resolves location relative to doc location
 *
 * @param {Object} path  Relative or absolute URL
 * @param {Object} base  (semi-optional)  The base url used in resolving "path" above
 */
Envjs.uri = function(path, base) {
    //console.log('constructing uri from path %s and base %s', path, base);

    // Semi-common trick is to make an iframe with src='javascript:false'
    //  (or some equivalent).  By returning '', the load is skipped
    if (path.indexOf('javascript') === 0) {
        return '';
    }

    // if path is absolute, then just normalize and return
    if (path.match('^[a-zA-Z]+://')) {
        return urlparse.urlnormalize(path);
    }

    // interesting special case, a few very large websites use
    // '//foo/bar/' to mean 'http://foo/bar'
    if (path.match('^//')) {
        path = 'http:' + path;
    }

    // if base not passed in, try to get it from document
    // Ideally I would like the caller to pass in document.baseURI to
    //  make this more self-sufficient and testable
    if (!base && document) {
        base = document.baseURI;
    }

    // about:blank doesn't count
    if (base === 'about:blank'){
        base = '';
    }

    // if base is still empty, then we are in QA mode loading local
    // files.  Get current working directory
    if (!base) {
        base = 'file://' +  Envjs.getcwd() + '/';
    }
    // handles all cases if path is abosulte or relative to base
    // 3rd arg is "false" --> remove fragments
    var newurl = urlparse.urlnormalize(urlparse.urljoin(base, path, false));

    return newurl;
};



/**
 * Used in the XMLHttpRquest implementation to run a
 * request in a seperate thread
 * @param {Object} fn
 */
Envjs.runAsync = function(fn){};


/**
 * Used to write to a local file
 * @param {Object} text
 * @param {Object} url
 */
Envjs.writeToFile = function(text, url){};


/**
 * Used to write to a local file
 * @param {Object} text
 * @param {Object} suffix
 */
Envjs.writeToTempFile = function(text, suffix){};

/**
 * Used to read the contents of a local file
 * @param {Object} url
 */
Envjs.readFromFile = function(url){};

/**
 * Used to delete a local file
 * @param {Object} url
 */
Envjs.deleteFile = function(url){};

/**
 * establishes connection and calls responsehandler
 * @param {Object} xhr
 * @param {Object} responseHandler
 * @param {Object} data
 */
Envjs.connection = function(xhr, responseHandler, data){};


__extend__(Envjs, urlparse);

/**
 * Makes an object window-like by proxying object accessors
 * @param {Object} scope
 * @param {Object} parent
 */
Envjs.proxy = function(scope, parent, aliasList){};

Envjs.javaEnabled = false;

Envjs.homedir        = '';
Envjs.tmpdir         = '';
Envjs.os_name        = '';
Envjs.os_arch        = '';
Envjs.os_version     = '';
Envjs.lang           = '';
Envjs.platform       = '';

/**
 *
 * @param {Object} frameElement
 * @param {Object} url
 */
Envjs.loadFrame = function(frame, url){
    try {
        if(frame.contentWindow){
            //mark for garbage collection
            frame.contentWindow = null;
        }

        //create a new scope for the window proxy
        //platforms will need to override this function
        //to make sure the scope is global-like
        frame.contentWindow = (function(){return this;})();
        new Window(frame.contentWindow, window);

        //I dont think frames load asynchronously in firefox
        //and I think the tests have verified this but for
        //some reason I'm less than confident... Are there cases?
        frame.contentDocument = frame.contentWindow.document;
        frame.contentDocument.async = false;
        if(url){
            //console.log('envjs.loadFrame async %s', frame.contentDocument.async);
            frame.contentWindow.location = url;
        }
    } catch(e) {
        console.log("failed to load frame content: from %s %s", url, e);
    }
};


// The following are in rhino/window.js
// TODO: Envjs.unloadFrame
// TODO: Envjs.proxy

/**
 * @author john resig & the envjs team
 * @uri http://www.envjs.com/
 * @copyright 2008-2010
 * @license MIT
 */
//CLOSURE_END
}());
