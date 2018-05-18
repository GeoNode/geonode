var FS = require("fs");
var MERGE = require("./merge");
var CONFIG = require("./config");
var exit = require("system").exit;
var compile;
try {
    compile = require("./closure").compile;
} catch (e) {
    // if Java 1.6 is not available, we can't use closure compiler
    compile = require("./jsmin").jsmin;
}

var parser = new (require("ringo/args").Parser)();

parser.addOption("l", "list", "","list files to be included in a build");
parser.addOption("o", "outdir", "outdir", "output directory for scripts");
parser.addOption("h", "help", "", "display this help message");

exports.main = function main(args) {

    var options = parser.parse(args);

    if (options.help || args.length < 1) {
        print("Builds concatenated and minified scripts from a JavaScript library.");
        print("build [options] config");
        print(parser.help());
        exit(1);
    }
    
    var config = args[0];
    if (!FS.isFile(config)) {
        print("Can't find config file: " + config);
        exit(1);
    }
    
    var sections = CONFIG.parse(config);
        
    var group, separator, ordered, concat, outfile;
    for (var section in sections) {
        group = sections[section];
        group.root = group.root.map(function(r) {
            return FS.join(FS.directory(config), r);
        });
        if (options.list) {
            ordered = MERGE.order(group).map(function(script) {
                return script.path;
            });
            print(section);
            print(section.replace(/./g, "-"));
            print(ordered.join("\n"));
            print();
        } else {
            concat = MERGE.concat(group);
            concat = compile(concat);
            outfile = section;
            if (options.outdir) {
                if (!FS.isDirectory(options.outdir)) {
                    FS.makeTree(options.outdir);
                }
                outfile = FS.join(options.outdir, outfile);
            }
            FS.write(outfile, concat);
        }
    }
    
};


if (module.id == require.main) {
    exports.main(system.args.slice(1));
}
