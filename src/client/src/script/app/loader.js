(function() {

    var jsfiles = new Array(
        "../../src/script/app/GeoExplorer.js",
        "../../src/script/app/Lang.js",
        "../../src/script/app/Embed.js",
        "../../src/script/app/ExportWizard.js",
        "../../src/script/app/Page.js",
        "../../src/script/app/DeveloperPage.js",
        "../../src/script/app/DataPage.js",
        "../../src/script/app/HelpPage.js",
        "../../src/script/app/FeaturedPage.js",
        "../../src/script/app/CommunityPage.js",
        "../../src/script/app/IndexPage.js",
        "../../src/script/app/MapGrid.js",
        "../../src/script/app/GeoExplorer/CapabilitiesGrid.js",
        "../../src/script/app/GeoExplorer/CapabilitiesRowExpander.js",
        "../../src/script/app/GeoExplorer/GroupContainer.js",
        "../../src/script/app/GeoExplorer/GoogleEarthPanel.js",
        "../../src/script/app/GeoExplorer/util.js",
        "../../src/script/app/GeoExplorer/NewSourceWindow.js"
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
