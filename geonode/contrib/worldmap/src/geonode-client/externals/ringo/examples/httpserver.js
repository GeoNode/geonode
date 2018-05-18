// Minimal hello-world HTTP server demo

exports.app = function(req) {
    return {
        status: 200,
        headers: {"Content-Type": "text/plain"},
        body: ["Hello World!"]
    };
};

if (require.main == module) {
    require("ringo/httpserver").main(module.id);
}
