#!/usr/bin/env ringo

var actions = require("./actions");
var response = require("ringo/jsgi/response");

// Minimalistic request dispatcher in lieu of a proper framework
exports.app = function(request) {
    var path = request.pathInfo.slice(1) || "index";
    // 1. resolve against actions
    if (typeof actions[path] === "function") {
        return actions[path](request);
    }
    // 2. resolve against public folder
    var resource = getResource("./public/" + path);
    if (resource.exists()) {
        return response.static(resource);
    }
    // 3. return 404 response
    return response.notFound(request.pathInfo);
}

// main script to start application
if (require.main == module) {
    require("ringo/httpserver").main(module.id);
}
