var {Application} = require("stick");
var helpers = require("stick/helpers");
var response = require("ringo/jsgi/response");

var app = exports.app = Application(),
    foo = module.resolve("foo"),
    home = module.resolve("app");

app.configure("route");

// Define an index route that takes optional name and ext arguments.
// Link to the other module's index action with the same name and ext.
app.get("/:name?.:ext?", function(req, name, ext) {
    return response.html(
        "<html><body><h1>Bar</h1>",
        "<p>This is module <b>'bar'</b> called with <b>", name, "</b>, <b>", ext, "</b>. ",
        "Go to ", helpers.linkTo(foo, {name: name, ext: ext}),
        " or back ", helpers.linkTo(home, {}, "home"), ".</p></body></html>"
    );
});
