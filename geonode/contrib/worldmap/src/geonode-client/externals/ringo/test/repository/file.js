var {join} = require("fs");

importPackage(org.ringojs.repository);
var path = join(module.directory, "data");
var repo = new FileRepository(path);

require("./common").setup(exports, path, repo);

if (require.main == module.id) {
    require("test").run(exports);
}
