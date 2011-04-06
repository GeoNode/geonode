var clientRequest = require("ringo/httpclient").request;
var Request = require("ringo/webapp/request").Request;
var MemoryStream = require("io").MemoryStream;
var merge = require("ringo/utils/objects").merge;
var responseForStatus = require("./util").responseForStatus;

var app = exports.app = function(env) {
    var response;
    var request = new Request(env);
    var url = request.queryParams.url;
    if (url) {
        response = proxyPass(request, url);
    } else {
        response = responseForStatus(400, "Request must contain url parameter.");
    }
    return response;
};

var pass = exports.pass = function(config) {
    if (typeof config == "string") {
        config = {url: config};
    }
    return function(env, match) {
        var request = new Request(env);
        var newUrl = config.url + match + (request.queryString ? "?" + request.queryString : "");
        return proxyPass(request, newUrl, config.preserveHost);
    };
};

function proxyPass(request, url, preserveHost) {
    var parts = url.split("/");
    var response;
    if (parts[0] !== (request.scheme + ":") || parts[1] !== "") {
        response = responseForStatus(400, "The url parameter value must be absolute url with same scheme as request.");
    } else {
        // re-issue request
        var host = parts[2];
        var exchange = clientRequest({
            url: url,
            method: request.method,
            headers: preserveHost ? merge({host: host}, request.headers) : request.headers,
            data: request.contentLength && request.input
        });
        exchange.wait();
        
        response = {
            status: exchange.status,
            headers: exchange.headers,
            body: new MemoryStream(exchange.contentBytes)
        };
    }
    return response;
}
