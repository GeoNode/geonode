var clientRequest = require("ringo/httpclient").request;
var Headers = require("ringo/utils/http").Headers;
var MemoryStream = require("io").MemoryStream;
var objects = require("ringo/utils/objects");
var responseForStatus = require("../util").responseForStatus;

var URL = java.net.URL;

var app = exports.app = function(request) {
    var response;
    var url = request.queryParams.url;
    if (url) {
        response = proxyPass({
            request: request, 
            url: url
        });
    } else {
        response = responseForStatus(400, "Request must contain url parameter.");
    }
    return response;
};

var pass = exports.pass = function(config) {
    if (typeof config == "string") {
        config = {url: config};
    }
    return function(request) {
        var query = request.queryString;
        var path = request.pathInfo && request.pathInfo.substring(1) || "";
        var newUrl = config.url + path + (query ? "?" + query : "");
        return proxyPass(objects.merge({
            request: request, 
            url: newUrl
        }, config));
    };
};

var getUrlProps = exports.getUrlProps = function(url) {
    var o, props;
    try {
        o = new URL(url);
    } catch(err) {
        // pass
    }
    if (o) {
        var username, password;
        var userInfo = o.getUserInfo();
        if (userInfo) {
            // this could potentially be removed if the following ticket is closed
            // https://github.com/ringo/ringojs/issues/issue/121
            // but, it could make sense to keep it here as well
            [username, password] = userInfo.split(":");
            url = url.replace(userInfo + "@", "");
        }
        var port = o.getPort();
        if (port < 0) {
            port = null;
        }
        props = {
            url: url,
            scheme: o.getProtocol(),
            username: username || null,
            password: password || null,
            host: o.getHost(),
            port: port,
            path: o.getPath() || "/",
            query: o.getQuery(),
            hash: o.getRef()
        };
    }
    return props;
};

var createProxyRequestProps = exports.createProxyRequestProps = function(config) {
    var props;
    var request = config.request;
    var url = config.url;
    var urlProps = getUrlProps(url);
    if (urlProps) {
        var headers = new Headers(objects.clone(request.headers));
        if (!config.preserveHost) {
            headers.set("Host", urlProps.host + (urlProps.port ? ":" + urlProps.port : ""));
        }
        if (!config.allowAuth) {
            // strip authorization and cookie headers
            headers.unset("Authorization");
            headers.unset("Cookie");
        }
        var data;
        var method = request.method;
        if (method == "PUT" || method == "POST") {
            if (request.headers.get("content-length")) {
                data = request.input;
            }
        }
        props = {
            url: urlProps.url,
            method: request.method,
            scheme: urlProps.scheme,
            username: urlProps.username,
            password: urlProps.password,
            headers: headers,
            data: data
        };
    }
    return props;
};

function proxyPass(config) {
    var response;
    var outgoing = createProxyRequestProps(config);
    var incoming = config.request;
    if (!outgoing || outgoing.scheme !== incoming.scheme) {
        response = responseForStatus(400, "The url parameter value must be absolute url with same scheme as request.");
    } else {
        // re-issue request
        var exchange = clientRequest({
            url: outgoing.url,
            method: outgoing.method,
            username: outgoing.username,
            password: outgoing.password,
            headers: outgoing.headers,
            data: outgoing.data,
            async: false
        });
    }
    exchange.wait();
    var headers = new Headers(objects.clone(exchange.headers));
    if (!config.allowAuth) {
        // strip out authorization and cookie headers
        headers.unset("WWW-Authenticate");
        headers.unset("Set-Cookie");
    }
    return {
        status: exchange.status,
        headers: headers,
        body: new MemoryStream(exchange.contentBytes)
    };
}
