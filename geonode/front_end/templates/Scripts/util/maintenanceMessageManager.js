var maintenanceMessageManager = {
    ShowMessageIfPossible: function () {
        var currentMaitainanceId = $("#hidden-maintainance-id").val();

        if (cookieManager.canShowMaintainaceMessage(currentMaitainanceId)) {
            showMessage();
            addEventHandlerToCloseButton();
        } else {
            removeMessage();
        }

        function addEventHandlerToCloseButton() {
            $("#btn-close-message").click(function () {
                if ($("#checkbox-maintainance-message").is(":checked")) {
                    cookieManager.dontShowMaintainanceMessageAgain(currentMaitainanceId);
                }
                removeMessage();
            });
        }

        function showMessage() {
            var $maintenanceMessageDiv = $("#div-maintainance-message");
            $maintenanceMessageDiv.show();
        }

        function removeMessage() {
            $("#div-maintainance-message").remove();
        }
    }
};