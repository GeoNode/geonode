var MyHazard = Ext.extend(Ext.util.Observable, {
    constructor: function (config) {
        this.initialConfig = config;
        Ext.apply(this, this.initialConfig);
        this.addEvents(
            "ready"
        );

        this.load();
    },

    load: function() {
        alert("Loaded MyHazard!")
    }
});
