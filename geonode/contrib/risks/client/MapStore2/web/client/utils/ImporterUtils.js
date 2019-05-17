module.exports = {
    getbsStyleForState: function(state) {
        switch (state) {
            case "NO_FORMAT":
            case "NO_CRS":
            case "BAD_FORMAT":
            case "NO_BOUNDS":
            case "ERROR":
            case "CANCELED":
            case "INIT_ERROR":
                return "danger";
            case "READY":
            case "PENDING":
                return "info";
            case "INIT":
            case "RUNNING":
                return "warning";
            case "COMPLETE":
                return "success";
            default:
                return "default";

        }
    }
};
