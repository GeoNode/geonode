/**
 * @fileoverview This module provides middleware for HTTP sessions.
 *
 * It adds a `session` property to the request object that allows to store
 * arbitrary data on on a per-visitor basis.
 *
 * The default session implementation is based on Java Servlet sessions.
 * This can be overridden by setting the `app.session.impl` property to an
 * alternative session constructor.
 *
 *     app.session.impl = MySession;
 *
 * The session constructor will be called
 * with the request object as only argument when the session is first accessed.
 */

/**
 * This middleware provides support for anonymous user sessions.
 *
 * @param {Function} next the wrapped middleware chain
 * @param {Object} app the Stick Application object
 * @returns {Function} a JSGI middleware function
 */
exports.middleware = function session(next, app) {

    // make session implementation configurable
    app.session = {
        impl: ServletSession
    };

    return function session(req) {

        var _session;

        /**
         * A session object for the current request. If no session exists
         * a new one will be created.
         * @see ServletSession
         * @name request.session
         */
        Object.defineProperty(req, "session", {
            get: function() {
                if (!_session)
                    _session = new app.session.impl(req);
                return _session;
            }
        });

        return next(req);
    };
};


/**
 * An HTTP session object based on top of servlet sessions.
 * Properties of the session's data object are persisted
 * between requests of the same client.
 * @param request a JSGI or servlet request object
 */
var ServletSession = exports.ServletSession = function(request) {

    var data;
    var volatileData;
    
    var servletRequest = request instanceof javax.servlet.ServletRequest ?
            request : request.env.servletRequest;

    function getSession() {
        return servletRequest.getSession();
    }

    /**
     * A container for things to store in this session between requests.
     */
    Object.defineProperty(this, "data", {
        get: function() {
            if (!data) {
                // session.data is a JavaAdapter that directly proxies property access
                // to the attributes in the servlet session object.
                data = new JavaAdapter(org.mozilla.javascript.NativeObject, {
                    put: function(name, start, value) {
                        getSession().setAttribute(name, value);
                    },
                    get: function(name, start) {
                        return getSession().getAttribute(name);
                    }
                });
            }
            return data;
        }
    });

    /**
     * True if this session was created in the current request.
     * This can be useful to find out if the client has cookies disabled
     * for cookie-based sessions.
     */
    Object.defineProperty(this, "isNew", {
        get: function() {
            return getSession().isNew();
        }
    });
    
    /**
     * Createtime of the current session.
     */
    Object.defineProperty(this, "creationTime", {
        get: function() {
            return getSession().getCreationTime();
        }
    });

    /**
     * A time interval in seconds, which the session will be open.
     * If the interval is exceeded, the session gets invalidated.
     */
    Object.defineProperty(this, "maxInactiveInterval", {
        get: function() {
            return getSession().getMaxInactiveInterval();
        },
        set: function(interval) {
            return getSession().setMaxInactiveInterval(interval); 
        }
    });
    
    /**
     * Time in Unix epoch milliseconds since the last client access.
     */
    Object.defineProperty(this, "lastAccessedTime", {
        get: function() {
            return getSession().getLastAccessedTime();
        }
    });

    /**
     * Destroys the current session and any data bound to it.
     */
    this.invalidate = function() {
        getSession().invalidate();
    };
    
    // save and reset the volatile session object
    volatileData = getSession().getAttribute("__volatileData__");
    getSession().setAttribute("__volatileData__", null);
    
    /**
     * A volatile property which survives a HTTP redirect and can be used
     * for warnings or error messages in forms. After a requests was handled,
     * the property is reset to null.
     */
    Object.defineProperty(this, "volatile", {
        get: function() {
            return volatileData;
        },
        set: function(value) {
            getSession().setAttribute("__volatileData__", value);
        }
    });
};
