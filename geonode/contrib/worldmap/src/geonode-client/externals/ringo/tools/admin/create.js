/**
 * @fileoverview Script to create a new RingoJS web application.
 */

var {join, Path, makeDirectory, move, copy, exists, symbolicLink, base}
        = require('fs');
var engine = require('ringo/engine');
var shell = require('ringo/shell');
var Parser = require('ringo/args').Parser;

export('createApplication', 'createPackage', 'main', 'description');

/** @ignore */
var description = "Create a new RingoJS web application or package";

/**
 * Create a new RingoJS web application at the given path.
 * @param path the path where to create the application
 */
function createApplication(path, options) {
    var dest = getTargetDir(path);
    var home = engine.properties["ringo.home"];
    var skeletons = join(home, "tools", "admin", "skeletons");
    var appTemplate = options.googleAppengine ? "appengine"
                    : options.javaWebapp ? "webapp" : null;
    var appSource = options.appSource || join(skeletons, "app")

    if (appTemplate) {
        var symlink = Boolean(options.symlink);
        copyTree(join(skeletons, appTemplate), dest);
        // symlink app source if requested unless it's the skeleton app
        copyTree(appSource, join(dest, "WEB-INF", "app"), symlink && options.appSource);
        copyTree(join(home, "modules"), join(dest, "WEB-INF", "modules"), symlink);
        fixAppEngineDirs(dest);
        copyJars(home, dest, symlink);
    } else {
        copyTree(appSource, dest);
    }
}

/**
 * Create a new RingoJS package at the given path.
 * @param path the path where to create the package
 */
function createPackage(path, options) {
    var dest = getTargetDir(path);
    var home = engine.properties["ringo.home"];
    var source = join(home, "tools/admin/skeletons/package");
    copyTree(source, dest);
}

function copyTree(from, to, symlink) {
    var source = new Path(from);
    if (!source.exists() || !source.isDirectory()) {
        throw new Error("Can't find directory " + source);
    }
    var msg = symlink ? "Linking" : "Copying";
    shell.write(" +", msg, from, "to", to, "... ");
    if (symlink) {
        symbolicLink(source, to);
    } else {
        source.copyTree(to);
    }
    print("done");
}

function fixAppEngineDirs(dest) {
    var webinf = join(dest, "WEB-INF");
    makeDirectory(join(webinf, "lib"));
    makeDirectory(join(webinf, "packages"));
    var staticDir = join(webinf, "app", "static");
    if (exists(staticDir)) {
        move(staticDir, join(dest, "static"));
    }
}

function copyJars(home, dest, symlink) {
    var jars = [
        "ringo.jar",
        "ivy/rhino-1.7R3.jar",
        "ivy/jaffl-0.5.11.jar",
        "ivy/jnr-posix-1.1.8.jar"
    ];
    var libsrc = join(home, "lib");
    var libdest = join(dest, "WEB-INF", "lib");
    var msg = symlink ? "Linking" : "Copying";
    shell.write(" +", msg, "jar files to", libdest, "... ");
    for each (var jar in jars) {
        if (symlink) {
            symbolicLink(join(libsrc, jar), join(libdest, base(jar)));
        } else {
            copy(join(libsrc, jar), join(libdest, base(jar)));
        }
    }
    shell.writeln("done");
}

function getTargetDir(path) {
    if (!path) {
        throw new Error("No destination path given");
    }

    var dest = new Path(path);

    if (dest.exists() && !dest.isDirectory()) {
        throw dest + " exists but is not a directory.";
    } else if (dest.isDirectory() && dest.list().length > 0) {
        throw new Error("Directory " + dest + " exists but is not empty");
    }

    return dest;
}

/**
 * Create a new RingoJS web application from the command line.
 * @param args
 */
function main(args) {
    var script = args.shift();
    var parser = new Parser();
    parser.addOption("a", "app-source", "[DIR]", "Copy application from [DIR] instead of skeleton");
    parser.addOption("g", "google-appengine", null, "Create a new Google App Engine application");
    parser.addOption("p", "ringo-package", null, "Create a new Ringo package");
    parser.addOption("s", "symlink", null, "Create symbolic links for jar and module files");
    parser.addOption("w", "java-webapp", null, "Create a new Java Web application (WAR)");
    parser.addOption("h", "help", null, "Print help message and exit");
    var opts = parser.parse(args);
    if (opts.help) {
        print("Creates a Ringo application or package.");
        print("Usage:");
        print("  ringo-admin " + script + " [options] [path]");
        print("Options:");
        print(parser.help());
        return;
    }

    // undefined > boolean > number conversion FTW
    if (!!opts.googleAppengine + !!opts.ringoPackage + !!opts.javaWebapp > 1) {
        throw new Error("Options are mutually exclusive.");
    }

    var type;
    if (opts.googleAppengine) {
        type = "Google App Engine app";
    } else if (opts.ringoPackage) {
        type =  "Ringo package";
    } else if (opts.javaWebapp) {
        type = "Java web application";
    } else {
        type = "Ringo web application";
    }

    var path = args[0]
            || shell.readln("Path for new " + type + ": ");

    if (!path) {
        print("No path, exiting.");
    } else {
        print("Creating " + type + " in " + path);
        if (opts.ringoPackage) {
            createPackage(path, opts);
        } else {
            createApplication(path, opts);
        }
    }
}

if (require.main == module) {
    main(system.args);
}
