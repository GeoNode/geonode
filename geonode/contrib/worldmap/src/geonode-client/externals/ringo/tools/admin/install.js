/**
 * @fileoverview Download and install a RingoJS package from a zip URL
 */

var system = require("system");
var shell = require("ringo/shell");
var fs = require("fs");
var files = require("ringo/utils/files");
var {ZipFile} = require("ringo/zip");
var {Parser} = require("ringo/args");
var strings = require('ringo/utils/strings');

export('installPackage', 'main', 'description');

/** @ignore */
var description = "Download and install a RingoJS package from a zip URL";

/**
 * Install package from the given zip url into the packages directory
 * @param {String} url the URL of a zipped package
 * @param {Object} options
 */
function installPackage(url, options) {
    var directory = (options && options.directory)
            || fs.join(system.prefix, "packages");
    // expand foo/bar to a github zipball url for user foo, project bar
    if (url.match(/^\w+\/[\w\-_\.]+$/)) {
        url = "http://github.com/" + url + "/zipball/master";
    }
    url = new java.net.URL(url);
    var temp = files.createTempFile("ringo-install", ".zip");
    try {
        print("Downloading " + url);
        var out = fs.openRaw(temp, {write: true});
        var stream = getUrlStream(url);
        new Stream(stream).copy(out).close();
        out.close();
        var zip = new ZipFile(temp);
        // get common prefix shared by all items in zip file
        var prefix = zip.entries.reduce(function(prev, current) {
            return strings.getCommonPrefix(prev, current);
        });
        // we assume package.json to be in prefix/package.json
        var json = prefix + "package.json";
        if (!zip.isFile(json)) {
            throw json + " not found in zip file";
        }
        var package = JSON.parse(zip.open(json).read().decodeToString("UTF-8"));
        var name = package.name
                || fail("package.json does not contain a package name");
        var dir = fs.join(directory, name);
        if (fs.exists(dir)) {
            if (!options.force)
                throw new Error("Package already installed: " + dir);
            print("Removing currently installed version of package " + name);
            fs.removeTree(dir);
        }
        print("Installing package '" + name + "' in " + dir);
        for each (var entry in zip.entries) {
            var path = fs.join(dir, entry.substring(prefix.length));
            if (zip.isDirectory(entry)) {
                fs.makeDirectory(path);
            } else {
                print(" + " + path);
                var parent = fs.directory(path);
                if (!fs.isDirectory(parent)) {
                     fs.makeTree(parent);
                }
                var dest = fs.openRaw(path, {write: true});
                zip.open(entry).copy(dest).close();
            }
            if (entry.time > -1) {
                fs.touch(path, entry.time);
            }
        }
        // create symlinks for binaries and make executable
        var bindir = fs.join(dir, "bin");
        if (fs.isDirectory(bindir)) {
            var ringoBin = fs.join(system.prefix, "bin");
            for each (var bin in fs.list(bindir)) {
                var binfile = fs.join(bindir, bin);
                fs.changePermissions(binfile, 0755);
                fs.symbolicLink(binfile, fs.join(ringoBin, bin));
            }
        }
        print("Done");
    } finally {
        if (fs.exists(temp)) {
            fs.remove(temp);
        }
    }
}

function fail(message) {
    throw message;
}

function getUrlStream(url) {
    var conn = url.openConnection();
    var status = conn.getResponseCode();
    // java.net.URLConnection won't follow redirects across different protocols (such as https -> http)
    // so we have to do that manually here
    // see http://bugs.sun.com/bugdatabase/view_bug.do?bug_id=4620571
    while (conn && status >= 301 && status <= 303) {
        // loop through headers to find location field. welcome to the middle ages
        for (var i = 1; ; i++) {
            var key = conn.getHeaderFieldKey(i);
            if (key == null || i == 50) {
                throw new Error("Failed to follow redirect: Location header not found");
            }
            if (key.toLowerCase() == "location") {
                url = new java.net.URL(conn.getHeaderField(i));
                conn = url.openConnection();
                status = conn.getResponseCode();
                break;
            }
        }
    }
    return new Stream(conn.getInputStream());
}

/**
 * Install a RingoJS package from a zip URL.
 * @param args
 */
function main(args) {
    var script = args.shift();
    var parser = new Parser();
    parser.addOption("f", "force", null, "Force install, even if package already exists");
    parser.addOption("d", "directory", "DIR", "Packages directory to install into");
    parser.addOption("h", "help", null, "Print help message and exit");
    var opts = parser.parse(args);
    if (opts.help) {
        print("Installs a Ringo package from a zip URL.");
        print("Usage:");
        print("  ringo-admin " + script + " [url]");
        print("Options:");
        print(parser.help());
        return;
    }

    var url = args[0]
            || shell.readln("URL of the zip file to install: ");

    if (!url) {
        print("No URL, exiting.");
    } else {
        installPackage(url, opts);
    }
}

if (require.main == module) {
    main(system.args);
}
