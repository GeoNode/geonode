/**
 * @fileoverview Exports an EventEmitter classes that provide methods
 * to emit events and register event listener functions.
 */

defineClass(org.ringojs.wrappers.EventAdapter);

/**
 * This class provides methods to emit events and add or remove event listeners.
 *
 * The `EventEmitter` function can be used as constructor or as mix-in. Use the
 * `new` keyword to construct a new EventEmitter:
 *
 *     var emitter = new EventEmitter();
 *
 * To add event handling methods to an existing object, call or apply the
 * `EventEmitter` function with the object as `this`:
 *
 *     EventEmitter.call(object);
 */
var EventEmitter = exports.EventEmitter = function() {
    // if called on an object other than EventEmitter define properties
    if (!(this instanceof EventEmitter)) {
        Object.defineProperties(this, emitterImpl);
    }
};

/**
 * An adapter for dispatching Java events to Ringo. This class takes a Java
 * class or interface as argument and creates a Java object that extends or
 * implements the  class or interface and forwards method calls to event
 * listener functions registered using the EventEmitter methods.
 *
 * Like [EventEmitter](#EventEmitter), `JavaEventEmitter` can be used as
 * constructor or as mix-in. Use the `new` keyword to construct a new
 * JavaEventEmitter:
 *
 *     var emitter = new JavaEventEmitter(JavaClassOrInterface);
 *
 * To add event handling methods to an existing object, call or apply the
 * `JavaEventEmitter` function with the object as `this`:
 *
 *     JavaEventEmitter.call(object, JavaClassOrInterface);
 *
 * JavaEventEmitter accepts an object as optional second argument that maps
 * Java methods to event names. If the first argument is a Java class
 * this mapping also allows to select which methods should be overridden. If
 * called without event mapping the method name is used as event name, except
 * for methods like `onFoo` which will trigger event `foo`.
 *
 * @param classOrInterface a Java class or interface
 * @param eventMapping optional object mapping method names to event names.
 *     If this parameter is defined only methods whose name is a property
 *     key in the object will be overridden, and the event type will be
 *     set to the property value instead of the method name.
 */
exports.JavaEventEmitter = function(classOrInterface, eventMapping) {
    var e = new EventAdapter(classOrInterface, eventMapping);
    Object.defineProperties(this, {
        /**
         * The generated Java object. This implements the Java interface
         * passed to the `JavaEventEmitter` constructor and can be passed
         * to Java code that expects given interface.
         */
        impl: {
            value: e.impl
        },
        /**
         * Emit an event to all listeners registered for this event type
         * @param {string} type type the event type
         * @param {...} [args...] optional arguments to pass to the listeners
         * @return true if the event was handled by at least one listener, false otherwise
         * @throws Error if the event type was "error" and there were no listeners
         * @function
         */
        emit: {
            value: e.emit.bind(e)
        },
        /**
         * Add a listener function for the given event. The function will be
         * called asynchronously on the thread of the local event loop.
         * @param {string} type the event type
         * @param {function} listener the listener
         * @function
         */
        addListener: {
            value: e.addListener.bind(e)
        },
        /**
         * Add a listener function for the given event. This is a shortcut for
         * [addListener()](#EventEmitter.prototype.addListener)
         * @param {string} type the event type
         * @param {function} listener the listener
         * @function
         */
        on: {
            get: function() this.addListener
        },
        /**
         * Add a synchronous listener function for the given event. A
         * synchronous listener will be called by an outside thread instead
         * of the thread of the local event loop. This means it can be
         * called concurrently while this worker is running other code.
         * @param {string} type the event type
         * @param {function} listener the listener
         * @function
         */
        addSyncListener: {
            value: e.addSyncListener.bind(e)
        },
        /**
         * Remove a listener function for the given event.
         * @param {string} type the event type
         * @param {function} listener the listener
         * @function
         */
        removeListener: {
            value: e.removeListener.bind(e)
        }
    });
    return this;
};

