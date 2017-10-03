var cookieManager = {
    setCookie: function (name, value, exdays) {
        var d = new Date();
        d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
        var expires = "expires=" + d.toGMTString();
        document.cookie = name + "=" + value + "; " + expires;
    },

    getCookie: function (name) {
        name += "=";
        var ca = document.cookie.split(';');
        for (var i = 0; i < ca.length; i++) {
            var c = ca[i].trim();
            if (c.indexOf(name) == 0) return c.substring(name.length, c.length);
        }
        return "";
    },

    canShowMaintainaceMessage: function (id) {
        var maintainaceMessageId = cookieManager.getCookie("maintainaceMessageId");
        if (maintainaceMessageId == id || !id) {
            return false;
        }
        return true;
    },

    dontShowMaintainanceMessageAgain: function (id) {
        cookieManager.setCookie("maintainaceMessageId", id, 30);
    }
};





