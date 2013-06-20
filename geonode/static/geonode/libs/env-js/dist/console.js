
/**
 * @author envjs team
 */
var Console,
    console;

/*
 * Envjs console.1.2.13 
 * Pure JavaScript Browser Environment
 * By John Resig <http://ejohn.org/> and the Envjs Team
 * Copyright 2008-2010 John Resig, under the MIT License
 */

//CLOSURE_START
(function(){





/**
 * @author envjs team
 * borrowed 99%-ish with love from firebug-lite
 *
 * http://wiki.commonjs.org/wiki/Console
 */
Console = function(module){
    var $level,
    $logger,
    $null = function(){};


    if(Envjs[module] && Envjs[module].loglevel){
        $level = Envjs.module.loglevel;
        $logger = {
            log: function(level){
                logFormatted(arguments, (module)+" ");
            },
            debug: $level>1 ? $null: function() {
                logFormatted(arguments, (module)+" debug");
            },
            info: $level>2 ? $null:function(){
                logFormatted(arguments, (module)+" info");
            },
            warn: $level>3 ? $null:function(){
                logFormatted(arguments, (module)+" warning");
            },
            error: $level>4 ? $null:function(){
                logFormatted(arguments, (module)+" error");
            }
        };
    } else {
        $logger = {
            log: function(level){
                logFormatted(arguments, "");
            },
            debug: $null,
            info: $null,
            warn: $null,
            error: $null
        };
    }

    return $logger;
};

console = new Console("console",1);

function logFormatted(objects, className)
{
    var html = [];

    var format = objects[0];
    var objIndex = 0;

    if (typeof(format) != "string")
    {
        format = "";
        objIndex = -1;
    }

    var parts = parseFormat(format);
    for (var i = 0; i < parts.length; ++i)
    {
        var part = parts[i];
        if (part && typeof(part) == "object")
        {
            var object = objects[++objIndex];
            part.appender(object, html);
        }
        else {
            appendText(part, html);
	}
    }

    for (var i = objIndex+1; i < objects.length; ++i)
    {
        appendText(" ", html);

        var object = objects[i];
        if (typeof(object) == "string") {
            appendText(object, html);
        } else {
            appendObject(object, html);
	}
    }

    Envjs.log(html.join(' '));
}

function parseFormat(format)
{
    var parts = [];

    var reg = /((^%|[^\\]%)(\d+)?(\.)([a-zA-Z]))|((^%|[^\\]%)([a-zA-Z]))/;
    var appenderMap = {s: appendText, d: appendInteger, i: appendInteger, f: appendFloat};

    for (var m = reg.exec(format); m; m = reg.exec(format))
    {
        var type = m[8] ? m[8] : m[5];
        var appender = type in appenderMap ? appenderMap[type] : appendObject;
        var precision = m[3] ? parseInt(m[3]) : (m[4] == "." ? -1 : 0);

        parts.push(format.substr(0, m[0][0] == "%" ? m.index : m.index+1));
        parts.push({appender: appender, precision: precision});

        format = format.substr(m.index+m[0].length);
    }

    parts.push(format);

    return parts;
}

function escapeHTML(value)
{
    return value;
}

function objectToString(object)
{
    try
    {
        return object+"";
    }
    catch (exc)
    {
        return null;
    }
}

// ********************************************************************************************

function appendText(object, html)
{
    html.push(escapeHTML(objectToString(object)));
}

function appendNull(object, html)
{
    html.push(escapeHTML(objectToString(object)));
}

function appendString(object, html)
{
    html.push(escapeHTML(objectToString(object)));
}

function appendInteger(object, html)
{
    html.push(escapeHTML(objectToString(object)));
}

function appendFloat(object, html)
{
    html.push(escapeHTML(objectToString(object)));
}

function appendFunction(object, html)
{
    var reName = /function ?(.*?)\(/;
    var m = reName.exec(objectToString(object));
    var name = m ? m[1] : "function";
    html.push(escapeHTML(name));
}

function appendObject(object, html)
{
    try
    {
        if (object == undefined) {
            appendNull("undefined", html);
        } else if (object == null) {
            appendNull("null", html);
        } else if (typeof object == "string") {
            appendString(object, html);
	} else if (typeof object == "number") {
            appendInteger(object, html);
	} else if (typeof object == "function") {
            appendFunction(object, html);
        } else if (object.nodeType == 1) {
            appendSelector(object, html);
        } else if (typeof object == "object") {
            appendObjectFormatted(object, html);
        } else {
            appendText(object, html);
	}
    }
    catch (exc)
    {
    }
}

function appendObjectFormatted(object, html)
{
    var text = objectToString(object);
    var reObject = /\[object (.*?)\]/;

    var m = reObject.exec(text);
    html.push( m ? m[1] : text);
}

function appendSelector(object, html)
{

    html.push(escapeHTML(object.nodeName.toLowerCase()));
    if (object.id) {
        html.push(escapeHTML(object.id));
    }
    if (object.className) {
        html.push(escapeHTML(object.className));
    }
}

function appendNode(node, html)
{
    if (node.nodeType == 1)
    {
        html.push( node.nodeName.toLowerCase());

        for (var i = 0; i < node.attributes.length; ++i)
        {
            var attr = node.attributes[i];
            if (!attr.specified) {
                continue;
	    }

            html.push( attr.nodeName.toLowerCase(),escapeHTML(attr.nodeValue));
        }

        if (node.firstChild)
        {
            for (var child = node.firstChild; child; child = child.nextSibling) {
                appendNode(child, html);
	    }

            html.push( node.nodeName.toLowerCase());
        }
    }
    else if (node.nodeType === 3)
    {
        html.push(escapeHTML(node.nodeValue));
    }
};

/**
 * @author john resig & the envjs team
 * @uri http://www.envjs.com/
 * @copyright 2008-2010
 * @license MIT
 */
//CLOSURE_END
}());
