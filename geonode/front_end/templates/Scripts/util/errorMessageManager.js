var errorMessageManager = {

    isUnclosableDialogOn: false,

    isUnexpectedErrorOn: false,

    isServerUnreachableErrorOn: false,

    unclosableDialogInstance: null,

    showInternetErrorMessage: function () {
        if (!errorMessageManager.isUnclosableDialogOn && !errorMessageManager.isUnexpectedErrorOn) {
            var title = "No internet connection!";
            var text = "You are currently disconnected from the internet. Please connect to the internet and try again.";
            errorMessageManager.showUnclosableDialog(title, text);
        }
    },

    showUnclosableDialog: function (title, text) {
        errorMessageManager.isUnclosableDialogOn = true,
        errorMessageManager.unclosableDialogInstance =
                dialogBox.multiAction({
                    title: title,
                    text: text,
                    actions: {
                    },
                    canCancel: false,
                    closeOnEscape: false,
                    open: function (event, ui) {
                        $("a.ui-dialog-titlebar-close", ui.dialog).remove();
                        $('.ui-widget-overlay', ui.dialog).click(function (e) {
                            e.preventDefault();
                            return false;
                        });
                    },
                    width: '340px',
                    resizable: false
                });
    },

    closeUnclosableDialog: function () {
        if (errorMessageManager.unclosableDialogInstance) {

            errorMessageManager.unclosableDialogInstance.dialog('close');

            errorMessageManager.unclosableDialogInstance = null;
            errorMessageManager.isUnclosableDialogOn = false;
        }
    },

    showServerUnreachableMessage: function () {
        if (!errorMessageManager.isUnclosableDialogOn && !errorMessageManager.isUnexpectedErrorOn) {
            var title = "Server unreachable!";
            var text = "The server is currently unreachable. Please wait for sometime to get the server back or try again later.";
            errorMessageManager.showUnclosableDialog(title, text);
        }
    },

    showUnexpectedErrorMessage: function () {
        if (!errorMessageManager.isUnclosableDialogOn && !errorMessageManager.isUnexpectedErrorOn) {
            errorMessageManager.isUnexpectedErrorOn = true;
            dialogBox.multiAction({
                title: "Unexpected error!",
                text: "An unexpected error occured. Please reload and try again.",
                actions: {
                    "Reload": function () {
                        location.reload();
                    },
                    "Cancel": function () {
                        errorMessageManager.isUnexpectedErrorOn = false;
                    }
                },
                canCancel: false
            });
        }
    }
};