var isArray = Array.isArray;

var emitterImpl = {
    /**
     * Emit an event to all listeners registered for this event type
     * @param {string} type type the event type
     * @param {...} [args...] optional arguments to pass to the listeners
     * @name EventEmitter.prototype.emit
     * @return true if the event was handled by at least one listener, false otherwise
     * @throws Error if the event type was "error" and there were no listeners
     * @function
     */
    emit: {
        value: function(type) {
            var args;
            var listeners = this._events ? this._events[type] : null;
            if (isArray(listeners) && !listeners.length) {
                listeners = null; // normalize empty listener array
            }
            if (typeof listeners === "function") {
                args = Array.slice(arguments, 1);
                listeners.apply(this, args);
                return true;
            } else if (isArray(listeners)) {
                args = Array.slice(arguments, 1);
                for (var i = 0; i < listeners.length; i++) {
                    listeners[i].apply(this, args);
                }
                return true;
            } else {
                return false;
            }
        }
    },
    /**
     * Add a listener function for the given event. This is a shortcut for
     * [addListener()](#EventEmitter.prototype.addListener)
     * @param {string} type the event type
     * @param {function} listener the listener
     * @returns this object for chaining
     * @name EventEmitter.prototype.on
     * @function
     */
    on: {
        get: function() this.addListener
    },
    /**
     * Add a listener function for the given event. This is a shortcut for
     * [addListener()](#EventEmitter.prototype.addListener)
     * @param {string} type the event type
     * @param {function} listener the listener
     * @returns this object for chaining
     * @name EventEmitter.prototype.on
     * @function
     */
    addListener: {
        value: function(type, listener) {
            if (typeof listener !== "function") {
                throw new Error ("Event listener must be a function");
            }

            if (!this._events) this._events = {};
            this.emit("newListener", type, listener);

            if (!this._events[type]) {
                // store as single function
                this._events[type] = listener;
            } else if (isArray(this._events[type])) {
                this._events[type].push(listener);
            } else {
                // convert to array
                this._events[type] = [this._events[type], listener];
            }

            return this;
        }
    },
    /**
     * Remove a listener function for the given event.
     * @param {string} type the event type
     * @param {function} listener the listener
     * @returns this object for chaining
     * @name EventEmitter.prototype.removeListener
     * @function
     */
    removeListener: {
        value: function(type, listener) {
            if (typeof listener !== "function") {
                throw new Error ("Event listener must be a function");
            }

            if (this._events && this._events[type]) {
                var listeners = this._events[type];
                if (listeners === listener) {
                    delete this._events[type];
                } else if (isArray(listeners)) {
                    var i = listeners.indexOf(listener);
                    if (i > -1) {
                        if (listeners.length === 1) {
                            this._events = null;
                        } else {
                            listeners.splice(i, 1);
                        }
                    }
                }
            }
            return this;
        }
    },
    /**
     * Remove all listener function for the given event.
     * @param {string} type the event type
     * @returns this object for chaining
     * @name EventEmitter.prototype.removeAllListeners
     * @function
     */
    removeAllListeners: {
        value: function(type) {
            if (type && this._events) this._events[type] = undefined;
            return this;
        }
    },
    /**
     * Get an array containing the listener functions for the given event.
     * If no listeners exist for the given event a new array is created.
     * Changes on the return value will be reflected in the EventEmitter instance.
     * @param {string} type the event type
     * @returns {array} the lister array
     * @name EventEmitter.prototype.listeners
     * @function
     */
    listeners: {
        value: function(type) {
            if (!this._events) {
                this._events = {};
            }
            if (!this._events[type]) {
                this._events[type] = [];
            } else if (!isArray(this._events[type])) {
                this._events[type] = [this._events[type]];
            }
            return this._events[type];
        }
    }
};

Object.defineProperties(EventEmitter.prototype, emitterImpl);
