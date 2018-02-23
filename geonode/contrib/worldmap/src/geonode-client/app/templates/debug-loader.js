(function() {
    var jsfiles = [{{paths}}];

    var scripts = document.getElementsByTagName("script");
    var parts = scripts[scripts.length-1].src.split("/");
    parts.pop();
    var path = parts.join("/");

    var pieces = new Array(jsfiles.length);

    var src;
    for(var i=0; i<jsfiles.length; i++) {
        src = path + "/" + jsfiles[i];
        pieces[i] = "<script src='" + src + "'></script>";
    }
    document.write(pieces.join(""));
})();
