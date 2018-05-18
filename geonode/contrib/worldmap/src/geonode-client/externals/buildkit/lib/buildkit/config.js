var FS = require("fs");

var SECTION_RE = /^\s*\[\s*(.+?)\s*\]\s*$/;
var PROPERTY_RE = /^\s*(\w+)\s*=\s*(.*?)\s*$/;
var VALUE_RE = /^\s*(\S+)\s*$/;
var BLANK_RE = /^\s*$/;

var parse = function(path) {
    var source = FS.read(path);
    var lines = source.split("\n");
    var sections = {};
    var match, section, list, value;
    lines.forEach(function(line, i) {
        match = line.match(SECTION_RE);
        if (match) {
            // new section
            section = {};
            sections[match[1]] = section;
        } else {
            // existing section or pre-section
            // check for new list
            match = line.match(PROPERTY_RE);
            if (match) {
                // new list
                list = [];
                section[match[1]] = list;
                // may have value on same line
                value = match[2];
                if (value) {
                    list.push(value);
                }
            } else {
                match = line.match(VALUE_RE);
                if (match) {
                    if (list) {
                        // new entry for list
                        list.push(match[1]);
                    } else {
                        throw "Bad config syntax, got value outside of list (line " + i + "): " + line;
                    }
                } else if (BLANK_RE.test(line)) {
                    // done with list
                    list = null;
                } else {
                    throw "Bad config syntax, expected list value (line " + i + "): " + line;
                }
            }
        }
    });
    return sections;
};

exports.parse = parse;
