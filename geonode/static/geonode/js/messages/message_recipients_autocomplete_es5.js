"use strict";

function _toConsumableArray(arr) { return _arrayWithoutHoles(arr) || _iterableToArray(arr) || _unsupportedIterableToArray(arr) || _nonIterableSpread(); }

function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }

function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }

function _iterableToArray(iter) { if (typeof Symbol !== "undefined" && Symbol.iterator in Object(iter)) return Array.from(iter); }

function _arrayWithoutHoles(arr) { if (Array.isArray(arr)) return _arrayLikeToArray(arr); }

function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) { arr2[i] = arr[i]; } return arr2; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } }

function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); return Constructor; }

function get_users_data(data) {
  return data.objects.map(function (elem) {
    return {
      value: elem.username,
      id: elem.id
    };
  });
}

function get_groups_data(data) {
  return data.objects.map(function (elem) {
    return {
      value: elem.title,
      id: elem.id
    };
  });
}

var MessageRecipientsTags = /*#__PURE__*/function () {
  function MessageRecipientsTags(input, data_extract_func, url) {
    var blacklist = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : [];

    _classCallCheck(this, MessageRecipientsTags);

    if (input.tagName !== 'INPUT' || input.type !== 'text') {
      throw Error('Base element should be <input type="text">');
    }

    this.input = input;
    this.tagify = null;
    this.data_extract_func = data_extract_func;
    this.url = url;
    this.blacklist = blacklist;
    this.request_controller = null;
  }

  _createClass(MessageRecipientsTags, [{
    key: "init",
    value: function init() {
      this.tagify = new Tagify(this.input, {
        whitelist: [],
        blacklist: this.blacklist
      });
      this.tagify.on('input', this._onInputHandler.bind(this));
      this.request_controller = new AbortController();
    }
  }, {
    key: "_onInputHandler",
    value: function _onInputHandler(event) {
      var _this = this;

      var value = event.detail.value;
      this.tagify.settings.whitelist.length = 0;
      this.tagify.loading(true).dropdown.hide.call(this.tagify);
      this.request_controller.abort();
      this.request_controller = new AbortController();
      fetch(this.url + value, {
        signal: this.request_controller.signal
      }).then(function (response) {
        return response.json().then(_this.data_extract_func).then(function (res) {
          var _this$tagify$settings;

          res = res.filter(function (elem) {
            if (!_this.blacklist.includes(elem.value)) {
              return elem;
            }
          });

          (_this$tagify$settings = _this.tagify.settings.whitelist).splice.apply(_this$tagify$settings, [0, res.length].concat(_toConsumableArray(res)));

          _this.tagify.loading(false).dropdown.show.call(_this.tagify, value);
        });
      });
    }
  }, {
    key: "fixOutputValue",
    value: function fixOutputValue() {
      var _this2 = this;

      if (this.input.value !== '') {
        JSON.parse(this.input.value).filter(function (elem) {
          return 'id' in elem;
        }).forEach(function (elem) {
          $('<input>').attr({
            type: 'hidden',
            id: 'foo',
            name: _this2.input.name,
            value: elem.id
          }).appendTo('form');
        });
      }

      this.input.disabled = true;
    }
  }]);

  return MessageRecipientsTags;
}();
//# sourceMappingURL=message_recipients_autocomplete_es5.js.map
