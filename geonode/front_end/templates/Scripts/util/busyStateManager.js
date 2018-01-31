var busyStateManager = {
    isBusy: false,
    showBusyState: function (message) {
        this.isBusy = true;
        setMessage(message);
        getBusyStateShower().show();
    },
    hideBusyState: function () {
        this.isBusy = false;
        getBusyStateShower().text("");
        getBusyStateShower().hide();
    }
};

function setMessage(message) {
    getBusyStateShower().text(message);
}

function getBusyStateShower() {
    return $(".loading-message");
}