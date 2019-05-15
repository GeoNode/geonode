var path = require("path");

module.exports = {
    mouseposition: path.join(__dirname, "web", "client", "examples", "mouseposition", "app"),
    scalebar: path.join(__dirname, "web", "client", "examples", "scalebar", "app"),
    layertree: path.join(__dirname, "web", "client", "examples", "layertree", "app"),
    "3dviewer": path.join(__dirname, "web", "client", "examples", "3dviewer", "app"),
    queryform: path.join(__dirname, "web", "client", "examples", "queryform", "app"),
    featuregrid: path.join(__dirname, "web", "client", "examples", "featuregrid", "app"),
    print: path.join(__dirname, "web", "client", "examples", "print", "app"),
    login: path.join(__dirname, "web", "client", "examples", "login", "app"),
    plugins: path.join(__dirname, "web", "client", "examples", "plugins", "app"),
    rasterstyler: path.join(__dirname, "web", "client", "examples", "rasterstyler", "app"),
    api: path.join(__dirname, "web", "client", "examples", "api", "app")
    // this example is not linked and seems to cause a big slow down with uglyfyplugin. disabled temporary
    // styler: path.join(__dirname, "web", "client", "examples", "styler", "app")
};
