/**
 * @fileoverview <p>This module provides generic logging support for Ringo
 * applications. It uses <a href="http://www.slf4j.org/">SLF4J</a> or
 * <a href="http://logging.apache.org/log4j/">Apache log4j</a> if either is
 * detected in the classpath, and will fall back to java.util.logging
 * otherwise.<p>
 *
 * <p>If the first argument passed to any of the logging methods is a string
 * containing any number of curly bracket pairs ({}), the logger will interpret
 * it as format string and use any following arguments to replace the curly
 * bracket pairs. If an argument is an Error or Java Exception object, the
 * logger will render a stack trace for it and append it to the log message.</p>
 *
 * <p>This module's exports object implements the [EventEmitter](../events/)
 * interface and emits logged messages using the log level name as event type.</p>
 */

var strings = require('ringo/utils/strings');
var {EventEmitter} = require('ringo/events');

export('getLogger', 'setConfig', 'getScriptStack', 'getJavaStack');

var configured = false;
// interval id for configuration watcher
var configWatcher;

var verbose = require('ringo/engine').getRhinoEngine().getConfig().isVerbose();

// Make exports object emit log events
EventEmitter.call(exports);

/**
 * Logger class. This constructor is not exported, use this module's
 * {@link getLogger} to get a logger instance.
 * @param name the Logger name
 * @param impl the logger implementation
 * @constructor
 * @name Logger
 * @see #getLogger()
 */
function Logger(name, impl) {

    this.trace = function() {
        if (impl.isTraceEnabled()) {
            var msg = formatMessage(arguments);
            impl.trace(msg);
            exports.emit("trace", name, msg);
        }
    };

    this.debug = function() {
        if (impl.isDebugEnabled()) {
            var msg = formatMessage(arguments);
            impl.debug(msg);
            exports.emit("debug", name, msg);
        }
    };

    this.info = function() {
        if (impl.isInfoEnabled()) {
            var msg = formatMessage(arguments);
            impl.info(msg);
            exports.emit("info", name, msg);
        }
    };

    this.warn = function() {
        if (impl.isWarnEnabled()) {
            var msg = formatMessage(arguments);
            impl.warn(msg);
            exports.emit("warn", name, msg);
        }
    };

    this.error = function() {
        if (impl.isErrorEnabled()) {
            var msg = formatMessage(arguments);
            impl.error(msg);
            exports.emit("error", name, msg);
        }
    };

    /**
     * @function
     */
    this.isTraceEnabled = impl.isTraceEnabled.bind(impl);

    /**
     * @function
     */
    this.isDebugEnabled = impl.isDebugEnabled.bind(impl);

    /**
     * @function
     */
    this.isInfoEnabled = impl.isInfoEnabled.bind(impl);

    /**
     * @function
     */
    this.isWarnEnabled = impl.isWarnEnabled.bind(impl);

    /**
     * @function
     */
    this.isErrorEnabled = impl.isErrorEnabled.bind(impl);
}

/**
 * Configure log4j using the given file resource.
 *
 * If you plan to update the configuration make sure to set the
 * reset property to true in your configuration file.
 *
 * @param {Resource} resource the configuration resource in XML or properties format
 * @param {Boolean} watchForUpdates if true a scheduler thread is started that
 * repeatedly checks the resource for updates.
 */
function setConfig(resource, watchForUpdates) {
    var {path, url} = resource;
    var PropertyConfigurator = org.apache.log4j.PropertyConfigurator;
    var DOMConfigurator = org.apache.log4j.xml.DOMConfigurator;
    var configurator = strings.endsWith(path, '.properties') || strings.endsWith(path, '.props') ?
                       PropertyConfigurator : DOMConfigurator;
    if (typeof configurator.configure === "function") {
        configurator.configure(url);
        if (watchForUpdates) {
            try {
                // set up a scheduler to watch the configuration file for changes
                var {setInterval, clearInterval} = require("./scheduler");
                var lastModified = resource.lastModified();
                if (configWatcher) {
                    clearInterval(configWatcher);
                }
                configWatcher = setInterval(function() {
                    if (resource.exists() && resource.lastModified() != lastModified) {
                        lastModified = resource.lastModified();
                        configurator.configure(url);
                    }
                }, 3000);
            } catch (e) {
                print("Error watching log configuration file:", e);
            }
        }
    }
    configured = true;
};

/**
 * Get a logger for the given name.
 * @param {string} name the name of the logger
 * @returns {Logger} a logger instance for the given name
 */
