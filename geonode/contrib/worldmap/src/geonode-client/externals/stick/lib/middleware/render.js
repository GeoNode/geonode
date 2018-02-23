/**
 * @fileOverview This module provides middleware for rendering responses
 * using ringo/mustache.
 *
 * This middleware installs a `render` function in the application object
 * which is used to render HTTP responses. The behaviour of `app.render` can
 * be tweaked by setting the following properties:
 *
 *  - `render.base` - the base path or repository to look for templates
 *  - `render.helpers` - helper functions that will be merged in the context
 *  - `render.master`  - master template to apply to every page
 *  - `render.contentType` - MIME type to use for HTTP response
 *  - `render.charset` - charset name to use for HTTP response
 *
 * @example
 * app.configure("render");
 * app.render.base = module.resolve("templates");
 * app.render("index.tmpl", {data: "Hello World!"});
 */
var objects = require("ringo/utils/objects");
var mustache = require("ringo/mustache");
var {isRelative} = require("fs");
var {Resource, Repository} =  org.ringojs.repository;

/**
 * Middleware for template based response generation.
 * @param {Function} next the wrapped middleware chain
 * @param {Object} app the Stick Application object
 * @returns {Function} a JSGI middleware function
 */
exports.middleware = function render(next, app) {

    var _base, _master, _helpers,
        _contentType = "text/html",
        _charset = "utf-8";

    app.render = function(template, context, options) {
        var content = app.renderPart(template, context, options);

        var base = options && options.base || _base;
        var contentType = options && options.contentType || _contentType;
        var charset = options && options.charset || _charset;
        var req = app.request;
        var master = options && options.master
                || req && req.env.masterTemplate
                || _master;

        if (_helpers) {
            context = objects.merge(context, _helpers);
        }
        if (master) {
            context.content = content;
            content = mustache.to_html(resolve(master, base), context);
        }

        return {
            status: 200,
            headers: {"Content-Type": contentType + "; charset=" + charset},
            body: [content]
        };
    };

    app.renderPart = function(template, context, options) {
        var base = options && options.base || _base;

        if (_helpers) {
            context = objects.merge(context, _helpers);
        }

        template = resolve(template, base);
        return mustache.to_html(template, context);
    };

    function resolve(template, base) {
        if (!(template instanceof Resource)) {
            template = base && isRelative(template) ?
                    base.getResource(template) : getResource(template);
        }
        if (!template || !template.exists()) {
            throw new Error("Template " + template + " not found");
        }
        return template.getContent();
    }

    Object.defineProperty(app.render, "base", {
        get: function() _base,
        set: function(value) {
            _base = value instanceof Repository ?
                value : getRepository(value);
        },
        enumerable: true
    });

    Object.defineProperty(app.render, "master", {
        get: function() _master,
        set: function(value) {_master = value},
        enumerable: true
    });

    Object.defineProperty(app.render, "helpers", {
        get: function() _helpers,
        set: function(value) {_helpers = value},
        enumerable: true
    });

    Object.defineProperty(app.render, "contentType", {
        get: function() _contentType,
        set: function(value) {_contentType = value},
        enumerable: true
    });

    Object.defineProperty(app.render, "charset", {
        get: function() _charset,
        set: function(value) {_charset = value},
        enumerable: true
    });

    // We don't actually add any middleware
    return next;

};

