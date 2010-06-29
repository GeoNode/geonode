(function() {

    var jsfiles = new Array(
        "/static/src/script/app/GeoExplorer.js",
        "/static/src/script/app/GeoNode/DataGrid.js",
        "/static/src/script/app/Lang.js",
        "/static/src/script/app/GeoExplorer/Viewer.js",
        "/static/src/script/app/ExportWizard.js",
        "/static/src/script/app/MapGrid.js",
        "/static/src/script/app/GeoNode/ConfigManager.js",
        "/static/src/script/app/GeoExplorer/CapabilitiesRowExpander.js",
        "/static/src/script/app/GeoExplorer/NewSourceWindow.js",
        "/static/src/script/app/GeoNode/SearchTable.js"
    );

    var appendable = !((/MSIE/).test(navigator.userAgent) ||
                       (/Safari/).test(navigator.userAgent));
    var pieces = new Array(jsfiles.length);

    var element = document.getElementsByTagName("head").length ?
                    document.getElementsByTagName("head")[0] :
                    document.body;
    var script;

    for(var i=0; i<jsfiles.length; i++) {
        if(!appendable) {
            pieces[i] = "<script src='" + jsfiles[i] + "'></script>"; 
        } else {
            script = document.createElement("script");
            script.src = jsfiles[i];
            element.appendChild(script);
        }
    }
    if(!appendable) {
        document.write(pieces.join(""));
    }
})();
