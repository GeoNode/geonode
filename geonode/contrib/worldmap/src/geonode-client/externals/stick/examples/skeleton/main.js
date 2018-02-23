// Set up application
var {Application} = require("stick");

var app = exports.app = Application();
app.configure("notfound", "error", "static", "params", "mount");
app.static(module.resolve("public"));
app.mount("/", require("./actions"));

// export init(), start(), stop(), destroy() functions to get called
// on daemon life-cycle events

// Script to run app from command line
if (require.main === module) {
    require("ringo/httpserver").main(module.directory);
}
