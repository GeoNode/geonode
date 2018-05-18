var response = require('ringo/jsgi/response');
var mustache = require('ringo/mustache');

exports.index = function (req) {
    var template = getResource("./templates/index.html").content;
    return response.html(
        mustache.to_html(template, {
            title: "It's working!"
        })
    );
};
