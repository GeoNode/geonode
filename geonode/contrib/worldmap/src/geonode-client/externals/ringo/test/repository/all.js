exports.testZip = require("./zip");
exports.testFile = require("./file");

if (require.main == module.id) {
    require("test").run(exports);
}
