angular.module('Jantrik.Event', [])
.factory('jantrik.Event', [
    function () {
        return function Event() {
            var _thisEvent = this;
            var handlers = {};

            function getHandlerList(eventName) {
                eventName = (eventName || "").toLowerCase();
                if (!handlers[eventName]) {
                    handlers[eventName] = [];
                }

                return handlers[eventName];
            }

            this.register = function (eventName, handler) {
                var handlerList = getHandlerList(eventName);
                handlerList.push(handler);

                return _thisEvent;
            };

            this.broadcast = function (eventName) {
                var handlerList = getHandlerList(eventName);
                var eventData = Array.prototype.slice.call(arguments, 1);

                handlerList.forEach(function(handler) {
                    handler.apply(_thisEvent, eventData);
                });

                return _thisEvent;
            };

            this.unRegister = function (eventName, handler) {
                var handlerList = getHandlerList(eventName);
                var i = 0;
                for (; i < handlerList.length; i++) {
                    if (handlerList[i] === handler) {
                        break;
                    }   
                }

                handlerList.splice(i, 1);
                return _thisEvent;
            };
        };
    }
]);