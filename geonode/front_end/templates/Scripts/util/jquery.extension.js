var ArrayContains = function (array, element) {
    return $.inArray(element, array) > -1;
};

var ArrayConainsAll = function (array, anotherArray) {
    var contains = true;

    if (!$.isArray(anotherArray)) {
        contains = false;
    } else if (anotherArray.length > array.length) {
        contains = false;
    } else {
        for (var i = 0; i < anotherArray.length; i++) {
            if (!ArrayContains(array, anotherArray[i])) {
                contains = false;
                break;
            }
        }
    }

    return contains;
};

var RemoveFromArray = function (array, item) {
    array.splice($.inArray(item, array), 1);
};

$.fn.ajaxDialog = function (options) {
    var $this = this;
    options.autoOpen = false;
    options.modal = true;
    options.position = 'center';

    $this.dialog(options).on("dialogopen", function () {
        $this.load(options.url, options.data, options.complete);
    });

    return $this;
};

var dialogBox = {
    confirm: function (options) {
        options = $.extend({
            'autoOpen': true, modal: true, text: "Are you sure you want to do this?", title: "Confirm", width: 'auto'
        }, options);

        var $dialogIcon = $("<span>").addClass("ui-icon ui-icon-alert").css({ "float": "left", "margin-right": "2px", "margin-top": "2px" });
        $("<span>").append($dialogIcon).append(options.title);

        var $dialogMessage = $("<span>").html(options.text);
        var $dialog = $("<div>").append($dialogMessage);

        options.buttons = [
                {
                    text: "Ok",
                    click: function () {
                        if (typeof (options.action) == "function") {
                            options.action();
                        }

                        $dialog.dialog("close").remove();
                    }
                },
                {
                    text: "Cancel",
                    click: function () {
                        $dialog.dialog("close").remove();
                    }
                }
        ];

        return $dialog.dialog(options);
    },

    message: function (options) {

        options = $.extend({
            autoOpen: true, modal: true, text: "Insert value", title: "Message", width: 'auto'
        }, options);

        var $dialogMessage = $("<span>").html(options.text);
        var $dialog = $("<div>").append($dialogMessage);

        options.buttons = [
                {
                    text: "Ok",
                    click: function () {
                        $dialog.dialog("close").remove();
                    }
                }
        ];

        return $dialog.dialog(options);
    },

    prompt: function (options) {
        options = $.extend({
            autoOpen: true, modal: true, text: "Insert value", title: "Input", width: 'auto'
        }, options);

        var $dialogMessage = $("<span>").html(options.text);
        var $inputBox = $("<input type='text'>");
        var $dialog = $("<div>").append($dialogMessage).append($inputBox);

        options.buttons = [
                {
                    text: "Ok",
                    click: function () {
                        var val = $inputBox.val();
                        if (typeof (options.action) == "function") {
                            options.action(val);
                        }

                        $dialog.dialog("close").remove();
                    }
                },
                {
                    text: "Cancel",
                    click: function () {
                        $dialog.dialog("close").remove();
                    }
                }
        ];

        return $dialog.dialog(options);
    },

    multiAction: function (options) {
        options = $.extend({
            'autoOpen': true, modal: true, text: "What do you want to do", title: "Choose", width: 'auto', canCancel: true, closeOnEscape: true, actions: {}
        }, options);

        var $dialogIcon = $("<span>").addClass("ui-icon ui-icon-alert").css({ "float": "left", "margin-right": "2px", "margin-top": "2px"});
        $("<span>").append($dialogIcon).append(options.title);

        var $dialogMessage = $("<span>").html(options.text);
        var $dialog = $("<div>").append($dialogMessage);

        options.buttons = [];
        for (var name in options.actions) {
            options.buttons.push({
                text: name,
                click: action(name)
            });
        }

        function action(actionName) {
            return function () {
                options.actions[actionName]();
                $dialog.dialog("close").remove();
            };
        }

        if (options.canCancel) {
            options.buttons.push({
                text: "Cancel",
                click: function () {
                    $dialog.dialog("close").remove();
                }
            });
        }


        return $dialog.dialog(options);
    }
};


