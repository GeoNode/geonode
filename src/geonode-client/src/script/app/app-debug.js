(function() {

    var jsfiles = new Array(
        "/static/src/script/app/GeoNode/DataGrid.js",
        "/static/src/script/app/GeoNode/SearchTable.js",
        "/static/src/script/app/GeoNode/BatchDownloadWidget.js",
        "/static/src/script/app/GeoNode/BoundingBoxWidget.js",
        "/static/src/script/app/GeoNode/DataCart.js",
        "/static/src/script/app/GeoNode/DataCartOps.js",
        "/static/src/script/app/GeoNode/DataCartStore.js",
        "/static/src/script/app/GeoNode/SearchTableRowExpander.js",
        "/static/src/script/app/GeoNode/MapSearchTable.js",
        "/static/src/script/app/GeoNode/PermissionsEditor.js",
        "/static/src/script/app/Lang.js"
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
