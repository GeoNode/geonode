var fs = require('fs');
var {GREEN, BLUE, writeln} = require('ringo/term');

var filename = module.path;

// text streams have an iterator that reads the next line
var file = fs.open(filename);  // text mode
file.forEach(function(line) {
   writeln(GREEN, line);
});

// binary streams read into ByteArrays/ByteStrings
file = fs.open(filename, {binary: true});
writeln(BLUE, file.read())
