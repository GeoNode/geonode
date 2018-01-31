var jantrik = jantrik || { };
jantrik.EventPool = (function () {
    var events = {};

    function getHandlerList(eventName) {
        eventName = (eventName || "").toLowerCase();
        if (!events[eventName]) {
            events[eventName] = [];
        }

        return events[eventName];
    }

    function register(eventName, handler) {
        var handlerList = getHandlerList(eventName);
        handlerList.push(handler);

        return this;
    }

    function registerAll(eventNames, handler) {
        for (var i in eventNames) {
            register(eventNames[i], handler);
        }

        return this;
    }

    function broadcast(eventName) {
        var handlerList = getHandlerList(eventName);
        var eventData = Array.prototype.slice.call(arguments, 1);

        for (var i in handlerList) {
            handlerList[i].apply(this, eventData);
        }

        return this;
    }

    this.register = register;
    this.registerAll = registerAll;
    this.broadcast = broadcast;

    return this;
})();