function getLogger(name) {
    name = name.replace(/\//g, '.');
    var impl = new LoggerImpl(name);
    return new Logger(name, impl);
}

function formatMessage(args) {
    var message = strings.format.apply(null, args);
    for each (var arg in args) {
        if (arg instanceof Error || arg instanceof java.lang.Throwable) {
            message  = [
                message,
                getScriptStack(arg, "\nScript stack:\n"),
                verbose ? getJavaStack(arg, "Java stack:\n") : null
            ].join('');
        }
    }
    return message;
}

/**
 * Get a rendered JavaScript stack trace from a caught error.
 * @param {Error} error an error object
 * @param {String} prefix to prepend to result if available
 * @return {String} the rendered JavaScript stack trace
 */
function getScriptStack(error, prefix) {
    prefix = prefix || "";
    if (error && error.stack)
        return prefix + error.stack;
    return "";
}

/**
 * Get a rendered JavaScript stack trace from a caught error.
 * @param {Error} error an error object
 * @param {String} prefix to prepend to result if available
 * @return {String} the rendered JavaScript stack trace
 */
function getJavaStack(error, prefix) {
    prefix = prefix || "";
    var exception = error && error.rhinoException ?
        error.rhinoException : error;
    if (exception instanceof java.lang.Throwable) {
        var writer = new java.io.StringWriter();
        var printer = new java.io.PrintWriter(writer);
        exception.printStackTrace(printer);
        return prefix + writer.toString();
    }
    return "";
}

/**
 * Logger implementation based on java.util.logging
 * @param name the logger name
 */
function JdkLogger(name) {

    var log = java.util.logging.Logger.getLogger(name);
    var Level = java.util.logging.Level;

    this.trace = function(msg) {
        log.logp(Level.FINEST, null, null, msg);
    };

    this.debug = function(msg) {
        log.logp(Level.FINE, null, null, msg);
    };

    this.info = function(msg) {
        log.logp(Level.INFO, null, null, msg);
    };

    this.warn = function(msg) {
        log.logp(Level.WARNING, null, null, msg);
    };

    this.error = function(msg) {
        log.logp(Level.SEVERE, null, null, msg);
    };

    this.isTraceEnabled = function() {
        return log.isLoggable(Level.FINEST);
    };

    this.isDebugEnabled = function() {
        return log.isLoggable(Level.FINE);
    };

    this.isInfoEnabled = function() {
        return log.isLoggable(Level.INFO);
    };

    this.isWarnEnabled = function() {
        return log.isLoggable(Level.WARNING);
    };

    this.isErrorEnabled = function() {
        return log.isLoggable(Level.SEVERE);
    };
}

/**
 * Logger implementation based on log4j
 * @param name the logger name
 */
function Log4jLogger(name) {

    if (!configured) {
        setConfig(getResource('config/log4j.properties'));
    }
    var Level = org.apache.log4j.Level;
    var log = org.apache.log4j.LogManager.getLogger(name);

    this.trace = function(msg) {
        // TODO: older versions of log4j don't support trace
        log.trace(msg);
    };

    this.debug = function(msg) {
        log.debug(msg);
    };

    this.info = function(msg) {
        log.info(msg);
    };

    this.warn = function(msg) {
        log.warn(msg);
    };

    this.error = function(msg) {
        log.error(msg);
    };

    this.isTraceEnabled = function() {
        return log.isTraceEnabled();
    };

    this.isDebugEnabled = function() {
        return log.isDebugEnabled();
    };

    this.isInfoEnabled = function() {
        return log.isInfoEnabled();
    };

    this.isWarnEnabled = function() {
        return log.isEnabledFor(Level.WARN);
    };

    this.isErrorEnabled = function() {
        return log.isEnabledFor(Level.ERROR);
    };
}

/**
 * Logger implementation based on SLF4J
 * @param name the logger name
 */
function Slf4jLogger(name) {

    if (!configured) {
        setConfig(getResource('config/log4j.properties'));
    }
    var log = org.slf4j.LoggerFactory.getLogger(name);

    this.trace = function(msg) {
        log.trace(msg);
    };

    this.debug = function(msg) {
        log.debug(msg);
    };

    this.info = function(msg) {
        log.info(msg);
    };

    this.warn = function(msg) {
        log.warn(msg);
    };

    this.error = function(msg) {
        log.error(msg);
    };

    this.isTraceEnabled = function() {
        return log.isTraceEnabled();
    };

    this.isDebugEnabled = function() {
        return log.isDebugEnabled();
    };

    this.isInfoEnabled = function() {
        return log.isInfoEnabled();
    };

    this.isWarnEnabled = function() {
        return log.isWarnEnabled();
    };

    this.isErrorEnabled = function() {
        return log.isErrorEnabled();
    };
}

var LoggerImpl;
if (typeof org.slf4j.LoggerFactory.getLogger === "function") {
    LoggerImpl = Slf4jLogger;
} else if (typeof org.apache.log4j.LogManager.getLogger === "function") {
    LoggerImpl = Log4jLogger;
} else {
    LoggerImpl = JdkLogger;
}