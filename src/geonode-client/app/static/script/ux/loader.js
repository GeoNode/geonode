(function() {

    var jsfiles = new Array(
        "/static/src/script/ux/RowExpander.js",
        "/static/src/script/ux/fileuploadfield/FileUploadField.js",
        "/static/src/script/ux/colorpicker/color-picker.ux.js",
        "/static/src/script/ux/colorpicker/ColorManager.js"
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
