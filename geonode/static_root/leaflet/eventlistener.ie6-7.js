// EventListener | MIT/GPL2 | github.com/jonathantneal/EventListener

!this.addEventListener && this.attachEvent && (function (window, document) {
	var registry = [];

	// add
	function addEventListener(type, listener) {
		var target = this;

		registry.unshift({
			__listener: function (event) {
				event.currentTarget = target;
				event.pageX = event.clientX + document.documentElement.scrollLeft;
				event.pageY = event.clientY + document.documentElement.scrollTop;
				event.preventDefault = function () { event.returnValue = false };
				event.relatedTarget = event.fromElement || null;
				event.stopPropagation = function () { event.cancelBubble = true };
				event.relatedTarget = event.fromElement || null;
				event.target = event.srcElement || target;
				event.timeStamp = +new Date;

				listener.call(target, event);
			},
			listener: listener,
			target: target,
			type: type
		});

		target.attachEvent("on" + type, registry[0].__listener);
	}

	// remove
	function removeEventListener(type, listener) {
		for (var index = 0, length = registry.length; index < length; ++index) {
			if (registry[index].target == this && registry[index].type == type && registry[index].listener == listener) {
				return this.detachEvent("on" + type, registry.splice(index, 1)[0].__listener);
			}
		}
	}

	// dispatch
	function dispatchEvent(eventObject) {
		try {
			return this.fireEvent("on" + eventObject.type, eventObject);
		} catch (error) {
			for (var index = 0, length = registry.length; index < length; ++index) {
				if (registry[index].target == this && registry[index].type == eventObject.type) {
					registry[index].__listener.call(this, eventObject);
				}
			}
		}
	}

	// custom
	function CustomEvent(type, canBubble, cancelable, detail) {
		var event = document.createEventObject(), key;

		event.type = type;
		event.returnValue = !cancelable;
		event.cancelBubble = !canBubble;

		for (key in detail) {
			event[key] = detail[key];
		}

		return event;
	}

	function _patchNode(node) {
		if (node.dispatchEvent) {
			return;
		}

		node.addEventListener = addEventListener;
		node.removeEventListener = removeEventListener;
		node.dispatchEvent = dispatchEvent;

		var appendChild = node.appendChild, createElement = node.createElement, insertBefore = node.insertBefore;

		if (appendChild) {
			node.appendChild = function (node) {
				var returnValue = appendChild(node);

				_patchNodeList(node.all);

				return returnValue;
			};
		}

		if (createElement) {
			node.createElement = function (nodeName) {
				var returnValue = createElement(nodeName);

				_patchNodeList(node.all);

				return returnValue;
			};
		}

		if (insertBefore) {
			node.insertBefore = function (node, referenceElement) {
				var returnValue = insertBefore(node, referenceElement);

				_patchNodeList(node.all);

				return returnValue;
			};
		}

		if ("innerHTML" in node) {
			node.attachEvent("onpropertychange", function (event) {
				if (event.propertyName != "innerHTML") return;

				_patchNodeList(node.all);
			});
		}
	}

	function _patchNodeList(nodeList) {
		for (var i = 0, node; node = nodeList[i]; ++i) {
			_patchNode(node);
		}
	}

	document.attachEvent("onreadystatechange", function (event) {
		if (document.readyState == "complete") {
			_patchNodeList(document.all);

			// ready
			document.dispatchEvent(new CustomEvent("DOMContentLoaded", false, false));
		}
	});

	_patchNode(window);
	_patchNode(document);

	_patchNodeList(document.all);

	window.CustomEvent = CustomEvent;
})(this, document);