exports["test: buildkit"] = require("./test_buildkit");
exports["test: integration"] = require("./test_integration");

if (require.main == module || require.main == module.id) {
    require("test").run(exports);
}

