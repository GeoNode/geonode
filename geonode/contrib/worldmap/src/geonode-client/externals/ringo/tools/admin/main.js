
function main(args) {
    args.shift();
    if (!args.length || args[0] == "main") {
        printUsage();
    } else {
        var module;
        try {
            module = require("./" + args[0]);
        } catch (error) {
            printUsage();
            return;
        }
        module.main(args);
    }
}

function printUsage() {
    var resources = getRepository("./").getResources();
    print("Please specify one of the following commands:");
    for each(var res in resources.sort()) {
        if (res.baseName != "main") {
            var description = require(res.moduleName).description;
            print("   ", res.baseName, "\t-", description || "no description available");
        }
    }
}

if (require.main == module.id) {
    main(system.args);
}