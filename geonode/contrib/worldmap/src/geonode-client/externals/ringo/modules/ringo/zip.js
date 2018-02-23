/**
 * @fileoverview This module provides classes to uncompress zip files and streams.
 * @since 0.5
 */

var fs = require('fs');
var {Stream} = require('io');

export('ZipFile', 'ZipIterator');

/**
 * A class to read and unpack a local zip file.
 * @param {String} path the location of the zip file
 */
function ZipFile(path) {
    var zipfile = new java.util.zip.ZipFile(path);
    var entries = [];
    var map = {};
    var e = zipfile.entries();
    while (e.hasMoreElements()) {
        var entry = e.nextElement();
        map[entry.name] = entry;
        entries.push(entry.name);
    }

    function getEntry(name) {
        var entry = map[name];
        if (!entry) {
            throw new Error("Invalid zip entry: " + name);
        }
        return entry;
    }

    /**
     * An array containing the names of all entries in this zip file.
     * @type Array
     */
    this.entries = entries;

    /**
     * Get an input stream to read the entry with the given name.
     * @param {String} name the entry name
     */
    this.open = function(name) {
        return new Stream(zipfile.getInputStream(getEntry(name)));
    };

    /**
     * Returns true if the entry with the given name represents a directory.
     * @param {String} name the entry name
     */
    this.isDirectory = function(name) {
        var entry = map[name];
        return entry && entry.isDirectory();
    };

    /**
     * Returns true if the entry with the given name represents a file.
     * @param {String} name the entry name
     */
    this.isFile = function(name) {
        var entry = map[name];
        return entry && !entry.isDirectory();
    };

    /**
     * Returns the uncompressed size in bytes in the given entry, or -1 if not known.
     * @param {String} name the entry name
     */
    this.getSize = function(name) {
        return getEntry(name).getSize();
    };

    /**
     * Returns the last modification timestamp of the given entry, or -1 if not available.
     * @param {String} name the entry name
     */
    this.getTime = function(name) {
        return getEntry(name).getTime();
    };

    /**
     * Close the zip file.
     */
    this.close = function() {
        zipfile.close();
    };
}

/**
 * A streaming iterator over a zip file or stream. Each item yielded
 * by this iterator is an input stream to read a single zip entry.
 * Each entry stream has additional name, isDirectory, isFile, size, and time
 * properties with the same semantics of the corresponding methods in ZipFile.
 * @param {Stream|String} resource an input stream or file name
 * @see #ZipFile
 */
function ZipIterator(resource) {
    var stream = typeof resource == "string" ?
            fs.openRaw(resource) : resource;
    var zipstream = new java.util.zip.ZipInputStream(stream);
    stream = new Stream(zipstream);
    try {
        var entry = zipstream.getNextEntry();
        while (entry) {
            stream.name = entry.getName();
            stream.isDirectory = entry.isDirectory();
            stream.isFile = !stream.isDirectory;
            stream.size = entry.getSize();
            stream.time = entry.getTime();
            yield stream;
            entry = zipstream.getNextEntry();
        }
    } finally {
        stream.close();
    }
}
