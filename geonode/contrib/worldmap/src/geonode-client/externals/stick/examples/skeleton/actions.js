var {Application} = require("stick");

export("app");

var app = Application();
app.configure("params", "route", "render");
app.render.base = module.resolve("templates");
app.render.master = "page.html";


app.get("/", function(request) {
    var context = {title: "It's working!"};
    return app.render("index.html", context);
});
