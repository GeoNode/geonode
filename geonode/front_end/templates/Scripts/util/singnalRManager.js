var signalRManager = {
    manageSignalR: function(redirectLocation, loggedInUsername) {
        var closeExtraTabsHub = $.connection.closeExtraTabsHub;
        closeExtraTabsHub.client.closeThisTab = function () {
            window.isAutoLeave = true;
            window.location = redirectLocation;
        };

        function startSignalR() {
            closeExtraTabsHub.server.joinGroup(loggedInUsername);
            closeExtraTabsHub.server.closeExtraTabs(loggedInUsername);
        }

        $.connection.hub.start().done(function () {
            startSignalR();
        });

        $.connection.hub.disconnected(function () {
            setTimeout(function () {
                startSignalR();
            }, 5000);
        });
    }
};